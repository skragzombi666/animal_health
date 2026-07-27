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


def _base_database() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
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


def main() -> None:
    connection = _base_database()
    connection.execute("INSERT INTO animals VALUES ('AH-TEST', 'Test animal')")

    connection.execute(
        "INSERT INTO tasks VALUES ('TK-WEIGHT', 'AH-TEST', 'Record weight', NULL)"
    )
    connection.execute(
        """
        INSERT INTO task_record_configs VALUES (
            'TK-WEIGHT',
            'weight',
            '{"measurement":"weight"}',
            '2026-07-27T10:00:00+00:00',
            '2026-07-27T10:00:00+00:00'
        )
        """
    )
    connection.execute(
        """
        INSERT INTO task_occurrences VALUES (
            'OC-WEIGHT',
            'TK-WEIGHT',
            '2026-07-27T22:00:00+00:00',
            'pending',
            NULL,
            NULL,
            '2026-07-27T10:00:00+00:00',
            '2026-07-27T10:00:00+00:00'
        )
        """
    )
    planned = connection.execute(
        "SELECT planned_json FROM task_occurrence_plans WHERE occurrence_id = 'OC-WEIGHT'"
    ).fetchone()
    assert planned == ('{"measurement":"weight"}',)

    try:
        connection.execute(
            """
            UPDATE task_occurrences
            SET status = 'completed',
                completed_at = '2026-07-27T11:00:00+00:00',
                updated_at = '2026-07-27T11:00:00+00:00'
            WHERE id = 'OC-WEIGHT'
            """
        )
    except sqlite3.IntegrityError as err:
        assert "must be completed through their record action" in str(err)
    else:
        raise AssertionError("Structured task completed without a linked record")

    connection.execute(
        "INSERT INTO events VALUES ('EV-WEIGHT', 'TK-WEIGHT', 'OC-WEIGHT')"
    )
    connection.execute(
        """
        UPDATE task_occurrences
        SET status = 'completed',
            completed_at = '2026-07-27T11:00:00+00:00',
            updated_at = '2026-07-27T11:00:00+00:00'
        WHERE id = 'OC-WEIGHT'
        """
    )
    resolved = connection.execute(
        "SELECT resolved_at FROM task_occurrence_plans WHERE occurrence_id = 'OC-WEIGHT'"
    ).fetchone()
    assert resolved == ('2026-07-27T11:00:00+00:00',)

    try:
        connection.execute(
            "INSERT INTO events VALUES ('EV-DUPLICATE', 'TK-WEIGHT', 'OC-WEIGHT')"
        )
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError("Duplicate record for one occurrence was accepted")

    connection.execute(
        "INSERT INTO tasks VALUES ('TK-REMINDER', NULL, 'Order feed', NULL)"
    )
    connection.execute(
        """
        INSERT INTO task_record_configs VALUES (
            'TK-REMINDER',
            'reminder',
            '{}',
            '2026-07-27T10:00:00+00:00',
            '2026-07-27T10:00:00+00:00'
        )
        """
    )
    connection.execute(
        """
        INSERT INTO task_occurrences VALUES (
            'OC-REMINDER',
            'TK-REMINDER',
            '2026-07-27T22:00:00+00:00',
            'pending',
            NULL,
            NULL,
            '2026-07-27T10:00:00+00:00',
            '2026-07-27T10:00:00+00:00'
        )
        """
    )
    connection.execute(
        """
        UPDATE task_occurrences
        SET status = 'completed',
            completed_at = '2026-07-27T12:00:00+00:00',
            updated_at = '2026-07-27T12:00:00+00:00'
        WHERE id = 'OC-REMINDER'
        """
    )
    reminder_status = connection.execute(
        "SELECT status FROM task_occurrences WHERE id = 'OC-REMINDER'"
    ).fetchone()
    assert reminder_status == ("completed",)
    connection.close()
    print("task-record schema smoke test passed")


if __name__ == "__main__":
    main()
