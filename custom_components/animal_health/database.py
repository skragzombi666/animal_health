from __future__ import annotations

import json
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
    EVENT_TYPES,
    EVENT_TYPE_STATUS_CHANGE,
)
from .models import Animal, HealthEvent

ANIMAL_FIELDS = {
    "name",
    "species",
    "breed",
    "color",
    "sex",
    "birth_date",
    "arrival_date",
}

RECORD_ID_ALPHABET = "23456789ABCDEFGHJKMNPQRSTVWXYZ"
RECORD_ID_LENGTH = 7


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
                3: self._migrate_to_v3,
            }
            for target_version in range(current_version + 1, DATABASE_SCHEMA_VERSION + 1):
                migrations[target_version](connection)
                connection.execute(f"PRAGMA user_version = {target_version}")

    @staticmethod
    def _create_animals_table(
        connection: sqlite3.Connection,
        table_name: str = "animals",
    ) -> None:
        connection.execute(
            f"""
            CREATE TABLE {table_name} (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                species TEXT NOT NULL,
                breed TEXT,
                color TEXT,
                sex TEXT CHECK (sex IS NULL OR sex IN ('male', 'female', 'other')),
                birth_date TEXT,
                arrival_date TEXT,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK (
                        status IN (
                            'active',
                            'missing',
                            'sold',
                            'rehomed',
                            'deceased',
                            'other_departure'
                        )
                    ),
                status_changed_at TEXT NOT NULL,
                is_archived INTEGER NOT NULL DEFAULT 0
                    CHECK (is_archived IN (0, 1)),
                archived_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CHECK (
                    (is_archived = 0 AND archived_at IS NULL)
                    OR (is_archived = 1 AND archived_at IS NOT NULL)
                )
            )
            """
        )

    @staticmethod
    def _create_events_table(
        connection: sqlite3.Connection,
        table_name: str = "events",
    ) -> None:
        connection.execute(
            f"""
            CREATE TABLE {table_name} (
                id TEXT PRIMARY KEY,
                animal_id TEXT NOT NULL REFERENCES animals(id) ON DELETE RESTRICT,
                event_type TEXT NOT NULL
                    CHECK (
                        event_type IN (
                            'observation',
                            'symptom',
                            'weight',
                            'diagnosis',
                            'treatment',
                            'medication',
                            'vaccination',
                            'veterinary_visit',
                            'care',
                            'status_change',
                            'other'
                        )
                    ),
                occurred_at TEXT NOT NULL,
                title TEXT NOT NULL,
                notes TEXT,
                value REAL,
                unit TEXT,
                correction_of_event_id TEXT REFERENCES {table_name}(id) ON DELETE RESTRICT,
                data_json TEXT NOT NULL DEFAULT '{{}}',
                task_id TEXT REFERENCES tasks(id) ON DELETE SET NULL,
                task_occurrence_id TEXT REFERENCES task_occurrences(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL,
                CHECK (
                    (value IS NULL AND unit IS NULL)
                    OR (value IS NOT NULL AND unit IS NOT NULL)
                ),
                CHECK (correction_of_event_id IS NULL OR correction_of_event_id <> id)
            )
            """
        )

    @classmethod
    def _migrate_to_v1(cls, connection: sqlite3.Connection) -> None:
        cls._create_animals_table(connection)
        connection.executescript(
            """
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
            """
        )
        cls._create_events_table(connection)
        connection.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_animals_name
                ON animals(name COLLATE NOCASE);
            CREATE INDEX IF NOT EXISTS idx_animals_status
                ON animals(status);
            CREATE INDEX IF NOT EXISTS idx_animals_archived
                ON animals(is_archived);
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
            CREATE INDEX IF NOT EXISTS idx_events_correction
                ON events(correction_of_event_id);
            """
        )

    @classmethod
    def _migrate_to_v2(cls, connection: sqlite3.Connection) -> None:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(animals)").fetchall()
        }
        if {"status_changed_at", "is_archived", "archived_at"} <= columns:
            return

        connection.commit()
        connection.execute("PRAGMA foreign_keys = OFF")
        try:
            connection.execute("BEGIN IMMEDIATE")
            cls._create_animals_table(connection, "animals_new")
            connection.execute(
                """
                INSERT INTO animals_new (
                    id,
                    name,
                    species,
                    breed,
                    color,
                    sex,
                    birth_date,
                    arrival_date,
                    status,
                    status_changed_at,
                    is_archived,
                    archived_at,
                    created_at,
                    updated_at
                )
                SELECT
                    id,
                    name,
                    species,
                    breed,
                    NULL,
                    sex,
                    birth_date,
                    arrival_date,
                    CASE
                        WHEN status = 'deceased' THEN 'deceased'
                        ELSE 'active'
                    END,
                    updated_at,
                    CASE WHEN status = 'inactive' THEN 1 ELSE 0 END,
                    CASE WHEN status = 'inactive' THEN updated_at ELSE NULL END,
                    created_at,
                    updated_at
                FROM animals
                """
            )
            connection.execute("DROP TABLE animals")
            connection.execute("ALTER TABLE animals_new RENAME TO animals")
            connection.execute(
                "CREATE INDEX idx_animals_name ON animals(name COLLATE NOCASE)"
            )
            connection.execute("CREATE INDEX idx_animals_status ON animals(status)")
            connection.execute(
                "CREATE INDEX idx_animals_archived ON animals(is_archived)"
            )

            violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise RuntimeError(
                    f"Animal Health migration created foreign-key violations: {violations}"
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.execute("PRAGMA foreign_keys = ON")

    @classmethod
    def _migrate_to_v3(cls, connection: sqlite3.Connection) -> None:
        animal_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(animals)").fetchall()
        }
        if "color" not in animal_columns:
            connection.execute("ALTER TABLE animals ADD COLUMN color TEXT")

        event_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(events)").fetchall()
        }
        required = {
            "value",
            "unit",
            "correction_of_event_id",
            "data_json",
        }
        if required <= event_columns:
            return

        connection.commit()
        connection.execute("PRAGMA foreign_keys = OFF")
        try:
            connection.execute("BEGIN IMMEDIATE")
            cls._create_events_table(connection, "events_new")
            connection.execute(
                """
                INSERT INTO events_new (
                    id,
                    animal_id,
                    event_type,
                    occurred_at,
                    title,
                    notes,
                    value,
                    unit,
                    correction_of_event_id,
                    data_json,
                    task_id,
                    task_occurrence_id,
                    created_at
                )
                SELECT
                    id,
                    animal_id,
                    CASE
                        WHEN event_type IN (
                            'observation',
                            'symptom',
                            'weight',
                            'diagnosis',
                            'treatment',
                            'medication',
                            'vaccination',
                            'veterinary_visit',
                            'care',
                            'status_change',
                            'other'
                        ) THEN event_type
                        ELSE 'other'
                    END,
                    occurred_at,
                    title,
                    notes,
                    NULL,
                    NULL,
                    NULL,
                    '{}',
                    task_id,
                    task_occurrence_id,
                    created_at
                FROM events
                """
            )
            connection.execute("DROP TABLE events")
            connection.execute("ALTER TABLE events_new RENAME TO events")
            connection.execute(
                "CREATE INDEX idx_events_animal_occurred ON events(animal_id, occurred_at DESC)"
            )
            connection.execute("CREATE INDEX idx_events_type ON events(event_type)")
            connection.execute(
                "CREATE INDEX idx_events_correction ON events(correction_of_event_id)"
            )

            violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise RuntimeError(
                    f"Animal Health migration created foreign-key violations: {violations}"
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.execute("PRAGMA foreign_keys = ON")

    @staticmethod
    def _generate_record_id(
        prefix: str,
        existing_ids: set[str] | None = None,
    ) -> str:
        existing_ids = existing_ids or set()
        while True:
            suffix = "".join(
                secrets.choice(RECORD_ID_ALPHABET) for _ in range(RECORD_ID_LENGTH)
            )
            record_id = f"{prefix}-{suffix}"
            if record_id not in existing_ids:
                return record_id

    async def get_animals(self) -> list[Animal]:
        return await self._hass.async_add_executor_job(self._get_animals_sync)

    def _get_animals_sync(self) -> list[Animal]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    name,
                    species,
                    breed,
                    color,
                    sex,
                    birth_date,
                    arrival_date,
                    status,
                    status_changed_at,
                    is_archived,
                    archived_at,
                    created_at,
                    updated_at
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
        color: str | None = None,
        sex: str | None = None,
        birth_date: date | None = None,
        arrival_date: date | None = None,
    ) -> Animal:
        return await self._hass.async_add_executor_job(
            self._create_animal_sync,
            name,
            species,
            breed,
            color,
            sex,
            birth_date,
            arrival_date,
        )

    def _create_animal_sync(
        self,
        name: str,
        species: str,
        breed: str | None,
        color: str | None,
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
            animal_id = self._generate_record_id("AH", existing_ids)
            connection.execute(
                """
                INSERT INTO animals (
                    id,
                    name,
                    species,
                    breed,
                    color,
                    sex,
                    birth_date,
                    arrival_date,
                    status,
                    status_changed_at,
                    is_archived,
                    archived_at,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    animal_id,
                    name,
                    species,
                    breed,
                    color,
                    sex,
                    birth_date.isoformat() if birth_date else None,
                    arrival_date.isoformat() if arrival_date else None,
                    ANIMAL_STATUS_ACTIVE,
                    now,
                    0,
                    None,
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

        now_dt = datetime.now(UTC).replace(microsecond=0)
        now = now_dt.isoformat()
        with self._connect() as connection:
            current = self._get_animal_from_connection(connection, animal_id)
            if current is None:
                raise KeyError(animal_id)
            if current.status == status:
                return current
            connection.execute(
                """
                UPDATE animals
                SET status = ?, status_changed_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, now, now, animal_id),
            )
            self._create_event_in_connection(
                connection,
                animal_id=animal_id,
                event_type=EVENT_TYPE_STATUS_CHANGE,
                occurred_at=now_dt,
                title="status_change",
                data={
                    "previous_status": current.status,
                    "new_status": status,
                },
            )
            animal = self._get_animal_from_connection(connection, animal_id)
        if animal is None:
            raise KeyError(animal_id)
        return animal

    async def set_animal_archived(
        self,
        animal_id: str,
        archived: bool,
    ) -> Animal:
        return await self._hass.async_add_executor_job(
            self._set_animal_archived_sync, animal_id, archived
        )

    def _set_animal_archived_sync(
        self,
        animal_id: str,
        archived: bool,
    ) -> Animal:
        now = datetime.now(UTC).isoformat(timespec="seconds")
        with self._connect() as connection:
            current = self._get_animal_from_connection(connection, animal_id)
            if current is None:
                raise KeyError(animal_id)
            if current.is_archived == archived:
                return current
            connection.execute(
                """
                UPDATE animals
                SET is_archived = ?, archived_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (1 if archived else 0, now if archived else None, now, animal_id),
            )
            animal = self._get_animal_from_connection(connection, animal_id)
        if animal is None:
            raise KeyError(animal_id)
        return animal

    async def create_event(
        self,
        *,
        animal_id: str,
        event_type: str,
        occurred_at: datetime,
        title: str,
        notes: str | None = None,
        value: float | None = None,
        unit: str | None = None,
        correction_of_event_id: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> HealthEvent:
        return await self._hass.async_add_executor_job(
            self._create_event_sync,
            animal_id,
            event_type,
            occurred_at,
            title,
            notes,
            value,
            unit,
            correction_of_event_id,
            data,
        )

    def _create_event_sync(
        self,
        animal_id: str,
        event_type: str,
        occurred_at: datetime,
        title: str,
        notes: str | None,
        value: float | None,
        unit: str | None,
        correction_of_event_id: str | None,
        data: dict[str, Any] | None,
    ) -> HealthEvent:
        with self._connect() as connection:
            if self._get_animal_from_connection(connection, animal_id) is None:
                raise KeyError(animal_id)
            return self._create_event_in_connection(
                connection,
                animal_id=animal_id,
                event_type=event_type,
                occurred_at=occurred_at,
                title=title,
                notes=notes,
                value=value,
                unit=unit,
                correction_of_event_id=correction_of_event_id,
                data=data,
            )

    def _create_event_in_connection(
        self,
        connection: sqlite3.Connection,
        *,
        animal_id: str,
        event_type: str,
        occurred_at: datetime,
        title: str,
        notes: str | None = None,
        value: float | None = None,
        unit: str | None = None,
        correction_of_event_id: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> HealthEvent:
        if event_type not in EVENT_TYPES:
            raise ValueError(f"Unsupported event type: {event_type}")
        if not title.strip():
            raise ValueError("Event title must not be empty")
        if (value is None) != (unit is None):
            raise ValueError("Event value and unit must be supplied together")

        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=UTC)
        occurred_at = occurred_at.astimezone(UTC).replace(microsecond=0)

        if correction_of_event_id is not None:
            corrected = connection.execute(
                "SELECT animal_id FROM events WHERE id = ?",
                (correction_of_event_id,),
            ).fetchone()
            if corrected is None:
                raise KeyError(correction_of_event_id)
            if corrected["animal_id"] != animal_id:
                raise ValueError("A correction must reference an event for the same animal")

        existing_ids = {
            row[0] for row in connection.execute("SELECT id FROM events").fetchall()
        }
        event_id = self._generate_record_id("EV", existing_ids)
        created_at = datetime.now(UTC).isoformat(timespec="seconds")
        connection.execute(
            """
            INSERT INTO events (
                id,
                animal_id,
                event_type,
                occurred_at,
                title,
                notes,
                value,
                unit,
                correction_of_event_id,
                data_json,
                task_id,
                task_occurrence_id,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)
            """,
            (
                event_id,
                animal_id,
                event_type,
                occurred_at.isoformat(),
                title.strip(),
                notes,
                value,
                unit,
                correction_of_event_id,
                json.dumps(data or {}, ensure_ascii=False, sort_keys=True),
                created_at,
            ),
        )
        event = self._get_event_from_connection(connection, event_id)
        if event is None:
            raise RuntimeError("Created event could not be loaded")
        return event

    async def get_events(
        self,
        animal_id: str,
        limit: int = 50,
    ) -> list[HealthEvent]:
        return await self._hass.async_add_executor_job(
            self._get_events_sync, animal_id, limit
        )

    def _get_events_sync(
        self,
        animal_id: str,
        limit: int,
    ) -> list[HealthEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    animal_id,
                    event_type,
                    occurred_at,
                    title,
                    notes,
                    value,
                    unit,
                    correction_of_event_id,
                    data_json,
                    task_id,
                    task_occurrence_id,
                    created_at
                FROM events
                WHERE animal_id = ?
                ORDER BY occurred_at DESC, created_at DESC
                LIMIT ?
                """,
                (animal_id, limit),
            ).fetchall()
        return [HealthEvent.from_mapping(row) for row in rows]

    @staticmethod
    def _get_event_from_connection(
        connection: sqlite3.Connection,
        event_id: str,
    ) -> HealthEvent | None:
        row = connection.execute(
            """
            SELECT
                id,
                animal_id,
                event_type,
                occurred_at,
                title,
                notes,
                value,
                unit,
                correction_of_event_id,
                data_json,
                task_id,
                task_occurrence_id,
                created_at
            FROM events
            WHERE id = ?
            """,
            (event_id,),
        ).fetchone()
        return HealthEvent.from_mapping(row) if row is not None else None

    @staticmethod
    def _get_animal_from_connection(
        connection: sqlite3.Connection,
        animal_id: str,
    ) -> Animal | None:
        row = connection.execute(
            """
            SELECT
                id,
                name,
                species,
                breed,
                color,
                sex,
                birth_date,
                arrival_date,
                status,
                status_changed_at,
                is_archived,
                archived_at,
                created_at,
                updated_at
            FROM animals
            WHERE id = ?
            """,
            (animal_id,),
        ).fetchone()
        return Animal.from_mapping(row) if row is not None else None
