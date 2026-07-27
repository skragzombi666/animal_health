from __future__ import annotations

from datetime import date, time
from typing import Any, cast

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import (
    ADMINISTRATION_ROUTES,
    DOSE_UNITS,
    DOMAIN,
    VACCINATION_TARGETS,
)
from .runtime import AnimalHealthRuntimeData
from .task_records import (
    ATTR_PLANNED_ANTIGEN,
    ATTR_PLANNED_CARE_ACTION,
    ATTR_PLANNED_CHECK_FOCUS,
    ATTR_PLANNED_CUSTOM_VACCINATION_TARGET,
    ATTR_PLANNED_DOSE,
    ATTR_PLANNED_DOSE_UNIT,
    ATTR_PLANNED_MEDICATION_NAME,
    ATTR_PLANNED_PROVIDER,
    ATTR_PLANNED_ROUTE,
    ATTR_PLANNED_VACCINATION_DOSE,
    ATTR_PLANNED_VACCINATION_DOSE_UNIT,
    ATTR_PLANNED_VACCINATION_ROUTE,
    ATTR_PLANNED_VACCINATION_TARGETS,
    ATTR_PLANNED_VACCINE_NAME,
    ATTR_PLANNED_VISIT_REASON,
    ATTR_TASK_KIND,
    TASK_KIND_REMINDER,
    TASK_KINDS,
    TaskRecordStore,
    build_task_template,
)
from .task_store import (
    RECURRENCE_TYPES,
    TASK_SCOPE_ANIMAL,
    TASK_SCOPE_GENERAL,
)

SERVICE_CREATE_RECORD_TASK = "create_record_task"

ATTR_TASK_SCOPE = "task_scope"
ATTR_DEVICE_ID = "device_id"
ATTR_DEVICE_IDS = "device_ids"
ATTR_TITLE = "title"
ATTR_DESCRIPTION = "description"
ATTR_RECURRENCE_TYPE = "recurrence_type"
ATTR_RECURRENCE_INTERVAL = "recurrence_interval"
ATTR_START_DATE = "start_date"
ATTR_END_DATE = "end_date"
ATTR_DUE_TIME = "due_time"


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


def _text_list(value: Any) -> list[str]:
    result: list[str] = []
    for item in cv.ensure_list(value):
        text = _required_text(item)
        if text not in result:
            result.append(text)
    return result


def _positive_integer(value: Any) -> int:
    number = vol.Coerce(int)(value)
    if number < 1:
        raise vol.Invalid("value must be at least 1")
    return number


def _positive_number(value: Any) -> float:
    number = vol.Coerce(float)(value)
    if number <= 0:
        raise vol.Invalid("value must be greater than zero")
    return number


def _date_value(value: Any) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(cv.string(value))
    except ValueError as err:
        raise vol.Invalid("date must use YYYY-MM-DD") from err


def _time_value(value: Any) -> time:
    if isinstance(value, time):
        return value.replace(second=0, microsecond=0)
    try:
        return time.fromisoformat(cv.string(value)).replace(second=0, microsecond=0)
    except ValueError as err:
        raise vol.Invalid("time must use HH:MM") from err


CREATE_RECORD_TASK_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_TASK_SCOPE, default=TASK_SCOPE_ANIMAL): vol.In(
            (TASK_SCOPE_ANIMAL, TASK_SCOPE_GENERAL)
        ),
        vol.Optional(ATTR_DEVICE_ID): _required_text,
        vol.Optional(ATTR_DEVICE_IDS): _text_list,
        vol.Required(ATTR_TASK_KIND): vol.In(TASK_KINDS),
        vol.Required(ATTR_TITLE): _required_text,
        vol.Optional(ATTR_DESCRIPTION): _optional_text,
        vol.Required(ATTR_RECURRENCE_TYPE): vol.In(RECURRENCE_TYPES),
        vol.Optional(ATTR_RECURRENCE_INTERVAL, default=1): _positive_integer,
        vol.Required(ATTR_START_DATE): _date_value,
        vol.Optional(ATTR_END_DATE): _date_value,
        vol.Optional(ATTR_DUE_TIME): _time_value,
        vol.Optional(ATTR_PLANNED_MEDICATION_NAME): _optional_text,
        vol.Optional(ATTR_PLANNED_DOSE): _positive_number,
        vol.Optional(ATTR_PLANNED_DOSE_UNIT): vol.In(DOSE_UNITS),
        vol.Optional(ATTR_PLANNED_ROUTE): vol.In(ADMINISTRATION_ROUTES),
        vol.Optional(ATTR_PLANNED_VACCINATION_TARGETS): vol.All(
            cv.ensure_list,
            [vol.In(VACCINATION_TARGETS)],
        ),
        vol.Optional(ATTR_PLANNED_CUSTOM_VACCINATION_TARGET): _optional_text,
        vol.Optional(ATTR_PLANNED_VACCINE_NAME): _optional_text,
        vol.Optional(ATTR_PLANNED_ANTIGEN): _optional_text,
        vol.Optional(ATTR_PLANNED_VACCINATION_DOSE): _positive_number,
        vol.Optional(ATTR_PLANNED_VACCINATION_DOSE_UNIT): vol.In(DOSE_UNITS),
        vol.Optional(ATTR_PLANNED_VACCINATION_ROUTE): vol.In(ADMINISTRATION_ROUTES),
        vol.Optional(ATTR_PLANNED_CHECK_FOCUS): _optional_text,
        vol.Optional(ATTR_PLANNED_CARE_ACTION): _optional_text,
        vol.Optional(ATTR_PLANNED_VISIT_REASON): _optional_text,
        vol.Optional(ATTR_PLANNED_PROVIDER): _optional_text,
    }
)


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise ServiceValidationError("Animal Health is not loaded")


def _animal_id_from_device(hass: HomeAssistant, device_id: str) -> str:
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        raise ServiceValidationError("The selected animal device no longer exists")
    for identifier_domain, identifier in device.identifiers:
        if identifier_domain == DOMAIN and identifier != "general_tasks":
            return identifier
    raise ServiceValidationError("The selected device is not an Animal Health animal")


def _selected_device_ids(data: dict[str, Any]) -> list[str]:
    selected: list[str] = []
    if device_id := data.get(ATTR_DEVICE_ID):
        selected.append(device_id)
    for device_id in data.get(ATTR_DEVICE_IDS, []):
        if device_id not in selected:
            selected.append(device_id)
    return selected


def async_setup_task_record_creation(hass: HomeAssistant) -> None:
    async def handle_create_record_task(call: ServiceCall) -> ServiceResponse:
        runtime_data = _runtime_data(hass)
        task_store = runtime_data.coordinator.task_store
        record_store = TaskRecordStore(hass)
        scope = call.data[ATTR_TASK_SCOPE]
        task_kind = call.data[ATTR_TASK_KIND]
        device_ids = _selected_device_ids(call.data)

        if scope == TASK_SCOPE_GENERAL:
            if device_ids:
                raise ServiceValidationError(
                    "Do not select animals for a general task"
                )
            if task_kind != TASK_KIND_REMINDER:
                raise ServiceValidationError(
                    "Only a reminder may be created as a general task"
                )
            animal_ids: list[str | None] = [None]
        else:
            if not device_ids:
                raise ServiceValidationError(
                    "Select at least one animal for an animal-specific task"
                )
            animal_ids = [
                _animal_id_from_device(hass, device_id) for device_id in device_ids
            ]

        try:
            template = build_task_template(
                task_kind,
                call.data,
                title=call.data[ATTR_TITLE],
            )
            tasks = []
            for animal_id in animal_ids:
                task = await task_store.create_task(
                    animal_id=animal_id,
                    title=call.data[ATTR_TITLE],
                    description=call.data.get(ATTR_DESCRIPTION),
                    recurrence_type=call.data[ATTR_RECURRENCE_TYPE],
                    recurrence_interval=call.data[ATTR_RECURRENCE_INTERVAL],
                    start_date=call.data[ATTR_START_DATE],
                    end_date=call.data.get(ATTR_END_DATE),
                    due_time=call.data.get(ATTR_DUE_TIME),
                )
                await record_store.configure_task(task.id, task_kind, template)
                tasks.append(task.as_dict(task_store.timezone))
        except KeyError as err:
            raise ServiceValidationError(
                "The selected animal no longer exists"
            ) from err
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err

        await runtime_data.coordinator.async_request_refresh()
        enriched = await record_store.enrich_tasks(tasks)
        response: dict[str, Any] = {"tasks": enriched}
        if len(enriched) == 1:
            response["task"] = enriched[0]
        return response

    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_RECORD_TASK,
        handle_create_record_task,
        schema=CREATE_RECORD_TASK_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
