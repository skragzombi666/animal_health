from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .confirmation_policy import (
    CONFIRMATION_MODES,
    CONFIRMATION_ROUTINE,
    WEEK_START_KEYS,
    async_resolve_routine_occurrences,
    save_week_start_sync,
    set_week_start,
    update_confirmation_mode_sync,
)
from .const import DATABASE_NAME, DOMAIN
from .runtime import AnimalHealthRuntimeData

_UPDATE_MODE = f"{DOMAIN}/confirmation/mode/update"
_UPDATE_WEEK_START = f"{DOMAIN}/confirmation/week_start/update"


def _runtime(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def async_setup_confirmation_policy(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command(
        {
            vol.Required("type"): _UPDATE_MODE,
            vol.Required("task_id"): str,
            vol.Required("confirmation_mode"): vol.In(CONFIRMATION_MODES),
        }
    )
    @websocket_api.async_response
    async def update_mode(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        runtime = _runtime(hass)
        try:
            mode = await hass.async_add_executor_job(
                update_confirmation_mode_sync,
                Path(hass.config.path(DATABASE_NAME)),
                str(msg["task_id"]),
                str(msg["confirmation_mode"]),
            )
            if mode == CONFIRMATION_ROUTINE:
                await async_resolve_routine_occurrences(runtime.coordinator.task_store)
            await runtime.coordinator.async_request_refresh()
        except KeyError:
            connection.send_error(msg["id"], "task_not_found", "The selected task no longer exists")
            return
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "confirmation_mode_failed", str(err))
            return
        connection.send_result(msg["id"], {"task_id": msg["task_id"], "confirmation_mode": mode})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _UPDATE_WEEK_START,
            vol.Required("week_start"): vol.In(WEEK_START_KEYS),
        }
    )
    @websocket_api.async_response
    async def update_week_start(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        value = str(msg["week_start"])
        try:
            await hass.async_add_executor_job(
                save_week_start_sync,
                Path(hass.config.path(DATABASE_NAME)),
                value,
            )
            set_week_start(value)
            await _runtime(hass).coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "week_start_failed", str(err))
            return
        connection.send_result(msg["id"], {"week_start": value})

    websocket_api.async_register_command(hass, update_mode)
    websocket_api.async_register_command(hass, update_week_start)
