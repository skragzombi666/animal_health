from __future__ import annotations

import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .const import ADMINISTRATION_ROUTES, DATABASE_NAME, DOMAIN, DOSE_UNITS
from .runtime import AnimalHealthRuntimeData

_STATE_COMMAND = f"{DOMAIN}/v0911/state"
_SAVE_TREATMENT_COMMAND = f"{DOMAIN}/v0911/treatment/save"
_DELETE_TREATMENT_COMMAND = f"{DOMAIN}/v0911/treatment/delete"
_LIST_TARGETS = ("medication", "task", "both")


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _database_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(DATABASE_NAME))


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _required_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
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
            CREATE TABLE IF NOT EXISTS v0911_treatment_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                species_id TEXT NOT NULL DEFAULT '',
                list_as TEXT NOT NULL DEFAULT 'task'
                    CHECK (list_as IN ('medication', 'task', 'both')),
                description TEXT,
                default_unit TEXT NOT NULL DEFAULT 'dose',
                default_route TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(normalized_name, species_id)
            );
            CREATE INDEX IF NOT EXISTS idx_v0911_treatment_plans_name
                ON v0911_treatment_plans(normalized_name, species_id);
            CREATE INDEX IF NOT EXISTS idx_v0911_treatment_plans_list_as
                ON v0911_treatment_plans(list_as, species_id);
            """
        )


def _row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "name": str(row["name"]),
        "species_id": str(row["species_id"] or ""),
        "list_as": str(row["list_as"]),
        "description": str(row["description"] or ""),
        "default_unit": str(row["default_unit"] or "dose"),
        "default_route": str(row["default_route"] or ""),
    }


def _state_sync(path: Path) -> dict[str, Any]:
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT id, name, species_id, list_as, description,
                   default_unit, default_route
            FROM v0911_treatment_plans
            ORDER BY name COLLATE NOCASE, species_id, id
            """
        ).fetchall()
    return {"treatment_plans": [_row_dict(row) for row in rows]}


def _save_treatment_sync(
    path: Path,
    name: str,
    species_id: str | None,
    list_as: str,
    description: str | None,
    default_unit: str,
    default_route: str | None,
) -> dict[str, Any]:
    clean_name = _required_text(name)
    species = str(species_id or "").strip().casefold()
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        connection.execute(
            """
            INSERT INTO v0911_treatment_plans (
                name, normalized_name, species_id, list_as, description,
                default_unit, default_route, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(normalized_name, species_id) DO UPDATE SET
                name = excluded.name,
                list_as = excluded.list_as,
                description = excluded.description,
                default_unit = excluded.default_unit,
                default_route = excluded.default_route,
                updated_at = excluded.updated_at
            """,
            (
                clean_name,
                _normalize(clean_name),
                species,
                list_as,
                description,
                default_unit,
                default_route,
                now,
                now,
            ),
        )
        row = connection.execute(
            """
            SELECT id, name, species_id, list_as, description,
                   default_unit, default_route
            FROM v0911_treatment_plans
            WHERE normalized_name = ? AND species_id = ?
            """,
            (_normalize(clean_name), species),
        ).fetchone()
    if row is None:
        raise RuntimeError("Saved treatment plan could not be loaded")
    return _row_dict(row)


def _delete_treatment_sync(path: Path, treatment_id: int) -> None:
    with _connect(path) as connection:
        cursor = connection.execute(
            "DELETE FROM v0911_treatment_plans WHERE id = ?",
            (treatment_id,),
        )
        if cursor.rowcount < 1:
            raise KeyError(treatment_id)


async def async_initialize_v0911_features(hass: HomeAssistant) -> None:
    await hass.async_add_executor_job(_initialize_sync, _database_path(hass))


def async_setup_v0911_features(hass: HomeAssistant) -> None:
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
            connection.send_error(msg["id"], "v0911_state_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SAVE_TREATMENT_COMMAND,
            vol.Required("name"): _required_text,
            vol.Optional("species_id"): _optional_text,
            vol.Required("list_as"): vol.In(_LIST_TARGETS),
            vol.Optional("description"): _optional_text,
            vol.Optional("default_unit", default="dose"): vol.In(DOSE_UNITS),
            vol.Optional("default_route"): vol.Any(
                None,
                "",
                vol.In(ADMINISTRATION_ROUTES),
            ),
        }
    )
    @websocket_api.async_response
    async def websocket_save_treatment(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _save_treatment_sync,
                _database_path(hass),
                msg["name"],
                msg.get("species_id"),
                msg["list_as"],
                msg.get("description"),
                msg.get("default_unit") or "dose",
                msg.get("default_route") or None,
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0911_treatment_save_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _DELETE_TREATMENT_COMMAND,
            vol.Required("treatment_id"): vol.Coerce(int),
        }
    )
    @websocket_api.async_response
    async def websocket_delete_treatment(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            await hass.async_add_executor_job(
                _delete_treatment_sync,
                _database_path(hass),
                int(msg["treatment_id"]),
            )
        except KeyError:
            connection.send_error(
                msg["id"],
                "v0911_treatment_missing",
                "The selected treatment plan no longer exists",
            )
            return
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0911_treatment_delete_failed", str(err))
            return
        connection.send_result(msg["id"], {"deleted": True})

    websocket_api.async_register_command(hass, websocket_state)
    websocket_api.async_register_command(hass, websocket_save_treatment)
    websocket_api.async_register_command(hass, websocket_delete_treatment)
