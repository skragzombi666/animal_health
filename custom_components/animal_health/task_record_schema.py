from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from homeassistant.core import HomeAssistant

from .const import DATABASE_NAME


async def async_initialize_task_record_schema(hass: HomeAssistant) -> None:
    database_path = Path(hass.config.path(DATABASE_NAME))
    await hass.async_add_executor_job(_initialize_sync, database_path)


def _initialize_sync(database_path: Path) -> None:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS task_record_configs (
                task_id TEXT PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
                task_kind TEXT NOT NULL DEFAULT 'reminder'
                    CHECK (
                        task_kind IN (
                            'reminder',
                            'weight',
                            'medication',
                            'vaccination',
                            'health_check',
                            'care',
                            'veterinary_visit'
                        )
                    ),
                template_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS task_occurrence_plans (
                occurrence_id TEXT PRIMARY KEY
                    REFERENCES task_occurrences(id) ON DELETE CASCADE,
                planned_json TEXT NOT NULL DEFAULT '{}',
                resolved_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_task_record_configs_kind
                ON task_record_configs(task_kind);
            CREATE INDEX IF NOT EXISTS idx_task_occurrence_plans_resolved
                ON task_occurrence_plans(resolved_at);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_events_task_occurrence_unique
                ON events(task_occurrence_id)
                WHERE task_occurrence_id IS NOT NULL;
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO task_record_configs (
                task_id,
                task_kind,
                template_json,
                created_at,
                updated_at
            )
            SELECT id, 'reminder', '{}', ?, ?
            FROM tasks
            """,
            (now, now),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO task_occurrence_plans (
                occurrence_id,
                planned_json,
                resolved_at,
                created_at,
                updated_at
            )
            SELECT
                occurrence.id,
                COALESCE(config.template_json, '{}'),
                CASE
                    WHEN occurrence.status = 'completed' THEN occurrence.completed_at
                    WHEN occurrence.status IN ('skipped', 'cancelled') THEN occurrence.updated_at
                    ELSE NULL
                END,
                ?,
                ?
            FROM task_occurrences AS occurrence
            LEFT JOIN task_record_configs AS config ON config.task_id = occurrence.task_id
            """,
            (now, now),
        )
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(
                f"Animal Health task-record migration created foreign-key violations: {violations}"
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
