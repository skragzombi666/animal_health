from __future__ import annotations

from datetime import date, time, timedelta
from typing import Any, cast

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .runtime import AnimalHealthRuntimeData
from .task_store import (
    OCCURRENCE_CANCELLED,
    OCCURRENCE_COMPLETED,
    OCCURRENCE_STATUSES,
    OCCURRENCE_SKIPPED,
    RECURRENCE_TYPES,
    TASK_ACTIVE_ALL,
    TASK_ACTIVE_STATES,
    TASK_SCOPE_ALL,
    TASK_SCOPE_ANIMAL,
    TASK_SCOPE_GENERAL,
    TASK_SCOPES,
    TaskOccurrenceRecord,
    TaskStore,
)

SERVICE_CREATE_TASK = "create_task"
SERVICE_LIST_TASKS = "list_tasks"
SERVICE_LIST_DUE_TASKS = "list_due_tasks"
SERVICE_LIST_TASK_OCCURRENCES = "list_task_occurrences"
SERVICE_UPDATE_TASK = "update_task"
SERVICE_SET_TASK_ACTIVE = "set_task_active"
SERVICE_COMPLETE_TASK_OCCURRENCE = "complete_task_occurrence"
SERVICE_SKIP_TASK_OCCURRENCE = "skip_task_occurrence"
SERVICE_CANCEL_TASK_OCCURRENCE = "cancel_task_occurrence"

ATTR_TASK_ID = "task_id"
ATTR_OCCURRENCE_ID = "occurrence_id"
ATTR_TASK_ENTITY_IDS = "task_entity_ids"
ATTR_SCHEDULED_DATE = "scheduled_date"
ATTR_TASK_SCOPE = "task_scope"
ATTR_DEVICE_ID = "device_id"
ATTR_DEVICE_IDS = "device_ids"
ATTR_ENTITY_IDS = "entity_ids"
ATTR_TITLE = "title"
ATTR_DESCRIPTION = "description"
ATTR_RECURRENCE_TYPE = "recurrence_type"
ATTR_RECURRENCE_INTERVAL = "recurrence_interval"
ATTR_START_DATE = "start_date"
ATTR_END_DATE = "end_date"
ATTR_DUE_TIME = "due_time"
ATTR_CLEAR_END_DATE = "clear_end_date"
ATTR_CLEAR_DUE_TIME = "clear_due_time"
ATTR_ACTIVE_STATE = "active_state"
ATTR_IS_ACTIVE = "is_active"
ATTR_THROUGH_DATE = "through_date"
ATTR_FROM_DATE = "from_date"
ATTR_TO_DATE = "to_date"
ATTR_STATUS = "status"
ATTR_INCLUDE_GENERAL = "include_general"
ATTR_LIMIT = "limit"
ATTR_NOTES = "notes"

_TASK_SWITCH_UNIQUE_ID_PREFIX = "task_active_"
_INTERNAL_FILTER_LIMIT = 10000


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
    values = cv.ensure_list(value)
    result: list[str] = []
    for item in values:
        text = _required_text(item)
        if text not in result:
            result.append(text)
    return result


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
        parsed = time.fromisoformat(cv.string(value))
    except ValueError as err:
        raise vol.Invalid("time must use HH:MM") from err
    return parsed.replace(second=0, microsecond=0)


def _positive_integer(value: Any) -> int:
    number = vol.Coerce(int)(value)
    if number < 1:
        raise vol.Invalid("value must be at least 1")
    return number


CREATE_TASK_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_TASK_SCOPE, default=TASK_SCOPE_ANIMAL): vol.In(
            (TASK_SCOPE_ANIMAL, TASK_SCOPE_GENERAL)
        ),
        vol.Optional(ATTR_DEVICE_ID): _required_text,
        vol.Optional(ATTR_DEVICE_IDS): _text_list,
        vol.Required(ATTR_TITLE): _required_text,
        vol.Optional(ATTR_DESCRIPTION): _optional_text,
        vol.Required(ATTR_RECURRENCE_TYPE): vol.In(RECURRENCE_TYPES),
        vol.Optional(ATTR_RECURRENCE_INTERVAL, default=1): _positive_integer,
        vol.Required(ATTR_START_DATE): _date_value,
        vol.Optional(ATTR_END_DATE): _date_value,
        vol.Optional(ATTR_DUE_TIME): _time_value,
    }
)

LIST_TASKS_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_TASK_SCOPE, default=TASK_SCOPE_ALL): vol.In(TASK_SCOPES),
        vol.Optional(ATTR_DEVICE_ID): _required_text,
        vol.Optional(ATTR_ACTIVE_STATE, default=TASK_ACTIVE_ALL): vol.In(
            TASK_ACTIVE_STATES
        ),
        vol.Optional(ATTR_LIMIT, default=200): vol.All(
            vol.Coerce(int),
            vol.Range(min=1, max=500),
        ),
    }
)

LIST_DUE_TASKS_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_THROUGH_DATE): _date_value,
        vol.Optional(ATTR_DEVICE_ID): _required_text,
        vol.Optional(ATTR_DEVICE_IDS): _text_list,
        vol.Optional(ATTR_INCLUDE_GENERAL, default=True): cv.boolean,
        vol.Optional(ATTR_LIMIT, default=200): vol.All(
            vol.Coerce(int),
            vol.Range(min=1, max=500),
        ),
    }
)

LIST_TASK_OCCURRENCES_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_TASK_ID): _required_text,
        vol.Optional(ATTR_TASK_SCOPE, default=TASK_SCOPE_ALL): vol.In(TASK_SCOPES),
        vol.Optional(ATTR_DEVICE_ID): _required_text,
        vol.Optional(ATTR_INCLUDE_GENERAL, default=True): cv.boolean,
        vol.Optional(ATTR_STATUS, default=TASK_ACTIVE_ALL): vol.In(
            (*OCCURRENCE_STATUSES, TASK_ACTIVE_ALL)
        ),
        vol.Optional(ATTR_FROM_DATE): _date_value,
        vol.Optional(ATTR_TO_DATE): _date_value,
        vol.Optional(ATTR_LIMIT, default=200): vol.All(
            vol.Coerce(int),
            vol.Range(min=1, max=500),
        ),
    }
)

UPDATE_TASK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TASK_ID): _required_text,
        vol.Optional(ATTR_TASK_SCOPE): vol.In(
            (TASK_SCOPE_ANIMAL, TASK_SCOPE_GENERAL)
        ),
        vol.Optional(ATTR_DEVICE_ID): _required_text,
        vol.Optional(ATTR_TITLE): _required_text,
        vol.Optional(ATTR_DESCRIPTION): _optional_text,
        vol.Optional(ATTR_RECURRENCE_TYPE): vol.In(RECURRENCE_TYPES),
        vol.Optional(ATTR_RECURRENCE_INTERVAL): _positive_integer,
        vol.Optional(ATTR_START_DATE): _date_value,
        vol.Optional(ATTR_END_DATE): _date_value,
        vol.Optional(ATTR_CLEAR_END_DATE, default=False): cv.boolean,
        vol.Optional(ATTR_DUE_TIME): _time_value,
        vol.Optional(ATTR_CLEAR_DUE_TIME, default=False): cv.boolean,
    }
)

SET_TASK_ACTIVE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_TASK_ID): _required_text,
        vol.Optional(ATTR_ENTITY_IDS): _text_list,
        vol.Required(ATTR_IS_ACTIVE): cv.boolean,
    }
)

OCCURRENCE_ACTION_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_OCCURRENCE_ID): _required_text,
        vol.Optional(ATTR_TASK_ENTITY_IDS): _text_list,
        vol.Optional(ATTR_SCHEDULED_DATE): _date_value,
        vol.Optional(ATTR_NOTES): _optional_text,
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
    legacy_device_id = data.get(ATTR_DEVICE_ID)
    if legacy_device_id is not None:
        selected.append(legacy_device_id)
    for device_id in data.get(ATTR_DEVICE_IDS, []):
        if device_id not in selected:
            selected.append(device_id)
    return selected


def _animal_ids_from_devices(
    hass: HomeAssistant,
    data: dict[str, Any],
) -> list[str]:
    return [
        _animal_id_from_device(hass, device_id)
        for device_id in _selected_device_ids(data)
    ]


def _optional_animal_id(hass: HomeAssistant, data: dict[str, Any]) -> str | None:
    device_id = data.get(ATTR_DEVICE_ID)
    return _animal_id_from_device(hass, device_id) if device_id else None


def _create_scope_animal_ids(
    hass: HomeAssistant,
    data: dict[str, Any],
) -> list[str | None]:
    scope = data[ATTR_TASK_SCOPE]
    animal_ids = _animal_ids_from_devices(hass, data)
    if scope == TASK_SCOPE_ANIMAL:
        if not animal_ids:
            raise ServiceValidationError(
                "At least one animal must be selected for an animal-specific task"
            )
        return list(animal_ids)
    if animal_ids:
        raise ServiceValidationError("Do not select animals for a general task")
    return [None]


def _validate_scope_filter(scope: str, animal_id: str | None) -> None:
    if scope == TASK_SCOPE_GENERAL and animal_id is not None:
        raise ServiceValidationError(
            "An animal filter cannot be combined with general tasks only"
        )


def _task_ids_from_entities(
    hass: HomeAssistant,
    entity_ids: list[str],
) -> list[str]:
    registry = er.async_get(hass)
    task_ids: list[str] = []
    for entity_id in entity_ids:
        entry = registry.async_get(entity_id)
        if (
            entry is None
            or entry.domain != "switch"
            or entry.platform != DOMAIN
            or not entry.unique_id.startswith(_TASK_SWITCH_UNIQUE_ID_PREFIX)
        ):
            raise ServiceValidationError(
                f"The selected entity is not an Animal Health task switch: {entity_id}"
            )
        task_id = entry.unique_id.removeprefix(_TASK_SWITCH_UNIQUE_ID_PREFIX)
        if task_id not in task_ids:
            task_ids.append(task_id)
    return task_ids


async def _list_due_for_animals(
    store: TaskStore,
    *,
    through_date: date,
    animal_ids: list[str],
    include_general: bool,
    limit: int,
) -> list[TaskOccurrenceRecord]:
    occurrences: dict[str, TaskOccurrenceRecord] = {}

    if animal_ids:
        for animal_id in animal_ids:
            animal_occurrences = await store.list_due_occurrences(
                through_date=through_date,
                animal_id=animal_id,
                include_general=False,
                limit=_INTERNAL_FILTER_LIMIT,
            )
            occurrences.update(
                (occurrence.id, occurrence) for occurrence in animal_occurrences
            )
        if include_general:
            all_occurrences = await store.list_due_occurrences(
                through_date=through_date,
                animal_id=None,
                include_general=True,
                limit=_INTERNAL_FILTER_LIMIT,
            )
            occurrences.update(
                (occurrence.id, occurrence)
                for occurrence in all_occurrences
                if occurrence.animal_id is None
            )
    else:
        all_occurrences = await store.list_due_occurrences(
            through_date=through_date,
            animal_id=None,
            include_general=True,
            limit=_INTERNAL_FILTER_LIMIT,
        )
        occurrences.update(
            (occurrence.id, occurrence)
            for occurrence in all_occurrences
            if include_general or occurrence.animal_id is not None
        )

    return sorted(
        occurrences.values(),
        key=lambda occurrence: (
            occurrence.scheduled_for,
            occurrence.task_title.casefold(),
            occurrence.id,
        ),
    )[:limit]


def async_setup_task_services(hass: HomeAssistant) -> None:
    async def handle_create_task(call: ServiceCall) -> ServiceResponse:
        runtime_data = _runtime_data(hass)
        store = runtime_data.coordinator.task_store
        task_animal_ids = _create_scope_animal_ids(hass, call.data)
        tasks = []
        try:
            for animal_id in task_animal_ids:
                tasks.append(
                    await store.create_task(
                        animal_id=animal_id,
                        title=call.data[ATTR_TITLE],
                        description=call.data.get(ATTR_DESCRIPTION),
                        recurrence_type=call.data[ATTR_RECURRENCE_TYPE],
                        recurrence_interval=call.data[ATTR_RECURRENCE_INTERVAL],
                        start_date=call.data[ATTR_START_DATE],
                        end_date=call.data.get(ATTR_END_DATE),
                        due_time=call.data.get(ATTR_DUE_TIME),
                    )
                )
        except KeyError as err:
            raise ServiceValidationError(
                "The selected animal no longer exists"
            ) from err
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        await runtime_data.coordinator.async_request_refresh()
        task_data = [task.as_dict(store.timezone) for task in tasks]
        response: dict[str, Any] = {"tasks": task_data}
        if len(task_data) == 1:
            response["task"] = task_data[0]
        return response if call.return_response else None

    async def handle_list_tasks(call: ServiceCall) -> ServiceResponse:
        runtime_data = _runtime_data(hass)
        store = runtime_data.coordinator.task_store
        animal_id = _optional_animal_id(hass, call.data)
        scope = call.data[ATTR_TASK_SCOPE]
        _validate_scope_filter(scope, animal_id)
        try:
            tasks = await store.list_tasks(
                scope=scope,
                animal_id=animal_id,
                active_state=call.data[ATTR_ACTIVE_STATE],
                limit=call.data[ATTR_LIMIT],
            )
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        return {"tasks": [task.as_dict(store.timezone) for task in tasks]}

    async def handle_list_due_tasks(call: ServiceCall) -> ServiceResponse:
        runtime_data = _runtime_data(hass)
        store = runtime_data.coordinator.task_store
        animal_ids = _animal_ids_from_devices(hass, call.data)
        through_date = call.data.get(ATTR_THROUGH_DATE, store.local_today())
        try:
            occurrences = await _list_due_for_animals(
                store,
                through_date=through_date,
                animal_ids=animal_ids,
                include_general=call.data[ATTR_INCLUDE_GENERAL],
                limit=call.data[ATTR_LIMIT],
            )
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        return {
            "through_date": through_date.isoformat(),
            "animal_ids": animal_ids,
            "include_general": call.data[ATTR_INCLUDE_GENERAL],
            "occurrences": [
                occurrence.as_dict(store.timezone) for occurrence in occurrences
            ],
        }

    async def handle_list_task_occurrences(call: ServiceCall) -> ServiceResponse:
        runtime_data = _runtime_data(hass)
        store = runtime_data.coordinator.task_store
        animal_id = _optional_animal_id(hass, call.data)
        scope = call.data[ATTR_TASK_SCOPE]
        _validate_scope_filter(scope, animal_id)
        today = store.local_today()
        from_date = call.data.get(ATTR_FROM_DATE, today - timedelta(days=30))
        to_date = call.data.get(ATTR_TO_DATE, today + timedelta(days=90))
        try:
            occurrences = await store.list_occurrences(
                task_id=call.data.get(ATTR_TASK_ID),
                scope=scope,
                animal_id=animal_id,
                status=call.data[ATTR_STATUS],
                start_date=from_date,
                end_date=to_date,
                include_general=call.data[ATTR_INCLUDE_GENERAL],
                limit=call.data[ATTR_LIMIT],
            )
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        return {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "occurrences": [
                occurrence.as_dict(store.timezone) for occurrence in occurrences
            ],
        }

    async def handle_update_task(call: ServiceCall) -> ServiceResponse:
        runtime_data = _runtime_data(hass)
        store = runtime_data.coordinator.task_store
        task_id = call.data[ATTR_TASK_ID]
        current = await store.get_task(task_id)
        if current is None:
            raise ServiceValidationError("The selected task no longer exists")

        changes: dict[str, Any] = {}
        scope = call.data.get(ATTR_TASK_SCOPE)
        device_id = call.data.get(ATTR_DEVICE_ID)
        if scope == TASK_SCOPE_GENERAL:
            if device_id is not None:
                raise ServiceValidationError(
                    "Do not select an animal when changing a task to general"
                )
            changes["animal_id"] = None
        elif scope == TASK_SCOPE_ANIMAL:
            if device_id is not None:
                changes["animal_id"] = _animal_id_from_device(hass, device_id)
            elif current.animal_id is None:
                raise ServiceValidationError(
                    "Select an animal when changing a general task to animal-specific"
                )
        elif device_id is not None:
            changes["animal_id"] = _animal_id_from_device(hass, device_id)

        for field in (
            ATTR_TITLE,
            ATTR_DESCRIPTION,
            ATTR_RECURRENCE_TYPE,
            ATTR_RECURRENCE_INTERVAL,
            ATTR_START_DATE,
        ):
            if field in call.data:
                changes[field] = call.data[field]

        if call.data[ATTR_CLEAR_END_DATE] and ATTR_END_DATE in call.data:
            raise ServiceValidationError(
                "End date and clear end date cannot be used together"
            )
        if call.data[ATTR_CLEAR_END_DATE]:
            changes[ATTR_END_DATE] = None
        elif ATTR_END_DATE in call.data:
            changes[ATTR_END_DATE] = call.data[ATTR_END_DATE]

        if call.data[ATTR_CLEAR_DUE_TIME] and ATTR_DUE_TIME in call.data:
            raise ServiceValidationError(
                "Due time and clear due time cannot be used together"
            )
        if call.data[ATTR_CLEAR_DUE_TIME]:
            changes[ATTR_DUE_TIME] = None
        elif ATTR_DUE_TIME in call.data:
            changes[ATTR_DUE_TIME] = call.data[ATTR_DUE_TIME]

        if not changes:
            raise ServiceValidationError("No task fields were supplied")
        try:
            task = await store.update_task(task_id, **changes)
        except KeyError as err:
            raise ServiceValidationError(
                "The selected task or animal no longer exists"
            ) from err
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        await runtime_data.coordinator.async_request_refresh()
        response = {"task": task.as_dict(store.timezone)}
        return response if call.return_response else None

    async def handle_set_task_active(call: ServiceCall) -> ServiceResponse:
        runtime_data = _runtime_data(hass)
        store = runtime_data.coordinator.task_store
        task_ids: list[str] = []
        if task_id := call.data.get(ATTR_TASK_ID):
            task_ids.append(task_id)
        for task_id in _task_ids_from_entities(
            hass,
            call.data.get(ATTR_ENTITY_IDS, []),
        ):
            if task_id not in task_ids:
                task_ids.append(task_id)
        if not task_ids:
            raise ServiceValidationError("Select at least one task")

        tasks = []
        try:
            for task_id in task_ids:
                tasks.append(
                    await store.set_task_active(
                        task_id,
                        call.data[ATTR_IS_ACTIVE],
                    )
                )
        except KeyError as err:
            raise ServiceValidationError("The selected task no longer exists") from err
        await runtime_data.coordinator.async_request_refresh()
        task_data = [task.as_dict(store.timezone) for task in tasks]
        response: dict[str, Any] = {"tasks": task_data}
        if len(task_data) == 1:
            response["task"] = task_data[0]
        return response if call.return_response else None

    async def _resolve_occurrence_ids(call: ServiceCall, store: TaskStore) -> list[str]:
        direct_id = call.data.get(ATTR_OCCURRENCE_ID)
        entity_ids = call.data.get(ATTR_TASK_ENTITY_IDS, [])
        if direct_id and entity_ids:
            raise ServiceValidationError(
                "Use either a task selection or an occurrence ID, not both"
            )
        if direct_id:
            return [str(direct_id)]
        if not entity_ids:
            raise ServiceValidationError(
                "Select one or more open tasks or enter an occurrence ID"
            )

        today = store.local_today()
        start_date = today - timedelta(days=3660)
        end_date = today + timedelta(days=3660)
        scheduled_date = call.data.get(ATTR_SCHEDULED_DATE)
        occurrence_ids: list[str] = []
        for task_id in _task_ids_from_entities(hass, entity_ids):
            occurrences = await store.list_occurrences(
                task_id=task_id,
                scope=TASK_SCOPE_ALL,
                animal_id=None,
                status=OCCURRENCE_PENDING,
                start_date=start_date,
                end_date=end_date,
                include_general=True,
                limit=100,
            )
            if scheduled_date is not None:
                occurrences = [
                    occurrence
                    for occurrence in occurrences
                    if occurrence.scheduled_for.astimezone(store.timezone).date()
                    == scheduled_date
                ]
            if not occurrences:
                raise ServiceValidationError(
                    "No matching open occurrence exists for one of the selected tasks"
                )
            selected = min(occurrences, key=lambda occurrence: occurrence.scheduled_for)
            if selected.id not in occurrence_ids:
                occurrence_ids.append(selected.id)
        return occurrence_ids

    async def _set_occurrence_status(
        call: ServiceCall,
        status: str,
    ) -> ServiceResponse:
        runtime_data = _runtime_data(hass)
        store = runtime_data.coordinator.task_store
        occurrence_ids = await _resolve_occurrence_ids(call, store)
        occurrences: list[dict[str, Any]] = []
        try:
            for occurrence_id in occurrence_ids:
                occurrence = await store.set_occurrence_status(
                    occurrence_id,
                    status,
                    call.data.get(ATTR_NOTES),
                )
                occurrences.append(occurrence.as_dict(store.timezone))
        except KeyError as err:
            raise ServiceValidationError(
                "The selected task occurrence no longer exists"
            ) from err
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        await runtime_data.coordinator.async_request_refresh()
        response: dict[str, Any] = {"occurrences": occurrences}
        if len(occurrences) == 1:
            response["occurrence"] = occurrences[0]
        return response if call.return_response else None

    async def handle_complete_occurrence(call: ServiceCall) -> ServiceResponse:
        return await _set_occurrence_status(call, OCCURRENCE_COMPLETED)

    async def handle_skip_occurrence(call: ServiceCall) -> ServiceResponse:
        return await _set_occurrence_status(call, OCCURRENCE_SKIPPED)

    async def handle_cancel_occurrence(call: ServiceCall) -> ServiceResponse:
        return await _set_occurrence_status(call, OCCURRENCE_CANCELLED)

    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_TASK,
        handle_create_task,
        schema=CREATE_TASK_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LIST_TASKS,
        handle_list_tasks,
        schema=LIST_TASKS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LIST_DUE_TASKS,
        handle_list_due_tasks,
        schema=LIST_DUE_TASKS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LIST_TASK_OCCURRENCES,
        handle_list_task_occurrences,
        schema=LIST_TASK_OCCURRENCES_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_TASK,
        handle_update_task,
        schema=UPDATE_TASK_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TASK_ACTIVE,
        handle_set_task_active,
        schema=SET_TASK_ACTIVE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_COMPLETE_TASK_OCCURRENCE,
        handle_complete_occurrence,
        schema=OCCURRENCE_ACTION_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SKIP_TASK_OCCURRENCE,
        handle_skip_occurrence,
        schema=OCCURRENCE_ACTION_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CANCEL_TASK_OCCURRENCE,
        handle_cancel_occurrence,
        schema=OCCURRENCE_ACTION_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
