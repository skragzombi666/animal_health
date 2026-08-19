from __future__ import annotations

import ast
import calendar
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
import sqlite3
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"


def _selected_functions(source: str, names: set[str]) -> dict[str, Any]:
    tree = ast.parse(source)
    nodes = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in names
    ]
    namespace: dict[str, Any] = {
        "Any": Any,
        "UTC": UTC,
        "Path": Path,
        "calendar": calendar,
        "date": date,
        "datetime": datetime,
        "sqlite3": sqlite3,
        "timedelta": timedelta,
        "CONFIRMATION_REQUIRED": "required",
        "CONFIRMATION_ROUTINE": "routine",
        "OCCURRENCE_NOT_DOCUMENTED": "not_documented",
        "WEEK_START_KEYS": (
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ),
        "_CURRENT_WEEK_START": "monday",
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "confirmation_policy.py", "exec"), namespace)
    return namespace


def test_confirmation_periods_cover_whole_week_and_month() -> None:
    source = (INTEGRATION / "confirmation_policy.py").read_text(encoding="utf-8")
    helpers = _selected_functions(
        source,
        {
            "default_confirmation_mode",
            "week_start_index",
            "recurrence_period_bounds",
            "recurring_period_state",
        },
    )
    bounds = helpers["recurrence_period_bounds"]
    state = helpers["recurring_period_state"]

    assert bounds("daily", date(2026, 8, 19)) == (
        date(2026, 8, 19),
        date(2026, 8, 19),
    )
    assert bounds("weekly", date(2026, 8, 19)) == (
        date(2026, 8, 17),
        date(2026, 8, 23),
    )
    assert bounds("weekly", date(2026, 8, 19), week_start="sunday") == (
        date(2026, 8, 16),
        date(2026, 8, 22),
    )
    assert bounds("monthly", date(2026, 8, 19)) == (
        date(2026, 8, 1),
        date(2026, 8, 31),
    )
    assert state("weekly", date(2026, 8, 19), date(2026, 8, 17)) == "current"
    assert state("weekly", date(2026, 8, 19), date(2026, 8, 24)) == "past"
    assert helpers["default_confirmation_mode"]("care") == "routine"
    assert helpers["default_confirmation_mode"]("reminder") == "routine"
    assert helpers["default_confirmation_mode"]("medication") == "required"


def test_occurrence_schema_migration_accepts_not_documented(tmp_path: Path) -> None:
    source = (INTEGRATION / "confirmation_policy.py").read_text(encoding="utf-8")
    helpers = _selected_functions(source, {"_connect", "_migrate_occurrence_status_sync"})
    path = tmp_path / "animal_health.db"
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE tasks (id TEXT PRIMARY KEY);
            CREATE TABLE task_occurrences (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                scheduled_for TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','completed','skipped','cancelled')),
                completed_at TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(task_id, scheduled_for)
            );
            INSERT INTO tasks VALUES ('TK-1');
            INSERT INTO task_occurrences VALUES (
                'OC-1','TK-1','2026-08-01T00:00:00+00:00','pending',
                NULL,NULL,'2026-08-01T00:00:00+00:00','2026-08-01T00:00:00+00:00'
            );
            """
        )
    helpers["_migrate_occurrence_status_sync"](path)
    with sqlite3.connect(path) as connection:
        sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE name='task_occurrences'"
        ).fetchone()[0]
        assert "not_documented" in sql
        connection.execute(
            "UPDATE task_occurrences SET status='not_documented' WHERE id='OC-1'"
        )
        assert connection.execute(
            "SELECT status FROM task_occurrences WHERE id='OC-1'"
        ).fetchone() == ("not_documented",)


def test_routine_occurrences_close_without_claiming_completion(tmp_path: Path) -> None:
    source = (INTEGRATION / "confirmation_policy.py").read_text(encoding="utf-8")
    helpers = _selected_functions(
        source,
        {
            "week_start_index",
            "recurrence_period_bounds",
            "_connect",
            "_resolve_routine_occurrences_sync",
        },
    )
    path = tmp_path / "animal_health.db"
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE tasks (
                id TEXT PRIMARY KEY,
                recurrence_type TEXT NOT NULL
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
            CREATE TABLE task_record_configs (
                task_id TEXT PRIMARY KEY,
                template_json TEXT NOT NULL,
                confirmation_mode TEXT NOT NULL
            );
            CREATE TABLE task_occurrence_plans (
                occurrence_id TEXT PRIMARY KEY,
                planned_json TEXT NOT NULL,
                resolved_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            INSERT INTO tasks VALUES ('TK-R','daily'),('TK-P','daily');
            INSERT INTO task_record_configs VALUES
                ('TK-R','{}','routine'),('TK-P','{}','required');
            INSERT INTO task_occurrences VALUES
                ('OC-R','TK-R','2020-01-01T00:00:00+00:00','pending',NULL,NULL,'2020-01-01T00:00:00+00:00','2020-01-01T00:00:00+00:00'),
                ('OC-P','TK-P','2020-01-01T00:00:00+00:00','pending',NULL,NULL,'2020-01-01T00:00:00+00:00','2020-01-01T00:00:00+00:00');
            """
        )
    resolved = helpers["_resolve_routine_occurrences_sync"](path, UTC)
    assert resolved == ["OC-R"]
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT status,completed_at FROM task_occurrences WHERE id='OC-R'"
        ).fetchone() == ("not_documented", None)
        assert connection.execute(
            "SELECT status FROM task_occurrences WHERE id='OC-P'"
        ).fetchone() == ("pending",)


def test_confirmation_policy_is_registered() -> None:
    init_source = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")
    api_source = (INTEGRATION / "confirmation_api.py").read_text(encoding="utf-8")
    patches = (INTEGRATION / "confirmation_patches.py").read_text(encoding="utf-8")
    schema = (INTEGRATION / "task_record_schema.py").read_text(encoding="utf-8")

    for source in (init_source, api_source, patches, schema):
        ast.parse(source)
    assert "await async_initialize_confirmation_policy(hass)" in init_source
    assert "apply_confirmation_policy_patches()" in init_source
    assert "async_setup_confirmation_policy(hass)" in init_source
    assert 'confirmation/mode/update' in api_source
    assert 'confirmation/week_start/update' in api_source
    assert "confirmation_mode" in schema
    assert "not_documented" in schema
    assert "reopen_not_documented" in patches
