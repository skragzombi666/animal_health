from __future__ import annotations

import secrets
import sqlite3
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant

from .const import (
    ANIMAL_SEX_FEMALE,
    ANIMAL_SEX_MALE,
    ANIMAL_SEX_OTHER,
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

ANIMAL_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTVWXYZ"
ANIMAL_CODE_LENGTH = 7


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
                2: self._migrate_to_v2,
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

    @classmethod
    def _migrate_to_v2(cls, connection: sqlite3.Connection) -> None:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(animals)").fetchall()
        }
        if "animal_code" not in columns:
            connection.execute("ALTER TABLE animals ADD COLUMN animal_code TEXT")

        existing_codes = {
            row[0]
            for row in connection.execute(
                "SELECT animal_code FROM animals WHERE animal_code IS NOT NULL"
            ).fetchall()
        }
        rows_without_code = connection.execute(
            "SELECT id FROM animals WHERE animal_code IS NULL OR animal_code = ''"
        ).fetchall()
        for row in rows_without_code:
            animal_code = cls._generate_animal_code(existing_codes)
            existing_codes.add(animal_code)
            connection.execute(
                "UPDATE animals SET animal_code = ? WHERE id = ?",
                (animal_code, row[0]),
            )

        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_animals_code ON animals(animal_code)"
        )
        connection.execute(
            """
            UPDATE animals
            SET sex = CASE lower(trim(sex))
                WHEN 'male' THEN ?
                WHEN 'männlich' THEN ?
                WHEN 'mannlich' THEN ?
                WHEN 'female' THEN ?
                WHEN 'weiblich' THEN ?
                WHEN 'other' THEN ?
                WHEN 'anderes' THEN ?
                WHEN 'divers' THEN ?
                ELSE ?
            END
            WHERE sex IS NOT NULL
            """,
            (
                ANIMAL_SEX_MALE,
                ANIMAL_SEX_MALE,
                ANIMAL_SEX_MALE,
                ANIMAL_SEX_FEMALE,
                ANIMAL_SEX_FEMALE,
                ANIMAL_SEX_OTHER,
                ANIMAL_SEX_OTHER,
                ANIMAL_SEX_OTHER,
                ANIMAL_SEX_OTHER,
            ),
        )

    @staticmethod
    def _generate_animal_code(existing_codes: set[str] | None = None) -> str:
        existing_codes = existing_codes or set()
        while True:
            suffix = "".join(
                secrets.choice(ANIMAL_CODE_ALPHABET)
                for _ in range(ANIMAL_CODE_LENGTH)
            )
            animal_code = f"AH-{suffix}"
            if animal_code not in existing_codes:
                return animal_code

    async def get_animals(self) -> list[Animal]:
        return await self._hass.async_add_executor_job(self._get_animals_sync)

    def _get_animals_sync(self) -> list[Animal]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, animal_code, name, species, breed, sex, birth_date,
                       arrival_date, status, created_at, updated_at
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
        animal_id = uuid4().hex
        now = datetime.now(UTC).isoformat(timespec="seconds")
        with self._connect() as connection:
            existing_codes = {
                row[0]
                for row in connection.execute("SELECT animal_code FROM animals").fetchall()
                if row[0]
            }
            animal_code = self._generate_animal_code(existing_codes)
            connection.execute(
                """
                INSERT INTO animals (
                    id, animal_code, name, species, breed, sex, birth_date,
                    arrival_date, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    animal_id,
                    animal_code,
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
            SELECT id, animal_code, name, species, breed, sex, birth_date,
                   arrival_date, status, created_at, updated_at
            FROM animals
            WHERE id = ?
            """,
            (animal_id,),
        ).fetchone()
        return Animal.from_mapping(row) if row is not None else None
