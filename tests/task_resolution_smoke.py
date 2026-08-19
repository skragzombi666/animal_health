from __future__ import annotations

import ast
import sqlite3
from pathlib import Path


SCHEMA_MODULE = Path("custom_components/animal_health/task_record_schema.py")


def _schema_sql() -> str:
    tree = ast.parse(SCHEMA_MODULE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "executescript" or not node.args:
            continue
        argument = node.args[0]
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
            return argument.value
    raise AssertionError("Could not find task-record schema SQL")


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        """
        CREATE TABLE animals (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            animal_id TEXT REFERENCES animals(id),
            title TEXT NOT NULL,
            due_time TEXT
        );
        CREATE TABLE task_occurrences (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            scheduled_for TEXT NOT NULL,
            status TEXT NOT NULL,
            completed_at TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE events (
            id TEXT PRIMARY KEY,
            task_id TEXT REFERENCES tasks(id),
            task_occurrence_id TEXT REFERENCES task_occurrences(id)
        );
        """
    )
    connection.executescript(_schema_sql())
    return connection


def _add_reminder(
    connection: sqlite3.Connection,
    task_id: str,
    occurrence_id: str,
) -> None:
    connection.execute(
        "INSERT INTO tasks VALUES (?, NULL, ?, NULL)",
        (task_id, task_id),
    )
    connection.execute(
        """
        INSERT INTO task_record_configs (
            task_id, task_kind, template_json, confirmation_mode,
            created_at, updated_at
        ) VALUES (?, 'reminder', '{}', 'required', ?, ?)
        """,
        (
            task_id,
            "2026-07-27T10:00:00+00:00",
            "2026-07-27T10:00:00+00:00",
        ),
    )
    connection.execute(
        """
        INSERT INTO task_occurrences VALUES (?, ?, ?, 'pending', NULL, NULL, ?, ?)
        """,
        (
            occurrence_id,
            task_id,
            "2026-07-27T08:00:00+00:00",
            "2026-07-27T10:00:00+00:00",
            "2026-07-27T10:00:00+00:00",
        ),
    )


def main() -> None:
    connection = _connection()

    cases = (
        (
            "completed",
            "2026-07-27T11:00:00+00:00",
            "completed to test",
        ),
        (
            "skipped",
            "2026-07-27T11:01:00+00:00",
            "skipped to test",
        ),
        (
            "cancelled",
            "2026-07-27T11:02:00+00:00",
            "cancelled to test",
        ),
    )

    for index, (status, resolved_at, notes) in enumerate(cases, start=1):
        task_id = f"TK-{index}"
        occurrence_id = f"OC-{index}"
        _add_reminder(connection, task_id, occurrence_id)
        completed_at = resolved_at if status == "completed" else None
        connection.execute(
            """
            UPDATE task_occurrences
            SET status = ?, completed_at = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, completed_at, notes, resolved_at, occurrence_id),
        )
        row = connection.execute(
            """
            SELECT
                occurrence.status,
                occurrence.completed_at,
                occurrence.notes,
                plan.resolved_at
            FROM task_occurrences AS occurrence
            JOIN task_occurrence_plans AS plan
              ON plan.occurrence_id = occurrence.id
            WHERE occurrence.id = ?
            """,
            (occurrence_id,),
        ).fetchone()
        assert row is not None
        assert row["status"] == status
        assert row["notes"] == notes
        assert row["resolved_at"] == resolved_at
        if status == "completed":
            assert row["completed_at"] == resolved_at
        else:
            assert row["completed_at"] is None

    connection.close()
    print("task resolution smoke test passed")


if __name__ == "__main__":
    main()
