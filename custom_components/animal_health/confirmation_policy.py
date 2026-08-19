from __future__ import annotations

import calendar
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
import sqlite3
from typing import Any

from homeassistant.core import HomeAssistant

from .const import DATABASE_NAME
from .task_store import TaskStore

CONFIRMATION_REQUIRED = "required"
CONFIRMATION_ROUTINE = "routine"
CONFIRMATION_MODES = (CONFIRMATION_REQUIRED, CONFIRMATION_ROUTINE)
OCCURRENCE_NOT_DOCUMENTED = "not_documented"
WEEK_START_KEYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)

_WEEK_START_SETTING = "week_start"
_CURRENT_WEEK_START = "monday"


def default_confirmation_mode(task_kind: str) -> str:
    return CONFIRMATION_ROUTINE if task_kind in {"reminder", "care"} else CONFIRMATION_REQUIRED


def week_start_key() -> str:
    return _CURRENT_WEEK_START


def week_start_index(value: str | None = None) -> int:
    key = value if value in WEEK_START_KEYS else _CURRENT_WEEK_START
    return WEEK_START_KEYS.index(key)


def recurrence_period_bounds(
    recurrence_type: str,
    scheduled_date: date,
    *,
    week_start: str | None = None,
) -> tuple[date, date]:
    if recurrence_type == "weekly":
        offset = (scheduled_date.weekday() - week_start_index(week_start)) % 7
        start = scheduled_date - timedelta(days=offset)
        return start, start + timedelta(days=6)
    if recurrence_type == "monthly":
        return (
            scheduled_date.replace(day=1),
            date(
                scheduled_date.year,
                scheduled_date.month,
                calendar.monthrange(scheduled_date.year, scheduled_date.month)[1],
            ),
        )
    return scheduled_date, scheduled_date


def recurring_period_state(
    recurrence_type: str,
    scheduled_date: date,
    today: date,
    *,
    week_start: str | None = None,
) -> str:
    start, end = recurrence_period_bounds(
        recurrence_type,
        scheduled_date,
        week_start=week_start,
    )
    if end < today:
        return "past"
    if start <= today <= end:
        return "current"
    return "future"


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _migrate_occurrence_status_sync(path: Path) -> None:
    connection = _connect(path)
    try:
        row = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='task_occurrences'"
        ).fetchone()
        if row is None:
            raise RuntimeError("Animal Health task occurrence table is missing")
        if OCCURRENCE_NOT_DOCUMENTED in str(row["sql"] or ""):
            return
        connection.commit()
        connection.execute("PRAGMA foreign_keys = OFF")
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DROP TABLE IF EXISTS task_occurrences_new")
            connection.execute(
                """
                CREATE TABLE task_occurrences_new (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                    scheduled_for TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN (
                            'pending', 'completed', 'skipped', 'cancelled',
                            'not_documented'
                        )),
                    completed_at TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE (task_id, scheduled_for)
                )
                """
            )
            connection.execute(
                """
                INSERT INTO task_occurrences_new (
                    id, task_id, scheduled_for, status, completed_at,
                    notes, created_at, updated_at
                )
                SELECT id, task_id, scheduled_for, status, completed_at,
                       notes, created_at, updated_at
                FROM task_occurrences
                """
            )
            connection.execute("DROP TABLE task_occurrences")
            connection.execute("ALTER TABLE task_occurrences_new RENAME TO task_occurrences")
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_occurrences_due_status "
                "ON task_occurrences(scheduled_for, status)"
            )
            violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise RuntimeError(
                    f"Animal Health confirmation migration created foreign-key violations: {violations}"
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.execute("PRAGMA foreign_keys = ON")
    finally:
        connection.close()


async def async_initialize_confirmation_policy(hass: HomeAssistant) -> None:
    await hass.async_add_executor_job(
        _migrate_occurrence_status_sync,
        Path(hass.config.path(DATABASE_NAME)),
    )


def _load_week_start_sync(path: Path) -> str:
    with _connect(path) as connection:
        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='v081_settings'"
        ).fetchone() is None:
            return "monday"
        row = connection.execute(
            "SELECT value FROM v081_settings WHERE key = ?",
            (_WEEK_START_SETTING,),
        ).fetchone()
    value = str(row["value"] if row is not None else "monday")
    return value if value in WEEK_START_KEYS else "monday"


async def async_load_confirmation_policy_settings(hass: HomeAssistant) -> None:
    global _CURRENT_WEEK_START
    _CURRENT_WEEK_START = await hass.async_add_executor_job(
        _load_week_start_sync,
        Path(hass.config.path(DATABASE_NAME)),
    )


def save_week_start_sync(path: Path, value: str) -> None:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        connection.execute(
            """
            INSERT INTO v081_settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (_WEEK_START_SETTING, value, now),
        )


def set_week_start(value: str) -> str:
    global _CURRENT_WEEK_START
    _CURRENT_WEEK_START = value if value in WEEK_START_KEYS else "monday"
    return _CURRENT_WEEK_START


def confirmation_modes_sync(
    connection: sqlite3.Connection,
    task_ids: list[str],
) -> dict[str, str]:
    if not task_ids:
        return {}
    placeholders = ",".join("?" for _ in task_ids)
    rows = connection.execute(
        f"""
        SELECT task.id, COALESCE(config.confirmation_mode, 'required') AS mode
        FROM tasks AS task
        LEFT JOIN task_record_configs AS config ON config.task_id = task.id
        WHERE task.id IN ({placeholders})
        """,
        task_ids,
    ).fetchall()
    return {
        str(row["id"]): (
            str(row["mode"])
            if str(row["mode"]) in CONFIRMATION_MODES
            else CONFIRMATION_REQUIRED
        )
        for row in rows
    }


def update_confirmation_mode_sync(path: Path, task_id: str, mode: str) -> str:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        task = connection.execute(
            "SELECT id, recurrence_type FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        if task is None:
            raise KeyError(task_id)
        selected = CONFIRMATION_REQUIRED if task["recurrence_type"] == "once" else mode
        existing = connection.execute(
            "SELECT task_kind, template_json FROM task_record_configs WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        is_group = bool(
            connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='task_group_targets'"
            ).fetchone()
            and connection.execute(
                "SELECT 1 FROM task_group_targets WHERE task_id = ?",
                (task_id,),
            ).fetchone()
        )
        task_kind = "reminder" if is_group else str(existing["task_kind"] if existing else "reminder")
        template = str(existing["template_json"] if existing else "{}")
        connection.execute(
            """
            INSERT INTO task_record_configs (
                task_id, task_kind, template_json, confirmation_mode,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                confirmation_mode = excluded.confirmation_mode,
                updated_at = excluded.updated_at
            """,
            (task_id, task_kind, template, selected, now, now),
        )
    return selected


def _resolve_routine_occurrences_sync(path: Path, timezone: Any) -> list[str]:
    today = datetime.now(UTC).astimezone(timezone).date()
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    resolved: list[str] = []
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT occurrence.id, occurrence.scheduled_for, task.recurrence_type
            FROM task_occurrences AS occurrence
            JOIN tasks AS task ON task.id = occurrence.task_id
            LEFT JOIN task_record_configs AS config ON config.task_id = task.id
            WHERE occurrence.status = 'pending'
              AND task.recurrence_type <> 'once'
              AND COALESCE(config.confirmation_mode, 'required') = 'routine'
            ORDER BY occurrence.scheduled_for
            """
        ).fetchall()
        for row in rows:
            scheduled = datetime.fromisoformat(str(row["scheduled_for"]))
            scheduled_date = scheduled.astimezone(timezone).date()
            _, period_end = recurrence_period_bounds(
                str(row["recurrence_type"]), scheduled_date
            )
            if period_end >= today:
                continue
            occurrence_id = str(row["id"])
            connection.execute(
                """
                UPDATE task_occurrences
                SET status='not_documented', completed_at=NULL, updated_at=?
                WHERE id=? AND status='pending'
                """,
                (now, occurrence_id),
            )
            connection.execute(
                """
                INSERT INTO task_occurrence_plans (
                    occurrence_id, planned_json, resolved_at, created_at, updated_at
                )
                SELECT occurrence.id, COALESCE(config.template_json, '{}'), ?,
                       occurrence.created_at, ?
                FROM task_occurrences AS occurrence
                LEFT JOIN task_record_configs AS config
                    ON config.task_id = occurrence.task_id
                WHERE occurrence.id = ?
                ON CONFLICT(occurrence_id) DO UPDATE SET
                    resolved_at=excluded.resolved_at,
                    updated_at=excluded.updated_at
                """,
                (now, now, occurrence_id),
            )
            resolved.append(occurrence_id)
    return resolved


async def async_resolve_routine_occurrences(store: TaskStore) -> list[str]:
    return await store._hass.async_add_executor_job(  # noqa: SLF001
        _resolve_routine_occurrences_sync,
        store._database_path,  # noqa: SLF001
        store.timezone,
    )


def reopen_not_documented(
    path: Path,
    occurrence_id: str,
) -> tuple[bool, str | None, str | None]:
    with _connect(path) as connection:
        row = connection.execute(
            """
            SELECT occurrence.status, occurrence.updated_at, plan.resolved_at
            FROM task_occurrences AS occurrence
            LEFT JOIN task_occurrence_plans AS plan
                ON plan.occurrence_id = occurrence.id
            WHERE occurrence.id = ?
            """,
            (occurrence_id,),
        ).fetchone()
        if row is None:
            raise KeyError(occurrence_id)
        if row["status"] != OCCURRENCE_NOT_DOCUMENTED:
            return False, None, None
        original_updated = str(row["updated_at"])
        original_resolved = str(row["resolved_at"]) if row["resolved_at"] else None
        now = datetime.now(UTC).replace(microsecond=0).isoformat()
        connection.execute(
            "UPDATE task_occurrences SET status='pending', completed_at=NULL, updated_at=? WHERE id=?",
            (now, occurrence_id),
        )
        connection.execute(
            "UPDATE task_occurrence_plans SET resolved_at=NULL, updated_at=? WHERE occurrence_id=?",
            (now, occurrence_id),
        )
    return True, original_updated, original_resolved


def restore_not_documented(
    path: Path,
    occurrence_id: str,
    updated_at: str | None,
    resolved_at: str | None,
) -> None:
    stamp = updated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        connection.execute(
            "UPDATE task_occurrences SET status='not_documented', completed_at=NULL, updated_at=? WHERE id=?",
            (stamp, occurrence_id),
        )
        connection.execute(
            "UPDATE task_occurrence_plans SET resolved_at=?, updated_at=? WHERE occurrence_id=?",
            (resolved_at, stamp, occurrence_id),
        )
