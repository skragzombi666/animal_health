from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .feature_store import AnimalHealthFeatureStore
from .runtime import AnimalHealthRuntimeData

_GROUP_LIFECYCLE_COMMAND = f"{DOMAIN}/groups/lifecycle"
_ARCHIVE_GROUP_COMMAND = f"{DOMAIN}/groups/archive"
_RESTORE_GROUP_COMMAND = f"{DOMAIN}/groups/restore"


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _required_text(value: Any) -> str:
    text = str(value).strip()
    if not text:
        raise vol.Invalid("value must not be empty")
    return text


def _initialize_sync(store: AnimalHealthFeatureStore) -> None:
    with store._connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS animal_group_lifecycle (
                group_id TEXT PRIMARY KEY
                    REFERENCES animal_groups(id) ON DELETE CASCADE,
                archived_at TEXT NOT NULL
            )
            """
        )


def _lifecycle_sync(store: AnimalHealthFeatureStore) -> dict[str, str]:
    with store._connect() as connection:
        rows = connection.execute(
            "SELECT group_id, archived_at FROM animal_group_lifecycle"
        ).fetchall()
    return {str(row["group_id"]): str(row["archived_at"]) for row in rows}


def _archive_sync(store: AnimalHealthFeatureStore, group_id: str) -> str:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with store._connect() as connection:
        if connection.execute(
            "SELECT 1 FROM animal_groups WHERE id = ?", (group_id,)
        ).fetchone() is None:
            raise KeyError(group_id)
        connection.execute(
            """
            INSERT INTO animal_group_lifecycle (group_id, archived_at)
            VALUES (?, ?)
            ON CONFLICT(group_id) DO UPDATE SET archived_at = excluded.archived_at
            """,
            (group_id, now),
        )
    return now


def _restore_sync(store: AnimalHealthFeatureStore, group_id: str) -> None:
    with store._connect() as connection:
        if connection.execute(
            "SELECT 1 FROM animal_groups WHERE id = ?", (group_id,)
        ).fetchone() is None:
            raise KeyError(group_id)
        connection.execute(
            "DELETE FROM animal_group_lifecycle WHERE group_id = ?", (group_id,)
        )


async def async_initialize_group_lifecycle_store(
    store: AnimalHealthFeatureStore,
) -> None:
    await store._hass.async_add_executor_job(_initialize_sync, store)


def async_setup_group_lifecycle_api(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command(
        {vol.Required("type"): _GROUP_LIFECYCLE_COMMAND}
    )
    @websocket_api.async_response
    async def websocket_group_lifecycle(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            store = _runtime_data(hass).feature_store
            archived = await hass.async_add_executor_job(_lifecycle_sync, store)
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "group_lifecycle_failed", str(err))
            return
        connection.send_result(msg["id"], {"archived": archived})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _ARCHIVE_GROUP_COMMAND,
            vol.Required("group_id"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_archive_group(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            store = _runtime_data(hass).feature_store
            archived_at = await hass.async_add_executor_job(
                _archive_sync, store, msg["group_id"]
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "archive_group_failed", str(err))
            return
        connection.send_result(
            msg["id"],
            {"group_id": msg["group_id"], "archived_at": archived_at},
        )

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _RESTORE_GROUP_COMMAND,
            vol.Required("group_id"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_restore_group(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            store = _runtime_data(hass).feature_store
            await hass.async_add_executor_job(_restore_sync, store, msg["group_id"])
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "restore_group_failed", str(err))
            return
        connection.send_result(msg["id"], {"group_id": msg["group_id"]})

    websocket_api.async_register_command(hass, websocket_group_lifecycle)
    websocket_api.async_register_command(hass, websocket_archive_group)
    websocket_api.async_register_command(hass, websocket_restore_group)
