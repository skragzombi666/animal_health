from __future__ import annotations

import secrets
import sqlite3
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    ANIMAL_SEXES,
    ANIMAL_STATUSES,
    ANIMAL_STATUS_ACTIVE,
    DATABASE_SCHEMA_VERSION,
)
from .models import Animal

ANIMAL_FIELDS = {
    "name",
    "species",
    "breed",
    "sex",
    "birth_date",
    "arrival_date",
}

ANIMAL_ID_ALPHABET = "23456789ABCDEFGHJKMNPQRSTVWXYZ"
ANIMAL_ID_LENGTH = 7


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
                sex TEXT CHECK (sex IS NULL OR sex IN ('male', 'female', 'other')),
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

    @staticmethod
    def _generate_animal_id(existing_ids: set[str] | None = None) -> str:
        existing_ids = existing_ids or set()
        while True:
            suffix = "".join(
                secrets.choice(ANIMAL_ID_ALPHABET) for _ in range(ANIMAL_ID_LENGTH)
            )
            animal_id = f"AH-{suffix}"
            if animal_id not in existing_ids:
                return animal_id

    async def get_animals(self) -> list[Animal]:
        return await self._hass.async_add_executor_job(self._get_animals_sync)

    def _get_animals_sync(self) -> list[Animal]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, species, breed, sex, birth_date, arrival_date,
                       status, created_at, updated_at
                FROM animals
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()
        return [Animal.from_mapping(row) for row in rows]

    async def get_animal(self, animal_id: str) -> Animal | None:
        return await self._hass.async_add_executor_job(
            self._get_animal_sync, animal_id
        )

    def _get_animal_sync(self, animal_id: str) -> Animal | None:
        with self._connect() as connection:
            return self._get_animal_from_connection(connection, animal_id)

    async def create_animal(
        self,
        *,
        name: str,
        species: str,
        breed: str | None = None,
        sex: str | None = None,
        birth_date: date | None = None,
        arrival_date: date | None = None,
    ) -> Animal:
        return await self._hass.async_add_executor_job(
            self._create_animal_sync,
            name,
            species,
            breed,
            sex,
            birth_date,
            arrival_date,
        )

    def _create_animal_sync(
        self,
        name: str,
        species: str,
        breed: str | None,
        sex: str | None,
        birth_date: date | None,
        arrival_date: date | None,
    ) -> Animal:
        if sex is not None and sex not in ANIMAL_SEXES:
            raise ValueError(f"Unsupported animal sex: {sex}")

        now = datetime.now(UTC).isoformat(timespec="seconds")
        with self._connect() as connection:
            existing_ids = {
                row[0] for row in connection.execute("SELECT id FROM animals").fetchall()
            }
            animal_id = self._generate_animal_id(existing_ids)
            connection.execute(
                """
                INSERT INTO animals (
                    id, name, species, breed, sex, birth_date, arrival_date,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    animal_id,
                    name,
                    species,
                    breed,
                    sex,
                    birth_date.isoformat() if birth_date else None,
                    arrival_date.isoformat() if arrival_date else None,
                    ANIMAL_STATUS_ACTIVE,
                    now,
                    now,
                ),
            )
            animal = self._get_animal_from_connection(connection, animal_id)
        if animal is None:
            raise RuntimeError("Created animal could not be loaded")
        return animal

    async def update_animal(
        self,
        animal_id: str,
        changes: dict[str, Any],
    ) -> Animal:
        return await self._hass.async_add_executor_job(
            self._update_animal_sync, animal_id, changes
        )

    def _update_animal_sync(
        self,
        animal_id: str,
        changes: dict[str, Any],
    ) -> Animal:
        invalid_fields = set(changes) - ANIMAL_FIELDS
        if invalid_fields:
            raise ValueError(f"Unsupported animal fields: {sorted(invalid_fields)}")

        sex = changes.get("sex")
        if sex is not None and sex not in ANIMAL_SEXES:
            raise ValueError(f"Unsupported animal sex: {sex}")

        if not changes:
            animal = self._get_animal_sync(animal_id)
            if animal is None:
                raise KeyError(animal_id)
            return animal

        serialized_changes = {
            field: value.isoformat() if isinstance(value, date) else value
            for field, value in changes.items()
        }
        serialized_changes["updated_at"] = datetime.now(UTC).isoformat(
            timespec="seconds"
        )
        assignments = ", ".join(f"{field} = ?" for field in serialized_changes)
        values = [*serialized_changes.values(), animal_id]

        with self._connect() as connection:
            cursor = connection.execute(
                f"UPDATE animals SET {assignments} WHERE id = ?",
                values,
            )
            if cursor.rowcount == 0:
                raise KeyError(animal_id)
            animal = self._get_animal_from_connection(connection, animal_id)
        if animal is None:
            raise KeyError(animal_id)
        return animal

    async def set_animal_status(self, animal_id: str, status: str) -> Animal:
        return await self._hass.async_add_executor_job(
            self._set_animal_status_sync, animal_id, status
        )

    def _set_animal_status_sync(self, animal_id: str, status: str) -> Animal:
        if status not in ANIMAL_STATUSES:
            raise ValueError(f"Unsupported animal status: {status}")

        now = datetime.now(UTC).isoformat(timespec="seconds")
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE animals SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, animal_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(animal_id)
            animal = self._get_animal_from_connection(connection, animal_id)
        if animal is None:
            raise KeyError(animal_id)
        return animal

    @staticmethod
    def _get_animal_from_connection(
        connection: sqlite3.Connection,
        animal_id: str,
    ) -> Animal | None:
        row = connection.execute(
            """
            SELECT id, name, species, breed, sex, birth_date, arrival_date,
                   status, created_at, updated_at
            FROM animals
            WHERE id = ?
            """,
            (animal_id,),
        ).fetchone()
        return Animal.from_mapping(row) if row is not None else None
