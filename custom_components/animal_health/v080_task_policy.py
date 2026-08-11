from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from . import task_record_creation, task_service_schema
from .const import (
    ATTR_NOTES,
    DATABASE_NAME,
    DOMAIN,
    EVENT_TYPE_OBSERVATION,
    EVENT_TYPE_TREATMENT,
)
from .task_record_services import (
    ATTR_OCCURRENCE_ID,
    _load_occurrence_plan,
    _optional_date,
    _optional_datetime,
    _optional_text,
    _performed_at_utc,
    _required_text,
    _resolve_occurrence_id,
    _runtime_data,
)
from .task_records import (
    ATTR_DEVIATION_REASON,
    ATTR_PERFORMED_AT,
    ATTR_SCHEDULED_DATE,
    ATTR_TASK_ENTITY_ID,
    SERVICE_RECORD_TASK_REMINDER,
    TASK_KIND_REMINDER,
    TaskRecordStore,
)
from .task_kinds import TASK_KIND_TREATMENT

ATTR_DOCUMENT_IN_TIMELINE = "document_in_timeline"
ATTR_TREATMENT_ACTION = "treatment_action"
ATTR_TREATMENT_OUTCOME = "outcome"
SERVICE_RECORD_TASK_TREATMENT = "record_task_treatment"

RECORD_REMINDER_V080_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_OCCURRENCE_ID): _required_text,
        vol.Optional(ATTR_TASK_ENTITY_ID): _required_text,
        vol.Optional(ATTR_SCHEDULED_DATE): _optional_date,
        vol.Optional(ATTR_PERFORMED_AT): _optional_datetime,
        vol.Optional(ATTR_DEVIATION_REASON): _optional_text,
        vol.Optional(ATTR_NOTES): _optional_text,
        vol.Optional(ATTR_DOCUMENT_IN_TIMELINE, default=False): cv.boolean,
    }
)

RECORD_TREATMENT_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_OCCURRENCE_ID): _required_text,
        vol.Optional(ATTR_TASK_ENTITY_ID): _required_text,
        vol.Optional(ATTR_SCHEDULED_DATE): _optional_date,
        vol.Optional(ATTR_PERFORMED_AT): _optional_datetime,
        vol.Optional(ATTR_DEVIATION_REASON): _optional_text,
        vol.Optional(ATTR_NOTES): _optional_text,
        vol.Optional(ATTR_TREATMENT_ACTION): _optional_text,
        vol.Optional(ATTR_TREATMENT_OUTCOME): _optional_text,
    }
)


def _install_treatment_template_support() -> None:
    if getattr(task_record_creation, "_animal_health_v080_treatment_patch", False):
        return
    original = task_record_creation.build_task_template

    def build_task_template(
        task_kind: str,
        data: dict[str, Any],
        *,
        title: str,
        current: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if task_kind == TASK_KIND_TREATMENT:
            action = str((current or {}).get("treatment_action") or title).strip()
            if not action:
                raise ValueError("A treatment description is required")
            return {"treatment_action": action}
        return original(task_kind, data, title=title, current=current)

    task_record_creation.build_task_template = build_task_template
    task_record_creation._animal_health_v080_treatment_patch = True


def _install_task_description_support() -> None:
    if getattr(task_service_schema, "_animal_health_v080_description_patch", False):
        return
    original = task_service_schema.task_record_descriptions

    def descriptions(language: str) -> dict[str, dict[str, Any]]:
        german = language.startswith("de")
        result = original(language)
        create = result.get("create_record_task", {})
        options = (
            create.get("fields", {})
            .get("task_kind", {})
            .get("selector", {})
            .get("select", {})
            .get("options", [])
        )
        if not any(option.get("value") == TASK_KIND_TREATMENT for option in options):
            options.append(
                {
                    "value": TASK_KIND_TREATMENT,
                    "label": "Behandlung" if german else "Treatment",
                }
            )

        reminder = result.get(SERVICE_RECORD_TASK_REMINDER)
        if reminder is not None:
            fields = reminder.setdefault("fields", {})
            ordered: dict[str, Any] = {}
            for key, value in fields.items():
                if key == "deviation_reason":
                    ordered[ATTR_DOCUMENT_IN_TIMELINE] = {
                        "name": (
                            "Erledigung in Chronik dokumentieren"
                            if german
                            else "Document completion in timeline"
                        ),
                        "description": (
                            "Nur für tierbezogene generische Erinnerungen. Gesundheitlich relevante Aufgaben werden immer automatisch dokumentiert."
                            if german
                            else "Only for animal-specific generic reminders. Health-relevant tasks are always documented automatically."
                        ),
                        "default": False,
                        "selector": {"boolean": {}},
                    }
                ordered[key] = value
            reminder["fields"] = ordered
            reminder["description"] = (
                "Dokumentiert die Ausführung einer reinen Erinnerung. Bei tierbezogenen Erinnerungen kann optional ein Eintrag im Aktivitätsverlauf erzeugt werden."
                if german
                else "Records completion of a reminder. Animal-specific reminders may optionally create an activity-timeline entry."
            )

        common = original(language)[SERVICE_RECORD_TASK_REMINDER]["fields"]
        treatment_fields: dict[str, Any] = {}
        for key in ("task_entity_id", "scheduled_date", "occurrence_id", "performed_at"):
            treatment_fields[key] = common[key]
        treatment_fields[ATTR_TREATMENT_ACTION] = {
            "name": "Durchgeführte Behandlung" if german else "Treatment performed",
            "description": (
                "Die tatsächlich durchgeführte Behandlung; standardmässig wird der Aufgabentitel verwendet."
                if german
                else "The treatment actually performed; the task title is used by default."
            ),
            "selector": {"text": {}},
        }
        treatment_fields[ATTR_TREATMENT_OUTCOME] = {
            "name": "Ergebnis" if german else "Outcome",
            "description": (
                "Optionales Ergebnis der Behandlung."
                if german
                else "Optional treatment outcome."
            ),
            "selector": {"text": {"multiline": True}},
        }
        for key in ("deviation_reason", "notes"):
            treatment_fields[key] = common[key]
        result[SERVICE_RECORD_TASK_TREATMENT] = {
            "name": "Behandlungsaufgabe ausführen" if german else "Record treatment task",
            "description": (
                "Dokumentiert die Behandlung verpflichtend in der Gesundheitschronik und erledigt die Fälligkeit atomar."
                if german
                else "Documents the treatment in the health timeline and completes the occurrence atomically."
            ),
            "fields": treatment_fields,
        }
        return result

    task_service_schema.task_record_descriptions = descriptions
    task_service_schema._animal_health_v080_description_patch = True


def _insert_optional_reminder_event_sync(
    database_path: Path,
    occurrence_id: str,
    performed_at: datetime,
    notes: str | None,
    deviation_reason: str | None,
) -> dict[str, Any] | None:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        row = connection.execute(
            """
            SELECT
                occurrence.task_id,
                occurrence.scheduled_for,
                task.animal_id,
                task.title AS task_title
            FROM task_occurrences AS occurrence
            JOIN tasks AS task ON task.id = occurrence.task_id
            WHERE occurrence.id = ?
            """,
            (occurrence_id,),
        ).fetchone()
        if row is None:
            raise KeyError(occurrence_id)
        if row["animal_id"] is None:
            return None
        linked = connection.execute(
            "SELECT id FROM events WHERE task_occurrence_id = ?",
            (occurrence_id,),
        ).fetchone()
        if linked is not None:
            return None

        existing = {
            str(item[0]) for item in connection.execute("SELECT id FROM events").fetchall()
        }
        from .database import AnimalHealthDatabase

        event_id = AnimalHealthDatabase._generate_record_id("EV", existing)
        performed_at = performed_at.astimezone(UTC).replace(microsecond=0)
        now = datetime.now(UTC).replace(microsecond=0).isoformat()
        data = {
            "source": "task_occurrence",
            "generic_reminder": True,
            "documented_by_user": True,
            "task_execution": {
                "source": "task_occurrence",
                "task_id": str(row["task_id"]),
                "task_title": str(row["task_title"]),
                "task_kind": TASK_KIND_REMINDER,
                "occurrence_id": occurrence_id,
                "scheduled_for": str(row["scheduled_for"]),
                "performed_at": performed_at.isoformat(),
                "actual": {"result": "completed"},
                "deviation_reason": deviation_reason,
            },
        }
        connection.execute(
            """
            INSERT INTO events (
                id,
                animal_id,
                event_type,
                occurred_at,
                title,
                notes,
                value,
                unit,
                correction_of_event_id,
                data_json,
                task_id,
                task_occurrence_id,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?, ?, ?, ?)
            """,
            (
                event_id,
                str(row["animal_id"]),
                EVENT_TYPE_OBSERVATION,
                performed_at.isoformat(),
                str(row["task_title"]),
                notes,
                json.dumps(data, ensure_ascii=False, sort_keys=True),
                str(row["task_id"]),
                occurrence_id,
                now,
            ),
        )
        return {
            "id": event_id,
            "animal_id": str(row["animal_id"]),
            "event_type": EVENT_TYPE_OBSERVATION,
            "occurred_at": performed_at.isoformat(),
            "title": str(row["task_title"]),
            "notes": notes,
            "task_id": str(row["task_id"]),
            "task_occurrence_id": occurrence_id,
            "data": data,
        }
    finally:
        connection.close()


async def _context(
    hass: HomeAssistant,
    store: TaskRecordStore,
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
        raise ServiceValidationError(str(err)) from err
    if context["task_kind"] != expected_kind:
        raise ServiceValidationError(f"This occurrence is not a {expected_kind} task")
    if context["status"] != "pending":
        raise ServiceValidationError("Occurrence is not pending")
    return (
        occurrence_id,
        context,
        _performed_at_utc(hass, call.data.get(ATTR_PERFORMED_AT)),
    )


def async_setup_v080_task_policy(hass: HomeAssistant) -> None:
    _install_treatment_template_support()
    _install_task_description_support()
    store = TaskRecordStore(hass)

    async def handle_record_reminder(call: ServiceCall) -> ServiceResponse:
        occurrence_id, _context_data, performed_at = await _context(
            hass, store, call, TASK_KIND_REMINDER
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
            response = result.as_dict()
            if call.data.get(ATTR_DOCUMENT_IN_TIMELINE):
                event = await hass.async_add_executor_job(
                    _insert_optional_reminder_event_sync,
                    Path(hass.config.path(DATABASE_NAME)),
                    occurrence_id,
                    performed_at,
                    call.data.get(ATTR_NOTES),
                    call.data.get(ATTR_DEVIATION_REASON),
                )
                response["event"] = event
        except (KeyError, ValueError) as err:
            raise ServiceValidationError(str(err)) from err
        await _runtime_data(hass).coordinator.async_request_refresh()
        return response

    async def handle_record_treatment(call: ServiceCall) -> ServiceResponse:
        occurrence_id, context, performed_at = await _context(
            hass, store, call, TASK_KIND_TREATMENT
        )
        action = str(
            call.data.get(ATTR_TREATMENT_ACTION)
            or context.get("planned", {}).get("treatment_action")
            or context.get("task_title")
            or "Behandlung"
        ).strip()
        outcome = call.data.get(ATTR_TREATMENT_OUTCOME)
        actual: dict[str, Any] = {"treatment_action": action}
        if outcome:
            actual["outcome"] = outcome
        try:
            result = await store.execute(
                occurrence_id=occurrence_id,
                expected_kind=TASK_KIND_TREATMENT,
                performed_at=performed_at,
                actual=actual,
                notes=call.data.get(ATTR_NOTES),
                deviation_reason=call.data.get(ATTR_DEVIATION_REASON),
                event_type=EVENT_TYPE_TREATMENT,
                event_title=action,
                event_data={
                    "treatment_action": action,
                    **({"outcome": outcome} if outcome else {}),
                },
            )
        except (KeyError, ValueError) as err:
            raise ServiceValidationError(str(err)) from err
        await _runtime_data(hass).coordinator.async_request_refresh()
        return result.as_dict()

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECORD_TASK_REMINDER,
        handle_record_reminder,
        schema=RECORD_REMINDER_V080_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RECORD_TASK_TREATMENT,
        handle_record_treatment,
        schema=RECORD_TREATMENT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
