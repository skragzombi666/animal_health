from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import task_kinds, task_record_creation, task_records, v0912_features, v0923_features, v0924_features, v0926_features
from .const import DATABASE_NAME, DOMAIN
from .runtime import AnimalHealthRuntimeData
from .v0927_data import (
    GABE_DEWORMING,
    GABE_FEED,
    GABE_MEDICATION,
    GABE_SUPPLEMENT,
    GABE_TYPES,
    GABE_VACCINATION,
    PRODUCT_KINDS,
    archive_product_sync,
    connect,
    initialize_products_sync,
    required_text,
    reset_product_sync,
    save_product_sync,
    state_sync,
    text,
)
from .v0927_gabe import backfill_gabe_events, catalog_metadata_fallback, enrich_event_in_connection, record_gabe_sync

_STATE_COMMAND = f"{DOMAIN}/v0927/state"
_RECORD_COMMAND = f"{DOMAIN}/v0927/gabe/record"
_PRODUCT_SAVE_COMMAND = f"{DOMAIN}/v0927/product/save"
_PRODUCT_ARCHIVE_COMMAND = f"{DOMAIN}/v0927/product/archive"
_PRODUCT_RESET_COMMAND = f"{DOMAIN}/v0927/product/reset"
_TASK_GABE_EXECUTE_COMMAND = f"{DOMAIN}/v0927/task/gabe/execute"
_PATCHED = False
_BASE_BUILD_TASK_TEMPLATE = task_records.build_task_template


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _database_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(DATABASE_NAME))


async def async_initialize_v0927_features(hass: HomeAssistant) -> None:
    path = _database_path(hass)
    await hass.async_add_executor_job(initialize_products_sync, path)
    await hass.async_add_executor_job(backfill_gabe_events, path)


def _task_template_v0927(task_kind_value: str, data: dict[str, Any], *, title: str, current=None) -> dict[str, Any]:
    if task_kind_value == task_kinds.TASK_KIND_DEWORMING:
        transformed = dict(data)
        transformed.setdefault("planned_medication_name", data.get("planned_product_name") or data.get("medication_name") or title)
        template = _BASE_BUILD_TASK_TEMPLATE(task_kinds.TASK_KIND_MEDICATION, transformed, title=title, current=current)
        template["gabe_type"] = GABE_DEWORMING
        return template
    if task_kind_value in (task_kinds.TASK_KIND_SUPPLEMENT, task_kinds.TASK_KIND_FEED):
        template = dict(current or {})
        name = text(data.get("planned_product_name") or data.get("planned_medication_name") or data.get("product_name") or title)
        template["product_name"] = name
        template["gabe_type"] = GABE_SUPPLEMENT if task_kind_value == task_kinds.TASK_KIND_SUPPLEMENT else GABE_FEED
        if data.get("planned_dose") not in (None, ""):
            template["dose"] = float(data["planned_dose"])
        if text(data.get("planned_dose_unit")):
            template["dose_unit"] = text(data["planned_dose_unit"])
        if text(data.get("planned_route")):
            template["route"] = text(data["planned_route"])
        if text(data.get("dose_basis")):
            template["dose_basis"] = text(data["dose_basis"])
        if text(data.get("feed_status")):
            template["feed_status"] = text(data["feed_status"])
        return template
    return _BASE_BUILD_TASK_TEMPLATE(task_kind_value, data, title=title, current=current)


def apply_v0927_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    task_records.TASK_KINDS = task_kinds.TASK_KINDS
    task_record_creation.TASK_KINDS = task_kinds.TASK_KINDS
    v0926_features.TASK_KINDS = task_kinds.TASK_KINDS
    task_records.build_task_template = _task_template_v0927
    task_record_creation.build_task_template = _task_template_v0927

    base_task_execute = task_records.TaskRecordStore.execute

    async def task_execute_v0927(self, **kwargs):
        result = await base_task_execute(self, **kwargs)
        event = result.event
        if not event:
            return result

        def enrich_task_event() -> dict[str, Any] | None:
            with self._connect() as connection:  # noqa: SLF001
                updated = enrich_event_in_connection(connection, str(event["id"]), forced_source="task")
                return updated.as_dict() if updated else event

        enriched = await self._hass.async_add_executor_job(enrich_task_event)  # noqa: SLF001
        return task_records.TaskExecutionResult(result.occurrence, enriched)

    task_records.TaskRecordStore.execute = task_execute_v0927  # type: ignore[method-assign]

    base_component_validator = v0912_features._validate_component  # noqa: SLF001

    def validate_component_v0927(raw: dict[str, Any]) -> dict[str, Any]:
        item = base_component_validator(raw)
        optional = bool(item.get("optional"))
        item["default_selected"] = bool(raw.get("default_selected")) if optional else False
        return item

    v0912_features._validate_component = validate_component_v0927  # type: ignore[attr-defined]  # noqa: SLF001

    base_catalog_state = v0924_features._catalog_state_sync  # noqa: SLF001

    def catalog_state_v0927(path: Path) -> list[dict[str, Any]]:
        items = base_catalog_state(path)
        for item in items:
            catalog_metadata_fallback(item)
        return items

    v0924_features._catalog_state_sync = catalog_state_v0927  # type: ignore[attr-defined]  # noqa: SLF001

    from .database import AnimalHealthDatabase

    base_create = AnimalHealthDatabase._create_event_in_connection

    def create_event_v0927(self, connection, *args, **kwargs):
        event = base_create(self, connection, *args, **kwargs)
        return enrich_event_in_connection(connection, event.id) or event

    AnimalHealthDatabase._create_event_in_connection = create_event_v0927  # type: ignore[method-assign]


async def async_setup_v0927_features(hass: HomeAssistant) -> None:
    target_fields = {
        vol.Required("target_scope"): vol.In(("general", "group", "animals")),
        vol.Optional("animal_ids", default=[]): [required_text],
        vol.Optional("group_id"): str,
    }

    @websocket_api.websocket_command({vol.Required("type"): _STATE_COMMAND})
    @websocket_api.async_response
    async def websocket_state(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(state_sync, _database_path(hass))
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0927_state_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({
        vol.Required("type"): _PRODUCT_SAVE_COMMAND,
        vol.Required("kind"): vol.In(PRODUCT_KINDS),
        vol.Optional("item_id"): str,
        vol.Optional("name"): str,
        vol.Optional("target_species", default=[]): [str],
        vol.Optional("fields", default={}): dict,
    })
    @websocket_api.async_response
    async def websocket_product_save(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(save_product_sync, _database_path(hass), msg)
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0927_product_save_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({vol.Required("type"): _PRODUCT_ARCHIVE_COMMAND, vol.Required("item_id"): required_text, vol.Required("hidden"): bool})
    @websocket_api.async_response
    async def websocket_product_archive(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(archive_product_sync, _database_path(hass), msg["item_id"], bool(msg["hidden"]))
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0927_product_archive_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({vol.Required("type"): _PRODUCT_RESET_COMMAND, vol.Required("item_id"): required_text})
    @websocket_api.async_response
    async def websocket_product_reset(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(reset_product_sync, _database_path(hass), msg["item_id"])
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0927_product_reset_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({
        vol.Required("type"): _TASK_GABE_EXECUTE_COMMAND,
        vol.Required("occurrence_id"): required_text,
        vol.Required("gabe_type"): vol.In((GABE_DEWORMING, GABE_SUPPLEMENT, GABE_FEED)),
        vol.Required("product_name"): required_text,
        vol.Required("dose"): vol.Coerce(float),
        vol.Required("dose_unit"): required_text,
        vol.Optional("route"): str,
        vol.Optional("occurred_date"): str,
        vol.Optional("occurred_time"): str,
        vol.Optional("notes"): str,
        vol.Optional("deviation_reason"): str,
        vol.Optional("dose_basis"): str,
        vol.Optional("feed_status"): str,
    })
    @websocket_api.async_response
    async def websocket_task_gabe_execute(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            occurred_at, _precision, _day = v0923_features._event_when(hass, msg.get("occurred_date"), msg.get("occurred_time"))  # noqa: SLF001
            gabe_type = str(msg["gabe_type"])
            expected_kind = {GABE_DEWORMING: task_kinds.TASK_KIND_DEWORMING, GABE_SUPPLEMENT: task_kinds.TASK_KIND_SUPPLEMENT, GABE_FEED: task_kinds.TASK_KIND_FEED}[gabe_type]
            dose = float(msg["dose"])
            if dose <= 0:
                raise ValueError("Dose/amount must be greater than zero")
            actual = {"gabe_type": gabe_type, "product_name": msg["product_name"], "dose": dose, "dose_unit": msg["dose_unit"]}
            for key in ("route", "dose_basis", "feed_status"):
                if text(msg.get(key)):
                    actual[key] = text(msg[key])
            event_data = dict(actual)
            event_data["medication_name"] = msg["product_name"]
            result = await task_records.TaskRecordStore(hass).execute(
                occurrence_id=msg["occurrence_id"], expected_kind=expected_kind, performed_at=occurred_at,
                actual=actual, notes=text(msg.get("notes")) or None, deviation_reason=text(msg.get("deviation_reason")) or None,
                event_type="care" if gabe_type == GABE_FEED else "medication", event_title=msg["product_name"],
                event_value=dose, event_unit=msg["dose_unit"], event_data=event_data,
            )
            event_dict = dict(result.event) if result.event else None
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0927_task_gabe_execute_failed", str(err))
            return
        connection.send_result(msg["id"], {"occurrence": result.occurrence, "event": event_dict})

    @websocket_api.websocket_command({
        vol.Required("type"): _RECORD_COMMAND,
        **target_fields,
        vol.Required("items"): vol.All([dict], vol.Length(min=1, max=30)),
        vol.Optional("occurred_date"): str,
        vol.Optional("occurred_time"): str,
        vol.Optional("notes"): str,
    })
    @websocket_api.async_response
    async def websocket_record(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        path = _database_path(hass)
        try:
            target_ids, metadata = await hass.async_add_executor_job(v0926_features._resolve_target_sync, path, msg["target_scope"], list(msg.get("animal_ids") or []), msg.get("group_id"))  # noqa: SLF001
            if metadata["target_scope"] == "general":
                raise ValueError("An administration requires an animal or group target")
            occurred_at, precision, day = v0923_features._event_when(hass, msg.get("occurred_date"), msg.get("occurred_time"))  # noqa: SLF001
            result = await hass.async_add_executor_job(record_gabe_sync, runtime.database, path, target_ids, metadata, occurred_at, day, precision, msg.get("notes"), list(msg["items"]))
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0927_gabe_record_failed", str(err))
            return
        connection.send_result(msg["id"], {"events": result, "target": metadata})

    websocket_api.async_register_command(hass, websocket_state)
    websocket_api.async_register_command(hass, websocket_product_save)
    websocket_api.async_register_command(hass, websocket_product_archive)
    websocket_api.async_register_command(hass, websocket_product_reset)
    websocket_api.async_register_command(hass, websocket_task_gabe_execute)
    websocket_api.async_register_command(hass, websocket_record)
