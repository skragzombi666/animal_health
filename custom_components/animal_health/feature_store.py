from __future__ import annotations

import mimetypes
import re
import secrets
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

from .database import RECORD_ID_ALPHABET, RECORD_ID_LENGTH

_MAX_ATTACHMENT_SIZE = 15 * 1024 * 1024


class AnimalHealthFeatureStore:
    """Store groups, memberships and locally persisted attachments."""

    def __init__(
        self,
        hass: HomeAssistant,
        database_path: Path,
        attachment_root: Path,
    ) -> None:
        self._hass = hass
        self._database_path = database_path
        self._attachment_root = attachment_root

    async def initialize(self) -> None:
        await self._hass.async_add_executor_job(self._initialize_sync)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def _initialize_sync(self) -> None:
        self._attachment_root.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS animal_groups (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    species TEXT,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_animal_groups_name
                    ON animal_groups(name COLLATE NOCASE);

                CREATE TABLE IF NOT EXISTS animal_group_memberships (
                    animal_id TEXT PRIMARY KEY
                        REFERENCES animals(id) ON DELETE CASCADE,
                    group_id TEXT NOT NULL
                        REFERENCES animal_groups(id) ON DELETE CASCADE,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_animal_group_memberships_group
                    ON animal_group_memberships(group_id);

                CREATE TABLE IF NOT EXISTS attachments (
                    id TEXT PRIMARY KEY,
                    animal_id TEXT NOT NULL
                        REFERENCES animals(id) ON DELETE CASCADE,
                    event_id TEXT
                        REFERENCES events(id) ON DELETE SET NULL,
                    filename TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
                    storage_name TEXT NOT NULL UNIQUE,
                    title TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_attachments_animal
                    ON attachments(animal_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_attachments_event
                    ON attachments(event_id, created_at DESC);
                """
            )

    @staticmethod
    def _record_id(prefix: str, existing: set[str]) -> str:
        while True:
            suffix = "".join(
                secrets.choice(RECORD_ID_ALPHABET) for _ in range(RECORD_ID_LENGTH)
            )
            value = f"{prefix}-{suffix}"
            if value not in existing:
                return value

    async def list_groups(self) -> list[dict[str, Any]]:
        return await self._hass.async_add_executor_job(self._list_groups_sync)

    def _list_groups_sync(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    g.id,
                    g.name,
                    g.species,
                    g.description,
                    g.created_at,
                    g.updated_at,
                    COUNT(m.animal_id) AS animal_count
                FROM animal_groups AS g
                LEFT JOIN animal_group_memberships AS m ON m.group_id = g.id
                GROUP BY g.id
                ORDER BY g.name COLLATE NOCASE
                """
            ).fetchall()
        return [dict(row) for row in rows]

    async def create_group(
        self,
        *,
        name: str,
        species: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        return await self._hass.async_add_executor_job(
            self._create_group_sync,
            name,
            species,
            description,
        )

    def _create_group_sync(
        self,
        name: str,
        species: str | None,
        description: str | None,
    ) -> dict[str, Any]:
        name = name.strip()
        if not name:
            raise ValueError("Group name must not be empty")
        now = datetime.now(UTC).replace(microsecond=0).isoformat()
        with self._connect() as connection:
            existing = {
                str(row[0])
                for row in connection.execute("SELECT id FROM animal_groups").fetchall()
            }
            group_id = self._record_id("GR", existing)
            try:
                connection.execute(
                    """
                    INSERT INTO animal_groups (
                        id, name, species, description, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        group_id,
                        name,
                        species.strip() if species and species.strip() else None,
                        description.strip()
                        if description and description.strip()
                        else None,
                        now,
                        now,
                    ),
                )
            except sqlite3.IntegrityError as err:
                raise ValueError("A group with this name already exists") from err
        return {
            "id": group_id,
            "name": name,
            "species": species.strip() if species and species.strip() else None,
            "description": description.strip()
            if description and description.strip()
            else None,
            "created_at": now,
            "updated_at": now,
            "animal_count": 0,
        }

    async def update_group(
        self,
        group_id: str,
        *,
        name: str,
        species: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        return await self._hass.async_add_executor_job(
            self._update_group_sync,
            group_id,
            name,
            species,
            description,
        )

    def _update_group_sync(
        self,
        group_id: str,
        name: str,
        species: str | None,
        description: str | None,
    ) -> dict[str, Any]:
        name = name.strip()
        if not name:
            raise ValueError("Group name must not be empty")
        now = datetime.now(UTC).replace(microsecond=0).isoformat()
        with self._connect() as connection:
            try:
                cursor = connection.execute(
                    """
                    UPDATE animal_groups
                    SET name = ?, species = ?, description = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        name,
                        species.strip() if species and species.strip() else None,
                        description.strip()
                        if description and description.strip()
                        else None,
                        now,
                        group_id,
                    ),
                )
            except sqlite3.IntegrityError as err:
                raise ValueError("A group with this name already exists") from err
            if cursor.rowcount == 0:
                raise KeyError(group_id)
            count = connection.execute(
                "SELECT COUNT(*) FROM animal_group_memberships WHERE group_id = ?",
                (group_id,),
            ).fetchone()[0]
        return {
            "id": group_id,
            "name": name,
            "species": species.strip() if species and species.strip() else None,
            "description": description.strip()
            if description and description.strip()
            else None,
            "updated_at": now,
            "animal_count": count,
        }

    async def delete_group(self, group_id: str) -> None:
        await self._hass.async_add_executor_job(self._delete_group_sync, group_id)

    def _delete_group_sync(self, group_id: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM animal_groups WHERE id = ?",
                (group_id,),
            )
            if cursor.rowcount == 0:
                raise KeyError(group_id)

    async def memberships(self) -> dict[str, str]:
        return await self._hass.async_add_executor_job(self._memberships_sync)

    def _memberships_sync(self) -> dict[str, str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT animal_id, group_id FROM animal_group_memberships"
            ).fetchall()
        return {str(row["animal_id"]): str(row["group_id"]) for row in rows}

    async def set_animal_group(
        self,
        animal_id: str,
        group_id: str | None,
    ) -> None:
        await self._hass.async_add_executor_job(
            self._set_animal_group_sync,
            animal_id,
            group_id,
        )

    def _set_animal_group_sync(
        self,
        animal_id: str,
        group_id: str | None,
    ) -> None:
        now = datetime.now(UTC).replace(microsecond=0).isoformat()
        with self._connect() as connection:
            animal = connection.execute(
                "SELECT 1 FROM animals WHERE id = ?",
                (animal_id,),
            ).fetchone()
            if animal is None:
                raise KeyError(animal_id)
            if not group_id:
                connection.execute(
                    "DELETE FROM animal_group_memberships WHERE animal_id = ?",
                    (animal_id,),
                )
                return
            group = connection.execute(
                "SELECT 1 FROM animal_groups WHERE id = ?",
                (group_id,),
            ).fetchone()
            if group is None:
                raise KeyError(group_id)
            connection.execute(
                """
                INSERT INTO animal_group_memberships (animal_id, group_id, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(animal_id) DO UPDATE SET
                    group_id = excluded.group_id,
                    updated_at = excluded.updated_at
                """,
                (animal_id, group_id, now),
            )

    async def list_attachments(
        self,
        *,
        animal_id: str | None = None,
        event_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._hass.async_add_executor_job(
            self._list_attachments_sync,
            animal_id,
            event_id,
        )

    def _list_attachments_sync(
        self,
        animal_id: str | None,
        event_id: str | None,
    ) -> list[dict[str, Any]]:
        where: list[str] = []
        values: list[str] = []
        if animal_id is not None:
            where.append("animal_id = ?")
            values.append(animal_id)
        if event_id is not None:
            where.append("event_id = ?")
            values.append(event_id)
        clause = f"WHERE {' AND '.join(where)}" if where else ""
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    id,
                    animal_id,
                    event_id,
                    filename,
                    media_type,
                    size_bytes,
                    title,
                    created_at
                FROM attachments
                {clause}
                ORDER BY created_at DESC, id DESC
                """,
                values,
            ).fetchall()
        return [self._public_attachment(dict(row)) for row in rows]

    @staticmethod
    def _public_attachment(item: dict[str, Any]) -> dict[str, Any]:
        item["download_url"] = f"/api/animal_health/attachments/{item['id']}"
        return item

    async def create_attachment(
        self,
        *,
        animal_id: str,
        event_id: str | None,
        filename: str,
        media_type: str | None,
        content: bytes,
        title: str | None = None,
    ) -> dict[str, Any]:
        return await self._hass.async_add_executor_job(
            self._create_attachment_sync,
            animal_id,
            event_id,
            filename,
            media_type,
            content,
            title,
        )

    def _create_attachment_sync(
        self,
        animal_id: str,
        event_id: str | None,
        filename: str,
        media_type: str | None,
        content: bytes,
        title: str | None,
    ) -> dict[str, Any]:
        if not content:
            raise ValueError("Attachment must not be empty")
        if len(content) > _MAX_ATTACHMENT_SIZE:
            raise ValueError("Attachment exceeds the 15 MB size limit")
        clean_name = Path(filename or "document").name.strip()[:255] or "document"
        guessed_type = mimetypes.guess_type(clean_name)[0]
        proposed_type = (media_type or guessed_type or "application/octet-stream").strip()[:120]
        clean_type = (
            proposed_type
            if re.fullmatch(r"[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+", proposed_type)
            else "application/octet-stream"
        )
        suffix = Path(clean_name).suffix.lower()[:16]
        now = datetime.now(UTC).replace(microsecond=0).isoformat()

        with self._connect() as connection:
            if connection.execute(
                "SELECT 1 FROM animals WHERE id = ?",
                (animal_id,),
            ).fetchone() is None:
                raise KeyError(animal_id)
            if event_id is not None:
                event = connection.execute(
                    "SELECT animal_id FROM events WHERE id = ?",
                    (event_id,),
                ).fetchone()
                if event is None:
                    raise KeyError(event_id)
                if str(event["animal_id"]) != animal_id:
                    raise ValueError("Attachment event belongs to another animal")

            existing = {
                str(row[0])
                for row in connection.execute("SELECT id FROM attachments").fetchall()
            }
            attachment_id = self._record_id("AT", existing)
            storage_name = f"{attachment_id}{suffix}"
            target = self._attachment_root / storage_name
            temporary = target.with_suffix(target.suffix + ".tmp")
            temporary.write_bytes(content)
            temporary.replace(target)
            try:
                connection.execute(
                    """
                    INSERT INTO attachments (
                        id,
                        animal_id,
                        event_id,
                        filename,
                        media_type,
                        size_bytes,
                        storage_name,
                        title,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        attachment_id,
                        animal_id,
                        event_id,
                        clean_name,
                        clean_type,
                        len(content),
                        storage_name,
                        title.strip() if title and title.strip() else None,
                        now,
                    ),
                )
            except Exception:
                target.unlink(missing_ok=True)
                raise

        return self._public_attachment(
            {
                "id": attachment_id,
                "animal_id": animal_id,
                "event_id": event_id,
                "filename": clean_name,
                "media_type": clean_type,
                "size_bytes": len(content),
                "title": title.strip() if title and title.strip() else None,
                "created_at": now,
            }
        )

    async def delete_attachment(self, attachment_id: str) -> None:
        await self._hass.async_add_executor_job(
            self._delete_attachment_sync,
            attachment_id,
        )

    def _delete_attachment_sync(self, attachment_id: str) -> None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT storage_name FROM attachments WHERE id = ?",
                (attachment_id,),
            ).fetchone()
            if row is None:
                raise KeyError(attachment_id)
            connection.execute(
                "DELETE FROM attachments WHERE id = ?",
                (attachment_id,),
            )
        (self._attachment_root / str(row["storage_name"])).unlink(missing_ok=True)

    async def attachment_file(
        self,
        attachment_id: str,
    ) -> tuple[dict[str, Any], Path]:
        return await self._hass.async_add_executor_job(
            self._attachment_file_sync,
            attachment_id,
        )

    def _attachment_file_sync(
        self,
        attachment_id: str,
    ) -> tuple[dict[str, Any], Path]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    animal_id,
                    event_id,
                    filename,
                    media_type,
                    size_bytes,
                    storage_name,
                    title,
                    created_at
                FROM attachments
                WHERE id = ?
                """,
                (attachment_id,),
            ).fetchone()
        if row is None:
            raise KeyError(attachment_id)
        item = dict(row)
        storage_name = str(item.pop("storage_name"))
        path = self._attachment_root / storage_name
        if not path.is_file():
            raise FileNotFoundError(path)
        return self._public_attachment(item), path

    async def export_rows(self) -> dict[str, Any]:
        return await self._hass.async_add_executor_job(self._export_rows_sync)

    def _export_rows_sync(self) -> dict[str, Any]:
        with self._connect() as connection:
            groups = [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM animal_groups ORDER BY name COLLATE NOCASE"
                ).fetchall()
            ]
            memberships = [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM animal_group_memberships ORDER BY animal_id"
                ).fetchall()
            ]
            attachments = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT id, animal_id, event_id, filename, media_type,
                           size_bytes, storage_name, title, created_at
                    FROM attachments
                    ORDER BY created_at, id
                    """
                ).fetchall()
            ]
        return {
            "groups": groups,
            "memberships": memberships,
            "attachments": attachments,
        }

    @property
    def database_path(self) -> Path:
        return self._database_path

    @property
    def attachment_root(self) -> Path:
        return self._attachment_root
