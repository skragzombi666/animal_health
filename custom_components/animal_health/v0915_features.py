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
from homeassistant.util import dt as dt_util

from .const import DATABASE_NAME, DOMAIN, SYMPTOM_SEVERITIES
from .runtime import AnimalHealthRuntimeData

_STATE_COMMAND = f"{DOMAIN}/v0915/state"
_SAVE_SYMPTOM_COMMAND = f"{DOMAIN}/v0915/symptom/save"
_ARCHIVE_SYMPTOM_COMMAND = f"{DOMAIN}/v0915/symptom/archive"
_RECORD_SYMPTOMS_COMMAND = f"{DOMAIN}/v0915/symptoms/record"


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _database_path(hass: HomeAssistant) -> Path:
    try:
        return _runtime_data(hass).feature_store.database_path
    except RuntimeError:
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


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def _initialise_sync(path: Path) -> None:
    with _connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS v0915_symptoms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL UNIQUE,
                is_archived INTEGER NOT NULL DEFAULT 0
                    CHECK (is_archived IN (0, 1)),
                archived_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_v0915_symptoms_active_name
                ON v0915_symptoms(is_archived, name COLLATE NOCASE, id);
            """
        )


def _symptoms_sync(path: Path) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT id,name,is_archived,archived_at,created_at,updated_at
            FROM v0915_symptoms
            ORDER BY is_archived,name COLLATE NOCASE,id
            """
        ).fetchall()
    return [
        {
            "id": int(row["id"]),
            "name": str(row["name"]),
            "is_archived": bool(row["is_archived"]),
            "archived_at": str(row["archived_at"] or ""),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }
        for row in rows
    ]


def _state_sync(path: Path) -> dict[str, Any]:
    return {"symptoms": _symptoms_sync(path)}


def _save_symptom_sync(
    path: Path,
    symptom_id: int | None,
    name: str,
) -> dict[str, Any]:
    clean = _required_text(name)
    normalized = _normalise(clean)
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        if symptom_id is not None:
            cursor = connection.execute(
                """
                UPDATE v0915_symptoms
                SET name=?,normalized_name=?,updated_at=?
                WHERE id=?
                """,
                (clean, normalized, now, symptom_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(symptom_id)
            target_id = symptom_id
        else:
            connection.execute(
                """
                INSERT INTO v0915_symptoms(
                    name,normalized_name,is_archived,archived_at,created_at,updated_at
                ) VALUES(?,?,0,NULL,?,?)
                ON CONFLICT(normalized_name) DO UPDATE SET
                    name=excluded.name,
                    is_archived=0,
                    archived_at=NULL,
                    updated_at=excluded.updated_at
                """,
                (clean, normalized, now, now),
            )
            row = connection.execute(
                "SELECT id FROM v0915_symptoms WHERE normalized_name=?",
                (normalized,),
            ).fetchone()
            if row is None:
                raise RuntimeError("Saved symptom could not be loaded")
            target_id = int(row["id"])
    return next(item for item in _symptoms_sync(path) if item["id"] == target_id)


def _archive_symptom_sync(
    path: Path,
    symptom_id: int,
    archived: bool,
) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        cursor = connection.execute(
            """
            UPDATE v0915_symptoms
            SET is_archived=?,archived_at=?,updated_at=?
            WHERE id=?
            """,
            (1 if archived else 0, now if archived else None, now, symptom_id),
        )
        if cursor.rowcount == 0:
            raise KeyError(symptom_id)
    return next(item for item in _symptoms_sync(path) if item["id"] == symptom_id)


def _event_datetime_utc(hass: HomeAssistant, raw: Any) -> datetime:
    if raw in (None, ""):
        return datetime.now(UTC).replace(microsecond=0)
    value = raw if isinstance(raw, datetime) else datetime.fromisoformat(str(raw))
    if value.tzinfo is None:
        timezone = dt_util.get_time_zone(hass.config.time_zone) or UTC
        value = value.replace(tzinfo=timezone)
    return value.astimezone(UTC).replace(microsecond=0)


def _clean_symptom_list(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = _required_text(raw)
        key = _normalise(value)
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    if not result:
        raise vol.Invalid("at least one symptom is required")
    if len(result) > 30:
        raise vol.Invalid("at most 30 symptoms can be recorded together")
    return result


async def async_initialize_v0915_features(hass: HomeAssistant) -> None:
    await hass.async_add_executor_job(_initialise_sync, _database_path(hass))


def async_setup_v0915_features(hass: HomeAssistant) -> None:
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
            connection.send_error(msg["id"], "v0915_state_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SAVE_SYMPTOM_COMMAND,
            vol.Optional("symptom_id"): vol.Coerce(int),
            vol.Required("name"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_save_symptom(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _save_symptom_sync,
                _database_path(hass),
                msg.get("symptom_id"),
                msg["name"],
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0915_symptom_save_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _ARCHIVE_SYMPTOM_COMMAND,
            vol.Required("symptom_id"): vol.Coerce(int),
            vol.Required("archived"): bool,
        }
    )
    @websocket_api.async_response
    async def websocket_archive_symptom(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _archive_symptom_sync,
                _database_path(hass),
                int(msg["symptom_id"]),
                bool(msg["archived"]),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0915_symptom_archive_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _RECORD_SYMPTOMS_COMMAND,
            vol.Required("animal_id"): _required_text,
            vol.Required("symptoms"): vol.All(
                [_required_text],
                vol.Length(min=1, max=30),
            ),
            vol.Optional("severity", default="moderate"): vol.In(SYMPTOM_SEVERITIES),
            vol.Optional("occurred_at"): _optional_text,
            vol.Optional("notes"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_record_symptoms(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        runtime = _runtime_data(hass)
        try:
            symptoms = _clean_symptom_list(list(msg["symptoms"]))
            event = await runtime.database.create_event(
                animal_id=msg["animal_id"],
                event_type="symptom",
                occurred_at=_event_datetime_utc(hass, msg.get("occurred_at")),
                title="symptoms_recorded_015",
                notes=msg.get("notes"),
                data={
                    "symptoms": symptoms,
                    "severity": msg.get("severity") or "moderate",
                },
            )
            await runtime.coordinator.async_request_refresh()
        except KeyError:
            connection.send_error(msg["id"], "animal_not_found", "Animal not found")
            return
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0915_symptoms_record_failed", str(err))
            return
        connection.send_result(msg["id"], event.as_dict())

    websocket_api.async_register_command(hass, websocket_state)
    websocket_api.async_register_command(hass, websocket_save_symptom)
    websocket_api.async_register_command(hass, websocket_archive_symptom)
    websocket_api.async_register_command(hass, websocket_record_symptoms)
