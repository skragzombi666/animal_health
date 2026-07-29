from __future__ import annotations

import json
import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, cast

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import (
    ADMINISTRATION_ROUTES,
    ATTR_ANTIGEN,
    ATTR_BATCH_NUMBER,
    ATTR_CUSTOM_SYMPTOM,
    ATTR_CUSTOM_VACCINATION_TARGET,
    ATTR_DOSE,
    ATTR_DOSE_UNIT,
    ATTR_MEDICATION_NAME,
    ATTR_NOTES,
    ATTR_ROUTE,
    ATTR_SEVERITY,
    ATTR_SYMPTOM,
    ATTR_VACCINATION_TARGETS,
    ATTR_VACCINE_NAME,
    ATTR_WEIGHT,
    ATTR_WEIGHT_UNIT,
    DATABASE_NAME,
    DOSE_UNITS,
    DOMAIN,
    EVENT_TYPE_CARE,
    EVENT_TYPE_MEDICATION,
    EVENT_TYPE_OBSERVATION,
    EVENT_TYPE_VACCINATION,
    EVENT_TYPE_VETERINARY_VISIT,
    EVENT_TYPE_WEIGHT,
    SYMPTOM_SEVERITIES,
    SYMPTOMS,
    VACCINATION_TARGETS,
    WEIGHT_UNITS,
)
from .runtime import AnimalHealthRuntimeData
from .task_kinds import task_kind_label, task_language
from .task_records import (
    ATTR_CARE_ACTION,
    ATTR_CHECK_RESULT,
    ATTR_DEVIATION_REASON,
    ATTR_DIAGNOSIS,
    ATTR_OUTCOME,
    ATTR_PERFORMED_AT,
    ATTR_PROVIDER,
    ATTR_SCHEDULED_DATE,
    ATTR_TASK_ENTITY_ID,
    ATTR_VISIT_REASON,
    HEALTH_CHECK_RESULTS,
    SERVICE_RECORD_TASK_CARE,
    SERVICE_RECORD_TASK_HEALTH_CHECK,
    SERVICE_RECORD_TASK_MEDICATION,
    SERVICE_RECORD_TASK_REMINDER,
    SERVICE_RECORD_TASK_VACCINATION,
    SERVICE_RECORD_TASK_VETERINARY_VISIT,
    SERVICE_RECORD_TASK_WEIGHT,
    TASK_KIND_CARE,
    TASK_KIND_HEALTH_CHECK,
    TASK_KIND_MEDICATION,
    TASK_KIND_REMINDER,
    TASK_KIND_VACCINATION,
    TASK_KIND_VETERINARY_VISIT,
    TASK_KIND_WEIGHT,
    TaskRecordStore,
    actual_health_check,
    actual_medication,
    actual_vaccination,
)

ATTR_OCCURRENCE_ID = "occurrence_id"
_TASK_SWITCH_UNIQUE_ID_PREFIX = "task_active_"

_ERROR_MESSAGES = {
    "integration_not_loaded": {
        "de": "Animal Health ist nicht geladen.",
        "en": "Animal Health is not loaded.",
    },
    "invalid_task_switch": {
        "de": "Die ausgewählte Entität ist kein Animal-Health-Aufgabenschalter.",
        "en": "The selected entity is not an Animal Health task switch.",
    },
    "task_and_occurrence_mutually_exclusive": {
        "de": "Entweder eine Aufgabe oder eine Fälligkeits-ID angeben, nicht beides.",
        "en": "Use either a task selection or an occurrence ID, not both.",
    },
    "choose_task_or_occurrence": {
        "de": "Eine Aufgabe auswählen oder eine Fälligkeits-ID eingeben.",
        "en": "Select a task or enter an occurrence ID.",
    },
    "selected_task_missing": {
        "de": "Die ausgewählte Aufgabe existiert nicht mehr.",
        "en": "The selected task no longer exists.",
    },
    "no_matching_open_occurrence": {
        "de": "Für die ausgewählte Aufgabe gibt es keine passende offene Fälligkeit.",
        "en": "No matching open occurrence exists for the selected task.",
    },
    "occurrence_missing": {
        "de": "Die ausgewählte Aufgabenfälligkeit existiert nicht mehr.",
        "en": "The selected task occurrence no longer exists.",
    },
    "wrong_task_kind": {
        "de": (
            "Die ausgewählte Aufgabe hat die Aufgabenart „{actual_kind}“, "
            "erwartet wird „{expected_kind}“."
        ),
        "en": (
            "The selected task has the kind “{actual_kind}”; "
            "“{expected_kind}” is required."
        ),
    },
    "occurrence_not_pending": {
        "de": (
            "Die ausgewählte Aufgabenfälligkeit ist bereits „{status}“ "
            "und nicht mehr offen."
        ),
        "en": (
            "The selected task occurrence is already “{status}” "
            "and is no longer pending."
        ),
    },
}


def _validation_error(
    hass: HomeAssistant,
    message_key: str,
    **placeholders: str,
) -> ServiceValidationError:
    language = task_language(
        getattr(hass.config, "language", "en"),
        getattr(hass.config, "country", None),
    )
    template = _ERROR_MESSAGES[message_key][language]
    return ServiceValidationError(template.format(**placeholders))


def _wrong_task_kind_error(
    hass: HomeAssistant,
    actual_kind: str,
    expected_kind: str,
) -> ServiceValidationError:
    language = task_language(
        getattr(hass.config, "language", "en"),
        getattr(hass.config, "country", None),
    )
    return _validation_error(
        hass,
        "wrong_task_kind",
        actual_kind=task_kind_label(actual_kind, language),
        expected_kind=task_kind_label(expected_kind, language),
    )


def _required_text(value: Any) -> str:
    text = cv.string(value).strip()
    if not text:
        raise vol.Invalid("value must not be empty")
    return text


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = cv.string(value).strip()
    return text or None


def _optional_number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    number = vol.Coerce(float)(value)
    if number <= 0:
        raise vol.Invalid("value must be greater than zero")
    return number


def _positive_number(value: Any) -> float:
    number = vol.Coerce(float)(value)
    if number <= 0:
        raise vol.Invalid("value must be greater than zero")
    return number


def _optional_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(cv.string(value))
    except ValueError as err:
        raise vol.Invalid("date and time must use ISO format") from err


def _optional_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(cv.string(value))
    except ValueError as err:
        raise vol.Invalid("date must use YYYY-MM-DD") from err


def _optional_list(value: Any) -> list[str] | None:
    if value in (None, "", []):
        return None
    return [str(item) for item in cv.ensure_list(value)]


def _performed_at_utc(hass: HomeAssistant, value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC).replace(microsecond=0)
    if value.tzinfo is None:
        timezone = dt_util.get_time_zone(hass.config.time_zone) or UTC
        value = value.replace(tzinfo=timezone)
    return value.astimezone(UTC).replace(microsecond=0)


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise _validation_error(hass, "integration_not_loaded")


def _task_id_from_entity(hass: HomeAssistant, entity_id: str) -> str:
    entry = er.async_get(hass).async_get(entity_id)
    if (
        entry is None
        or entry.domain != "switch"
        or entry.platform != DOMAIN
        or not entry.unique_id.startswith(_TASK_SWITCH_UNIQUE_ID_PREFIX)
    ):
        raise _validation_error(hass, "invalid_task_switch")
    return entry.unique_id.removeprefix(_TASK_SWITCH_UNIQUE_ID_PREFIX)


async def _resolve_occurrence_id(
    hass: HomeAssistant,
    store: TaskRecordStore,
    data: dict[str, Any],
    expected_kind: str,
) -> str:
    occurrence_id = data.get(ATTR_OCCURRENCE_ID)
    task_entity_id = data.get(ATTR_TASK_ENTITY_ID)
    if occurrence_id and task_entity_id:
        raise _validation_error(hass, "task_and_occurrence_mutually_exclusive")
    if occurrence_id:
        return str(occurrence_id)
    if not task_entity_id:
        raise _validation_error(hass, "choose_task_or_occurrence")
    task_id = _task_id_from_entity(hass, str(task_entity_id))
    try:
        config = await store.get_task_config(task_id)
    except KeyError as err:
        raise _validation_error(hass, "selected_task_missing") from err
    if config.task_kind != expected_kind:
        raise _wrong_task_kind_error(hass, config.task_kind, expected_kind)
    try:
        return await store.resolve_occurrence(
            task_id,
            data.get(ATTR_SCHEDULED_DATE),
        )
    except KeyError as err:
        raise _validation_error(hass, "no_matching_open_occurrence") from err


async def _load_occurrence_plan(
    hass: HomeAssistant,
    occurrence_id: str,
) -> dict[str, Any]:
    database_path = Path(hass.config.path(DATABASE_NAME))
    return await hass.async_add_executor_job(
        _load_occurrence_plan_sync,
        database_path,
        occurrence_id,
    )


def _load_occurrence_plan_sync(
    database_path: Path,
    occurrence_id: str,
) -> dict[str, Any]:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        row = connection.execute(
            """
            SELECT
                occurrence.task_id,
                occurrence.status,
                task.title AS task_title,
                COALESCE(config.task_kind, 'reminder') AS task_kind,
                COALESCE(plan.planned_json, config.template_json, '{}') AS planned_json
            FROM task_occurrences AS occurrence
            JOIN tasks AS task ON task.id = occurrence.task_id
            LEFT JOIN task_record_configs AS config ON config.task_id = task.id
            LEFT JOIN task_occurrence_plans AS plan ON plan.occurrence_id = occurrence.id
            WHERE occurrence.id = ?
            """,
            (occurrence_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise KeyError(occurrence_id)
    planned = json.loads(str(row["planned_json"] or "{}"))
    return {
        "task_id": str(row["task_id"]),
        "task_title": str(row["task_title"]),
        "task_kind": str(row["task_kind"]),
        "status": str(row["status"]),
        "planned": planned if isinstance(planned, dict) else {},
    }


_COMMON_SCHEMA = {
    vol.Optional(ATTR_OCCURRENCE_ID): _required_text,
    vol.Optional(ATTR_TASK_ENTITY_ID): _required_text,
    vol.Optional(ATTR_SCHEDULED_DATE): _optional_date,
    vol.Optional(ATTR_PERFORMED_AT): _optional_datetime,
    vol.Optional(ATTR_DEVIATION_REASON): _optional_text,
    vol.Optional(ATTR_NOTES): _optional_text,
}

RECORD_REMINDER_SCHEMA = vol.Schema(dict(_COMMON_SCHEMA))
RECORD_WEIGHT_SCHEMA = vol.Schema(
    {
        **_COMMON_SCHEMA,
        vol.Required(ATTR_WEIGHT): _positive_number,
        vol.Optional(ATTR_WEIGHT_UNIT, default="kg"): vol.In(WEIGHT_UNITS),
    }
)
RECORD_MEDICATION_SCHEMA = vol.Schema(
    {
        **_COMMON_SCHEMA,
        vol.Optional(ATTR_MEDICATION_NAME): _optional_text,
        vol.Optional(ATTR_DOSE): _optional_number,
        vol.Optional(ATTR_DOSE_UNIT): vol.In(DOSE_UNITS),
        vol.Optional(ATTR_ROUTE): vol.In(ADMINISTRATION_ROUTES),
    }
)
RECORD_VACCINATION_SCHEMA = vol.Schema(
    {
        **_COMMON_SCHEMA,
        vol.Optional(ATTR_VACCINATION_TARGETS): vol.All(
            _optional_list,
            vol.Any(None, [vol.In(VACCINATION_TARGETS)]),
        ),
        vol.Optional(ATTR_CUSTOM_VACCINATION_TARGET): _optional_text,
        vol.Optional(ATTR_VACCINE_NAME): _optional_text,
        vol.Optional(ATTR_ANTIGEN): _optional_text,
        vol.Optional(ATTR_DOSE): _optional_number,
        vol.Optional(ATTR_DOSE_UNIT): vol.In(DOSE_UNITS),
        vol.Optional(ATTR_ROUTE): vol.In(ADMINISTRATION_ROUTES),
        vol.Optional(ATTR_BATCH_NUMBER): _optional_text,
    }
)
RECORD_HEALTH_CHECK_SCHEMA = vol.Schema(
    {
        **_COMMON_SCHEMA,
        vol.Required(ATTR_CHECK_RESULT): vol.In(HEALTH_CHECK_RESULTS),
        vol.Optional(ATTR_SYMPTOM): vol.In(SYMPTOMS),
        vol.Optional(ATTR_CUSTOM_SYMPTOM): _optional_text,
        vol.Optional(ATTR_SEVERITY): vol.In(SYMPTOM_SEVERITIES),
    }
)
RECORD_CARE_SCHEMA = vol.Schema(
    {
        **_COMMON_SCHEMA,
        vol.Optional(ATTR_CARE_ACTION): _optional_text,
        vol.Optional(ATTR_OUTCOME): _optional_text,
    }
)
RECORD_VETERINARY_VISIT_SCHEMA = vol.Schema(
    {
        **_COMMON_SCHEMA,
        vol.Optional(ATTR_VISIT_REASON): _optional_text,
        vol.Optional(ATTR_PROVIDER): _optional_text,
        vol.Optional(ATTR_DIAGNOSIS): _optional_text,
    }
)


def async_setup_task_record_services(hass: HomeAssistant) -> None:
    store = TaskRecordStore(hass)

    async def _context(
        call: ServiceCall,
        expected_kind: str,
    ) -> tuple[str, dict[str, Any], datetime]:
        occurrence_id = await _resolve_occurrence_id(
            hass,
            store,
            call.data,
            expected_kind,
        )
        try:
            context = await _load_occurrence_plan(hass, occurrence_id)
        except KeyError as err:
            raise _validation_error(hass, "occurrence_missing") from err
        if context["task_kind"] != expected_kind:
            raise _wrong_task_kind_error(
                hass,
                str(context["task_kind"]),
                expected_kind,
            )
        if context["status"] != "pending":
            raise _validation_error(
                hass,
                "occurrence_not_pending",
                status=str(context["status"]),
            )
        return (
            occurrence_id,
            context,
            _performed_at_utc(hass, call.data.get(ATTR_PERFORMED_AT)),
        )

    async def _finish(result: Any) -> ServiceResponse:
        runtime_data = _runtime_data(hass)
        await runtime_data.coordinator.async_request_refresh()
        return result.as_dict()

    async def handle_record_reminder(call: ServiceCall) -> ServiceResponse:
        occurrence_id, _context_data, performed_at = await _context(
            call,
            TASK_KIND_REMINDER,
        )
        try:
            result = await store.execute(
                occurrence_id=occurrence_id,
                expected_kind=TASK_KIND_REMINDER,
                performed_at=performed_at,
                actual={"result": "completed"},
                notes=call.data.get(ATTR_NOTES),
                deviation_reason=call.data.get(ATTR_DEVIATION_REASON),
                event_type=None,
                event_title=None,
            )
        except (KeyError, ValueError) as err:
            raise ServiceValidationError(str(err)) from err
        return await _finish(result)

    async def handle_record_weight(call: ServiceCall) -> ServiceResponse:
        occurrence_id, _context_data, performed_at = await _context(
            call,
            TASK_KIND_WEIGHT,
        )
        actual = {
            "weight": call.data[ATTR_WEIGHT],
            "weight_unit": call.data[ATTR_WEIGHT_UNIT],
        }
        try:
            result = await store.execute(
                occurrence_id=occurrence_id,
                expected_kind=TASK_KIND_WEIGHT,
                performed_at=performed_at,
                actual=actual,
                notes=call.data.get(ATTR_NOTES),
                deviation_reason=call.data.get(ATTR_DEVIATION_REASON),
                event_type=EVENT_TYPE_WEIGHT,
                event_title="weight_measurement",
                event_value=call.data[ATTR_WEIGHT],
                event_unit=call.data[ATTR_WEIGHT_UNIT],
                event_data={"measurement": "weight"},
            )
        except (KeyError, ValueError) as err:
            raise ServiceValidationError(str(err)) from err
        return await _finish(result)

    async def handle_record_medication(call: ServiceCall) -> ServiceResponse:
        occurrence_id, context, performed_at = await _context(
            call,
            TASK_KIND_MEDICATION,
        )
        try:
            actual, event_data, dose, unit, medication_name = actual_medication(
                context["planned"],
                medication_name=call.data.get(ATTR_MEDICATION_NAME),
                dose=call.data.get(ATTR_DOSE),
                dose_unit=call.data.get(ATTR_DOSE_UNIT),
                route=call.data.get(ATTR_ROUTE),
            )
            result = await store.execute(
                occurrence_id=occurrence_id,
                expected_kind=TASK_KIND_MEDICATION,
                performed_at=performed_at,
                actual=actual,
                notes=call.data.get(ATTR_NOTES),
                deviation_reason=call.data.get(ATTR_DEVIATION_REASON),
                event_type=EVENT_TYPE_MEDICATION,
                event_title=medication_name,
                event_value=dose,
                event_unit=unit,
                event_data=event_data,
            )
        except (KeyError, ValueError) as err:
            raise ServiceValidationError(str(err)) from err
        return await _finish(result)

    async def handle_record_vaccination(call: ServiceCall) -> ServiceResponse:
        occurrence_id, context, performed_at = await _context(
            call,
            TASK_KIND_VACCINATION,
        )
        try:
            actual, event_data, dose, unit, title = actual_vaccination(
                context["planned"],
                vaccination_targets=call.data.get(ATTR_VACCINATION_TARGETS),
                custom_target=call.data.get(ATTR_CUSTOM_VACCINATION_TARGET),
                vaccine_name=call.data.get(ATTR_VACCINE_NAME),
                antigen=call.data.get(ATTR_ANTIGEN),
                dose=call.data.get(ATTR_DOSE),
                dose_unit=call.data.get(ATTR_DOSE_UNIT),
                route=call.data.get(ATTR_ROUTE),
                batch_number=call.data.get(ATTR_BATCH_NUMBER),
            )
            result = await store.execute(
                occurrence_id=occurrence_id,
                expected_kind=TASK_KIND_VACCINATION,
                performed_at=performed_at,
                actual=actual,
                notes=call.data.get(ATTR_NOTES),
                deviation_reason=call.data.get(ATTR_DEVIATION_REASON),
                event_type=EVENT_TYPE_VACCINATION,
                event_title=title,
                event_value=dose,
                event_unit=unit,
                event_data=event_data,
            )
        except (KeyError, ValueError) as err:
            raise ServiceValidationError(str(err)) from err
        return await _finish(result)

    async def handle_record_health_check(call: ServiceCall) -> ServiceResponse:
        occurrence_id, _context_data, performed_at = await _context(
            call,
            TASK_KIND_HEALTH_CHECK,
        )
        try:
            actual, event_type, title, event_data = actual_health_check(
                result=call.data[ATTR_CHECK_RESULT],
                symptom=call.data.get(ATTR_SYMPTOM),
                custom_symptom=call.data.get(ATTR_CUSTOM_SYMPTOM),
                severity=call.data.get(ATTR_SEVERITY),
                notes=call.data.get(ATTR_NOTES),
            )
            result = await store.execute(
                occurrence_id=occurrence_id,
                expected_kind=TASK_KIND_HEALTH_CHECK,
                performed_at=performed_at,
                actual=actual,
                notes=call.data.get(ATTR_NOTES),
                deviation_reason=call.data.get(ATTR_DEVIATION_REASON),
                event_type=event_type,
                event_title=title,
                event_data=event_data,
            )
        except (KeyError, ValueError) as err:
            raise ServiceValidationError(str(err)) from err
        return await _finish(result)

    async def handle_record_care(call: ServiceCall) -> ServiceResponse:
        occurrence_id, context, performed_at = await _context(
            call,
            TASK_KIND_CARE,
        )
        care_action = (
            call.data.get(ATTR_CARE_ACTION)
            or context["planned"].get("care_action")
            or context["task_title"]
        )
        actual = {"care_action": care_action}
        if outcome := call.data.get(ATTR_OUTCOME):
            actual["outcome"] = outcome
        try:
            result = await store.execute(
                occurrence_id=occurrence_id,
                expected_kind=TASK_KIND_CARE,
                performed_at=performed_at,
                actual=actual,
                notes=call.data.get(ATTR_NOTES),
                deviation_reason=call.data.get(ATTR_DEVIATION_REASON),
                event_type=EVENT_TYPE_CARE,
                event_title=str(care_action),
                event_data=actual,
            )
        except (KeyError, ValueError) as err:
            raise ServiceValidationError(str(err)) from err
        return await _finish(result)

    async def handle_record_veterinary_visit(call: ServiceCall) -> ServiceResponse:
        occurrence_id, context, performed_at = await _context(
            call,
            TASK_KIND_VETERINARY_VISIT,
        )
        visit_reason = (
            call.data.get(ATTR_VISIT_REASON)
            or context["planned"].get("visit_reason")
            or context["task_title"]
        )
        actual: dict[str, Any] = {"visit_reason": visit_reason}
        if provider := call.data.get(ATTR_PROVIDER) or context["planned"].get("provider"):
            actual["provider"] = provider
        if diagnosis := call.data.get(ATTR_DIAGNOSIS):
            actual["diagnosis"] = diagnosis
        try:
            result = await store.execute(
                occurrence_id=occurrence_id,
                expected_kind=TASK_KIND_VETERINARY_VISIT,
                performed_at=performed_at,
                actual=actual,
                notes=call.data.get(ATTR_NOTES),
                deviation_reason=call.data.get(ATTR_DEVIATION_REASON),
                event_type=EVENT_TYPE_VETERINARY_VISIT,
                event_title=str(visit_reason),
                event_data=actual,
            )
        except (KeyError, ValueError) as err:
            raise ServiceValidationError(str(err)) from err
        return await _finish(result)

    registrations = (
        (SERVICE_RECORD_TASK_REMINDER, handle_record_reminder, RECORD_REMINDER_SCHEMA),
        (SERVICE_RECORD_TASK_WEIGHT, handle_record_weight, RECORD_WEIGHT_SCHEMA),
        (
            SERVICE_RECORD_TASK_MEDICATION,
            handle_record_medication,
            RECORD_MEDICATION_SCHEMA,
        ),
        (
            SERVICE_RECORD_TASK_VACCINATION,
            handle_record_vaccination,
            RECORD_VACCINATION_SCHEMA,
        ),
        (
            SERVICE_RECORD_TASK_HEALTH_CHECK,
            handle_record_health_check,
            RECORD_HEALTH_CHECK_SCHEMA,
        ),
        (SERVICE_RECORD_TASK_CARE, handle_record_care, RECORD_CARE_SCHEMA),
        (
            SERVICE_RECORD_TASK_VETERINARY_VISIT,
            handle_record_veterinary_visit,
            RECORD_VETERINARY_VISIT_SCHEMA,
        ),
    )
    for service_name, handler, schema in registrations:
        hass.services.async_register(
            DOMAIN,
            service_name,
            handler,
            schema=schema,
            supports_response=SupportsResponse.ONLY,
        )
