from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from . import v0924_features as features

_RECORD_EVENT_COMMAND = f"{DOMAIN}/v0924/event/record"


def async_setup_v0924_capture(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command(
        {
            vol.Required("type"): _RECORD_EVENT_COMMAND,
            vol.Required("animal_id"): features._required_text,
            vol.Optional("entry_type_id"): features._optional_text,
            vol.Optional("entry_type_label"): features._optional_text,
            vol.Required("title"): features._required_text,
            vol.Optional("notes"): features._optional_text,
            vol.Optional("occurred_date"): features._optional_text,
            vol.Optional("occurred_time"): features._optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_record_event(hass, connection, msg: dict[str, Any]) -> None:
        runtime = features._runtime_data(hass)
        try:
            when, precision, day = features._event_when(
                hass, msg.get("occurred_date"), msg.get("occurred_time")
            )
            entry_type_id = str(msg.get("entry_type_id") or "").strip()
            entry_type_label = str(msg.get("entry_type_label") or "").strip()
            storage_type = "other"
            data: dict[str, Any] = features._precision_data(precision, day)
            with runtime.database._connect() as database_connection:  # noqa: SLF001
                if entry_type_id:
                    master = features._master_item(database_connection, "entry_type", entry_type_id)
                    if master is None:
                        raise KeyError(entry_type_id)
                    if bool(master["is_hidden"]):
                        raise ValueError("The selected entry type is hidden")
                    storage_type = str(master["storage_value"])
                    entry_type_label = str(master["override_label"] or master["base_label_de"])
                    data["entry_type_id"] = entry_type_id
                    data["entry_type_label"] = entry_type_label
                elif entry_type_label:
                    data["entry_type_label"] = entry_type_label
                    data["entry_type_free_text"] = True
            event = await runtime.database.create_event(
                animal_id=msg["animal_id"],
                event_type=storage_type,
                occurred_at=when,
                title=msg["title"],
                notes=msg.get("notes"),
                data=data,
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0924_event_record_failed", str(err))
            return
        connection.send_result(msg["id"], event.as_dict())

    websocket_api.async_register_command(hass, websocket_record_event)
