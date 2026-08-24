from __future__ import annotations

import sqlite3
from pathlib import Path

from homeassistant.core import HomeAssistant

from .const import DATABASE_NAME


async def async_migrate_v0916_task_kinds(hass: HomeAssistant) -> None:
    database_path = Path(hass.config.path(DATABASE_NAME))
    await hass.async_add_executor_job(_migrate_task_record_configs_sync, database_path)


def _migrate_task_record_configs_sync(database_path: Path) -> None:
    if not database_path.exists():
        return
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        row = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='task_record_configs'"
        ).fetchone()
        if row is None or "'treatment'" in str(row["sql"] or ""):
            return

        columns = {
            str(item[1])
            for item in connection.execute(
                "PRAGMA table_info(task_record_configs)"
            ).fetchall()
        }
        connection.executescript(
            """
            DROP TRIGGER IF EXISTS trg_task_occurrence_plan_insert;
            DROP TRIGGER IF EXISTS trg_task_occurrence_plan_resolve;
            DROP TRIGGER IF EXISTS trg_record_task_completion_guard;

            CREATE TABLE task_record_configs_v0916 (
                task_id TEXT PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
                task_kind TEXT NOT NULL DEFAULT 'reminder'
                    CHECK (
                        task_kind IN (
                            'reminder',
                            'weight',
                            'medication',
                            'vaccination',
                            'treatment',
                            'health_check',
                            'care',
                            'veterinary_visit'
                        )
                    ),
                template_json TEXT NOT NULL DEFAULT '{}',
                confirmation_mode TEXT NOT NULL DEFAULT 'required'
                    CHECK (confirmation_mode IN ('required', 'routine')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        if "confirmation_mode" in columns:
            connection.execute(
                """
                INSERT INTO task_record_configs_v0916 (
                    task_id, task_kind, template_json, confirmation_mode,
                    created_at, updated_at
                )
                SELECT
                    task_id, task_kind, template_json,
                    COALESCE(confirmation_mode, 'required'),
                    created_at, updated_at
                FROM task_record_configs
                """
            )
        else:
            connection.execute(
                """
                INSERT INTO task_record_configs_v0916 (
                    task_id, task_kind, template_json, confirmation_mode,
                    created_at, updated_at
                )
                SELECT
                    task_id, task_kind, template_json, 'required',
                    created_at, updated_at
                FROM task_record_configs
                """
            )
        connection.executescript(
            """
            DROP TABLE task_record_configs;
            ALTER TABLE task_record_configs_v0916 RENAME TO task_record_configs;
            CREATE INDEX IF NOT EXISTS idx_task_record_configs_kind
                ON task_record_configs(task_kind);
            CREATE INDEX IF NOT EXISTS idx_task_record_configs_confirmation
                ON task_record_configs(confirmation_mode);
            """
        )
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(
                "Animal Health 0.9.16 task-kind migration created foreign-key violations: "
                f"{violations}"
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
