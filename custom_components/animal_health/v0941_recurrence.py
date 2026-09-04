from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from .confirmation_policy import WEEK_START_KEYS, recurrence_period_bounds
from .task_store import OCCURRENCE_PENDING, TaskRecord, TaskStore


def aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).replace(microsecond=0)


def local_date(value: datetime, timezone: ZoneInfo) -> date:
    return aware_utc(value).astimezone(timezone).date()


def next_series_date(task: TaskRecord, anchor: date) -> date | None:
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


def previous_series_date(task: TaskRecord, anchor: date) -> date | None:
    effective_anchor = min(anchor, task.end_date) if task.end_date else anchor
    if effective_anchor < task.start_date:
        return None
    if task.recurrence_type == "daily":
        step = task.recurrence_interval
        delta = (effective_anchor - task.start_date).days
        return task.start_date + timedelta(days=(delta // step) * step)
    if task.recurrence_type == "weekly":
        step = 7 * task.recurrence_interval
        delta = (effective_anchor - task.start_date).days
        return task.start_date + timedelta(days=(delta // step) * step)
    if task.recurrence_type == "monthly":
        months = (
            (effective_anchor.year - task.start_date.year) * 12
            + effective_anchor.month
            - task.start_date.month
        )
        index = max(0, months // task.recurrence_interval)
        candidate = TaskStore._add_months(
            task.start_date,
            index * task.recurrence_interval,
        )
        while candidate > effective_anchor and index > 0:
            index -= 1
            candidate = TaskStore._add_months(
                task.start_date,
                index * task.recurrence_interval,
            )
        while True:
            following = TaskStore._add_months(
                task.start_date,
                (index + 1) * task.recurrence_interval,
            )
            if following > effective_anchor:
                break
            index += 1
            candidate = following
        return candidate
    return None


def week_start(connection: sqlite3.Connection) -> str:
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='v081_settings'"
    ).fetchone()
    if exists is None:
        return "monday"
    row = connection.execute(
        "SELECT value FROM v081_settings WHERE key='week_start'"
    ).fetchone()
    value = str(row[0] if row is not None else "monday")
    return value if value in WEEK_START_KEYS else "monday"


def current_series_date(
    task: TaskRecord,
    today: date,
    *,
    configured_week_start: str,
) -> date | None:
    candidate = previous_series_date(task, today)
    if candidate is None:
        return None
    period_start, period_end = recurrence_period_bounds(
        task.recurrence_type,
        candidate,
        week_start=configured_week_start,
    )
    return candidate if period_start <= today <= period_end else None


def previous_closed_series_date(
    task: TaskRecord,
    today: date,
    *,
    configured_week_start: str,
) -> date | None:
    candidate = previous_series_date(task, today)
    while candidate is not None:
        _, period_end = recurrence_period_bounds(
            task.recurrence_type,
            candidate,
            week_start=configured_week_start,
        )
        if period_end < today:
            return candidate
        candidate = previous_series_date(task, candidate - timedelta(days=1))
    return None


def occurrence_rows(
    connection: sqlite3.Connection,
    task_id: str,
    timezone: ZoneInfo,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    rows = connection.execute(
        "SELECT id, scheduled_for, status FROM task_occurrences WHERE task_id=?",
        (task_id,),
    ).fetchall()
    for row in rows:
        scheduled = datetime.fromisoformat(str(row["scheduled_for"]))
        result.append(
            {
                "id": str(row["id"]),
                "scheduled_date": local_date(scheduled, timezone),
                "status": str(row["status"]),
            }
        )
    return result


def target_series_date(
    task: TaskRecord,
    today: date,
    rows: list[dict[str, Any]],
    *,
    configured_week_start: str,
) -> date | None:
    current = current_series_date(
        task,
        today,
        configured_week_start=configured_week_start,
    )
    if current is None:
        return next_series_date(task, today)
    statuses = [
        str(item["status"])
        for item in rows
        if item["scheduled_date"] == current
    ]
    if not statuses or OCCURRENCE_PENDING in statuses:
        return current
    return next_series_date(task, current + timedelta(days=1))
