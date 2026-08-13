from __future__ import annotations

import json
import secrets
import sqlite3
from datetime import UTC, date, datetime, time, timedelta
from functools import partial
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant

from . import panel as panel_module
from .const import DATABASE_NAME
from .task_kinds import TASK_KIND_MEDICATION
from .task_records import TaskRecordStore
from .task_store import RECURRENCE_ONCE, TaskRecord, TaskStore

_PATCHED = False
_ORIGINAL_ENSURE_OCCURRENCES = TaskStore._ensure_occurrences_for_task
_ORIGINAL_CREATE_CONFIGURED_TASKS = TaskRecordStore.create_configured_tasks
_ORIGINAL_FRONTEND_SOURCE = panel_module._frontend_source
_RECORD_ID_ALPHABET = "23456789ABCDEFGHJKMNPQRSTVWXYZ"
_RECORD_ID_LENGTH = 7


def _next_series_date(task: TaskRecord, anchor: date) -> date | None:
    if task.end_date is not None and task.end_date < anchor:
        return None
    if anchor <= task.start_date:
        candidate = task.start_date
    elif task.recurrence_type == "daily":
        step = task.recurrence_interval
        delta = (anchor - task.start_date).days
        candidate = task.start_date + timedelta(
            days=((delta + step - 1) // step) * step
        )
    elif task.recurrence_type == "weekly":
        step = 7 * task.recurrence_interval
        delta = (anchor - task.start_date).days
        candidate = task.start_date + timedelta(
            days=((delta + step - 1) // step) * step
        )
    elif task.recurrence_type == "monthly":
        months = (
            (anchor.year - task.start_date.year) * 12
            + anchor.month
            - task.start_date.month
        )
        index = max(0, months // task.recurrence_interval)
        candidate = TaskStore._add_months(
            task.start_date,
            index * task.recurrence_interval,
        )
        while candidate < anchor:
            index += 1
            candidate = TaskStore._add_months(
                task.start_date,
                index * task.recurrence_interval,
            )
    else:
        return None
    if task.end_date is not None and candidate > task.end_date:
        return None
    return candidate


def _ensure_compact_occurrence(
    self: TaskStore,
    connection: sqlite3.Connection,
    task: TaskRecord,
    through_date: date,
) -> None:
    if task.recurrence_type == RECURRENCE_ONCE:
        _ORIGINAL_ENSURE_OCCURRENCES(self, connection, task, through_date)
        return
    if not task.is_active:
        return

    target_date = _next_series_date(task, self.local_today())
    if target_date is None:
        connection.execute(
            "DELETE FROM task_occurrences WHERE task_id = ? AND status = 'pending'",
            (task.id,),
        )
        return

    scheduled_for = self._scheduled_for_utc(target_date, task.due_time).isoformat()
    connection.execute(
        """
        DELETE FROM task_occurrences
        WHERE task_id = ?
          AND status = 'pending'
          AND scheduled_for <> ?
        """,
        (task.id, scheduled_for),
    )
    existing = connection.execute(
        "SELECT 1 FROM task_occurrences WHERE task_id = ? AND scheduled_for = ?",
        (task.id, scheduled_for),
    ).fetchone()
    if existing is not None:
        return

    existing_ids = {
        str(row[0])
        for row in connection.execute("SELECT id FROM task_occurrences").fetchall()
    }
    occurrence_id = self._generate_record_id("OC", existing_ids)
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    connection.execute(
        """
        INSERT INTO task_occurrences (
            id,
            task_id,
            scheduled_for,
            status,
            completed_at,
            notes,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, 'pending', NULL, NULL, ?, ?)
        """,
        (occurrence_id, task.id, scheduled_for, now, now),
    )


def _generate_event_id(connection: sqlite3.Connection) -> str:
    existing_ids = {
        str(row[0]) for row in connection.execute("SELECT id FROM events").fetchall()
    }
    while True:
        suffix = "".join(
            secrets.choice(_RECORD_ID_ALPHABET) for _ in range(_RECORD_ID_LENGTH)
        )
        event_id = f"EV-{suffix}"
        if event_id not in existing_ids:
            return event_id


def _insert_series_summary(
    connection: sqlite3.Connection,
    *,
    task_id: str,
    animal_id: str,
    template: dict[str, Any],
    recurrence_type: str,
    recurrence_interval: int,
    start_date: date,
    end_date: date | None,
    due_time: time | None,
    timezone: ZoneInfo,
) -> None:
    exists = connection.execute(
        """
        SELECT 1
        FROM events
        WHERE task_id = ? AND title = 'series_medication_started'
        LIMIT 1
        """,
        (task_id,),
    ).fetchone()
    if exists is not None:
        return
    occurred_at = (
        datetime.combine(start_date, due_time or time.min, tzinfo=timezone)
        .astimezone(UTC)
        .replace(microsecond=0)
    )
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    data = {
        "series": {
            "compact_recurring": True,
            "task_id": task_id,
            "task_kind": TASK_KIND_MEDICATION,
            "recurrence_type": recurrence_type,
            "recurrence_interval": recurrence_interval,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat() if end_date else None,
            "due_time": due_time.isoformat(timespec="minutes") if due_time else None,
            "planned": template,
            "backdated_without_individual_records": True,
        }
    }
    connection.execute(
        """
        INSERT INTO events (
            id,
            animal_id,
            event_type,
            occurred_at,
            title,
            notes,
            value,
            unit,
            correction_of_event_id,
            data_json,
            task_id,
            task_occurrence_id,
            created_at
        ) VALUES (
            ?, ?, 'medication', ?, 'series_medication_started',
            NULL, NULL, NULL, NULL, ?, ?, NULL, ?
        )
        """,
        (
            _generate_event_id(connection),
            animal_id,
            occurred_at.isoformat(),
            json.dumps(data, ensure_ascii=False, sort_keys=True),
            task_id,
            now,
        ),
    )


def _record_backdated_series_summaries_sync(
    database_path: Path,
    tasks: list[TaskRecord],
    *,
    task_kind: str,
    template: dict[str, Any],
    recurrence_type: str,
    recurrence_interval: int,
    start_date: date,
    end_date: date | None,
    due_time: time | None,
    timezone: ZoneInfo,
) -> None:
    if task_kind != TASK_KIND_MEDICATION or recurrence_type == RECURRENCE_ONCE:
        return
    local_today = datetime.now(UTC).astimezone(timezone).date()
    if start_date >= local_today:
        return

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        for task in tasks:
            if task.animal_id is None:
                continue
            _insert_series_summary(
                connection,
                task_id=task.id,
                animal_id=task.animal_id,
                template=template,
                recurrence_type=recurrence_type,
                recurrence_interval=recurrence_interval,
                start_date=start_date,
                end_date=end_date,
                due_time=due_time,
                timezone=timezone,
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


async def _create_configured_tasks_compact(
    self: TaskRecordStore,
    task_store: TaskStore,
    *,
    animal_ids: list[str | None],
    task_kind: str,
    template: dict[str, Any],
    title: str,
    description: str | None,
    recurrence_type: str,
    recurrence_interval: int,
    start_date: date,
    end_date: date | None,
    due_time: time | None,
) -> list[TaskRecord]:
    tasks = await _ORIGINAL_CREATE_CONFIGURED_TASKS(
        self,
        task_store,
        animal_ids=animal_ids,
        task_kind=task_kind,
        template=template,
        title=title,
        description=description,
        recurrence_type=recurrence_type,
        recurrence_interval=recurrence_interval,
        start_date=start_date,
        end_date=end_date,
        due_time=due_time,
    )
    await self._hass.async_add_executor_job(
        partial(
            _record_backdated_series_summaries_sync,
            self._database_path,
            tasks,
            task_kind=task_kind,
            template=template,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
            start_date=start_date,
            end_date=end_date,
            due_time=due_time,
            timezone=task_store.timezone,
        )
    )
    return tasks


def _frontend_source_v0815() -> str:
    source = _ORIGINAL_FRONTEND_SOURCE()
    prefix = 'const V="'
    if not source.startswith(prefix):
        return source
    end = source.find('"', len(prefix))
    if end < 0:
        return source
    return f'{prefix}{panel_module.INTEGRATION_VERSION}{source[end:]}'


def apply_v0815_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    TaskStore._ensure_occurrences_for_task = _ensure_compact_occurrence
    TaskRecordStore.create_configured_tasks = _create_configured_tasks_compact
    panel_module._frontend_source = _frontend_source_v0815
    _PATCHED = True


def _initialize_v0815_sync(database_path: Path, timezone: ZoneInfo) -> None:
    local_today = datetime.now(UTC).astimezone(timezone).date()
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        connection.execute(
            """
            DELETE FROM task_occurrences
            WHERE status = 'pending'
              AND task_id IN (
                  SELECT id
                  FROM tasks
                  WHERE recurrence_type <> 'once'
              )
            """
        )
        rows = connection.execute(
            """
            SELECT
                task.id,
                task.animal_id,
                task.recurrence_type,
                task.recurrence_interval,
                task.start_date,
                task.end_date,
                task.due_time,
                config.template_json
            FROM tasks AS task
            JOIN task_record_configs AS config ON config.task_id = task.id
            WHERE task.recurrence_type <> 'once'
              AND config.task_kind = 'medication'
              AND task.animal_id IS NOT NULL
              AND task.start_date < ?
            """,
            (local_today.isoformat(),),
        ).fetchall()
        for row in rows:
            template = json.loads(str(row["template_json"] or "{}"))
            if not isinstance(template, dict):
                template = {}
            _insert_series_summary(
                connection,
                task_id=str(row["id"]),
                animal_id=str(row["animal_id"]),
                template=template,
                recurrence_type=str(row["recurrence_type"]),
                recurrence_interval=int(row["recurrence_interval"]),
                start_date=date.fromisoformat(str(row["start_date"])),
                end_date=(
                    date.fromisoformat(str(row["end_date"]))
                    if row["end_date"] is not None
                    else None
                ),
                due_time=(
                    time.fromisoformat(str(row["due_time"]))
                    if row["due_time"] is not None
                    else None
                ),
                timezone=timezone,
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


async def async_initialize_v0815_features(hass: HomeAssistant) -> None:
    database_path = Path(hass.config.path(DATABASE_NAME))
    timezone = ZoneInfo(hass.config.time_zone)
    await hass.async_add_executor_job(_initialize_v0815_sync, database_path, timezone)
