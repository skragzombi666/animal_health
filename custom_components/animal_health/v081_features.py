from __future__ import annotations

import json
import secrets
import sqlite3
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any, cast

import voluptuous as vol
from aiohttp import web

from homeassistant.components import websocket_api
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.http import KEY_HASS
from homeassistant.util import dt as dt_util

from .const import ADMINISTRATION_ROUTES, DOMAIN, DOSE_UNITS, WEIGHT_UNITS
from .database import AnimalHealthDatabase
from .exports import _build_pdf
from .runtime import AnimalHealthRuntimeData
from .task_kinds import TASK_KINDS
from .task_store import RECURRENCE_TYPES

_STATE_COMMAND = f"{DOMAIN}/v081/state"
_UPDATE_SETTINGS_COMMAND = f"{DOMAIN}/v081/settings/update"
_RECORD_PRODUCT_COMMAND = f"{DOMAIN}/v081/product/record"
_CORRECT_WEIGHT_COMMAND = f"{DOMAIN}/v081/weight/correct"
_CREATE_GROUP_EVENT_COMMAND = f"{DOMAIN}/v081/group_event/create"
_CREATE_GROUP_TASK_COMMAND = f"{DOMAIN}/v081/group_task/create"
_EXECUTE_GROUP_TASK_COMMAND = f"{DOMAIN}/v081/group_task/execute"
_GROUP_PDF_COMMAND = f"{DOMAIN}/v081/group_pdf"
_STATE_KEY = f"{DOMAIN}_v081"
_MAX_GROUP_EVENTS = 1000
_GROUP_EVENT_TYPES = (
    "observation",
    "symptom",
    "weight",
    "diagnosis",
    "treatment",
    "medication",
    "vaccination",
    "veterinary_visit",
    "care",
    "other",
)
_PRODUCT_TYPES = ("medication", "supplement")


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


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _positive_number(value: Any) -> float:
    number = float(value)
    if number <= 0:
        raise vol.Invalid("value must be greater than zero")
    return number


def _positive_integer(value: Any) -> int:
    number = int(value)
    if number < 1:
        raise vol.Invalid("value must be at least 1")
    return number


def _optional_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError as err:
        raise vol.Invalid("date and time must use ISO format") from err


def _date_value(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as err:
        raise vol.Invalid("date must use YYYY-MM-DD") from err


def _optional_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    return _date_value(value)


def _optional_time(value: Any) -> time | None:
    if value in (None, ""):
        return None
    if isinstance(value, time):
        return value.replace(second=0, microsecond=0)
    try:
        return time.fromisoformat(str(value)).replace(second=0, microsecond=0)
    except ValueError as err:
        raise vol.Invalid("time must use HH:MM") from err


def _event_datetime_utc(hass: HomeAssistant, value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC).replace(microsecond=0)
    if value.tzinfo is None:
        timezone = dt_util.get_time_zone(hass.config.time_zone) or UTC
        value = value.replace(tzinfo=timezone)
    return value.astimezone(UTC).replace(microsecond=0)


def _database_path(hass: HomeAssistant) -> Path:
    return _runtime_data(hass).feature_store.database_path


def _connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _initialize_sync(database_path: Path) -> None:
    with _connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS v081_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS group_events (
                id TEXT PRIMARY KEY,
                group_id TEXT NOT NULL REFERENCES animal_groups(id) ON DELETE CASCADE,
                event_type TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                title TEXT NOT NULL,
                notes TEXT,
                value REAL,
                unit TEXT,
                correction_of_event_id TEXT REFERENCES group_events(id) ON DELETE RESTRICT,
                data_json TEXT NOT NULL DEFAULT '{}',
                task_id TEXT REFERENCES tasks(id) ON DELETE SET NULL,
                task_occurrence_id TEXT REFERENCES task_occurrences(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL,
                CHECK ((value IS NULL AND unit IS NULL) OR (value IS NOT NULL AND unit IS NOT NULL)),
                CHECK (correction_of_event_id IS NULL OR correction_of_event_id <> id)
            );
            CREATE INDEX IF NOT EXISTS idx_group_events_group_occurred
                ON group_events(group_id, occurred_at DESC, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_group_events_task_occurrence
                ON group_events(task_occurrence_id);

            CREATE TABLE IF NOT EXISTS task_group_targets (
                task_id TEXT PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
                group_id TEXT NOT NULL REFERENCES animal_groups(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_task_group_targets_group
                ON task_group_targets(group_id, task_id);

            CREATE TABLE IF NOT EXISTS group_task_configs (
                task_id TEXT PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
                task_kind TEXT NOT NULL,
                template_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_group_task_configs_kind
                ON group_task_configs(task_kind);
            """
        )


def _row_event(row: sqlite3.Row) -> dict[str, Any]:
    try:
        data = json.loads(str(row["data_json"] or "{}"))
    except (TypeError, json.JSONDecodeError):
        data = {}
    return {
        "id": str(row["id"]),
        "group_id": str(row["group_id"]),
        "group_name": str(row["group_name"]) if row["group_name"] is not None else None,
        "event_type": str(row["event_type"]),
        "occurred_at": str(row["occurred_at"]),
        "title": str(row["title"]),
        "notes": str(row["notes"]) if row["notes"] is not None else None,
        "value": float(row["value"]) if row["value"] is not None else None,
        "unit": str(row["unit"]) if row["unit"] is not None else None,
        "correction_of_event_id": (
            str(row["correction_of_event_id"])
            if row["correction_of_event_id"] is not None
            else None
        ),
        "task_id": str(row["task_id"]) if row["task_id"] is not None else None,
        "task_occurrence_id": (
            str(row["task_occurrence_id"])
            if row["task_occurrence_id"] is not None
            else None
        ),
        "created_at": str(row["created_at"]),
        "data": data,
    }


def _state_sync(database_path: Path) -> dict[str, Any]:
    with _connect(database_path) as connection:
        settings = {
            str(row["key"]): str(row["value"] or "")
            for row in connection.execute(
                "SELECT key, value FROM v081_settings ORDER BY key"
            ).fetchall()
        }
        event_rows = connection.execute(
            """
            SELECT event.*, grp.name AS group_name
            FROM group_events AS event
            JOIN animal_groups AS grp ON grp.id = event.group_id
            ORDER BY event.occurred_at DESC, event.created_at DESC
            LIMIT ?
            """,
            (_MAX_GROUP_EVENTS,),
        ).fetchall()
        task_rows = connection.execute(
            """
            SELECT
                target.task_id,
                target.group_id,
                grp.name AS group_name,
                config.task_kind,
                config.template_json
            FROM task_group_targets AS target
            JOIN animal_groups AS grp ON grp.id = target.group_id
            LEFT JOIN group_task_configs AS config ON config.task_id = target.task_id
            ORDER BY grp.name COLLATE NOCASE, target.task_id
            """
        ).fetchall()
    group_tasks: list[dict[str, Any]] = []
    for row in task_rows:
        try:
            planned = json.loads(str(row["template_json"] or "{}"))
        except (TypeError, json.JSONDecodeError):
            planned = {}
        group_tasks.append(
            {
                "task_id": str(row["task_id"]),
                "group_id": str(row["group_id"]),
                "group_name": str(row["group_name"]),
                "task_kind": str(row["task_kind"] or "reminder"),
                "planned": planned,
            }
        )
    return {
        "settings": settings,
        "group_events": [_row_event(row) for row in event_rows],
        "group_tasks": group_tasks,
    }


def _save_settings_sync(database_path: Path, values: dict[str, str | None]) -> dict[str, str]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(database_path) as connection:
        for key, value in values.items():
            if value:
                connection.execute(
                    """
                    INSERT INTO v081_settings (key, value, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        updated_at = excluded.updated_at
                    """,
                    (key, value, now),
                )
            else:
                connection.execute("DELETE FROM v081_settings WHERE key = ?", (key,))
    return _state_sync(database_path)["settings"]


def _insert_group_event(
    connection: sqlite3.Connection,
    *,
    group_id: str,
    event_type: str,
    occurred_at: datetime,
    title: str,
    notes: str | None = None,
    value: float | None = None,
    unit: str | None = None,
    data: dict[str, Any] | None = None,
    correction_of_event_id: str | None = None,
    task_id: str | None = None,
    task_occurrence_id: str | None = None,
) -> dict[str, Any]:
    if event_type not in _GROUP_EVENT_TYPES:
        raise ValueError(f"Unsupported group event type: {event_type}")
    if (value is None) != (unit is None):
        raise ValueError("Event value and unit must be supplied together")
    group = connection.execute(
        "SELECT id, name FROM animal_groups WHERE id = ?",
        (group_id,),
    ).fetchone()
    if group is None:
        raise KeyError(group_id)
    existing = {
        str(row[0]) for row in connection.execute("SELECT id FROM group_events").fetchall()
    }
    event_id = AnimalHealthDatabase._generate_record_id("GE", existing)
    occurred_at = occurred_at.astimezone(UTC).replace(microsecond=0)
    created_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    connection.execute(
        """
        INSERT INTO group_events (
            id, group_id, event_type, occurred_at, title, notes,
            value, unit, correction_of_event_id, data_json,
            task_id, task_occurrence_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            group_id,
            event_type,
            occurred_at.isoformat(),
            title.strip(),
            notes,
            value,
            unit,
            correction_of_event_id,
            json.dumps(data or {}, ensure_ascii=False, sort_keys=True),
            task_id,
            task_occurrence_id,
            created_at,
        ),
    )
    row = connection.execute(
        """
        SELECT event.*, grp.name AS group_name
        FROM group_events AS event
        JOIN animal_groups AS grp ON grp.id = event.group_id
        WHERE event.id = ?
        """,
        (event_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("Created group event could not be loaded")
    return _row_event(row)


def _create_group_event_sync(
    database_path: Path,
    *,
    group_id: str,
    event_type: str,
    occurred_at: datetime,
    title: str,
    notes: str | None,
    value: float | None,
    unit: str | None,
    data: dict[str, Any] | None,
) -> dict[str, Any]:
    with _connect(database_path) as connection:
        return _insert_group_event(
            connection,
            group_id=group_id,
            event_type=event_type,
            occurred_at=occurred_at,
            title=title,
            notes=notes,
            value=value,
            unit=unit,
            data=data,
        )


def _latest_weight_event_sync(database_path: Path, event_id: str) -> sqlite3.Row:
    with _connect(database_path) as connection:
        row = connection.execute(
            """
            WITH RECURSIVE chain AS (
                SELECT id, animal_id, event_type, occurred_at, value, unit, notes, created_at, 0 AS depth
                FROM events
                WHERE id = ?
                UNION ALL
                SELECT e.id, e.animal_id, e.event_type, e.occurred_at, e.value, e.unit, e.notes, e.created_at, chain.depth + 1
                FROM events AS e
                JOIN chain ON e.correction_of_event_id = chain.id
                WHERE e.event_type = 'weight'
            )
            SELECT * FROM chain
            WHERE event_type = 'weight'
            ORDER BY depth DESC, created_at DESC
            LIMIT 1
            """,
            (event_id,),
        ).fetchone()
        if row is None:
            raise KeyError(event_id)
        return row


def _group_task_event_fields(
    task_kind: str,
    task_title: str,
    merged: dict[str, Any],
) -> tuple[str | None, str | None, float | None, str | None, dict[str, Any]]:
    event_type: str | None = None
    title: str | None = task_title
    value: float | None = None
    unit: str | None = None
    data = dict(merged)
    if task_kind == "weight":
        event_type = "weight"
        title = "weight_measurement"
        raw = merged.get("weight")
        if raw not in (None, ""):
            value = float(raw)
            unit = str(merged.get("weight_unit") or "kg")
    elif task_kind == "medication":
        event_type = "medication"
        title = str(merged.get("medication_name") or task_title)
        raw = merged.get("dose")
        if raw not in (None, ""):
            value = float(raw)
            unit = str(merged.get("dose_unit") or "mg")
    elif task_kind == "vaccination":
        event_type = "vaccination"
        title = str(merged.get("vaccine_name") or task_title)
        raw = merged.get("dose")
        if raw not in (None, ""):
            value = float(raw)
            unit = str(merged.get("dose_unit") or "ml")
    elif task_kind == "treatment":
        event_type = "treatment"
        title = str(merged.get("treatment_action") or task_title)
    elif task_kind == "health_check":
        event_type = "observation"
    elif task_kind == "care":
        event_type = "care"
        title = str(merged.get("care_action") or task_title)
    elif task_kind == "veterinary_visit":
        event_type = "veterinary_visit"
        title = str(merged.get("visit_reason") or task_title)
    return event_type, title, value, unit, data


def _execute_group_task_sync(
    database_path: Path,
    occurrence_id: str,
    performed_at: datetime,
    actual: dict[str, Any],
    notes: str | None,
    document_reminder: bool,
) -> dict[str, Any]:
    with _connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT
                occurrence.id,
                occurrence.task_id,
                occurrence.status,
                occurrence.scheduled_for,
                task.title,
                target.group_id,
                grp.name AS group_name,
                COALESCE(config.task_kind, 'reminder') AS task_kind,
                COALESCE(config.template_json, '{}') AS template_json
            FROM task_occurrences AS occurrence
            JOIN tasks AS task ON task.id = occurrence.task_id
            JOIN task_group_targets AS target ON target.task_id = task.id
            JOIN animal_groups AS grp ON grp.id = target.group_id
            LEFT JOIN group_task_configs AS config ON config.task_id = task.id
            WHERE occurrence.id = ?
            """,
            (occurrence_id,),
        ).fetchone()
        if row is None:
            raise KeyError(occurrence_id)
        if str(row["status"]) != "pending":
            raise ValueError("Occurrence is not pending")
        try:
            planned = json.loads(str(row["template_json"] or "{}"))
        except (TypeError, json.JSONDecodeError):
            planned = {}
        merged = {**planned, **{key: value for key, value in actual.items() if value not in (None, "")}}
        task_kind = str(row["task_kind"])
        event_type, title, value, unit, event_data = _group_task_event_fields(
            task_kind,
            str(row["title"]),
            merged,
        )
        event: dict[str, Any] | None = None
        if event_type is not None or (task_kind == "reminder" and document_reminder):
            if event_type is None:
                event_type = "observation"
            event_data["task_execution"] = {
                "source": "group_task_occurrence",
                "task_id": str(row["task_id"]),
                "task_title": str(row["title"]),
                "task_kind": task_kind,
                "occurrence_id": occurrence_id,
                "scheduled_for": str(row["scheduled_for"]),
                "performed_at": performed_at.isoformat(),
                "planned": planned,
                "actual": actual,
            }
            event = _insert_group_event(
                connection,
                group_id=str(row["group_id"]),
                event_type=event_type,
                occurred_at=performed_at,
                title=title or str(row["title"]),
                notes=notes,
                value=value,
                unit=unit,
                data=event_data,
                task_id=str(row["task_id"]),
                task_occurrence_id=occurrence_id,
            )
        now = datetime.now(UTC).replace(microsecond=0).isoformat()
        connection.execute(
            """
            UPDATE task_occurrences
            SET status = 'completed', completed_at = ?, notes = ?, updated_at = ?
            WHERE id = ? AND status = 'pending'
            """,
            (performed_at.isoformat(), notes, now, occurrence_id),
        )
        return {
            "occurrence_id": occurrence_id,
            "task_id": str(row["task_id"]),
            "group_id": str(row["group_id"]),
            "group_name": str(row["group_name"]),
            "task_kind": task_kind,
            "status": "completed",
            "performed_at": performed_at.isoformat(),
            "event": event,
        }


def _group_pdf_sync(database_path: Path, group_id: str) -> tuple[str, bytes]:
    with _connect(database_path) as connection:
        group = connection.execute(
            "SELECT id, name, species, description FROM animal_groups WHERE id = ?",
            (group_id,),
        ).fetchone()
        if group is None:
            raise KeyError(group_id)
        events = connection.execute(
            """
            SELECT * FROM group_events
            WHERE group_id = ?
            ORDER BY occurred_at, created_at, id
            """,
            (group_id,),
        ).fetchall()
    lines: list[tuple[str, int, str]] = [
        ("bold", 20, "Animal Health – Gruppenchronik"),
        ("regular", 10, f"Erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')}"),
        ("space", 8, ""),
        ("bold", 16, str(group["name"])),
        ("regular", 11, f"Tierart: {group['species'] or '–'}"),
        ("regular", 11, f"Beschreibung: {group['description'] or '–'}"),
        ("space", 12, ""),
        ("bold", 15, "Chronik"),
    ]
    if not events:
        lines.append(("regular", 11, "Keine gruppenbezogenen Einträge vorhanden."))
    for event in events:
        try:
            occurred = datetime.fromisoformat(str(event["occurred_at"])).strftime("%d.%m.%Y %H:%M")
        except ValueError:
            occurred = str(event["occurred_at"])
        lines.append(("bold", 12, f"{occurred} – {event['event_type']}: {event['title']}"))
        if event["value"] is not None and event["unit"]:
            lines.append(("regular", 10, f"Messwert/Dosis: {event['value']} {event['unit']}"))
        if event["notes"]:
            lines.append(("regular", 10, f"Notizen: {event['notes']}"))
        try:
            data = json.loads(str(event["data_json"] or "{}"))
        except (TypeError, json.JSONDecodeError):
            data = {}
        for key, value in data.items():
            if key == "task_execution" or value in (None, "", [], {}):
                continue
            display = ", ".join(map(str, value)) if isinstance(value, list) else str(value)
            lines.append(("regular", 10, f"{key.replace('_', ' ').title()}: {display}"))
        lines.append(("space", 7, ""))
    filename = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(group["name"]))
    return f"animal_health_{filename}_gruppenchronik.pdf", _build_pdf(lines, str(group["name"]))


class AnimalHealthGroupPdfView(HomeAssistantView):
    url = f"/api/{DOMAIN}/export/groups/{{group_id}}/health.pdf"
    name = f"api:{DOMAIN}:export_group_pdf"
    requires_auth = False

    async def get(self, request: web.Request, group_id: str) -> web.Response:
        hass: HomeAssistant = request.app[KEY_HASS]
        token = request.query.get("token", "")
        state = hass.data.setdefault(_STATE_KEY, {})
        record = state.setdefault("group_pdf_tokens", {}).pop(token, None)
        if (
            record is None
            or record.get("group_id") != group_id
            or datetime.now(UTC) > record.get("expires_at", datetime.min.replace(tzinfo=UTC))
        ):
            raise web.HTTPUnauthorized()
        try:
            filename, body = await hass.async_add_executor_job(
                _group_pdf_sync,
                _database_path(hass),
                group_id,
            )
        except KeyError:
            raise web.HTTPNotFound() from None
        safe = "".join(ch if ch.isascii() and ch not in '\\/:*?\"<>|' else "_" for ch in filename)
        return web.Response(
            body=body,
            content_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{safe}"',
                "Cache-Control": "no-store",
            },
        )


async def async_initialize_v081_features(hass: HomeAssistant) -> None:
    await hass.async_add_executor_job(_initialize_sync, _database_path(hass))


def async_setup_v081_features(hass: HomeAssistant) -> None:
    state = hass.data.setdefault(_STATE_KEY, {})
    if not state.get("view_registered"):
        hass.http.register_view(AnimalHealthGroupPdfView())
        state["view_registered"] = True

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
            connection.send_error(msg["id"], "v081_state_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _UPDATE_SETTINGS_COMMAND,
            vol.Optional("ai_task_entity_id"): _optional_text,
            vol.Optional("stt_entity_id"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_update_settings(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        values = {
            key: msg.get(key)
            for key in ("ai_task_entity_id", "stt_entity_id")
            if key in msg
        }
        try:
            ai_entity = values.get("ai_task_entity_id")
            stt_entity = values.get("stt_entity_id")
            if ai_entity and ai_entity not in hass.states.async_entity_ids("ai_task"):
                raise ValueError("Selected AI Task entity is not available")
            if stt_entity and stt_entity not in hass.states.async_entity_ids("stt"):
                raise ValueError("Selected speech-to-text entity is not available")
            result = await hass.async_add_executor_job(
                _save_settings_sync,
                _database_path(hass),
                values,
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v081_settings_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _RECORD_PRODUCT_COMMAND,
            vol.Required("animal_id"): _required_text,
            vol.Optional("product_type", default="medication"): vol.In(_PRODUCT_TYPES),
            vol.Required("product_name"): _required_text,
            vol.Required("dose"): _positive_number,
            vol.Required("dose_unit"): vol.In(DOSE_UNITS),
            vol.Optional("route"): vol.In(ADMINISTRATION_ROUTES),
            vol.Optional("occurred_at"): _optional_datetime,
            vol.Optional("notes"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_record_product(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        runtime = _runtime_data(hass)
        try:
            if await runtime.database.get_animal(msg["animal_id"]) is None:
                raise KeyError(msg["animal_id"])
            event = await runtime.database.create_event(
                animal_id=msg["animal_id"],
                event_type="medication",
                occurred_at=_event_datetime_utc(hass, msg.get("occurred_at")),
                title=msg["product_name"],
                notes=msg.get("notes"),
                value=msg["dose"],
                unit=msg["dose_unit"],
                data={
                    "medication_name": msg["product_name"],
                    "product_type": msg["product_type"],
                    **({"route": msg["route"]} if msg.get("route") else {}),
                    "entry_mode": "spontaneous",
                },
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v081_product_failed", str(err))
            return
        connection.send_result(msg["id"], event.as_dict())

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _CORRECT_WEIGHT_COMMAND,
            vol.Required("event_id"): _required_text,
            vol.Required("weight"): _positive_number,
            vol.Required("weight_unit"): vol.In(WEIGHT_UNITS),
            vol.Optional("occurred_at"): _optional_datetime,
            vol.Optional("notes"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_correct_weight(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        runtime = _runtime_data(hass)
        try:
            current = await hass.async_add_executor_job(
                _latest_weight_event_sync,
                _database_path(hass),
                msg["event_id"],
            )
            measured_at = msg.get("occurred_at") or datetime.fromisoformat(
                str(current["occurred_at"])
            )
            event = await runtime.database.create_event(
                animal_id=str(current["animal_id"]),
                event_type="weight",
                occurred_at=_event_datetime_utc(hass, measured_at),
                title="weight_measurement",
                notes=msg.get("notes"),
                value=msg["weight"],
                unit=msg["weight_unit"],
                correction_of_event_id=str(current["id"]),
                data={"measurement": "weight", "correction": True},
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v081_weight_correction_failed", str(err))
            return
        connection.send_result(msg["id"], event.as_dict())

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
    async def websocket_create_group_event(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            value = msg.get("value")
            unit = msg.get("unit")
            if (value is None) != (unit is None):
                raise ValueError("Value and unit must be supplied together")
            result = await hass.async_add_executor_job(
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
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v081_group_event_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _CREATE_GROUP_TASK_COMMAND,
            vol.Required("group_id"): _required_text,
            vol.Required("task_kind"): vol.In(TASK_KINDS),
            vol.Required("title"): _required_text,
            vol.Optional("description"): _optional_text,
            vol.Required("recurrence_type"): vol.In(RECURRENCE_TYPES),
            vol.Optional("recurrence_interval", default=1): _positive_integer,
            vol.Required("start_date"): _date_value,
            vol.Optional("end_date"): _optional_date,
            vol.Optional("due_time"): _optional_time,
            vol.Optional("planned", default={}): dict,
        }
    )
    @websocket_api.async_response
    async def websocket_create_group_task(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        runtime = _runtime_data(hass)
        now = datetime.now(UTC).replace(microsecond=0).isoformat()

        def configure(connection_db: sqlite3.Connection, task_id: str) -> None:
            if connection_db.execute(
                "SELECT 1 FROM animal_groups WHERE id = ?",
                (msg["group_id"],),
            ).fetchone() is None:
                raise KeyError(msg["group_id"])
            connection_db.execute(
                "INSERT INTO task_group_targets (task_id, group_id, created_at) VALUES (?, ?, ?)",
                (task_id, msg["group_id"], now),
            )
            connection_db.execute(
                """
                INSERT INTO group_task_configs (
                    task_id, task_kind, template_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    msg["task_kind"],
                    json.dumps(msg.get("planned") or {}, ensure_ascii=False, sort_keys=True),
                    now,
                    now,
                ),
            )

        try:
            tasks = await runtime.coordinator.task_store.create_tasks(
                animal_ids=[None],
                title=msg["title"],
                description=msg.get("description"),
                recurrence_type=msg["recurrence_type"],
                recurrence_interval=msg["recurrence_interval"],
                start_date=msg["start_date"],
                end_date=msg.get("end_date"),
                due_time=msg.get("due_time"),
                configure_task=configure,
            )
            await runtime.coordinator.async_request_refresh()
            task = tasks[0].as_dict(runtime.coordinator.task_store.timezone)
            task.update(
                {
                    "scope": "group",
                    "group_id": msg["group_id"],
                    "task_kind": msg["task_kind"],
                    "planned": msg.get("planned") or {},
                }
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v081_group_task_failed", str(err))
            return
        connection.send_result(msg["id"], task)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _EXECUTE_GROUP_TASK_COMMAND,
            vol.Required("occurrence_id"): _required_text,
            vol.Optional("performed_at"): _optional_datetime,
            vol.Optional("actual", default={}): dict,
            vol.Optional("notes"): _optional_text,
            vol.Optional("document_in_timeline", default=False): bool,
        }
    )
    @websocket_api.async_response
    async def websocket_execute_group_task(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        runtime = _runtime_data(hass)
        try:
            result = await hass.async_add_executor_job(
                _execute_group_task_sync,
                _database_path(hass),
                msg["occurrence_id"],
                _event_datetime_utc(hass, msg.get("performed_at")),
                msg.get("actual") or {},
                msg.get("notes"),
                bool(msg.get("document_in_timeline")),
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v081_group_task_execute_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _GROUP_PDF_COMMAND,
            vol.Required("group_id"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_group_pdf(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        token = secrets.token_urlsafe(32)
        tokens = hass.data.setdefault(_STATE_KEY, {}).setdefault("group_pdf_tokens", {})
        now = datetime.now(UTC)
        for old, record in list(tokens.items()):
            if record["expires_at"] < now:
                tokens.pop(old, None)
        tokens[token] = {
            "group_id": msg["group_id"],
            "expires_at": now + timedelta(minutes=2),
        }
        connection.send_result(
            msg["id"],
            {"url": f"/api/{DOMAIN}/export/groups/{msg['group_id']}/health.pdf?token={token}"},
        )

    websocket_api.async_register_command(hass, websocket_state)
    websocket_api.async_register_command(hass, websocket_update_settings)
    websocket_api.async_register_command(hass, websocket_record_product)
    websocket_api.async_register_command(hass, websocket_correct_weight)
    websocket_api.async_register_command(hass, websocket_create_group_event)
    websocket_api.async_register_command(hass, websocket_create_group_task)
    websocket_api.async_register_command(hass, websocket_execute_group_task)
    websocket_api.async_register_command(hass, websocket_group_pdf)
