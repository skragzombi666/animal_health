from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from custom_components.animal_health.v0934_features import (
    _enrich_task_completion_stats_sync,
    _repair_treatment_event_sync,
)


def _database(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE events (
            id TEXT PRIMARY KEY,
            animal_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            title TEXT NOT NULL,
            notes TEXT,
            value REAL,
            unit TEXT,
            correction_of_event_id TEXT,
            data_json TEXT NOT NULL,
            task_id TEXT,
            task_occurrence_id TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL
        );
        CREATE TABLE task_occurrences (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            status TEXT NOT NULL,
            scheduled_for TEXT NOT NULL,
            completed_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE task_record_configs (
            task_id TEXT PRIMARY KEY,
            task_kind TEXT NOT NULL,
            template_json TEXT NOT NULL
        );
        CREATE TABLE task_occurrence_plans (
            occurrence_id TEXT PRIMARY KEY,
            planned_json TEXT NOT NULL
        );
        CREATE TABLE v0911_treatment_plans (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            components_json TEXT NOT NULL,
            description TEXT
        );
        """
    )
    return connection


def test_treatment_task_repair_freezes_plan_and_links_components(tmp_path: Path) -> None:
    path = tmp_path / "animal_health.db"
    components = [
        {
            "type": "action",
            "name": "Mesof Vliesstoffkompressen",
            "dose": 2,
            "unit": "Stück",
            "instructions": "Unter dem Fuss platzieren",
        }
    ]
    with _database(path) as connection:
        connection.execute(
            "INSERT INTO tasks(id,title) VALUES(?,?)",
            ("task-1", "Fussverband täglich"),
        )
        connection.execute(
            """
            INSERT INTO task_occurrences(
                id,task_id,status,scheduled_for,completed_at,updated_at
            ) VALUES(?,?,?,?,?,?)
            """,
            (
                "occurrence-1",
                "task-1",
                "completed",
                "2026-09-01T08:30:00+00:00",
                "2026-09-01T08:31:00+00:00",
                "2026-09-01T08:31:00+00:00",
            ),
        )
        connection.execute(
            "INSERT INTO task_record_configs(task_id,task_kind,template_json) VALUES(?,?,?)",
            (
                "task-1",
                "treatment",
                json.dumps(
                    {
                        "treatment_plan_id": "plan-1",
                        "treatment_plan_name": "Fussverband Beidseitig",
                    }
                ),
            ),
        )
        connection.execute(
            "INSERT INTO task_occurrence_plans(occurrence_id,planned_json) VALUES(?,?)",
            (
                "occurrence-1",
                json.dumps(
                    {
                        "treatment_plan_id": "plan-1",
                        "treatment_plan_name": "Fussverband Beidseitig",
                    }
                ),
            ),
        )
        connection.execute(
            """
            INSERT INTO v0911_treatment_plans(
                id,name,components_json,description
            ) VALUES(?,?,?,?)
            """,
            (
                "plan-1",
                "Fussverband Beidseitig",
                json.dumps(components),
                "Verband vollständig erneuern",
            ),
        )
        connection.execute(
            """
            INSERT INTO events(
                id,animal_id,event_type,occurred_at,title,notes,value,unit,
                correction_of_event_id,data_json,task_id,task_occurrence_id,
                created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "event-parent",
                "animal-1",
                "treatment",
                "2026-09-01T08:31:00+00:00",
                "Fussverband Beidseitig",
                None,
                None,
                None,
                None,
                "{}",
                "task-1",
                "occurrence-1",
                "2026-09-01T08:31:00+00:00",
            ),
        )
        connection.execute(
            """
            INSERT INTO events(
                id,animal_id,event_type,occurred_at,title,notes,value,unit,
                correction_of_event_id,data_json,task_id,task_occurrence_id,
                created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "event-component",
                "animal-1",
                "care",
                "2026-09-01T08:31:00+00:00",
                "Mesof Vliesstoffkompressen",
                None,
                2,
                "Stück",
                None,
                "{}",
                None,
                None,
                "2026-09-01T08:31:00+00:00",
            ),
        )

    repaired = _repair_treatment_event_sync(path, "event-parent")

    assert repaired is not None
    parent = repaired["data"]
    assert parent["source"] == "task"
    assert parent["source_task_id"] == "task-1"
    assert parent["source_task_occurrence_id"] == "occurrence-1"
    assert parent["treatment_execution_role"] == "parent"
    assert parent["treatment_plan_id"] == "plan-1"
    assert parent["treatment_plan_components"] == components
    assert parent["treatment_plan_description"] == "Verband vollständig erneuern"
    assert parent["component_events"] == ["event-component"]

    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT data_json,task_id FROM events WHERE id='event-component'"
        ).fetchone()
    assert row is not None
    child = json.loads(row[0])
    assert row[1] == "task-1"
    assert child["source"] == "task"
    assert child["source_task_occurrence_id"] == "occurrence-1"
    assert child["treatment_parent_event_id"] == "event-parent"
    assert child["treatment_execution_role"] == "component"
    assert child["treatment_execution_id"] == parent["treatment_execution_id"]


def test_task_completion_stats_are_not_limited_to_dashboard_window(tmp_path: Path) -> None:
    path = tmp_path / "animal_health.db"
    with _database(path) as connection:
        connection.executemany(
            "INSERT INTO tasks(id,title) VALUES(?,?)",
            [("task-1", "Einmalig"), ("task-2", "Serie")],
        )
        connection.executemany(
            """
            INSERT INTO task_occurrences(
                id,task_id,status,scheduled_for,completed_at,updated_at
            ) VALUES(?,?,?,?,?,?)
            """,
            [
                (
                    "occurrence-1",
                    "task-1",
                    "completed",
                    "2026-08-01T08:00:00+00:00",
                    "2026-08-01T08:05:00+00:00",
                    "2026-08-01T08:05:00+00:00",
                ),
                (
                    "occurrence-2",
                    "task-2",
                    "completed",
                    "2026-08-31T08:00:00+00:00",
                    "2026-08-31T08:05:00+00:00",
                    "2026-08-31T08:05:00+00:00",
                ),
                (
                    "occurrence-3",
                    "task-2",
                    "pending",
                    "2026-09-02T08:00:00+00:00",
                    None,
                    "2026-09-01T08:00:00+00:00",
                ),
            ],
        )

    enriched = _enrich_task_completion_stats_sync(
        path,
        [{"id": "task-1"}, {"id": "task-2"}, {"id": "task-3"}],
    )
    by_id = {item["id"]: item for item in enriched}

    assert by_id["task-1"]["completed_count"] == 1
    assert by_id["task-1"]["pending_count"] == 0
    assert by_id["task-1"]["last_completed_at"] == "2026-08-01T08:05:00+00:00"
    assert by_id["task-2"]["completed_count"] == 1
    assert by_id["task-2"]["pending_count"] == 1
    assert by_id["task-3"]["completed_count"] == 0
    assert by_id["task-3"]["pending_count"] == 0
    assert by_id["task-3"]["last_completed_at"] is None
