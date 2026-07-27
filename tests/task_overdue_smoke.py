from __future__ import annotations

import ast
import sqlite3
from pathlib import Path


MODULE = Path("custom_components/animal_health/task_stabilization.py")


def _select_sql() -> str:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "_task_select_sql":
            continue
        for statement in node.body:
            if not isinstance(statement, ast.Return):
                continue
            value = statement.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                return value.value
    raise AssertionError("Could not find stabilized task-select SQL")


def _counts(
    connection: sqlite3.Connection,
    sql: str,
    *,
    now_utc: str,
    local_day_start_utc: str,
) -> dict[str, int]:
    rows = connection.execute(sql, (now_utc, local_day_start_utc)).fetchall()
    return {str(row["id"]): int(row["overdue_count"]) for row in rows}


def main() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
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
            description TEXT,
            recurrence_type TEXT NOT NULL,
            recurrence_interval INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,
            due_time TEXT,
            is_active INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE task_occurrences (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL REFERENCES tasks(id),
            scheduled_for TEXT NOT NULL,
            status TEXT NOT NULL
        );
        INSERT INTO tasks VALUES (
            'TK-ALL-DAY',
            NULL,
            'All-day task',
            NULL,
            'once',
            1,
            '2026-07-27',
            NULL,
            NULL,
            1,
            '2026-07-27T08:00:00+00:00',
            '2026-07-27T08:00:00+00:00'
        );
        INSERT INTO task_occurrences VALUES (
            'OC-ALL-DAY',
            'TK-ALL-DAY',
            '2026-07-26T22:00:00+00:00',
            'pending'
        );
        INSERT INTO tasks VALUES (
            'TK-TIMED',
            NULL,
            'Timed task',
            NULL,
            'once',
            1,
            '2026-07-27',
            NULL,
            '08:00',
            1,
            '2026-07-27T08:00:00+00:00',
            '2026-07-27T08:00:00+00:00'
        );
        INSERT INTO task_occurrences VALUES (
            'OC-TIMED',
            'TK-TIMED',
            '2026-07-27T06:00:00+00:00',
            'pending'
        );
        """
    )

    sql = _select_sql()

    counts = _counts(
        connection,
        sql,
        now_utc="2026-07-27T12:00:00+00:00",
        local_day_start_utc="2026-07-26T22:00:00+00:00",
    )
    assert counts["TK-ALL-DAY"] == 0
    assert counts["TK-TIMED"] == 1

    counts = _counts(
        connection,
        sql,
        now_utc="2026-07-26T21:00:00+00:00",
        local_day_start_utc="2026-07-25T22:00:00+00:00",
    )
    assert counts["TK-ALL-DAY"] == 0
    assert counts["TK-TIMED"] == 0

    counts = _counts(
        connection,
        sql,
        now_utc="2026-07-27T22:00:00+00:00",
        local_day_start_utc="2026-07-27T22:00:00+00:00",
    )
    assert counts["TK-ALL-DAY"] == 1
    assert counts["TK-TIMED"] == 1

    connection.execute(
        "UPDATE task_occurrences SET scheduled_for = ? WHERE id = 'OC-ALL-DAY'",
        ("2026-03-28T23:00:00+00:00",),
    )
    counts = _counts(
        connection,
        sql,
        now_utc="2026-03-29T21:59:00+00:00",
        local_day_start_utc="2026-03-28T23:00:00+00:00",
    )
    assert counts["TK-ALL-DAY"] == 0
    counts = _counts(
        connection,
        sql,
        now_utc="2026-03-29T22:00:00+00:00",
        local_day_start_utc="2026-03-29T22:00:00+00:00",
    )
    assert counts["TK-ALL-DAY"] == 1

    connection.execute(
        "UPDATE task_occurrences SET scheduled_for = ? WHERE id = 'OC-ALL-DAY'",
        ("2026-10-24T22:00:00+00:00",),
    )
    counts = _counts(
        connection,
        sql,
        now_utc="2026-10-25T22:59:00+00:00",
        local_day_start_utc="2026-10-24T22:00:00+00:00",
    )
    assert counts["TK-ALL-DAY"] == 0
    counts = _counts(
        connection,
        sql,
        now_utc="2026-10-25T23:00:00+00:00",
        local_day_start_utc="2026-10-25T23:00:00+00:00",
    )
    assert counts["TK-ALL-DAY"] == 1

    connection.close()
    print("task overdue smoke test passed")


if __name__ == "__main__":
    main()
