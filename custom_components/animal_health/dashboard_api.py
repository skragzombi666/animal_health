from __future__ import annotations

import asyncio
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .catalog import medicine_catalog_names, vaccine_catalog_names
from .const import (
    ADMINISTRATION_ROUTES,
    ANIMAL_SEXES,
    ANIMAL_STATUSES,
    DOMAIN,
    DOSE_UNITS,
    EVENT_TYPES,
    SYMPTOM_SEVERITIES,
    SYMPTOMS,
    VACCINATION_TARGETS,
    WEIGHT_UNITS,
)
from .panel import INTEGRATION_VERSION
from .runtime import AnimalHealthRuntimeData
from .task_kinds import TASK_KINDS
from .task_records import HEALTH_CHECK_RESULTS
from .task_store import TASK_ACTIVE_ALL, TASK_SCOPE_ALL

_DASHBOARD_COMMAND = f"{DOMAIN}/dashboard"
_ANIMAL_DETAIL_COMMAND = f"{DOMAIN}/animal_detail"
_CATALOG_COMMAND = f"{DOMAIN}/catalog"
_MAX_OCCURRENCES = 1000
_MAX_GLOBAL_EVENTS = 250
_MAX_EVENTS_PER_ANIMAL = 75


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _animal_device_id(hass: HomeAssistant, animal_id: str) -> str | None:
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, animal_id)})
    return device.id if device is not None else None


def _task_entity_id(hass: HomeAssistant, task_id: str) -> str | None:
    return er.async_get(hass).async_get_entity_id(
        "switch",
        DOMAIN,
        f"task_active_{task_id}",
    )


def _latest_weight_dict(weight: Any) -> dict[str, Any] | None:
    if weight is None:
        return None
    return {
        "event_id": weight.event_id,
        "value_kg": weight.value_kg,
        "original_value": weight.original_value,
        "original_unit": weight.original_unit,
        "occurred_at": weight.occurred_at.isoformat(),
    }


def _decorate_occurrences(
    occurrences: list[dict[str, Any]],
    tasks_by_id: dict[str, dict[str, Any]],
    *,
    today: date,
) -> list[dict[str, Any]]:
    now = datetime.now(UTC).replace(microsecond=0)
    decorated: list[dict[str, Any]] = []
    for occurrence in occurrences:
        item = dict(occurrence)
        scheduled = datetime.fromisoformat(str(item["scheduled_for"]))
        if scheduled.tzinfo is None:
            scheduled = scheduled.replace(tzinfo=UTC)
        local_date = date.fromisoformat(str(item["scheduled_date"]))
        task = tasks_by_id.get(str(item["task_id"]), {})
        has_due_time = task.get("due_time") is not None
        item["is_overdue"] = bool(
            item.get("status") == "pending"
            and (scheduled < now if has_due_time else local_date < today)
        )
        item["is_today"] = bool(
            item.get("status") == "pending" and local_date == today
        )
        item["is_upcoming"] = bool(
            item.get("status") == "pending" and local_date > today
        )
        item["task_entity_id"] = task.get("entity_id")
        decorated.append(item)
    return decorated


async def _events_for_animals(
    runtime_data: AnimalHealthRuntimeData,
    animals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not animals:
        return []
    event_lists = await asyncio.gather(
        *(
            runtime_data.database.get_events(
                str(animal["id"]),
                _MAX_EVENTS_PER_ANIMAL,
            )
            for animal in animals
        )
    )
    names = {str(animal["id"]): str(animal["name"]) for animal in animals}
    events: list[dict[str, Any]] = []
    for animal_events in event_lists:
        for event in animal_events:
            item = event.as_dict()
            item["animal_name"] = names.get(event.animal_id, event.animal_id)
            events.append(item)
    events.sort(
        key=lambda item: (str(item["occurred_at"]), str(item["created_at"])),
        reverse=True,
    )
    return events[:_MAX_GLOBAL_EVENTS]


def _catalog_items(filename: str) -> list[dict[str, Any]]:
    catalog_path = Path(__file__).parent / "catalogs" / filename
    with catalog_path.open(encoding="utf-8") as file:
        document = json.load(file)
    return [dict(item) for item in document.get("items", [])]


def _catalog_snapshot() -> dict[str, Any]:
    return {
        "animal_statuses": list(ANIMAL_STATUSES),
        "animal_sexes": list(ANIMAL_SEXES),
        "event_types": list(EVENT_TYPES),
        "weight_units": list(WEIGHT_UNITS),
        "dose_units": list(DOSE_UNITS),
        "administration_routes": list(ADMINISTRATION_ROUTES),
        "symptoms": list(SYMPTOMS),
        "symptom_severities": list(SYMPTOM_SEVERITIES),
        "vaccination_targets": list(VACCINATION_TARGETS),
        "task_kinds": list(TASK_KINDS),
        "health_check_results": list(HEALTH_CHECK_RESULTS),
        "medicine_names": medicine_catalog_names(),
        "vaccine_names": vaccine_catalog_names(),
        "species": _catalog_items("species.json"),
        "breeds": _catalog_items("breeds.json"),
    }


async def _dashboard_payload(hass: HomeAssistant) -> dict[str, Any]:
    runtime_data = _runtime_data(hass)
    coordinator = runtime_data.coordinator
    await coordinator.async_refresh()

    animals: list[dict[str, Any]] = []
    for animal in coordinator.data.values():
        item = animal.as_dict()
        item["device_id"] = _animal_device_id(hass, animal.id)
        item["latest_weight"] = _latest_weight_dict(
            coordinator.latest_weights.get(animal.id)
        )
        animals.append(item)
    animals.sort(key=lambda item: str(item["name"]).casefold())

    tasks: list[dict[str, Any]] = []
    for task_id, task in coordinator.tasks.items():
        item = dict(
            coordinator.task_metadata.get(
                task_id,
                task.as_dict(coordinator.task_store.timezone),
            )
        )
        item["entity_id"] = _task_entity_id(hass, task_id)
        tasks.append(item)
    tasks.sort(
        key=lambda item: (str(item.get("title", "")).casefold(), str(item["id"]))
    )
    tasks_by_id = {str(task["id"]): task for task in tasks}

    today = coordinator.task_store.local_today()
    occurrence_records = await coordinator.task_store.list_occurrences(
        task_id=None,
        scope=TASK_SCOPE_ALL,
        animal_id=None,
        status=TASK_ACTIVE_ALL,
        start_date=today - timedelta(days=60),
        end_date=today + timedelta(days=180),
        include_general=True,
        limit=_MAX_OCCURRENCES,
    )
    occurrences = await coordinator.task_record_store.enrich_occurrences(
        [
            occurrence.as_dict(coordinator.task_store.timezone)
            for occurrence in occurrence_records
        ]
    )
    occurrences = _decorate_occurrences(occurrences, tasks_by_id, today=today)
    events = await _events_for_animals(runtime_data, animals)

    pending = [item for item in occurrences if item.get("status") == "pending"]
    summary = {
        "active_animals": sum(
            1
            for animal in animals
            if not animal.get("is_archived") and animal.get("status") == "active"
        ),
        "archived_animals": sum(
            1 for animal in animals if animal.get("is_archived")
        ),
        "pending_tasks": len(pending),
        "overdue_tasks": sum(1 for item in pending if item.get("is_overdue")),
        "today_tasks": sum(1 for item in pending if item.get("is_today")),
        "upcoming_tasks": sum(1 for item in pending if item.get("is_upcoming")),
    }

    return {
        "version": INTEGRATION_VERSION,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "time_zone": hass.config.time_zone,
        "today": today.isoformat(),
        "summary": summary,
        "animals": animals,
        "tasks": tasks,
        "occurrences": occurrences,
        "events": events,
    }


async def _animal_detail_payload(
    hass: HomeAssistant,
    animal_id: str,
    event_limit: int,
) -> dict[str, Any]:
    runtime_data = _runtime_data(hass)
    coordinator = runtime_data.coordinator
    await coordinator.async_refresh()
    animal = coordinator.data.get(animal_id)
    if animal is None:
        raise KeyError(animal_id)

    animal_data = animal.as_dict()
    animal_data["device_id"] = _animal_device_id(hass, animal_id)
    animal_data["latest_weight"] = _latest_weight_dict(
        coordinator.latest_weights.get(animal_id)
    )

    tasks: list[dict[str, Any]] = []
    for task_id, task in coordinator.tasks.items():
        if task.animal_id != animal_id:
            continue
        item = dict(
            coordinator.task_metadata.get(
                task_id,
                task.as_dict(coordinator.task_store.timezone),
            )
        )
        item["entity_id"] = _task_entity_id(hass, task_id)
        tasks.append(item)
    tasks_by_id = {str(task["id"]): task for task in tasks}

    today = coordinator.task_store.local_today()
    occurrence_records = await coordinator.task_store.list_occurrences(
        task_id=None,
        scope=TASK_SCOPE_ALL,
        animal_id=animal_id,
        status=TASK_ACTIVE_ALL,
        start_date=today - timedelta(days=365),
        end_date=today + timedelta(days=365),
        include_general=False,
        limit=_MAX_OCCURRENCES,
    )
    occurrences = await coordinator.task_record_store.enrich_occurrences(
        [
            occurrence.as_dict(coordinator.task_store.timezone)
            for occurrence in occurrence_records
        ]
    )
    occurrences = _decorate_occurrences(occurrences, tasks_by_id, today=today)

    events = [
        event.as_dict()
        for event in await runtime_data.database.get_events(animal_id, event_limit)
    ]
    for event in events:
        event["animal_name"] = animal.name

    return {
        "version": INTEGRATION_VERSION,
        "animal": animal_data,
        "tasks": tasks,
        "occurrences": occurrences,
        "events": events,
    }


def async_setup_dashboard_api(hass: HomeAssistant) -> None:
    """Register WebSocket commands used by the Animal Health panel."""

    @websocket_api.websocket_command({vol.Required("type"): _DASHBOARD_COMMAND})
    @websocket_api.async_response
    async def websocket_dashboard(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            payload = await _dashboard_payload(hass)
        except RuntimeError as err:
            connection.send_error(msg["id"], "not_loaded", str(err))
            return
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "dashboard_failed", str(err))
            return
        connection.send_result(msg["id"], payload)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _ANIMAL_DETAIL_COMMAND,
            vol.Required("animal_id"): str,
            vol.Optional("event_limit", default=200): vol.All(
                vol.Coerce(int),
                vol.Range(min=1, max=500),
            ),
        }
    )
    @websocket_api.async_response
    async def websocket_animal_detail(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            payload = await _animal_detail_payload(
                hass,
                str(msg["animal_id"]),
                int(msg["event_limit"]),
            )
        except RuntimeError as err:
            connection.send_error(msg["id"], "not_loaded", str(err))
            return
        except KeyError:
            connection.send_error(
                msg["id"],
                "animal_not_found",
                "The selected animal no longer exists",
            )
            return
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "animal_detail_failed", str(err))
            return
        connection.send_result(msg["id"], payload)

    @websocket_api.websocket_command({vol.Required("type"): _CATALOG_COMMAND})
    @websocket_api.async_response
    async def websocket_catalog(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            payload = await hass.async_add_executor_job(_catalog_snapshot)
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "catalog_failed", str(err))
            return
        connection.send_result(msg["id"], payload)

    websocket_api.async_register_command(hass, websocket_dashboard)
    websocket_api.async_register_command(hass, websocket_animal_detail)
    websocket_api.async_register_command(hass, websocket_catalog)
