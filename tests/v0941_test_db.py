from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime, time

from v0941_test_support import TIMEZONE, TaskRecord


def schema(connection: sqlite3.Connection) -> None:
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        PRAGMA foreign_keys=ON;
        CREATE TABLE tasks(
            id TEXT PRIMARY KEY,
            animal_id TEXT,
            title TEXT,
            description TEXT,
            recurrence_type TEXT,
            recurrence_interval INTEGER,
            start_date TEXT,
            end_date TEXT,
            due_time TEXT,
            is_active INTEGER,
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE task_occurrences(
            id TEXT PRIMARY KEY,
            task_id TEXT REFERENCES tasks(id) ON DELETE CASCADE,
            scheduled_for TEXT,
            status TEXT,
            completed_at TEXT,
            notes TEXT,
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(task_id,scheduled_for)
        );
        CREATE TABLE task_record_configs(
            task_id TEXT PRIMARY KEY,
            task_kind TEXT,
            template_json TEXT,
            confirmation_mode TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE task_occurrence_plans(
            occurrence_id TEXT PRIMARY KEY,
            planned_json TEXT DEFAULT '{}',
            resolved_at TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TRIGGER plan_insert AFTER INSERT ON task_occurrences BEGIN
            INSERT OR IGNORE INTO task_occurrence_plans(
                occurrence_id,planned_json,resolved_at,created_at,updated_at
            )
            SELECT NEW.id,COALESCE(template_json,'{}'),NULL,
                   NEW.created_at,NEW.updated_at
            FROM task_record_configs WHERE task_id=NEW.task_id;
        END;
        CREATE TABLE events(id TEXT PRIMARY KEY,task_id TEXT,title TEXT);
        """
    )


def _utc_stamp(day: date) -> str:
    return datetime.combine(day, time(8), tzinfo=TIMEZONE).astimezone(UTC).replace(
        microsecond=0
    ).isoformat()


def add_task(
    connection: sqlite3.Connection,
    *,
    task_id: str = "T1",
    start: date = date(2026, 9, 1),
    recurrence_type: str = "daily",
    recurrence_interval: int = 1,
    created: date = date(2026, 9, 1),
    updated: date | None = None,
    mode: str = "required",
    active: bool = True,
    due_time: time | None = None,
    end: date | None = None,
) -> TaskRecord:
    updated = updated or created
    connection.execute(
        "INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            task_id,
            "A1",
            "Task",
            None,
            recurrence_type,
            recurrence_interval,
            start.isoformat(),
            end.isoformat() if end else None,
            due_time.isoformat(timespec="minutes") if due_time else None,
            1 if active else 0,
            _utc_stamp(created),
            _utc_stamp(updated),
        ),
    )
    connection.execute(
        "INSERT INTO task_record_configs VALUES(?,?,?,?,?,?)",
        (
            task_id,
            "medication",
            "{}",
            mode,
            _utc_stamp(created),
            _utc_stamp(updated),
        ),
    )
    connection.commit()
    row = connection.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    return TaskRecord(
        id=str(row["id"]),
        animal_id=str(row["animal_id"]),
        animal_name=None,
        title=str(row["title"]),
        description=None,
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


def add_occurrence(
    connection: sqlite3.Connection,
    task: TaskRecord,
    scheduled_date: date,
    status: str = "pending",
) -> None:
    scheduled_for = datetime.combine(
        scheduled_date,
        task.due_time or time.min,
        tzinfo=TIMEZONE,
    ).astimezone(UTC).replace(microsecond=0).isoformat()
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    index = int(
        connection.execute("SELECT COUNT(*) FROM task_occurrences").fetchone()[0]
    ) + 1
    connection.execute(
        "INSERT INTO task_occurrences VALUES(?,?,?,?,?,?,?,?)",
        (f"O{index}", task.id, scheduled_for, status, None, None, now, now),
    )
    connection.commit()


def occurrences(
    connection: sqlite3.Connection,
    task_id: str = "T1",
) -> list[tuple[date, str]]:
    rows = connection.execute(
        "SELECT scheduled_for,status FROM task_occurrences "
        "WHERE task_id=? ORDER BY scheduled_for",
        (task_id,),
    ).fetchall()
    return [
        (
            datetime.fromisoformat(str(row["scheduled_for"]))
            .astimezone(TIMEZONE)
            .date(),
            str(row["status"]),
        )
        for row in rows
    ]
