from __future__ import annotations

import json
import sqlite3
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from . import v0815_features
from .confirmation_policy import CONFIRMATION_REQUIRED
from .task_store import OCCURRENCE_PENDING, TaskRecord, TaskStore
from .v0941_occurrences import confirmation_mode, insert_occurrence
from .v0941_recurrence import (
    local_date,
    occurrence_rows,
    previous_closed_series_date,
    week_start,
)

_LEGACY_RECOVERY_DAYS = 60
_MIGRATION_TABLE = "v0941_state"
_RECOVERY_KEY = "legacy_required_occurrence_recovery"


def _recover_latest_required_occurrence(
    connection: sqlite3.Connection,
    task: TaskRecord,
    timezone: ZoneInfo,
    today: date,
    *,
    configured_week_start: str,
    existing_ids: set[str],
) -> None:
    if confirmation_mode(connection, task.id) != CONFIRMATION_REQUIRED:
        return
    candidate = previous_closed_series_date(
        task,
        today,
        configured_week_start=configured_week_start,
    )
    if candidate is None:
        return
    lifecycle_floor = max(
        task.start_date,
        local_date(task.created_at, timezone),
        local_date(task.updated_at, timezone),
        today - timedelta(days=_LEGACY_RECOVERY_DAYS),
    )
    if candidate < lifecycle_floor:
        return
    rows = occurrence_rows(connection, task.id, timezone)
    existing_dates = {item["scheduled_date"] for item in rows}
    if not any(existing_date > candidate for existing_date in existing_dates):
        return
    insert_occurrence(
        None,
        connection,
        task,
        candidate,
        timezone,
        status=OCCURRENCE_PENDING,
        existing_dates=existing_dates,
        existing_ids=existing_ids,
    )


def _active_series_tasks(connection: sqlite3.Connection) -> list[TaskRecord]:
    rows = connection.execute(
        """
        SELECT
            id, animal_id, title, description, recurrence_type,
            recurrence_interval, start_date, end_date, due_time, is_active,
            created_at, updated_at
        FROM tasks
        WHERE is_active=1 AND recurrence_type <> 'once'
        """
    ).fetchall()
    return [
        TaskRecord(
            id=str(row["id"]),
            animal_id=(
                str(row["animal_id"]) if row["animal_id"] is not None else None
            ),
            animal_name=None,
            title=str(row["title"]),
            description=(
                str(row["description"])
                if row["description"] is not None
                else None
            ),
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
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )
        for row in rows
    ]


def _recover_legacy_required_occurrences(
    connection: sqlite3.Connection,
    timezone: ZoneInfo,
    today: date,
) -> None:
    configured_week_start = week_start(connection)
    existing_ids = {
        str(row[0])
        for row in connection.execute("SELECT id FROM task_occurrences").fetchall()
    }
    for task in _active_series_tasks(connection):
        _recover_latest_required_occurrence(
            connection,
            task,
            timezone,
            today,
            configured_week_start=configured_week_start,
            existing_ids=existing_ids,
        )


def _ensure_migration_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {_MIGRATION_TABLE} (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )


def recover_legacy_required_occurrences_once(
    connection: sqlite3.Connection,
    timezone: ZoneInfo,
    today: date,
) -> None:
    _ensure_migration_schema(connection)
    migrated = connection.execute(
        f"SELECT 1 FROM {_MIGRATION_TABLE} WHERE key=?",
        (_RECOVERY_KEY,),
    ).fetchone()
    if migrated is not None:
        return
    _recover_legacy_required_occurrences(connection, timezone, today)
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    connection.execute(
        f"INSERT INTO {_MIGRATION_TABLE}(key,value,updated_at) VALUES(?,?,?)",
        (_RECOVERY_KEY, "completed", now),
    )


def _record_backdated_medication_summaries(
    connection: sqlite3.Connection,
    timezone: ZoneInfo,
    local_today: date,
) -> None:
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
        v0815_features._insert_series_summary(
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


def initialize_sync(database_path: Path, timezone: ZoneInfo) -> None:
    local_today = datetime.now(UTC).astimezone(timezone).date()
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        recover_legacy_required_occurrences_once(
            connection,
            timezone,
            local_today,
        )
        _record_backdated_medication_summaries(
            connection,
            timezone,
            local_today,
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
