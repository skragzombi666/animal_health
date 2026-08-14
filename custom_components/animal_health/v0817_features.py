from __future__ import annotations

import json
import re
import secrets
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import ADMINISTRATION_ROUTES, DOMAIN, DOSE_UNITS
from .database import AnimalHealthDatabase
from .runtime import AnimalHealthRuntimeData

_STATE_COMMAND = f"{DOMAIN}/v0817/state"
_SAVE_MEDICATION_COMMAND = f"{DOMAIN}/v0817/medication/save"
_UPDATE_SETTINGS_COMMAND = f"{DOMAIN}/v0817/settings/update"
_RECORD_MEDICATIONS_COMMAND = f"{DOMAIN}/v0817/medications/record"


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _database_path(hass: HomeAssistant) -> Path:
    return _runtime_data(hass).feature_store.database_path


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _required_text(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise vol.Invalid("value must not be empty")
    return text


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def _initialize_sync(path: Path) -> None:
    with _connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS v0817_medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                species_id TEXT NOT NULL DEFAULT '',
                default_unit TEXT NOT NULL,
                default_route TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(normalized_name, species_id)
            );
            CREATE INDEX IF NOT EXISTS idx_v0817_medications_name
                ON v0817_medications(normalized_name, species_id);
            """
        )


def _state_sync(path: Path) -> dict[str, Any]:
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT id, name, species_id, default_unit, default_route
            FROM v0817_medications
            ORDER BY name COLLATE NOCASE, species_id, id
            """
        ).fetchall()
        setting = connection.execute(
            "SELECT value FROM v081_settings WHERE key = 'off_label_enabled'"
        ).fetchone()
    return {
        "off_label_enabled": bool(setting and str(setting["value"]).strip() == "1"),
        "medications": [
            {
                "id": int(row["id"]),
                "name": str(row["name"]),
                "species_id": str(row["species_id"] or ""),
                "default_unit": str(row["default_unit"]),
                "default_route": str(row["default_route"] or ""),
            }
            for row in rows
        ],
    }


def _save_medication_sync(
    path: Path,
    name: str,
    species_id: str | None,
    default_unit: str,
    default_route: str | None,
) -> dict[str, Any]:
    clean_name = re.sub(r"\s+", " ", name.strip())
    species = str(species_id or "").strip().casefold()
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        connection.execute(
            """
            INSERT INTO v0817_medications (
                name, normalized_name, species_id, default_unit, default_route,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(normalized_name, species_id) DO UPDATE SET
                name = excluded.name,
                default_unit = excluded.default_unit,
                default_route = excluded.default_route,
                updated_at = excluded.updated_at
            """,
            (
                clean_name,
                _normalize(clean_name),
                species,
                default_unit,
                default_route,
                now,
                now,
            ),
        )
        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='animal_custom_values'"
        ).fetchone():
            connection.execute(
                """
                INSERT INTO animal_custom_values (
                    kind, species_id, breed_context, value, normalized_value,
                    created_at, updated_at
                ) VALUES ('medication', ?, '', ?, ?, ?, ?)
                ON CONFLICT(kind, species_id, breed_context, normalized_value) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (species, clean_name, _normalize(clean_name), now, now),
            )
        row = connection.execute(
            """
            SELECT id, name, species_id, default_unit, default_route
            FROM v0817_medications
            WHERE normalized_name = ? AND species_id = ?
            """,
            (_normalize(clean_name), species),
        ).fetchone()
    if row is None:
        raise RuntimeError("Saved medication could not be loaded")
    return {
        "id": int(row["id"]),
        "name": str(row["name"]),
        "species_id": str(row["species_id"] or ""),
        "default_unit": str(row["default_unit"]),
        "default_route": str(row["default_route"] or ""),
    }


def _save_settings_sync(path: Path, off_label_enabled: bool) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        connection.execute(
            """
            INSERT INTO v081_settings (key, value, updated_at)
            VALUES ('off_label_enabled', ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            ("1" if off_label_enabled else "0", now),
        )
    return _state_sync(path)


def _event_datetime_utc(hass: HomeAssistant, raw: Any) -> datetime:
    if raw in (None, ""):
        return datetime.now(UTC).replace(microsecond=0)
    value = raw if isinstance(raw, datetime) else datetime.fromisoformat(str(raw))
    if value.tzinfo is None:
        timezone = dt_util.get_time_zone(hass.config.time_zone) or UTC
        value = value.replace(tzinfo=timezone)
    return value.astimezone(UTC).replace(microsecond=0)


def _validate_item(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError("Each medication item must be an object")
    name = str(item.get("product_name") or "").strip()
    if not name:
        raise ValueError("Medication name is required")
    try:
        dose = float(item.get("dose"))
    except (TypeError, ValueError) as err:
        raise ValueError("Dose must be a number") from err
    if dose <= 0:
        raise ValueError("Dose must be greater than zero")
    unit = str(item.get("dose_unit") or "").strip()
    if unit not in DOSE_UNITS:
        raise ValueError(f"Unsupported dose unit: {unit}")
    route = str(item.get("route") or "").strip() or None
    if route is not None and route not in ADMINISTRATION_ROUTES:
        raise ValueError(f"Unsupported administration route: {route}")
    product_type = str(item.get("product_type") or "medication").strip()
    if product_type not in {"medication", "supplement"}:
        raise ValueError(f"Unsupported product type: {product_type}")
    correction = str(item.get("correction_event_id") or "").strip() or None
    return {
        "product_name": name,
        "dose": dose,
        "dose_unit": unit,
        "route": route,
        "product_type": product_type,
        "correction_event_id": correction,
        "notes": str(item.get("notes") or "").strip() or None,
    }


def _record_medications_sync(
    database: AnimalHealthDatabase,
    animal_id: str,
    occurred_at: datetime,
    common_notes: str | None,
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not items:
        raise ValueError("At least one medication is required")
    validated = [_validate_item(item) for item in items]
    batch_id = "MB-" + secrets.token_hex(6).upper()
    results = []
    with database._connect() as connection:
        if database._get_animal_from_connection(connection, animal_id) is None:
            raise KeyError(animal_id)
        for item in validated:
            correction = item["correction_event_id"]
            if correction:
                corrected = connection.execute(
                    "SELECT animal_id, event_type FROM events WHERE id = ?",
                    (correction,),
                ).fetchone()
                if corrected is None:
                    raise KeyError(correction)
                if str(corrected["animal_id"]) != animal_id:
                    raise ValueError("A correction must remain on the same animal")
                if str(corrected["event_type"]) != "medication":
                    raise ValueError("Only medication events can be edited here")
            data = {
                "medication_name": item["product_name"],
                "product_type": item["product_type"],
                "entry_mode": "correction" if correction else "batch" if len(validated) > 1 else "spontaneous",
                "batch_id": batch_id,
            }
            if item["route"]:
                data["route"] = item["route"]
            event = database._create_event_in_connection(
                connection,
                animal_id=animal_id,
                event_type="medication",
                occurred_at=occurred_at,
                title=item["product_name"],
                notes=item["notes"] or common_notes,
                value=item["dose"],
                unit=item["dose_unit"],
                correction_of_event_id=correction,
                data=data,
            )
            results.append(event.as_dict())
    return results


async def async_initialize_v0817_features(hass: HomeAssistant) -> None:
    await hass.async_add_executor_job(_initialize_sync, _database_path(hass))


def async_setup_v0817_features(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command({vol.Required("type"): _STATE_COMMAND})
    @websocket_api.async_response
    async def websocket_state(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(_state_sync, _database_path(hass))
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0817_state_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SAVE_MEDICATION_COMMAND,
            vol.Required("name"): _required_text,
            vol.Optional("species_id"): _optional_text,
            vol.Required("default_unit"): vol.In(DOSE_UNITS),
            vol.Optional("default_route"): vol.Any(None, "", vol.In(ADMINISTRATION_ROUTES)),
        }
    )
    @websocket_api.async_response
    async def websocket_save_medication(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _save_medication_sync,
                _database_path(hass),
                msg["name"],
                msg.get("species_id"),
                msg["default_unit"],
                msg.get("default_route") or None,
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0817_medication_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _UPDATE_SETTINGS_COMMAND,
            vol.Required("off_label_enabled"): bool,
        }
    )
    @websocket_api.async_response
    async def websocket_update_settings(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _save_settings_sync,
                _database_path(hass),
                bool(msg["off_label_enabled"]),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0817_settings_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _RECORD_MEDICATIONS_COMMAND,
            vol.Required("animal_id"): _required_text,
            vol.Optional("occurred_at"): _optional_text,
            vol.Optional("notes"): _optional_text,
            vol.Required("items"): list,
        }
    )
    @websocket_api.async_response
    async def websocket_record_medications(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        runtime = _runtime_data(hass)
        try:
            occurred_at = _event_datetime_utc(hass, msg.get("occurred_at"))
            result = await hass.async_add_executor_job(
                _record_medications_sync,
                runtime.database,
                msg["animal_id"],
                occurred_at,
                msg.get("notes"),
                msg["items"],
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0817_record_failed", str(err))
            return
        connection.send_result(msg["id"], {"events": result})

    websocket_api.async_register_command(hass, websocket_state)
    websocket_api.async_register_command(hass, websocket_save_medication)
    websocket_api.async_register_command(hass, websocket_update_settings)
    websocket_api.async_register_command(hass, websocket_record_medications)
