from __future__ import annotations

import sqlite3
from pathlib import Path


EXPECTED_TABLES = {"animals", "events", "tasks", "task_occurrences"}


def test_expected_schema_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "animal_health.db"
    connection = sqlite3.connect(database_path)
    connection.executescript(
        """
        CREATE TABLE animals (id TEXT PRIMARY KEY);
        CREATE TABLE events (id TEXT PRIMARY KEY);
        CREATE TABLE tasks (id TEXT PRIMARY KEY);
        CREATE TABLE task_occurrences (id TEXT PRIMARY KEY);
        """
    )
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert EXPECTED_TABLES <= tables
