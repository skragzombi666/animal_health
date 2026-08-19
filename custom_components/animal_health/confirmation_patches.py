from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
import sqlite3
from typing import Any

from . import dashboard_api, task_record_services, v080_task_policy, v081_features
from .confirmation_policy import (
    CONFIRMATION_REQUIRED,
    CONFIRMATION_ROUTINE,
    OCCURRENCE_NOT_DOCUMENTED,
    async_resolve_routine_occurrences,
    confirmation_modes_sync,
    default_confirmation_mode,
    recurrence_period_bounds,
    reopen_not_documented,
    restore_not_documented,
)
from .coordinator import AnimalHealthCoordinator
from .task_records import TaskRecordStore
from .task_store import TaskStore

_PATCHED = False


def _decorate_occurrences(
    occurrences: list[dict[str, Any]],
    tasks_by_id: dict[str, dict[str, Any]],
    *,
    today: date,
) -> list[dict[str, Any]]:
    now = datetime.now(UTC).replace(microsecond=0)
    result: list[dict[str, Any]] = []
    for raw in occurrences:
        item = dict(raw)
        task = tasks_by_id.get(str(item["task_id"]), {})
        recurrence = str(task.get("recurrence_type", "once"))
        mode = str(task.get("confirmation_mode", CONFIRMATION_REQUIRED))
        if mode not in {CONFIRMATION_REQUIRED, CONFIRMATION_ROUTINE}:
            mode = CONFIRMATION_REQUIRED
        status = str(item.get("status", "pending"))
        local_date = date.fromisoformat(str(item["scheduled_date"]))
        item["confirmation_mode"] = mode
        item["is_not_documented"] = status == OCCURRENCE_NOT_DOCUMENTED
        item["task_entity_id"] = task.get("entity_id")
        if recurrence != "once":
            start, end = recurrence_period_bounds(recurrence, local_date)
            item["period_start"] = start.isoformat()
            item["period_end"] = end.isoformat()
            current = start <= today <= end
            item["is_current_period"] = status == "pending" and current
            item["is_overdue"] = (
                status == "pending"
                and mode == CONFIRMATION_REQUIRED
                and end < today
            )
            item["is_today"] = status == "pending" and current
            item["is_upcoming"] = status == "pending" and start > today
        else:
            scheduled = datetime.fromisoformat(str(item["scheduled_for"]))
            if scheduled.tzinfo is None:
                scheduled = scheduled.replace(tzinfo=UTC)
            has_time = task.get("due_time") is not None
            item["period_start"] = local_date.isoformat()
            item["period_end"] = local_date.isoformat()
            item["is_current_period"] = status == "pending" and local_date == today
            item["is_overdue"] = status == "pending" and (
                scheduled < now if has_time else local_date < today
            )
            item["is_today"] = status == "pending" and local_date == today
            item["is_upcoming"] = status == "pending" and local_date > today
        result.append(item)
    return result


def _sync_occurrence_plans(
    connection: sqlite3.Connection,
    task_id: str,
    now: str,
) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO task_occurrence_plans (
            occurrence_id, planned_json, resolved_at, created_at, updated_at
        )
        SELECT occurrence.id, COALESCE(config.template_json, '{}'),
               CASE
                   WHEN occurrence.status='completed' THEN occurrence.completed_at
                   WHEN occurrence.status IN ('skipped','cancelled','not_documented')
                       THEN occurrence.updated_at
                   ELSE NULL
               END,
               ?, ?
        FROM task_occurrences AS occurrence
        LEFT JOIN task_record_configs AS config
            ON config.task_id=occurrence.task_id
        WHERE occurrence.task_id=?
        """,
        (now, now, task_id),
    )


def apply_confirmation_policy_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    original_update = AnimalHealthCoordinator._async_update_data

    async def coordinator_update(self: AnimalHealthCoordinator) -> Any:
        await async_resolve_routine_occurrences(self.task_store)
        return await original_update(self)

    AnimalHealthCoordinator._async_update_data = coordinator_update

    original_configure = TaskRecordStore._configure_task_in_connection

    def configure(
        self: TaskRecordStore,
        connection: sqlite3.Connection,
        task_id: str,
        task_kind: str,
        template: dict[str, Any],
    ) -> Any:
        existed = connection.execute(
            "SELECT 1 FROM task_record_configs WHERE task_id=?", (task_id,)
        ).fetchone()
        result = original_configure(self, connection, task_id, task_kind, template)
        if existed is None:
            connection.execute(
                "UPDATE task_record_configs SET confirmation_mode=?, updated_at=? WHERE task_id=?",
                (
                    default_confirmation_mode(task_kind),
                    datetime.now(UTC).replace(microsecond=0).isoformat(),
                    task_id,
                ),
            )
        return result

    TaskRecordStore._configure_task_in_connection = configure
    TaskRecordStore._sync_occurrence_plans = staticmethod(_sync_occurrence_plans)

    def resolve_occurrence(
        self: TaskRecordStore,
        task_id: str,
        scheduled_date: date | None,
    ) -> str:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scheduled_for, status
                FROM task_occurrences
                WHERE task_id=? AND status IN ('pending','not_documented')
                ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END,
                         scheduled_for
                """,
                (task_id,),
            ).fetchall()
        if scheduled_date is not None:
            rows = [
                row
                for row in rows
                if datetime.fromisoformat(str(row["scheduled_for"]))
                .astimezone(self._timezone)
                .date()
                == scheduled_date
            ]
        if not rows:
            raise KeyError(task_id)
        return str(rows[0]["id"])

    TaskRecordStore._resolve_occurrence_sync = resolve_occurrence

    original_enrich_tasks = TaskRecordStore._enrich_tasks_sync

    def enrich_tasks(
        self: TaskRecordStore,
        tasks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        enriched = original_enrich_tasks(self, tasks)
        if not enriched:
            return enriched
        today = datetime.now(UTC).astimezone(self._timezone).date()
        ids = [str(item["id"]) for item in enriched]
        with self._connect() as connection:
            modes = confirmation_modes_sync(connection, ids)
            for item in enriched:
                task_id = str(item["id"])
                recurring = str(item.get("recurrence_type", "once")) != "once"
                mode = modes.get(task_id, CONFIRMATION_REQUIRED) if recurring else CONFIRMATION_REQUIRED
                rows = connection.execute(
                    "SELECT scheduled_for,status FROM task_occurrences WHERE task_id=?",
                    (task_id,),
                ).fetchall()
                overdue = int(item.get("overdue_count", 0) or 0)
                undocumented = 0
                if recurring:
                    overdue = 0
                    for row in rows:
                        status = str(row["status"])
                        if status == OCCURRENCE_NOT_DOCUMENTED:
                            undocumented += 1
                        elif status == "pending" and mode == CONFIRMATION_REQUIRED:
                            scheduled = datetime.fromisoformat(str(row["scheduled_for"]))
                            _, end = recurrence_period_bounds(
                                str(item["recurrence_type"]),
                                scheduled.astimezone(self._timezone).date(),
                            )
                            overdue += int(end < today)
                item["confirmation_mode"] = mode
                item["overdue_count"] = overdue
                item["not_documented_count"] = undocumented
        return enriched

    TaskRecordStore._enrich_tasks_sync = enrich_tasks

    original_enrich_occurrences = TaskRecordStore._enrich_occurrences_sync

    def enrich_occurrences(
        self: TaskRecordStore,
        occurrences: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        enriched = original_enrich_occurrences(self, occurrences)
        if not enriched:
            return enriched
        with self._connect() as connection:
            modes = confirmation_modes_sync(
                connection,
                sorted({str(item["task_id"]) for item in enriched}),
            )
        for item in enriched:
            item["confirmation_mode"] = modes.get(
                str(item["task_id"]), CONFIRMATION_REQUIRED
            )
            item["is_not_documented"] = item.get("status") == OCCURRENCE_NOT_DOCUMENTED
        return enriched

    TaskRecordStore._enrich_occurrences_sync = enrich_occurrences

    original_execute = TaskRecordStore._execute_sync

    def execute(self: TaskRecordStore, occurrence_id: str, *args: Any, **kwargs: Any) -> Any:
        reopened, updated, resolved = reopen_not_documented(
            self._database_path, occurrence_id
        )
        try:
            return original_execute(self, occurrence_id, *args, **kwargs)
        except Exception:
            if reopened:
                restore_not_documented(
                    self._database_path, occurrence_id, updated, resolved
                )
            raise

    TaskRecordStore._execute_sync = execute

    original_status = TaskStore._set_occurrence_status_sync

    def set_status(self: TaskStore, occurrence_id: str, *args: Any, **kwargs: Any) -> Any:
        reopened, updated, resolved = reopen_not_documented(
            self._database_path, occurrence_id
        )
        try:
            return original_status(self, occurrence_id, *args, **kwargs)
        except Exception:
            if reopened:
                restore_not_documented(
                    self._database_path, occurrence_id, updated, resolved
                )
            raise

    TaskStore._set_occurrence_status_sync = set_status
    TaskStore.async_resolve_routine_occurrences = async_resolve_routine_occurrences

    original_plan = task_record_services._load_occurrence_plan

    async def load_plan(*args: Any, **kwargs: Any) -> dict[str, Any]:
        result = await original_plan(*args, **kwargs)
        if result.get("status") == OCCURRENCE_NOT_DOCUMENTED:
            result = dict(result)
            result["original_status"] = OCCURRENCE_NOT_DOCUMENTED
            result["status"] = "pending"
        return result

    task_record_services._load_occurrence_plan = load_plan
    v080_task_policy._load_occurrence_plan = load_plan

    original_group_execute = v081_features._execute_group_task_sync

    def group_execute(
        path: Path,
        occurrence_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        reopened, updated, resolved = reopen_not_documented(path, occurrence_id)
        try:
            return original_group_execute(path, occurrence_id, *args, **kwargs)
        except Exception:
            if reopened:
                restore_not_documented(path, occurrence_id, updated, resolved)
            raise

    v081_features._execute_group_task_sync = group_execute
    dashboard_api._decorate_occurrences = _decorate_occurrences
