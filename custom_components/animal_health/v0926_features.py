from __future__ import annotations

import json
import re
import secrets
import sqlite3
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import task_record_creation, v0923_features, v0924_features
from .const import DATABASE_NAME, DOMAIN, SYMPTOM_SEVERITIES
from .runtime import AnimalHealthRuntimeData
from .task_kinds import TASK_KIND_REMINDER, TASK_KINDS
from .task_records import TaskRecordStore
from .task_store import RECURRENCE_TYPES
from .v0817_features import _record_medications_sync

_SCOPE_GENERAL = "general"
_SCOPE_GROUP = "group"
_SCOPE_ANIMALS = "animals"
_SCOPES = (_SCOPE_GENERAL, _SCOPE_GROUP, _SCOPE_ANIMALS)

_START_SYMPTOMS_COMMAND = f"{DOMAIN}/v0926/symptoms/start"
_RECORD_MEDICATIONS_COMMAND = f"{DOMAIN}/v0926/medications/record"
_EXECUTE_TREATMENT_COMMAND = f"{DOMAIN}/v0926/treatment/execute"
_CREATE_TASK_COMMAND = f"{DOMAIN}/v0926/task/create"


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


def _unique_texts(value: Any) -> list[str]:
    values = value if isinstance(value, list) else ([] if value in (None, "") else [value])
    result: list[str] = []
    for item in values:
        text = _required_text(item)
        if text not in result:
            result.append(text)
    return result


def _target_batch_id() -> str:
    return f"TG-{secrets.token_hex(6).upper()}"


def _resolve_target_sync(
    path: Path,
    scope: str,
    animal_ids: list[str],
    group_id: str | None,
) -> tuple[list[str | None], dict[str, Any]]:
    if scope not in _SCOPES:
        raise ValueError(f"Unsupported target scope: {scope}")
    if scope == _SCOPE_GENERAL:
        return [None], {"target_scope": _SCOPE_GENERAL}

    with _connect(path) as connection:
        if scope == _SCOPE_GROUP:
            actual_group_id = _required_text(group_id)
            group = connection.execute(
                "SELECT id,name FROM animal_groups WHERE id=?",
                (actual_group_id,),
            ).fetchone()
            if group is None:
                raise KeyError(actual_group_id)
            rows = connection.execute(
                """
                SELECT m.animal_id
                FROM animal_group_memberships AS m
                JOIN animals AS a ON a.id=m.animal_id
                WHERE m.group_id=?
                ORDER BY a.name COLLATE NOCASE,m.animal_id
                """,
                (actual_group_id,),
            ).fetchall()
            targets = [str(row["animal_id"]) for row in rows]
            if not targets:
                raise ValueError("The selected group contains no animals")
            return targets, {
                "target_scope": _SCOPE_GROUP,
                "target_group_id": str(group["id"]),
                "target_group_name": str(group["name"]),
                "target_animal_ids": targets,
                "target_batch_id": _target_batch_id(),
            }

        targets = _unique_texts(animal_ids)
        if not targets:
            raise ValueError("At least one animal is required")
        placeholders = ",".join("?" for _ in targets)
        rows = connection.execute(
            f"SELECT id FROM animals WHERE id IN ({placeholders})",
            targets,
        ).fetchall()
        found = {str(row["id"]) for row in rows}
        missing = next((animal_id for animal_id in targets if animal_id not in found), None)
        if missing is not None:
            raise KeyError(missing)
    return targets, {
        "target_scope": _SCOPE_ANIMALS,
        "target_animal_ids": targets,
        "target_batch_id": _target_batch_id() if len(targets) > 1 else "",
    }


def _annotate_events_sync(
    path: Path,
    events: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    if not events:
        return events
    with _connect(path) as connection:
        for event in events:
            event_id = str(event.get("id") or "")
            if not event_id:
                continue
            row = connection.execute(
                "SELECT data_json FROM events WHERE id=?",
                (event_id,),
            ).fetchone()
            if row is None:
                continue
            try:
                payload = json.loads(str(row["data_json"] or "{}"))
            except json.JSONDecodeError:
                payload = {}
            if not isinstance(payload, dict):
                payload = {}
            payload.update(metadata)
            connection.execute(
                "UPDATE events SET data_json=? WHERE id=?",
                (json.dumps(payload, ensure_ascii=False, sort_keys=True), event_id),
            )
            event["data"] = payload
    return events


def _task_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(_required_text(value))


def _task_time(value: Any) -> time | None:
    text = _optional_text(value)
    if text is None:
        return None
    return time.fromisoformat(text).replace(second=0, microsecond=0)


def _positive_int(value: Any, default: int = 1) -> int:
    number = int(value if value not in (None, "") else default)
    if number < 1:
        raise ValueError("Value must be at least 1")
    return number


def _start_symptoms_for_target_sync(
    database,
    path: Path,
    target_ids: list[str | None],
    metadata: dict[str, Any],
    symptoms: list[str],
    severity: str,
    occurred_at: datetime,
    occurred_date: str,
    precision: str,
    notes: str | None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for animal_id in target_ids:
        if animal_id is None:
            continue
        results.extend(
            v0923_features._start_symptoms_sync(  # noqa: SLF001
                database,
                animal_id,
                symptoms,
                severity,
                occurred_at,
                occurred_date,
                precision,
                notes,
            )
        )
    return _annotate_events_sync(path, results, metadata)


def _record_medications_for_target_sync(
    database,
    path: Path,
    target_ids: list[str | None],
    metadata: dict[str, Any],
    occurred_at: datetime,
    occurred_date: str,
    precision: str,
    notes: str | None,
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for animal_id in target_ids:
        if animal_id is None:
            continue
        recorded = _record_medications_sync(
            database,
            animal_id,
            occurred_at,
            notes,
            items,
        )
        ids = [str(item.get("id") or "") for item in recorded if item.get("id")]
        v0923_features._mark_precision_sync(  # noqa: SLF001
            path,
            ids,
            precision,
            occurred_date,
        )
        for item in recorded:
            payload = dict(item.get("data") or {})
            payload.update(v0923_features._precision_data(precision, occurred_date))  # noqa: SLF001
            item["data"] = payload
        results.extend(recorded)
    return _annotate_events_sync(path, results, metadata)


def _execute_treatment_for_target_sync(
    database,
    path: Path,
    target_ids: list[str | None],
    metadata: dict[str, Any],
    plan_id: int,
    occurred_at: datetime,
    occurred_date: str,
    precision: str,
    notes: str | None,
    selected_optional: list[int],
    extras: list[dict[str, Any]],
    request_id: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for animal_id in target_ids:
        if animal_id is None:
            continue
        result = v0924_features._execute_treatment_sync(  # noqa: SLF001
            database,
            plan_id,
            animal_id,
            occurred_at,
            occurred_date,
            precision,
            notes,
            selected_optional,
            extras,
            f"{request_id}:{animal_id}",
        )
        results.extend(list(result.get("events") or []))
    return _annotate_events_sync(path, results, metadata)


def async_setup_v0926_features(hass: HomeAssistant) -> None:
    target_fields = {
        vol.Required("target_scope"): vol.In(_SCOPES),
        vol.Optional("animal_ids", default=[]): [_required_text],
        vol.Optional("group_id"): _optional_text,
    }
    temporal_fields = {
        vol.Optional("occurred_date"): _optional_text,
        vol.Optional("occurred_time"): _optional_text,
        vol.Optional("notes"): _optional_text,
    }

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _START_SYMPTOMS_COMMAND,
            **target_fields,
            vol.Required("symptoms"): vol.All([_required_text], vol.Length(min=1, max=30)),
            vol.Optional("severity", default="moderate"): vol.In(SYMPTOM_SEVERITIES),
            **temporal_fields,
        }
    )
    @websocket_api.async_response
    async def websocket_start_symptoms(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        path = _database_path(hass)
        try:
            target_ids, metadata = await hass.async_add_executor_job(
                _resolve_target_sync,
                path,
                msg["target_scope"],
                list(msg.get("animal_ids") or []),
                msg.get("group_id"),
            )
            if metadata["target_scope"] == _SCOPE_GENERAL:
                raise ValueError("Symptoms require an animal or group target")
            occurred_at, precision, day = v0923_features._event_when(  # noqa: SLF001
                hass,
                msg.get("occurred_date"),
                msg.get("occurred_time"),
            )
            result = await hass.async_add_executor_job(
                _start_symptoms_for_target_sync,
                runtime.database,
                path,
                target_ids,
                metadata,
                list(msg["symptoms"]),
                msg.get("severity") or "moderate",
                occurred_at,
                day,
                precision,
                msg.get("notes"),
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0926_symptoms_start_failed", str(err))
            return
        connection.send_result(msg["id"], {"events": result, "target": metadata})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _RECORD_MEDICATIONS_COMMAND,
            **target_fields,
            vol.Required("items"): [dict],
            **temporal_fields,
        }
    )
    @websocket_api.async_response
    async def websocket_record_medications(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        path = _database_path(hass)
        try:
            target_ids, metadata = await hass.async_add_executor_job(
                _resolve_target_sync,
                path,
                msg["target_scope"],
                list(msg.get("animal_ids") or []),
                msg.get("group_id"),
            )
            if metadata["target_scope"] == _SCOPE_GENERAL:
                raise ValueError("Medication requires an animal or group target")
            occurred_at, precision, day = v0923_features._event_when(  # noqa: SLF001
                hass,
                msg.get("occurred_date"),
                msg.get("occurred_time"),
            )
            result = await hass.async_add_executor_job(
                _record_medications_for_target_sync,
                runtime.database,
                path,
                target_ids,
                metadata,
                occurred_at,
                day,
                precision,
                msg.get("notes"),
                list(msg["items"]),
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0926_medications_record_failed", str(err))
            return
        connection.send_result(msg["id"], {"events": result, "target": metadata})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _EXECUTE_TREATMENT_COMMAND,
            **target_fields,
            vol.Required("plan_id"): vol.Coerce(int),
            vol.Optional("selected_optional", default=[]): [vol.Coerce(int)],
            vol.Optional("extras", default=[]): [dict],
            vol.Required("request_id"): _required_text,
            **temporal_fields,
        }
    )
    @websocket_api.async_response
    async def websocket_execute_treatment(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        path = _database_path(hass)
        try:
            target_ids, metadata = await hass.async_add_executor_job(
                _resolve_target_sync,
                path,
                msg["target_scope"],
                list(msg.get("animal_ids") or []),
                msg.get("group_id"),
            )
            if metadata["target_scope"] == _SCOPE_GENERAL:
                raise ValueError("Treatment requires an animal or group target")
            occurred_at, precision, day = v0923_features._event_when(  # noqa: SLF001
                hass,
                msg.get("occurred_date"),
                msg.get("occurred_time"),
            )
            result = await hass.async_add_executor_job(
                _execute_treatment_for_target_sync,
                runtime.database,
                path,
                target_ids,
                metadata,
                int(msg["plan_id"]),
                occurred_at,
                day,
                precision,
                msg.get("notes"),
                list(msg.get("selected_optional") or []),
                list(msg.get("extras") or []),
                msg["request_id"],
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0926_treatment_execute_failed", str(err))
            return
        connection.send_result(msg["id"], {"events": result, "target": metadata})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _CREATE_TASK_COMMAND,
            **target_fields,
            vol.Required("task"): dict,
        }
    )
    @websocket_api.async_response
    async def websocket_create_task(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        path = _database_path(hass)
        task_data = dict(msg["task"] or {})
        try:
            target_ids, metadata = await hass.async_add_executor_job(
                _resolve_target_sync,
                path,
                msg["target_scope"],
                list(msg.get("animal_ids") or []),
                msg.get("group_id"),
            )
            title = _required_text(task_data.get("title"))
            task_kind = _required_text(task_data.get("task_kind"))
            if task_kind not in TASK_KINDS:
                raise ValueError(f"Unsupported task kind: {task_kind}")
            if metadata["target_scope"] == _SCOPE_GENERAL:
                task_kind = TASK_KIND_REMINDER
            recurrence_type = str(task_data.get("recurrence_type") or "once")
            if recurrence_type not in RECURRENCE_TYPES:
                raise ValueError(f"Unsupported recurrence type: {recurrence_type}")
            template = task_record_creation.build_task_template(task_kind, task_data, title=title)
            template.update(metadata)
            created = await TaskRecordStore(hass).create_configured_tasks(
                runtime.coordinator.task_store,
                animal_ids=target_ids,
                task_kind=task_kind,
                template=template,
                title=title,
                description=_optional_text(task_data.get("description")),
                recurrence_type=recurrence_type,
                recurrence_interval=_positive_int(task_data.get("recurrence_interval")),
                start_date=_task_date(task_data.get("start_date")),
                end_date=(
                    _task_date(task_data.get("end_date"))
                    if _optional_text(task_data.get("end_date"))
                    else None
                ),
                due_time=_task_time(task_data.get("due_time")),
            )
            await runtime.coordinator.async_request_refresh()
            store = TaskRecordStore(hass)
            result = await store.enrich_tasks(
                [item.as_dict(runtime.coordinator.task_store.timezone) for item in created]
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0926_task_create_failed", str(err))
            return
        connection.send_result(msg["id"], {"tasks": result, "target": metadata})

    websocket_api.async_register_command(hass, websocket_start_symptoms)
    websocket_api.async_register_command(hass, websocket_record_medications)
    websocket_api.async_register_command(hass, websocket_execute_treatment)
    websocket_api.async_register_command(hass, websocket_create_task)
