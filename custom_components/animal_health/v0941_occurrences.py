from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from . import v0815_features
from .confirmation_policy import (
    CONFIRMATION_REQUIRED,
    CONFIRMATION_ROUTINE,
    OCCURRENCE_NOT_DOCUMENTED,
    recurrence_period_bounds,
)
from .task_store import (
    MAX_GENERATED_OCCURRENCES,
    OCCURRENCE_PENDING,
    RECURRENCE_ONCE,
    TaskRecord,
    TaskStore,
)
from .v0941_recurrence import (
    local_date,
    next_series_date,
    occurrence_rows,
    target_series_date,
    week_start,
)


def confirmation_mode(connection: sqlite3.Connection, task_id: str) -> str:
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master "
        "WHERE type='table' AND name='task_record_configs'"
    ).fetchone()
    if exists is None:
        return CONFIRMATION_REQUIRED
    row = connection.execute(
        "SELECT confirmation_mode FROM task_record_configs WHERE task_id=?",
        (task_id,),
    ).fetchone()
    value = str(row[0] if row is not None else CONFIRMATION_REQUIRED)
    return CONFIRMATION_ROUTINE if value == CONFIRMATION_ROUTINE else CONFIRMATION_REQUIRED


def insert_occurrence(
    store: TaskStore | None,
    connection: sqlite3.Connection,
    task: TaskRecord,
    occurrence_date: date,
    timezone: ZoneInfo,
    *,
    status: str,
    existing_dates: set[date],
    existing_ids: set[str],
) -> bool:
    if occurrence_date in existing_dates:
        return False
    scheduled_for = (
        store._scheduled_for_utc(occurrence_date, task.due_time)
        if store is not None
        else datetime.combine(
            occurrence_date,
            task.due_time or time.min,
            tzinfo=timezone,
        ).astimezone(UTC).replace(microsecond=0)
    )
    occurrence_id = TaskStore._generate_record_id("OC", existing_ids)
    existing_ids.add(occurrence_id)
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    connection.execute(
        """
        INSERT INTO task_occurrences (
            id, task_id, scheduled_for, status, completed_at, notes,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, NULL, NULL, ?, ?)
        """,
        (occurrence_id, task.id, scheduled_for.isoformat(), status, now, now),
    )
    existing_dates.add(occurrence_date)
    if status == OCCURRENCE_NOT_DOCUMENTED:
        plans_exist = connection.execute(
            "SELECT 1 FROM sqlite_master "
            "WHERE type='table' AND name='task_occurrence_plans'"
        ).fetchone()
        if plans_exist is not None:
            connection.execute(
                """
                UPDATE task_occurrence_plans
                SET resolved_at=?, updated_at=?
                WHERE occurrence_id=?
                """,
                (now, now, occurrence_id),
            )
    return True


def _status_for_date(
    task: TaskRecord,
    occurrence_date: date,
    today: date,
    mode: str,
    *,
    configured_week_start: str,
) -> str:
    if mode != CONFIRMATION_ROUTINE:
        return OCCURRENCE_PENDING
    _, period_end = recurrence_period_bounds(
        task.recurrence_type,
        occurrence_date,
        week_start=configured_week_start,
    )
    return (
        OCCURRENCE_NOT_DOCUMENTED if period_end < today else OCCURRENCE_PENDING
    )


def ensure_preserving_occurrences(
    self: TaskStore,
    connection: sqlite3.Connection,
    task: TaskRecord,
    through_date: date,
) -> None:
    if task.recurrence_type == RECURRENCE_ONCE:
        v0815_features._ORIGINAL_ENSURE_OCCURRENCES(
            self,
            connection,
            task,
            through_date,
        )
        return
    if not task.is_active:
        return

    timezone = self.timezone
    today = self.local_today()
    configured_week_start = week_start(connection)
    rows = occurrence_rows(connection, task.id, timezone)
    target = target_series_date(
        task,
        today,
        rows,
        configured_week_start=configured_week_start,
    )
    if target is None:
        return

    existing_dates = {item["scheduled_date"] for item in rows}
    existing_ids = {
        str(row[0])
        for row in connection.execute("SELECT id FROM task_occurrences").fetchall()
    }
    dates: list[date] = []
    latest_existing = max(existing_dates) if existing_dates else None
    if latest_existing is not None and latest_existing < target:
        floor = max(
            latest_existing + timedelta(days=1),
            local_date(task.updated_at, timezone),
            task.start_date,
        )
        candidate = next_series_date(task, floor)
        generated = 0
        while candidate is not None and candidate <= target:
            dates.append(candidate)
            generated += 1
            if generated > MAX_GENERATED_OCCURRENCES:
                raise ValueError(
                    "Task schedule would generate too many catch-up occurrences"
                )
            candidate = next_series_date(task, candidate + timedelta(days=1))
    if target not in dates:
        dates.append(target)

    mode = confirmation_mode(connection, task.id)
    for occurrence_date in sorted(set(dates)):
        insert_occurrence(
            self,
            connection,
            task,
            occurrence_date,
            timezone,
            status=_status_for_date(
                task,
                occurrence_date,
                today,
                mode,
                configured_week_start=configured_week_start,
            ),
            existing_dates=existing_dates,
            existing_ids=existing_ids,
        )
