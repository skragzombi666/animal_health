from __future__ import annotations

from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .runtime import AnimalHealthRuntimeData

_PREVIOUS_WEIGHT_COMMAND = f"{DOMAIN}/v080/previous_weight"


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


def _previous_weight_sync(runtime: AnimalHealthRuntimeData, event_id: str) -> dict[str, Any] | None:
    with runtime.feature_store._connect() as connection:
        current = connection.execute(
            """
            SELECT animal_id, occurred_at, created_at
            FROM events
            WHERE id = ? AND event_type = 'weight'
            """,
            (event_id,),
        ).fetchone()
        if current is None:
            raise KeyError(event_id)
        previous = connection.execute(
            """
            SELECT id, value, unit, occurred_at
            FROM events
            WHERE animal_id = ?
              AND event_type = 'weight'
              AND value IS NOT NULL
              AND (
                    occurred_at < ?
                    OR (occurred_at = ? AND created_at < ?)
              )
            ORDER BY occurred_at DESC, created_at DESC, id DESC
            LIMIT 1
            """,
            (
                str(current["animal_id"]),
                str(current["occurred_at"]),
                str(current["occurred_at"]),
                str(current["created_at"]),
            ),
        ).fetchone()
    if previous is None:
        return None
    return {
        "id": str(previous["id"]),
        "value": previous["value"],
        "unit": previous["unit"],
        "occurred_at": str(previous["occurred_at"]),
    }


def async_setup_v080_weight_api(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command(
        {
            vol.Required("type"): _PREVIOUS_WEIGHT_COMMAND,
            vol.Required("event_id"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_previous_weight(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            runtime = _runtime_data(hass)
            previous = await hass.async_add_executor_job(
                _previous_weight_sync, runtime, msg["event_id"]
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "previous_weight_failed", str(err))
            return
        connection.send_result(msg["id"], {"previous": previous})

    websocket_api.async_register_command(hass, websocket_previous_weight)
