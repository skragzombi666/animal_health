from __future__ import annotations

import json
import re
import secrets
import sqlite3
from datetime import UTC, date, datetime, time as dt_time
from pathlib import Path
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import DATABASE_NAME, DOMAIN, GENERAL_EVENT_TYPES, SYMPTOM_SEVERITIES, WEIGHT_UNITS
from .runtime import AnimalHealthRuntimeData
from .v0817_features import _record_medications_sync
from .v0912_features import _execute_treatment_sync

_STATE_COMMAND = f"{DOMAIN}/v0923/state"
_RECORD_WEIGHT_COMMAND = f"{DOMAIN}/v0923/weight/record"
_RECORD_EVENT_COMMAND = f"{DOMAIN}/v0923/event/record"
_RECORD_MEDICATIONS_COMMAND = f"{DOMAIN}/v0923/medications/record"
_EXECUTE_TREATMENT_COMMAND = f"{DOMAIN}/v0923/treatment/execute"
_START_SYMPTOMS_COMMAND = f"{DOMAIN}/v0923/symptoms/start"
_REASSESS_SYMPTOM_COMMAND = f"{DOMAIN}/v0923/symptom/reassess"
_RESOLVE_SYMPTOM_COMMAND = f"{DOMAIN}/v0923/symptom/resolve"


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


def _normalise(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def _record_id(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(6).upper()}"


def _event_when(
    hass: HomeAssistant,
    raw_date: Any,
    raw_time: Any,
) -> tuple[datetime, str, str]:
    timezone = dt_util.get_time_zone(hass.config.time_zone) or UTC
    date_text = str(raw_date or "").strip()
    time_text = str(raw_time or "").strip()
    if not date_text:
        now_local = datetime.now(UTC).astimezone(timezone).replace(microsecond=0)
        return now_local.astimezone(UTC), "datetime", now_local.date().isoformat()
    try:
        day = date.fromisoformat(date_text)
    except ValueError as err:
        raise ValueError("Date must use YYYY-MM-DD") from err
    if time_text:
        try:
            local_time = dt_time.fromisoformat(time_text)
        except ValueError as err:
            raise ValueError("Time must use HH:MM") from err
        local_value = datetime.combine(day, local_time, tzinfo=timezone).replace(microsecond=0)
        return local_value.astimezone(UTC), "datetime", day.isoformat()
    # Noon is only a stable storage anchor. time_precision=date is authoritative and
    # prevents this artificial anchor from ever being presented as a real time.
    local_value = datetime.combine(day, dt_time(12, 0), tzinfo=timezone)
    return local_value.astimezone(UTC), "date", day.isoformat()


def _precision_data(precision: str, occurred_date: str) -> dict[str, Any]:
    result: dict[str, Any] = {"time_precision": precision}
    if precision == "date":
        result["occurred_date"] = occurred_date
    return result


def _initialise_sync(path: Path) -> None:
    with _connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS v0923_symptom_episodes (
                id TEXT PRIMARY KEY,
                animal_id TEXT NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
                symptom TEXT NOT NULL,
                normalized_symptom TEXT NOT NULL,
                started_at TEXT NOT NULL,
                started_date TEXT NOT NULL,
                start_event_id TEXT NOT NULL REFERENCES events(id) ON DELETE RESTRICT,
                state TEXT NOT NULL DEFAULT 'active'
                    CHECK (state IN ('active','resolved')),
                ended_at TEXT,
                ended_date TEXT,
                latest_severity TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_v0923_symptom_episode_active
                ON v0923_symptom_episodes(animal_id,state,normalized_symptom,started_date);
            CREATE TABLE IF NOT EXISTS v0923_symptom_assessments (
                id TEXT PRIMARY KEY,
                episode_id TEXT NOT NULL REFERENCES v0923_symptom_episodes(id) ON DELETE CASCADE,
                event_id TEXT NOT NULL REFERENCES events(id) ON DELETE RESTRICT,
                action TEXT NOT NULL CHECK (action IN ('start','reassessment','resolved')),
                assessed_at TEXT NOT NULL,
                assessed_date TEXT NOT NULL,
                time_precision TEXT NOT NULL CHECK (time_precision IN ('date','datetime')),
                severity TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_v0923_symptom_assessment_episode
                ON v0923_symptom_assessments(episode_id,assessed_at,created_at);
            """
        )


def _episode_state_sync(path: Path) -> dict[str, Any]:
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT e.*,a.name AS animal_name
            FROM v0923_symptom_episodes AS e
            LEFT JOIN animals AS a ON a.id=e.animal_id
            ORDER BY CASE e.state WHEN 'active' THEN 0 ELSE 1 END,
                     e.started_date DESC,e.created_at DESC
            LIMIT 2000
            """
        ).fetchall()
        assessments = connection.execute(
            """
            SELECT id,episode_id,event_id,action,assessed_at,assessed_date,
                   time_precision,severity,notes,created_at
            FROM v0923_symptom_assessments
            ORDER BY assessed_at,created_at,id
            """
        ).fetchall()
    by_episode: dict[str, list[dict[str, Any]]] = {}
    for row in assessments:
        by_episode.setdefault(str(row["episode_id"]), []).append(
            {
                "id": str(row["id"]),
                "event_id": str(row["event_id"]),
                "action": str(row["action"]),
                "assessed_at": str(row["assessed_at"]),
                "assessed_date": str(row["assessed_date"]),
                "time_precision": str(row["time_precision"]),
                "severity": str(row["severity"]),
                "notes": str(row["notes"] or ""),
                "created_at": str(row["created_at"]),
            }
        )
    episodes = []
    for row in rows:
        episode_id = str(row["id"])
        episodes.append(
            {
                "id": episode_id,
                "animal_id": str(row["animal_id"]),
                "animal_name": str(row["animal_name"] or row["animal_id"]),
                "symptom": str(row["symptom"]),
                "started_at": str(row["started_at"]),
                "started_date": str(row["started_date"]),
                "start_event_id": str(row["start_event_id"]),
                "state": str(row["state"]),
                "ended_at": str(row["ended_at"] or ""),
                "ended_date": str(row["ended_date"] or ""),
                "latest_severity": str(row["latest_severity"]),
                "assessments": by_episode.get(episode_id, []),
            }
        )
    return {"episodes": episodes}


def _mark_precision_sync(
    path: Path,
    event_ids: list[str],
    precision: str,
    occurred_date: str,
) -> None:
    if not event_ids:
        return
    with _connect(path) as connection:
        for event_id in event_ids:
            row = connection.execute(
                "SELECT data_json FROM events WHERE id=?",
                (event_id,),
            ).fetchone()
            if row is None:
                continue
            try:
                data = json.loads(str(row["data_json"] or "{}"))
            except json.JSONDecodeError:
                data = {}
            if not isinstance(data, dict):
                data = {}
            data.update(_precision_data(precision, occurred_date))
            connection.execute(
                "UPDATE events SET data_json=? WHERE id=?",
                (json.dumps(data, ensure_ascii=False, sort_keys=True), event_id),
            )


def _episode_event(
    database,
    connection: sqlite3.Connection,
    *,
    episode_id: str,
    animal_id: str,
    symptom: str,
    severity: str,
    occurred_at: datetime,
    occurred_date: str,
    precision: str,
    action: str,
    state: str,
    notes: str | None,
    capture_batch_id: str | None = None,
):
    data = {
        "symptom": symptom,
        "symptoms": [symptom],
        "severity": severity,
        "symptom_episode_id": episode_id,
        "symptom_episode_action": action,
        "symptom_episode_state": state,
        **_precision_data(precision, occurred_date),
    }
    if capture_batch_id:
        data["symptom_capture_batch_id"] = capture_batch_id
    return database._create_event_in_connection(  # noqa: SLF001
        connection,
        animal_id=animal_id,
        event_type="symptom",
        occurred_at=occurred_at,
        title=symptom,
        notes=notes,
        data=data,
    )


def _insert_assessment(
    connection: sqlite3.Connection,
    *,
    episode_id: str,
    event_id: str,
    action: str,
    occurred_at: datetime,
    occurred_date: str,
    precision: str,
    severity: str,
    notes: str | None,
    created_at: str,
) -> None:
    connection.execute(
        """
        INSERT INTO v0923_symptom_assessments(
            id,episode_id,event_id,action,assessed_at,assessed_date,
            time_precision,severity,notes,created_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?)
        """,
        (
            _record_id("SA"),
            episode_id,
            event_id,
            action,
            occurred_at.isoformat(),
            occurred_date,
            precision,
            severity,
            notes,
            created_at,
        ),
    )


def _start_symptoms_sync(
    database,
    animal_id: str,
    symptoms: list[str],
    severity: str,
    occurred_at: datetime,
    occurred_date: str,
    precision: str,
    notes: str | None,
) -> list[dict[str, Any]]:
    clean_symptoms: list[str] = []
    seen: set[str] = set()
    for raw in symptoms:
        clean = _required_text(raw)
        key = _normalise(clean)
        if key in seen:
            continue
        seen.add(key)
        clean_symptoms.append(clean)
    if not clean_symptoms:
        raise ValueError("At least one symptom is required")
    if len(clean_symptoms) > 30:
        raise ValueError("At most 30 symptoms can be started together")
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    capture_batch_id = _record_id("SB") if len(clean_symptoms) > 1 else None
    results: list[dict[str, Any]] = []
    with database._connect() as connection:  # noqa: SLF001
        if database._get_animal_from_connection(connection, animal_id) is None:  # noqa: SLF001
            raise KeyError(animal_id)
        for symptom in clean_symptoms:
            normalized = _normalise(symptom)
            existing = connection.execute(
                """
                SELECT * FROM v0923_symptom_episodes
                WHERE animal_id=? AND state='active' AND normalized_symptom=?
                ORDER BY started_at DESC LIMIT 1
                """,
                (animal_id, normalized),
            ).fetchone()
            if existing is not None:
                episode_id = str(existing["id"])
                if occurred_date < str(existing["started_date"]):
                    raise ValueError("A reassessment cannot be before the symptom start date")
                event = _episode_event(
                    database,
                    connection,
                    episode_id=episode_id,
                    animal_id=animal_id,
                    symptom=str(existing["symptom"]),
                    severity=severity,
                    occurred_at=occurred_at,
                    occurred_date=occurred_date,
                    precision=precision,
                    action="reassessment",
                    state="active",
                    notes=notes,
                    capture_batch_id=capture_batch_id,
                )
                _insert_assessment(
                    connection,
                    episode_id=episode_id,
                    event_id=event.id,
                    action="reassessment",
                    occurred_at=occurred_at,
                    occurred_date=occurred_date,
                    precision=precision,
                    severity=severity,
                    notes=notes,
                    created_at=now,
                )
                connection.execute(
                    "UPDATE v0923_symptom_episodes SET latest_severity=?,updated_at=? WHERE id=?",
                    (severity, now, episode_id),
                )
                results.append(event.as_dict())
                continue
            episode_id = _record_id("SE")
            event = _episode_event(
                database,
                connection,
                episode_id=episode_id,
                animal_id=animal_id,
                symptom=symptom,
                severity=severity,
                occurred_at=occurred_at,
                occurred_date=occurred_date,
                precision=precision,
                action="start",
                state="active",
                notes=notes,
                capture_batch_id=capture_batch_id,
            )
            connection.execute(
                """
                INSERT INTO v0923_symptom_episodes(
                    id,animal_id,symptom,normalized_symptom,started_at,started_date,
                    start_event_id,state,ended_at,ended_date,latest_severity,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,'active',NULL,NULL,?,?,?)
                """,
                (
                    episode_id,
                    animal_id,
                    symptom,
                    normalized,
                    occurred_at.isoformat(),
                    occurred_date,
                    event.id,
                    severity,
                    now,
                    now,
                ),
            )
            _insert_assessment(
                connection,
                episode_id=episode_id,
                event_id=event.id,
                action="start",
                occurred_at=occurred_at,
                occurred_date=occurred_date,
                precision=precision,
                severity=severity,
                notes=notes,
                created_at=now,
            )
            results.append(event.as_dict())
    return results


def _update_episode_sync(
    database,
    episode_id: str,
    severity: str | None,
    occurred_at: datetime,
    occurred_date: str,
    precision: str,
    notes: str | None,
    resolve: bool,
) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with database._connect() as connection:  # noqa: SLF001
        row = connection.execute(
            "SELECT * FROM v0923_symptom_episodes WHERE id=?",
            (episode_id,),
        ).fetchone()
        if row is None:
            raise KeyError(episode_id)
        if str(row["state"]) != "active":
            raise ValueError("Symptom episode is already resolved")
        if occurred_date < str(row["started_date"]):
            raise ValueError("An episode update cannot be before its start date")
        actual_severity = severity or str(row["latest_severity"])
        action = "resolved" if resolve else "reassessment"
        state = "resolved" if resolve else "active"
        event = _episode_event(
            database,
            connection,
            episode_id=episode_id,
            animal_id=str(row["animal_id"]),
            symptom=str(row["symptom"]),
            severity=actual_severity,
            occurred_at=occurred_at,
            occurred_date=occurred_date,
            precision=precision,
            action=action,
            state=state,
            notes=notes,
        )
        _insert_assessment(
            connection,
            episode_id=episode_id,
            event_id=event.id,
            action=action,
            occurred_at=occurred_at,
            occurred_date=occurred_date,
            precision=precision,
            severity=actual_severity,
            notes=notes,
            created_at=now,
        )
        if resolve:
            connection.execute(
                """
                UPDATE v0923_symptom_episodes
                SET state='resolved',ended_at=?,ended_date=?,latest_severity=?,updated_at=?
                WHERE id=?
                """,
                (occurred_at.isoformat(), occurred_date, actual_severity, now, episode_id),
            )
        else:
            connection.execute(
                "UPDATE v0923_symptom_episodes SET latest_severity=?,updated_at=? WHERE id=?",
                (actual_severity, now, episode_id),
            )
        return event.as_dict()


async def async_initialize_v0923_features(hass: HomeAssistant) -> None:
    await hass.async_add_executor_job(_initialise_sync, _database_path(hass))


def async_setup_v0923_features(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command({vol.Required("type"): _STATE_COMMAND})
    @websocket_api.async_response
    async def websocket_state(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(_episode_state_sync, _database_path(hass))
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0923_state_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    temporal = {
        vol.Optional("occurred_date"): _optional_text,
        vol.Optional("occurred_time"): _optional_text,
        vol.Optional("notes"): _optional_text,
    }

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _RECORD_WEIGHT_COMMAND,
            vol.Required("animal_id"): _required_text,
            vol.Required("weight"): vol.All(vol.Coerce(float), vol.Range(min=0.000001)),
            vol.Required("weight_unit"): vol.In(WEIGHT_UNITS),
            **temporal,
        }
    )
    @websocket_api.async_response
    async def websocket_record_weight(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            when, precision, day = _event_when(hass, msg.get("occurred_date"), msg.get("occurred_time"))
            event = await runtime.database.create_event(
                animal_id=msg["animal_id"],
                event_type="weight",
                occurred_at=when,
                title="weight_measurement",
                notes=msg.get("notes"),
                value=float(msg["weight"]),
                unit=msg["weight_unit"],
                data={"measurement": "weight", **_precision_data(precision, day)},
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0923_weight_failed", str(err))
            return
        connection.send_result(msg["id"], event.as_dict())

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _RECORD_EVENT_COMMAND,
            vol.Required("animal_id"): _required_text,
            vol.Required("event_type"): vol.In(GENERAL_EVENT_TYPES),
            vol.Required("title"): _required_text,
            **temporal,
        }
    )
    @websocket_api.async_response
    async def websocket_record_event(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            when, precision, day = _event_when(hass, msg.get("occurred_date"), msg.get("occurred_time"))
            event = await runtime.database.create_event(
                animal_id=msg["animal_id"],
                event_type=msg["event_type"],
                occurred_at=when,
                title=msg["title"],
                notes=msg.get("notes"),
                data=_precision_data(precision, day),
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0923_event_failed", str(err))
            return
        connection.send_result(msg["id"], event.as_dict())

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _RECORD_MEDICATIONS_COMMAND,
            vol.Required("animal_id"): _required_text,
            vol.Required("items"): list,
            **temporal,
        }
    )
    @websocket_api.async_response
    async def websocket_record_medications(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            when, precision, day = _event_when(hass, msg.get("occurred_date"), msg.get("occurred_time"))
            result = await hass.async_add_executor_job(
                _record_medications_sync,
                runtime.database,
                msg["animal_id"],
                when,
                msg.get("notes"),
                msg["items"],
            )
            ids = [str(item.get("id") or "") for item in result if item.get("id")]
            await hass.async_add_executor_job(_mark_precision_sync, _database_path(hass), ids, precision, day)
            for item in result:
                data = dict(item.get("data") or {})
                data.update(_precision_data(precision, day))
                item["data"] = data
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0923_medications_failed", str(err))
            return
        connection.send_result(msg["id"], {"events": result})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _EXECUTE_TREATMENT_COMMAND,
            vol.Required("plan_id"): vol.Coerce(int),
            vol.Required("animal_id"): _required_text,
            **temporal,
        }
    )
    @websocket_api.async_response
    async def websocket_execute_treatment(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            when, precision, day = _event_when(hass, msg.get("occurred_date"), msg.get("occurred_time"))
            result = await hass.async_add_executor_job(
                _execute_treatment_sync,
                runtime,
                int(msg["plan_id"]),
                msg["animal_id"],
                when,
                msg.get("notes"),
            )
            ids = [str(item.get("id") or "") for item in result if item.get("id")]
            await hass.async_add_executor_job(_mark_precision_sync, _database_path(hass), ids, precision, day)
            for item in result:
                data = dict(item.get("data") or {})
                data.update(_precision_data(precision, day))
                item["data"] = data
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0923_treatment_failed", str(err))
            return
        connection.send_result(msg["id"], {"events": result})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _START_SYMPTOMS_COMMAND,
            vol.Required("animal_id"): _required_text,
            vol.Required("symptoms"): vol.All([_required_text], vol.Length(min=1, max=30)),
            vol.Optional("severity", default="moderate"): vol.In(SYMPTOM_SEVERITIES),
            **temporal,
        }
    )
    @websocket_api.async_response
    async def websocket_start_symptoms(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            when, precision, day = _event_when(hass, msg.get("occurred_date"), msg.get("occurred_time"))
            result = await hass.async_add_executor_job(
                _start_symptoms_sync,
                runtime.database,
                msg["animal_id"],
                list(msg["symptoms"]),
                msg.get("severity") or "moderate",
                when,
                day,
                precision,
                msg.get("notes"),
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0923_symptoms_start_failed", str(err))
            return
        connection.send_result(msg["id"], {"events": result})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _REASSESS_SYMPTOM_COMMAND,
            vol.Required("episode_id"): _required_text,
            vol.Required("severity"): vol.In(SYMPTOM_SEVERITIES),
            **temporal,
        }
    )
    @websocket_api.async_response
    async def websocket_reassess_symptom(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            when, precision, day = _event_when(hass, msg.get("occurred_date"), msg.get("occurred_time"))
            result = await hass.async_add_executor_job(
                _update_episode_sync,
                runtime.database,
                msg["episode_id"],
                msg["severity"],
                when,
                day,
                precision,
                msg.get("notes"),
                False,
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0923_symptom_reassess_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _RESOLVE_SYMPTOM_COMMAND,
            vol.Required("episode_id"): _required_text,
            **temporal,
        }
    )
    @websocket_api.async_response
    async def websocket_resolve_symptom(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            when, precision, day = _event_when(hass, msg.get("occurred_date"), msg.get("occurred_time"))
            result = await hass.async_add_executor_job(
                _update_episode_sync,
                runtime.database,
                msg["episode_id"],
                None,
                when,
                day,
                precision,
                msg.get("notes"),
                True,
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0923_symptom_resolve_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    websocket_api.async_register_command(hass, websocket_state)
    websocket_api.async_register_command(hass, websocket_record_weight)
    websocket_api.async_register_command(hass, websocket_record_event)
    websocket_api.async_register_command(hass, websocket_record_medications)
    websocket_api.async_register_command(hass, websocket_execute_treatment)
    websocket_api.async_register_command(hass, websocket_start_symptoms)
    websocket_api.async_register_command(hass, websocket_reassess_symptom)
    websocket_api.async_register_command(hass, websocket_resolve_symptom)
