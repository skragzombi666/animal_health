from __future__ import annotations

from functools import partial
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .v081_features import (
    _GROUP_EVENT_TYPES,
    _create_group_event_sync,
    _database_path,
    _event_datetime_utc,
    _optional_datetime,
    _optional_text,
    _positive_number,
    _required_text,
)

_CREATE_GROUP_EVENT_COMMAND = f"{DOMAIN}/v081/group_event/create_safe"


def async_setup_v081_fixes(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command(
        {
            vol.Required("type"): _CREATE_GROUP_EVENT_COMMAND,
            vol.Required("group_id"): _required_text,
            vol.Required("event_type"): vol.In(_GROUP_EVENT_TYPES),
            vol.Required("title"): _required_text,
            vol.Optional("occurred_at"): _optional_datetime,
            vol.Optional("notes"): _optional_text,
            vol.Optional("value"): _positive_number,
            vol.Optional("unit"): _optional_text,
            vol.Optional("data", default={}): dict,
        }
    )
    @websocket_api.async_response
    async def websocket_create_group_event_safe(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            value = msg.get("value")
            unit = msg.get("unit")
            if (value is None) != (unit is None):
                raise ValueError("Value and unit must be supplied together")
            operation = partial(
                _create_group_event_sync,
                _database_path(hass),
                group_id=msg["group_id"],
                event_type=msg["event_type"],
                occurred_at=_event_datetime_utc(hass, msg.get("occurred_at")),
                title=msg["title"],
                notes=msg.get("notes"),
                value=value,
                unit=unit,
                data=msg.get("data") or {},
            )
            result = await hass.async_add_executor_job(operation)
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v081_group_event_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    websocket_api.async_register_command(hass, websocket_create_group_event_safe)
