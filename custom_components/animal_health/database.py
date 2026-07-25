from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from homeassistant.core import HomeAssistant

from .const import DATABASE_SCHEMA_VERSION

_T = TypeVar("_T")


class AnimalHealthDatabase:
    def __init__(self, hass: HomeAssistant, database_path: Path) -> None:
        self._hass = hass
        self._database_path = database_path

    async def initialize(self) -> None:
        await self._hass.async_add_executor_job(self._initialize_sync)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def _initialize_sync(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            current_version = connection.execute("PRAGMA user_version").fetchone()[0]
            if current_version > DATABASE_SCHEMA_VERSION:
                raise RuntimeError(
                    "Animal Health database schema is newer than this integration"
                )

            migrations: dict[int, Callable[[sqlite3.Connection], None]] = {
                1: self._migrate_to_v1,
            }
            for target_version in range(current_version + 1, DATABASE_SCHEMA_VERSION + 1):
                migrations[target_version](connection)
                connection.execute(f"PRAGMA user_version = {target_version}")

    @staticmethod
    def _migrate_to_v1(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS animals (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                species TEXT NOT NULL,
                breed TEXT,
                sex TEXT,
                birth_date TEXT,
                arrival_date TEXT,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive', 'deceased')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                animal_id TEXT REFERENCES animals(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                description TEXT,
                recurrence_type TEXT NOT NULL
                    CHECK (recurrence_type IN ('once', 'daily', 'weekly', 'monthly')),
                recurrence_interval INTEGER NOT NULL DEFAULT 1
                    CHECK (recurrence_interval >= 1),
                start_date TEXT NOT NULL,
                end_date TEXT,
                due_time TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CHECK (end_date IS NULL OR end_date >= start_date)
            );

            CREATE TABLE IF NOT EXISTS task_occurrences (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                scheduled_for TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'completed', 'skipped', 'cancelled')),
                completed_at TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (task_id, scheduled_for)
            );

            CREATE TABLE IF NOT EXISTS events (
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

            CREATE INDEX IF NOT EXISTS idx_animals_name
                ON animals(name COLLATE NOCASE);
            CREATE INDEX IF NOT EXISTS idx_animals_status
                ON animals(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_animal_active
                ON tasks(animal_id, is_active);
            CREATE INDEX IF NOT EXISTS idx_tasks_start_end
                ON tasks(start_date, end_date);
            CREATE INDEX IF NOT EXISTS idx_task_occurrences_due_status
                ON task_occurrences(scheduled_for, status);
            CREATE INDEX IF NOT EXISTS idx_events_animal_occurred
                ON events(animal_id, occurred_at DESC);
            CREATE INDEX IF NOT EXISTS idx_events_type
                ON events(event_type);
            """
        )

    async def get_animals(self) -> list[dict[str, Any]]:
        return await self._hass.async_add_executor_job(self._get_animals_sync)

    def _get_animals_sync(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, species, breed, sex, birth_date, arrival_date,
                       status, created_at, updated_at
                FROM animals
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()
        return [dict(row) for row in rows]
