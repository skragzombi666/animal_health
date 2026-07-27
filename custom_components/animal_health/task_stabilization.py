from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from typing import Any

from .task_store import (
    INITIAL_OCCURRENCE_HORIZON_DAYS,
    TASK_ACTIVE_ACTIVE,
    TASK_ACTIVE_INACTIVE,
    TASK_ACTIVE_STATES,
    TASK_SCOPE_ANIMAL,
    TASK_SCOPE_GENERAL,
    TASK_SCOPES,
    TaskRecord,
    TaskStore,
)


def _task_select_sql() -> str:
    return """
        SELECT
            task.id,
            task.animal_id,
            animal.name AS animal_name,
            task.title,
            task.description,
            task.recurrence_type,
            task.recurrence_interval,
            task.start_date,
            task.end_date,
            task.due_time,
            task.is_active,
            task.created_at,
            task.updated_at,
            (
                SELECT MIN(occurrence.scheduled_for)
                FROM task_occurrences AS occurrence
                WHERE occurrence.task_id = task.id
                  AND occurrence.status = 'pending'
            ) AS next_pending_at,
            (
                SELECT COUNT(*)
                FROM task_occurrences AS occurrence
                WHERE occurrence.task_id = task.id
                  AND occurrence.status = 'pending'
            ) AS pending_count,
            (
                SELECT COUNT(*)
                FROM task_occurrences AS occurrence
                WHERE occurrence.task_id = task.id
                  AND occurrence.status = 'pending'
                  AND (
                      (
                          task.due_time IS NOT NULL
                          AND occurrence.scheduled_for < ?1
                      )
                      OR
                      (
                          task.due_time IS NULL
                          AND occurrence.scheduled_for < ?2
                      )
                  )
            ) AS overdue_count
        FROM tasks AS task
        LEFT JOIN animals AS animal ON animal.id = task.animal_id
    """


def _time_parameters(store: TaskStore) -> tuple[str, str]:
    now = datetime.now(UTC).replace(microsecond=0)
    local_today = now.astimezone(store.timezone).date()
    local_day_start = store._local_day_start_utc(local_today)
    return now.isoformat(), local_day_start.isoformat()


def _get_task_from_connection(
    self: TaskStore,
    connection: sqlite3.Connection,
    task_id: str,
) -> TaskRecord | None:
    now, local_day_start = _time_parameters(self)
    row = connection.execute(
        self._task_select_sql() + " WHERE task.id = ?",
        (now, local_day_start, task_id),
    ).fetchone()
    return self._task_from_row(row) if row is not None else None


def _ensure_occurrences_for_active_tasks(
    self: TaskStore,
    connection: sqlite3.Connection,
    through_date: Any,
) -> None:
    now, local_day_start = _time_parameters(self)
    rows = connection.execute(
        self._task_select_sql() + " WHERE task.is_active = 1",
        (now, local_day_start),
    ).fetchall()
    for row in rows:
        self._ensure_occurrences_for_task(
            connection,
            self._task_from_row(row),
            through_date,
        )


def _list_tasks_sync(
    self: TaskStore,
    scope: str,
    animal_id: str | None,
    active_state: str,
    limit: int,
) -> list[TaskRecord]:
    if scope not in TASK_SCOPES:
        raise ValueError(f"Unsupported task scope: {scope}")
    if active_state not in TASK_ACTIVE_STATES:
        raise ValueError(f"Unsupported active state: {active_state}")

    horizon = self.local_today() + timedelta(days=INITIAL_OCCURRENCE_HORIZON_DAYS)
    now, local_day_start = _time_parameters(self)
    with self._connect() as connection:
        self._ensure_occurrences_for_active_tasks(connection, horizon)
        clauses: list[str] = []
        values: list[Any] = [now, local_day_start]
        if scope == TASK_SCOPE_GENERAL:
            clauses.append("task.animal_id IS NULL")
        elif scope == TASK_SCOPE_ANIMAL:
            clauses.append("task.animal_id IS NOT NULL")
        if animal_id is not None:
            clauses.append("task.animal_id = ?")
            values.append(animal_id)
        if active_state == TASK_ACTIVE_ACTIVE:
            clauses.append("task.is_active = 1")
        elif active_state == TASK_ACTIVE_INACTIVE:
            clauses.append("task.is_active = 0")

        sql = self._task_select_sql()
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY task.title COLLATE NOCASE, task.id LIMIT ?"
        values.append(limit)
        rows = connection.execute(sql, values).fetchall()
    return [self._task_from_row(row) for row in rows]


def apply_task_stabilization() -> None:
    """Apply backwards-compatible task fixes before TaskStore instances are used."""
    TaskStore._task_select_sql = staticmethod(_task_select_sql)
    TaskStore._get_task_from_connection = _get_task_from_connection
    TaskStore._ensure_occurrences_for_active_tasks = _ensure_occurrences_for_active_tasks
    TaskStore._list_tasks_sync = _list_tasks_sync
