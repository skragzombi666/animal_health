from __future__ import annotations

import ast
import json
import sqlite3
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any


MODULE = Path("custom_components/animal_health/v084_features.py")


def _namespace() -> dict[str, Any]:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    wanted_assignments = {"_HISTORY_FIELDS", "_EXPECTED_TABLES", "_EXPECTED_INDEXES"}
    wanted_functions = {
        "_connect",
        "_walk_history_values",
        "_history_sync",
        "_diagnostics_sync",
        "_reset_activity_sync",
    }
    body: list[ast.stmt] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = {target.id for target in node.targets if isinstance(target, ast.Name)}
            if names & wanted_assignments:
                body.append(node)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in wanted_assignments:
                body.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in wanted_functions:
            body.append(node)
    module = ast.Module(body=body, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace: dict[str, Any] = {
        "json": json,
        "sqlite3": sqlite3,
        "defaultdict": defaultdict,
        "Path": Path,
        "Any": Any,
    }
    exec(compile(module, str(MODULE), "exec"), namespace)
    return namespace


def _history_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE animals (id TEXT PRIMARY KEY, species TEXT);
            CREATE TABLE events (
                id TEXT PRIMARY KEY,
                animal_id TEXT,
                data_json TEXT,
                occurred_at TEXT
            );
            CREATE TABLE tasks (
                id TEXT PRIMARY KEY,
                animal_id TEXT,
                updated_at TEXT
            );
            CREATE TABLE task_record_configs (
                task_id TEXT PRIMARY KEY,
                template_json TEXT
            );
            CREATE TABLE animal_groups (
                id TEXT PRIMARY KEY,
                species TEXT
            );
            CREATE TABLE group_events (
                id TEXT PRIMARY KEY,
                group_id TEXT,
                data_json TEXT,
                occurred_at TEXT
            );
            CREATE TABLE task_group_targets (
                task_id TEXT PRIMARY KEY,
                group_id TEXT
            );
            CREATE TABLE group_task_configs (
                task_id TEXT PRIMARY KEY,
                template_json TEXT
            );
            INSERT INTO animals VALUES ('A1', 'Chicken');
            INSERT INTO events VALUES (
                'E1', 'A1',
                '{"medication_name":"ExampleMed","provider":"Praxis A"}',
                '2026-08-10T10:00:00+00:00'
            );
            INSERT INTO events VALUES (
                'E2', 'A1',
                '{"task_execution":{"actual":{"medication_name":"ExampleMed"}}}',
                '2026-08-11T10:00:00+00:00'
            );
            INSERT INTO tasks VALUES ('T1', 'A1', '2026-08-12T08:00:00+00:00');
            INSERT INTO task_record_configs VALUES (
                'T1',
                '{"vaccine_name":"ExampleVax","visit_reason":"Kontrolle"}'
            );
            INSERT INTO animal_groups VALUES ('G1', 'Chicken');
            INSERT INTO group_events VALUES (
                'GE1', 'G1',
                '{"care_action":"Fuss kontrollieren"}',
                '2026-08-09T10:00:00+00:00'
            );
            """
        )


def test_history(namespace: dict[str, Any], root: Path) -> None:
    database_path = root / "history.db"
    _history_database(database_path)
    result = namespace["_history_sync"](database_path)
    medication = result["medication_name"][0]
    assert medication["value"] == "ExampleMed"
    assert medication["species_id"] == "Chicken"
    assert medication["count"] == 2
    assert result["provider"][0]["value"] == "Praxis A"
    assert result["vaccine_name"][0]["value"] == "ExampleVax"
    assert result["visit_reason"][0]["value"] == "Kontrolle"
    assert result["care_action"][0]["value"] == "Fuss kontrollieren"


def test_diagnostics(namespace: dict[str, Any], root: Path) -> None:
    database_path = root / "diagnostics.db"
    attachment_root = root / "attachments"
    attachment_root.mkdir()
    expected_tables = set(namespace["_EXPECTED_TABLES"])
    expected_indexes = set(namespace["_EXPECTED_INDEXES"])
    with sqlite3.connect(database_path) as connection:
        for table in sorted(expected_tables):
            if table == "attachments":
                connection.execute(
                    "CREATE TABLE attachments (id TEXT PRIMARY KEY, filename TEXT, storage_name TEXT, created_at TEXT)"
                )
            else:
                connection.execute(f'CREATE TABLE "{table}" (id TEXT PRIMARY KEY)')
        for index in sorted(expected_indexes):
            connection.execute(f'CREATE INDEX "{index}" ON animals(id)')
        connection.execute("PRAGMA user_version = 3")
        connection.execute(
            "INSERT INTO attachments VALUES ('AT1', 'present.pdf', 'present.bin', '2026-08-12T08:00:00+00:00')"
        )
        connection.execute(
            "INSERT INTO attachments VALUES ('AT2', 'missing.pdf', 'missing.bin', '2026-08-12T08:01:00+00:00')"
        )
    (attachment_root / "present.bin").write_bytes(b"ok")
    (attachment_root / "orphan.bin").write_bytes(b"orphan")
    report = namespace["_diagnostics_sync"](database_path, attachment_root)
    assert report["errors"] == []
    assert report["integrity_check"] == ["ok"]
    assert report["foreign_key_violations"] == []
    assert report["missing_tables"] == []
    assert report["missing_indexes"] == []
    assert report["missing_attachment_files"][0]["attachment_id"] == "AT2"
    assert report["orphaned_attachment_files"] == ["orphan.bin"]
    assert report["ok"] is False


def _activity_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            CREATE TABLE animals (id TEXT PRIMARY KEY, name TEXT);
            CREATE TABLE animal_groups (id TEXT PRIMARY KEY, name TEXT);
            CREATE TABLE animal_group_memberships (
                animal_id TEXT PRIMARY KEY REFERENCES animals(id) ON DELETE CASCADE,
                group_id TEXT NOT NULL REFERENCES animal_groups(id) ON DELETE CASCADE
            );
            CREATE TABLE tasks (
                id TEXT PRIMARY KEY,
                animal_id TEXT REFERENCES animals(id) ON DELETE CASCADE
            );
            CREATE TABLE task_occurrences (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE
            );
            CREATE TABLE task_record_configs (
                task_id TEXT PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE
            );
            CREATE TABLE task_occurrence_plans (
                occurrence_id TEXT PRIMARY KEY REFERENCES task_occurrences(id) ON DELETE CASCADE
            );
            CREATE TABLE task_group_targets (
                task_id TEXT PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
                group_id TEXT REFERENCES animal_groups(id) ON DELETE CASCADE
            );
            CREATE TABLE group_task_configs (
                task_id TEXT PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE
            );
            CREATE TABLE events (
                id TEXT PRIMARY KEY,
                animal_id TEXT REFERENCES animals(id) ON DELETE RESTRICT,
                correction_of_event_id TEXT REFERENCES events(id) ON DELETE RESTRICT,
                task_id TEXT REFERENCES tasks(id) ON DELETE SET NULL,
                task_occurrence_id TEXT REFERENCES task_occurrences(id) ON DELETE SET NULL
            );
            CREATE TABLE group_events (
                id TEXT PRIMARY KEY,
                group_id TEXT REFERENCES animal_groups(id) ON DELETE CASCADE,
                correction_of_event_id TEXT REFERENCES group_events(id) ON DELETE RESTRICT,
                task_id TEXT REFERENCES tasks(id) ON DELETE SET NULL,
                task_occurrence_id TEXT REFERENCES task_occurrences(id) ON DELETE SET NULL
            );
            CREATE TABLE attachments (
                id TEXT PRIMARY KEY,
                animal_id TEXT REFERENCES animals(id) ON DELETE CASCADE,
                event_id TEXT REFERENCES events(id) ON DELETE SET NULL,
                filename TEXT,
                storage_name TEXT,
                created_at TEXT
            );
            CREATE TABLE animal_profiles (
                animal_id TEXT PRIMARY KEY REFERENCES animals(id) ON DELETE CASCADE,
                image_attachment_id TEXT REFERENCES attachments(id) ON DELETE SET NULL
            );
            INSERT INTO animals VALUES ('A1', 'Tina');
            INSERT INTO animal_groups VALUES ('G1', 'Hühner');
            INSERT INTO animal_group_memberships VALUES ('A1', 'G1');
            INSERT INTO tasks VALUES ('T1', 'A1');
            INSERT INTO task_occurrences VALUES ('O1', 'T1');
            INSERT INTO task_record_configs VALUES ('T1');
            INSERT INTO task_occurrence_plans VALUES ('O1');
            INSERT INTO task_group_targets VALUES ('T1', 'G1');
            INSERT INTO group_task_configs VALUES ('T1');
            INSERT INTO events VALUES ('E1', 'A1', NULL, 'T1', 'O1');
            INSERT INTO events VALUES ('E2', 'A1', 'E1', 'T1', 'O1');
            INSERT INTO group_events VALUES ('GE1', 'G1', NULL, 'T1', 'O1');
            INSERT INTO group_events VALUES ('GE2', 'G1', 'GE1', 'T1', 'O1');
            INSERT INTO attachments VALUES ('AP', 'A1', NULL, 'profile.png', 'profile.bin', '2026-08-12');
            INSERT INTO attachments VALUES ('AE', 'A1', 'E2', 'event.pdf', 'event.bin', '2026-08-12');
            INSERT INTO animal_profiles VALUES ('A1', 'AP');
            """
        )


def test_activity_reset(namespace: dict[str, Any], root: Path) -> None:
    database_path = root / "activity.db"
    attachment_root = root / "activity_attachments"
    attachment_root.mkdir()
    _activity_database(database_path)
    (attachment_root / "profile.bin").write_bytes(b"profile")
    (attachment_root / "event.bin").write_bytes(b"event")

    result = namespace["_reset_activity_sync"](database_path, attachment_root)
    assert result["counts"] == {
        "events": 2,
        "group_events": 2,
        "tasks": 1,
        "attachments": 1,
    }
    assert result["file_errors"] == []

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        assert connection.execute("SELECT COUNT(*) FROM animals").fetchone() == (1,)
        assert connection.execute("SELECT COUNT(*) FROM animal_groups").fetchone() == (1,)
        assert connection.execute(
            "SELECT animal_id, group_id FROM animal_group_memberships"
        ).fetchone() == ("A1", "G1")
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone() == (0,)
        assert connection.execute("SELECT COUNT(*) FROM group_events").fetchone() == (0,)
        assert connection.execute("SELECT COUNT(*) FROM tasks").fetchone() == (0,)
        assert connection.execute("SELECT COUNT(*) FROM task_occurrences").fetchone() == (0,)
        assert connection.execute(
            "SELECT id FROM attachments ORDER BY id"
        ).fetchall() == [("AP",)]
        assert connection.execute(
            "SELECT animal_id, image_attachment_id FROM animal_profiles"
        ).fetchone() == ("A1", "AP")
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    assert (attachment_root / "profile.bin").is_file()
    assert not (attachment_root / "event.bin").exists()


def test_current_websocket_admin_pattern() -> None:
    source = MODULE.read_text(encoding="utf-8")
    assert "connection.require_admin()" not in source
    assert source.count("@websocket_api.require_admin") >= 2


def main() -> None:
    namespace = _namespace()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        test_history(namespace, root)
        test_diagnostics(namespace, root)
        test_activity_reset(namespace, root)
    test_current_websocket_admin_pattern()
    print("0.8.5 history, diagnostics and activity-reset smoke test passed")


if __name__ == "__main__":
    main()
