from __future__ import annotations

from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from . import v0913_patches, v0927_gabe
from .const import DATABASE_NAME, DOMAIN
from .v0928_data import (
    PRODUCT_KINDS,
    archive_product_sync,
    delete_database_sync,
    delete_product_sync,
    import_database_sync,
    initialize_product_databases_sync,
    load_product_snapshot,
    medication_snapshot_for_name,
    reset_product_sync,
    save_database_sync,
    save_product_sync,
    state_sync,
    toggle_database_sync,
)

_STATE_COMMAND = f"{DOMAIN}/v0928/state"
_DATABASE_SAVE_COMMAND = f"{DOMAIN}/v0928/database/save"
_DATABASE_TOGGLE_COMMAND = f"{DOMAIN}/v0928/database/toggle"
_DATABASE_DELETE_COMMAND = f"{DOMAIN}/v0928/database/delete"
_DATABASE_IMPORT_COMMAND = f"{DOMAIN}/v0928/database/import"
_PRODUCT_SAVE_COMMAND = f"{DOMAIN}/v0928/product/save"
_PRODUCT_ARCHIVE_COMMAND = f"{DOMAIN}/v0928/product/archive"
_PRODUCT_RESET_COMMAND = f"{DOMAIN}/v0928/product/reset"
_PRODUCT_DELETE_COMMAND = f"{DOMAIN}/v0928/product/delete"
_PATCHED = False


def _database_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(DATABASE_NAME))


def _required_text(value: Any) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise vol.Invalid("value must not be empty")
    return cleaned


async def async_initialize_v0928_features(hass: HomeAssistant) -> None:
    await hass.async_add_executor_job(
        initialize_product_databases_sync, _database_path(hass)
    )


def apply_v0928_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True
    v0927_gabe.load_product_snapshot = load_product_snapshot
    v0913_patches.medication_snapshot_for_name = medication_snapshot_for_name


async def async_setup_v0928_features(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command({vol.Required("type"): _STATE_COMMAND})
    @websocket_api.async_response
    async def websocket_state(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(
                state_sync, _database_path(hass)
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0928_state_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _DATABASE_SAVE_COMMAND,
            vol.Optional("database_id"): str,
            vol.Optional("name"): str,
            vol.Optional("product_types", default=[]): [str],
            vol.Optional("fields", default={}): dict,
        }
    )
    @websocket_api.async_response
    async def websocket_database_save(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(
                save_database_sync, _database_path(hass), msg
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(
                msg["id"], "v0928_database_save_failed", str(err)
            )
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _DATABASE_TOGGLE_COMMAND,
            vol.Required("database_id"): _required_text,
            vol.Required("enabled"): bool,
        }
    )
    @websocket_api.async_response
    async def websocket_database_toggle(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(
                toggle_database_sync,
                _database_path(hass),
                msg["database_id"],
                bool(msg["enabled"]),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(
                msg["id"], "v0928_database_toggle_failed", str(err)
            )
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _DATABASE_DELETE_COMMAND,
            vol.Required("database_id"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_database_delete(hass, connection, msg) -> None:
        try:
            await hass.async_add_executor_job(
                delete_database_sync,
                _database_path(hass),
                msg["database_id"],
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(
                msg["id"], "v0928_database_delete_failed", str(err)
            )
            return
        connection.send_result(msg["id"], {"deleted": msg["database_id"]})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _DATABASE_IMPORT_COMMAND,
            vol.Required("document"): dict,
        }
    )
    @websocket_api.async_response
    async def websocket_database_import(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(
                import_database_sync, _database_path(hass), msg
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(
                msg["id"], "v0928_database_import_failed", str(err)
            )
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _PRODUCT_SAVE_COMMAND,
            vol.Required("kind"): vol.In(PRODUCT_KINDS),
            vol.Optional("database_id"): str,
            vol.Optional("item_id"): str,
            vol.Optional("name"): str,
            vol.Optional("target_species", default=[]): [str],
            vol.Optional("fields", default={}): dict,
        }
    )
    @websocket_api.async_response
    async def websocket_product_save(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(
                save_product_sync, _database_path(hass), msg
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(
                msg["id"], "v0928_product_save_failed", str(err)
            )
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _PRODUCT_ARCHIVE_COMMAND,
            vol.Required("item_id"): _required_text,
            vol.Required("hidden"): bool,
        }
    )
    @websocket_api.async_response
    async def websocket_product_archive(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(
                archive_product_sync,
                _database_path(hass),
                msg["item_id"],
                bool(msg["hidden"]),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(
                msg["id"], "v0928_product_archive_failed", str(err)
            )
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _PRODUCT_RESET_COMMAND,
            vol.Required("item_id"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_product_reset(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(
                reset_product_sync, _database_path(hass), msg["item_id"]
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(
                msg["id"], "v0928_product_reset_failed", str(err)
            )
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _PRODUCT_DELETE_COMMAND,
            vol.Required("item_id"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_product_delete(hass, connection, msg) -> None:
        try:
            await hass.async_add_executor_job(
                delete_product_sync, _database_path(hass), msg["item_id"]
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(
                msg["id"], "v0928_product_delete_failed", str(err)
            )
            return
        connection.send_result(msg["id"], {"deleted": msg["item_id"]})

    websocket_api.async_register_command(hass, websocket_state)
    websocket_api.async_register_command(hass, websocket_database_save)
    websocket_api.async_register_command(hass, websocket_database_toggle)
    websocket_api.async_register_command(hass, websocket_database_delete)
    websocket_api.async_register_command(hass, websocket_database_import)
    websocket_api.async_register_command(hass, websocket_product_save)
    websocket_api.async_register_command(hass, websocket_product_archive)
    websocket_api.async_register_command(hass, websocket_product_reset)
    websocket_api.async_register_command(hass, websocket_product_delete)
