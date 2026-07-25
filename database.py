from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant


class AnimalHealthDatabase:
    def __init__(self, hass: HomeAssistant, database_path: Path) -> None:
        self._hass = hass
        self._database_path = database_path

    async def initialize(self) -> None:
        await self._hass.async_add_executor_job(self._initialize_sync)

    def _initialize_sync(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS animals (
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
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_animals_name
                ON animals(name)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_animals_status
                ON animals(status)
                """
            )

            connection.commit()

    async def get_animals(self) -> list[dict[str, Any]]:
        return await self._hass.async_add_executor_job(self._get_animals_sync)

    def _get_animals_sync(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self._database_path) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute(
                """
                SELECT
                    id,
                    name,
                    species,
                    breed,
                    sex,
                    birth_date,
                    arrival_date,
                    status,
                    created_at,
                    updated_at
                FROM animals
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()

        return [dict(row) for row in rows]