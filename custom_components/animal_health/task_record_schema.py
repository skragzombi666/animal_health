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

            DROP TRIGGER IF EXISTS trg_task_occurrence_plan_insert;
            DROP TRIGGER IF EXISTS trg_task_occurrence_plan_resolve;
            DROP TRIGGER IF EXISTS trg_record_task_completion_guard;

            CREATE TRIGGER trg_task_occurrence_plan_insert
            AFTER INSERT ON task_occurrences
            BEGIN
                INSERT OR IGNORE INTO task_occurrence_plans (
                    occurrence_id,
                    planned_json,
                    resolved_at,
                    created_at,
                    updated_at
                )
                SELECT
                    NEW.id,
                    config.template_json,
                    NULL,
                    NEW.created_at,
                    NEW.updated_at
                FROM task_record_configs AS config
                WHERE config.task_id = NEW.task_id;
            END;

            CREATE TRIGGER trg_record_task_completion_guard
            BEFORE UPDATE OF status ON task_occurrences
            WHEN NEW.status = 'completed'
              AND EXISTS (
                  SELECT 1
                  FROM task_record_configs AS config
                  WHERE config.task_id = NEW.task_id
                    AND config.task_kind <> 'reminder'
              )
              AND NOT EXISTS (
                  SELECT 1
                  FROM events AS event
                  WHERE event.task_occurrence_id = NEW.id
              )
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Record-linked task occurrences must be completed through their record action'
                );
            END;

            CREATE TRIGGER trg_task_occurrence_plan_resolve
            AFTER UPDATE OF status, completed_at, updated_at ON task_occurrences
            WHEN NEW.status IN ('completed', 'skipped', 'cancelled')
            BEGIN
                INSERT INTO task_occurrence_plans (
                    occurrence_id,
                    planned_json,
                    resolved_at,
                    created_at,
                    updated_at
                )
                SELECT
                    NEW.id,
                    COALESCE(config.template_json, '{}'),
                    COALESCE(NEW.completed_at, NEW.updated_at),
                    NEW.created_at,
                    NEW.updated_at
                FROM tasks AS task
                LEFT JOIN task_record_configs AS config ON config.task_id = task.id
                WHERE task.id = NEW.task_id
                ON CONFLICT(occurrence_id) DO UPDATE SET
                    resolved_at = excluded.resolved_at,
                    updated_at = excluded.updated_at;
            END;
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
