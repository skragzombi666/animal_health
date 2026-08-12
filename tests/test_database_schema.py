from __future__ import annotations

import importlib.util
import sqlite3
import sys
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"

EXPECTED_CORE_TABLES = {"animals", "events", "tasks", "task_occurrences"}
EXPECTED_RECORD_TABLES = {"task_record_configs", "task_occurrence_plans"}
EXPECTED_CORE_INDEXES = {
    "idx_animals_name",
    "idx_animals_status",
    "idx_animals_archived",
    "idx_tasks_animal_active",
    "idx_tasks_start_end",
    "idx_task_occurrences_due_status",
    "idx_events_animal_occurred",
    "idx_events_type",
    "idx_events_correction",
}
EXPECTED_RECORD_INDEXES = {
    "idx_task_record_configs_kind",
    "idx_task_occurrence_plans_resolved",
    "idx_events_task_occurrence_unique",
}
EXPECTED_RECORD_TRIGGERS = {
    "trg_task_occurrence_plan_insert",
    "trg_task_occurrence_plan_resolve",
    "trg_record_task_completion_guard",
}


def _load_module(name: str, path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _modules() -> tuple[types.ModuleType, types.ModuleType]:
    for name in [
        "custom_components.animal_health.database",
        "custom_components.animal_health.task_record_schema",
        "custom_components.animal_health.models",
        "custom_components.animal_health.const",
        "custom_components.animal_health",
        "custom_components",
        "homeassistant.core",
        "homeassistant",
    ]:
        sys.modules.pop(name, None)

    custom_components = types.ModuleType("custom_components")
    custom_components.__path__ = [str(ROOT / "custom_components")]
    sys.modules["custom_components"] = custom_components
    package = types.ModuleType("custom_components.animal_health")
    package.__path__ = [str(INTEGRATION)]
    sys.modules["custom_components.animal_health"] = package

    homeassistant = types.ModuleType("homeassistant")
    core = types.ModuleType("homeassistant.core")

    class HomeAssistant:
        pass

    core.HomeAssistant = HomeAssistant
    homeassistant.core = core
    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.core"] = core

    _load_module("custom_components.animal_health.const", INTEGRATION / "const.py")
    _load_module("custom_components.animal_health.models", INTEGRATION / "models.py")
    database = _load_module(
        "custom_components.animal_health.database", INTEGRATION / "database.py"
    )
    task_record_schema = _load_module(
        "custom_components.animal_health.task_record_schema",
        INTEGRATION / "task_record_schema.py",
    )
    return database, task_record_schema


def _database(database_module: types.ModuleType, path: Path) -> Any:
    class DummyHass:
        pass

    return database_module.AnimalHealthDatabase(DummyHass(), path)


def _objects(connection: sqlite3.Connection, kind: str) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = ? AND name NOT LIKE 'sqlite_%'",
            (kind,),
        ).fetchall()
    }


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {
        str(row[1])
        for row in connection.execute(f'PRAGMA table_info("{table}")').fetchall()
    }


def _assert_integrity(path: Path, expected_version: int = 3) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        assert connection.execute("PRAGMA user_version").fetchone()[0] == expected_version
        assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def _assert_current_core_schema(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        tables = _objects(connection, "table")
        indexes = _objects(connection, "index")
        assert EXPECTED_CORE_TABLES <= tables
        assert EXPECTED_CORE_INDEXES <= indexes
        assert {
            "id",
            "name",
            "species",
            "breed",
            "color",
            "sex",
            "birth_date",
            "arrival_date",
            "status",
            "status_changed_at",
            "is_archived",
            "archived_at",
            "created_at",
            "updated_at",
        } <= _columns(connection, "animals")
        assert {
            "id",
            "animal_id",
            "event_type",
            "occurred_at",
            "title",
            "notes",
            "value",
            "unit",
            "correction_of_event_id",
            "data_json",
            "task_id",
            "task_occurrence_id",
            "created_at",
        } <= _columns(connection, "events")


def _create_v1_legacy(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            CREATE TABLE animals (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                species TEXT NOT NULL,
                breed TEXT,
                sex TEXT,
                birth_date TEXT,
                arrival_date TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE tasks (
                id TEXT PRIMARY KEY,
                animal_id TEXT REFERENCES animals(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                description TEXT,
                recurrence_type TEXT NOT NULL,
                recurrence_interval INTEGER NOT NULL DEFAULT 1,
                start_date TEXT NOT NULL,
                end_date TEXT,
                due_time TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE task_occurrences (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                scheduled_for TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                completed_at TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(task_id, scheduled_for)
            );
            CREATE TABLE events (
                id TEXT PRIMARY KEY,
                animal_id TEXT NOT NULL REFERENCES animals(id) ON DELETE RESTRICT,
                event_type TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                title TEXT NOT NULL,
                notes TEXT,
                task_id TEXT REFERENCES tasks(id) ON DELETE SET NULL,
                task_occurrence_id TEXT REFERENCES task_occurrences(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX idx_animals_name ON animals(name COLLATE NOCASE);
            CREATE INDEX idx_tasks_animal_active ON tasks(animal_id, is_active);
            CREATE INDEX idx_tasks_start_end ON tasks(start_date, end_date);
            CREATE INDEX idx_task_occurrences_due_status ON task_occurrences(scheduled_for, status);
            CREATE INDEX idx_events_animal_occurred ON events(animal_id, occurred_at DESC);
            CREATE INDEX idx_events_type ON events(event_type);
            PRAGMA user_version = 1;
            """
        )
        connection.execute(
            """
            INSERT INTO animals (
                id, name, species, breed, sex, birth_date, arrival_date, status,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "AH-OLD",
                "Legacy Hen",
                "chicken",
                "Legacy Breed",
                "female",
                "2024-01-01",
                "2024-02-01",
                "inactive",
                "2024-01-01T10:00:00+00:00",
                "2026-01-01T10:00:00+00:00",
            ),
        )
        connection.execute(
            """
            INSERT INTO tasks (
                id, animal_id, title, description, recurrence_type, recurrence_interval,
                start_date, end_date, due_time, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, NULL, 'once', 1, ?, NULL, NULL, 1, ?, ?)
            """,
            (
                "TK-OLD",
                "AH-OLD",
                "Legacy task",
                "2026-01-02",
                "2026-01-01T10:00:00+00:00",
                "2026-01-01T10:00:00+00:00",
            ),
        )
        connection.execute(
            """
            INSERT INTO task_occurrences (
                id, task_id, scheduled_for, status, completed_at, notes, created_at, updated_at
            ) VALUES (?, ?, ?, 'pending', NULL, NULL, ?, ?)
            """,
            (
                "OC-OLD",
                "TK-OLD",
                "2026-01-02T00:00:00+00:00",
                "2026-01-01T10:00:00+00:00",
                "2026-01-01T10:00:00+00:00",
            ),
        )
        connection.execute(
            """
            INSERT INTO events (
                id, animal_id, event_type, occurred_at, title, notes,
                task_id, task_occurrence_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "EV-OLD",
                "AH-OLD",
                "legacy_unknown_type",
                "2026-01-01T09:00:00+00:00",
                "Legacy event",
                "must survive",
                "TK-OLD",
                "OC-OLD",
                "2026-01-01T10:00:00+00:00",
            ),
        )


def test_fresh_database_uses_real_initializers(tmp_path: Path) -> None:
    database_module, task_record_schema = _modules()
    path = tmp_path / "animal_health.db"
    database = _database(database_module, path)
    database._initialize_sync()
    _assert_current_core_schema(path)
    _assert_integrity(path)

    with sqlite3.connect(path) as connection:
        now = "2026-08-12T08:00:00+00:00"
        connection.execute(
            """
            INSERT INTO tasks (
                id, animal_id, title, description, recurrence_type, recurrence_interval,
                start_date, end_date, due_time, is_active, created_at, updated_at
            ) VALUES ('TK-FRESH', NULL, 'Test', NULL, 'once', 1, '2026-08-12', NULL, NULL, 1, ?, ?)
            """,
            (now, now),
        )
        connection.execute(
            """
            INSERT INTO task_occurrences (
                id, task_id, scheduled_for, status, completed_at, notes, created_at, updated_at
            ) VALUES ('OC-FRESH', 'TK-FRESH', '2026-08-12T00:00:00+00:00', 'pending', NULL, NULL, ?, ?)
            """,
            (now, now),
        )

    task_record_schema._initialize_sync(path)
    with sqlite3.connect(path) as connection:
        assert EXPECTED_RECORD_TABLES <= _objects(connection, "table")
        assert EXPECTED_RECORD_INDEXES <= _objects(connection, "index")
        assert EXPECTED_RECORD_TRIGGERS <= _objects(connection, "trigger")
        assert connection.execute(
            "SELECT task_kind FROM task_record_configs WHERE task_id='TK-FRESH'"
        ).fetchone() == ("reminder",)
        assert connection.execute(
            "SELECT occurrence_id FROM task_occurrence_plans WHERE occurrence_id='OC-FRESH'"
        ).fetchone() == ("OC-FRESH",)
    _assert_integrity(path)


def test_upgrade_from_v1_preserves_records_and_reaches_v3(tmp_path: Path) -> None:
    database_module, task_record_schema = _modules()
    path = tmp_path / "animal_health-v1.db"
    _create_v1_legacy(path)
    _database(database_module, path)._initialize_sync()

    _assert_current_core_schema(path)
    with sqlite3.connect(path) as connection:
        animal = connection.execute(
            "SELECT status, is_archived, archived_at, color FROM animals WHERE id='AH-OLD'"
        ).fetchone()
        assert animal == (
            "active",
            1,
            "2026-01-01T10:00:00+00:00",
            None,
        )
        event = connection.execute(
            """
            SELECT event_type, notes, data_json, task_id, task_occurrence_id
            FROM events WHERE id='EV-OLD'
            """
        ).fetchone()
        assert event == (
            "other",
            "must survive",
            "{}",
            "TK-OLD",
            "OC-OLD",
        )
    _assert_integrity(path)

    task_record_schema._initialize_sync(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT task_kind FROM task_record_configs WHERE task_id='TK-OLD'"
        ).fetchone() == ("reminder",)
        assert connection.execute(
            "SELECT occurrence_id FROM task_occurrence_plans WHERE occurrence_id='OC-OLD'"
        ).fetchone() == ("OC-OLD",)
    _assert_integrity(path)


def test_upgrade_from_v2_runs_only_v3_and_preserves_v2_state(tmp_path: Path) -> None:
    database_module, task_record_schema = _modules()
    path = tmp_path / "animal_health-v2.db"
    _create_v1_legacy(path)
    database = _database(database_module, path)
    with database._connect() as connection:
        database._migrate_to_v2(connection)
        connection.execute("PRAGMA user_version = 2")
    _assert_integrity(path, expected_version=2)

    database._initialize_sync()
    _assert_current_core_schema(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM animals WHERE id='AH-OLD'"
        ).fetchone() == (1,)
        assert connection.execute(
            "SELECT COUNT(*) FROM events WHERE id='EV-OLD'"
        ).fetchone() == (1,)
        assert connection.execute(
            "SELECT event_type FROM events WHERE id='EV-OLD'"
        ).fetchone() == ("other",)
    _assert_integrity(path)

    task_record_schema._initialize_sync(path)
    with sqlite3.connect(path) as connection:
        assert EXPECTED_RECORD_TRIGGERS <= _objects(connection, "trigger")
    _assert_integrity(path)
