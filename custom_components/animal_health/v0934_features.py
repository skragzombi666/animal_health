from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

from . import task_kinds, task_records
from .const import DATABASE_NAME

_PATCHED = False


def _loads_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if value in (None, ""):
        return {}
    try:
        decoded = json.loads(str(value))
    except (TypeError, json.JSONDecodeError):
        return {}
    return dict(decoded) if isinstance(decoded, dict) else {}


def _loads_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [dict(item) for item in value if isinstance(item, dict)]
    if value in (None, ""):
        return []
    try:
        decoded = json.loads(str(value))
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(decoded, list):
        return []
    return [dict(item) for item in decoded if isinstance(item, dict)]


def _first_text(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {
        str(row[1])
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }


def _plan_from_master(
    connection: sqlite3.Connection,
    plan_id: str,
) -> tuple[str, list[dict[str, Any]], str]:
    if not plan_id:
        return "", [], ""
    table = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='v0911_treatment_plans'"
    ).fetchone()
    if table is None:
        return "", [], ""
    columns = _table_columns(connection, "v0911_treatment_plans")
    select = ["name"]
    if "components_json" in columns:
        select.append("components_json")
    if "description" in columns:
        select.append("description")
    row = connection.execute(
        f"SELECT {', '.join(select)} FROM v0911_treatment_plans WHERE id=?",
        (plan_id,),
    ).fetchone()
    if row is None:
        return "", [], ""
    name = _first_text(row["name"])
    components = _loads_list(row["components_json"]) if "components_json" in row.keys() else []
    description = _first_text(row["description"]) if "description" in row.keys() else ""
    return name, components, description


def _event_dict(row: sqlite3.Row, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "animal_id": str(row["animal_id"]),
        "event_type": str(row["event_type"]),
        "occurred_at": str(row["occurred_at"]),
        "title": str(row["title"]),
        "notes": row["notes"],
        "value": row["value"],
        "unit": row["unit"],
        "correction_of_event_id": row["correction_of_event_id"],
        "data": data,
        "task_id": row["task_id"],
        "task_occurrence_id": row["task_occurrence_id"],
        "created_at": str(row["created_at"]),
    }


def _component_names(components: list[dict[str, Any]]) -> set[str]:
    return {
        _first_text(component.get("name"), component.get("product_name")).casefold()
        for component in components
        if _first_text(component.get("name"), component.get("product_name"))
    }


def _repair_treatment_event_sync(
    path: Path,
    event_id: str,
    planned_override: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    with _connect(path) as connection:
        row = connection.execute(
            """
            SELECT
                event.id,
                event.animal_id,
                event.event_type,
                event.occurred_at,
                event.title,
                event.notes,
                event.value,
                event.unit,
                event.correction_of_event_id,
                event.data_json,
                event.task_id,
                event.task_occurrence_id,
                event.created_at,
                task.title AS task_title,
                config.task_kind,
                config.template_json,
                plan.planned_json
            FROM events AS event
            LEFT JOIN task_occurrences AS occurrence
                ON occurrence.id = event.task_occurrence_id
            LEFT JOIN tasks AS task
                ON task.id = COALESCE(event.task_id, occurrence.task_id)
            LEFT JOIN task_record_configs AS config
                ON config.task_id = task.id
            LEFT JOIN task_occurrence_plans AS plan
                ON plan.occurrence_id = event.task_occurrence_id
            WHERE event.id = ?
            """,
            (event_id,),
        ).fetchone()
        if row is None or str(row["event_type"]) != "treatment":
            return None

        event_data = _loads_dict(row["data_json"])
        execution = _loads_dict(event_data.get("task_execution"))
        execution_planned = _loads_dict(execution.get("planned"))
        configured = _loads_dict(row["template_json"])
        occurrence_planned = _loads_dict(row["planned_json"])
        planned: dict[str, Any] = {}
        for source in (
            configured,
            occurrence_planned,
            execution_planned,
            event_data,
            planned_override or {},
        ):
            planned.update(_loads_dict(source))

        plan_id = _first_text(
            planned.get("treatment_plan_id"),
            event_data.get("treatment_plan_id"),
        )
        plan_name = _first_text(
            planned.get("treatment_plan_name"),
            event_data.get("treatment_plan_name"),
            row["title"],
        )
        components = _loads_list(
            planned.get("treatment_plan_components")
            or event_data.get("treatment_plan_components")
            or planned.get("components")
        )
        description = _first_text(
            planned.get("treatment_plan_description"),
            event_data.get("treatment_plan_description"),
        )
        master_name, master_components, master_description = _plan_from_master(
            connection,
            plan_id,
        )
        if not plan_name:
            plan_name = master_name
        if not components:
            components = master_components
        if not description:
            description = master_description

        task_id = _first_text(
            row["task_id"],
            event_data.get("source_task_id"),
            execution.get("task_id"),
        )
        occurrence_id = _first_text(
            row["task_occurrence_id"],
            event_data.get("source_task_occurrence_id"),
            execution.get("occurrence_id"),
        )
        if not task_id and occurrence_id:
            occurrence = connection.execute(
                "SELECT task_id FROM task_occurrences WHERE id=?",
                (occurrence_id,),
            ).fetchone()
            task_id = _first_text(occurrence["task_id"] if occurrence else "")
        task_title = _first_text(row["task_title"], execution.get("task_title"))
        task_kind = _first_text(row["task_kind"], execution.get("task_kind"), "treatment")
        treatment_execution_id = _first_text(
            event_data.get("treatment_execution_id"),
            execution.get("treatment_execution_id"),
            f"TX-{event_id}",
        )

        snapshot = dict(planned)
        if plan_id:
            snapshot["treatment_plan_id"] = plan_id
        if plan_name:
            snapshot["treatment_plan_name"] = plan_name
        if components:
            snapshot["treatment_plan_components"] = components
        if description:
            snapshot["treatment_plan_description"] = description

        execution.update(
            {
                "source": "task_occurrence",
                "task_id": task_id,
                "occurrence_id": occurrence_id,
                "task_title": task_title,
                "task_kind": task_kind,
                "planned": snapshot,
                "treatment_execution_id": treatment_execution_id,
            }
        )
        event_data.update(
            {
                "source": "task",
                "gabe_source": "task",
                "source_task_id": task_id,
                "source_task_occurrence_id": occurrence_id,
                "task_execution": execution,
                "treatment_execution_id": treatment_execution_id,
                "treatment_execution_role": "parent",
            }
        )
        if plan_id:
            event_data["treatment_plan_id"] = plan_id
        if plan_name:
            event_data["treatment_plan_name"] = plan_name
        if components:
            event_data["treatment_plan_components"] = components
        if description:
            event_data["treatment_plan_description"] = description

        component_ids: list[str] = []
        names = _component_names(components)
        candidates = connection.execute(
            """
            SELECT id,title,event_type,data_json
            FROM events
            WHERE animal_id=? AND occurred_at=? AND id<>?
            """,
            (row["animal_id"], row["occurred_at"], event_id),
        ).fetchall()
        for candidate in candidates:
            child_data = _loads_dict(candidate["data_json"])
            same_execution = (
                _first_text(child_data.get("treatment_execution_id"))
                == treatment_execution_id
            )
            same_parent = (
                _first_text(child_data.get("treatment_parent_event_id")) == event_id
            )
            same_plan = bool(
                plan_id
                and _first_text(child_data.get("treatment_plan_id")) == plan_id
            )
            same_name = bool(
                plan_name
                and _first_text(child_data.get("treatment_plan_name")).casefold()
                == plan_name.casefold()
            )
            component_name = _first_text(
                child_data.get("product_name"),
                child_data.get("medication_name"),
                candidate["title"],
            ).casefold()
            matches_snapshot = bool(component_name and component_name in names)
            if not (
                same_execution
                or same_parent
                or same_plan
                or same_name
                or matches_snapshot
            ):
                continue
            child_data.update(
                {
                    "source": "task",
                    "gabe_source": "task",
                    "source_task_id": task_id,
                    "source_task_occurrence_id": occurrence_id,
                    "treatment_parent_event_id": event_id,
                    "treatment_execution_id": treatment_execution_id,
                    "treatment_execution_role": "component",
                }
            )
            if plan_id:
                child_data["treatment_plan_id"] = plan_id
            if plan_name:
                child_data["treatment_plan_name"] = plan_name
            connection.execute(
                """
                UPDATE events
                SET data_json=?, task_id=COALESCE(task_id, ?)
                WHERE id=?
                """,
                (
                    json.dumps(child_data, ensure_ascii=False, sort_keys=True),
                    task_id or None,
                    candidate["id"],
                ),
            )
            component_ids.append(str(candidate["id"]))

        if component_ids:
            event_data["component_events"] = component_ids
            event_data["treatment_plan_component_event_ids"] = component_ids

        connection.execute(
            """
            UPDATE events
            SET data_json=?,
                task_id=COALESCE(task_id, ?),
                task_occurrence_id=COALESCE(task_occurrence_id, ?)
            WHERE id=?
            """,
            (
                json.dumps(event_data, ensure_ascii=False, sort_keys=True),
                task_id or None,
                occurrence_id or None,
                event_id,
            ),
        )
        refreshed = connection.execute(
            """
            SELECT id,animal_id,event_type,occurred_at,title,notes,value,unit,
                   correction_of_event_id,data_json,task_id,task_occurrence_id,created_at
            FROM events WHERE id=?
            """,
            (event_id,),
        ).fetchone()
        return _event_dict(refreshed, event_data) if refreshed is not None else None


def _repair_existing_treatment_events_sync(path: Path) -> int:
    if not path.exists():
        return 0
    with _connect(path) as connection:
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        required = {
            "events",
            "tasks",
            "task_occurrences",
            "task_record_configs",
            "task_occurrence_plans",
        }
        if not required <= tables:
            return 0
        rows = connection.execute(
            """
            SELECT DISTINCT event.id
            FROM events AS event
            LEFT JOIN task_occurrences AS occurrence
                ON occurrence.id = event.task_occurrence_id
            LEFT JOIN task_record_configs AS config
                ON config.task_id = COALESCE(event.task_id, occurrence.task_id)
            WHERE event.event_type='treatment'
              AND (
                  config.task_kind='treatment'
                  OR event.task_occurrence_id IS NOT NULL
                  OR event.task_id IS NOT NULL
              )
            """
        ).fetchall()
    repaired = 0
    for row in rows:
        if _repair_treatment_event_sync(path, str(row["id"])) is not None:
            repaired += 1
    return repaired


def _enrich_task_completion_stats_sync(
    path: Path,
    tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not tasks or not path.exists():
        return tasks
    task_ids = [str(task.get("id") or "") for task in tasks]
    task_ids = [task_id for task_id in task_ids if task_id]
    if not task_ids:
        return tasks
    placeholders = ",".join("?" for _ in task_ids)
    with _connect(path) as connection:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='task_occurrences'"
        ).fetchone()
        if table is None:
            return tasks
        rows = connection.execute(
            f"""
            SELECT
                task_id,
                SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) AS pending_count,
                SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed_count,
                MAX(
                    CASE
                        WHEN status='completed'
                        THEN COALESCE(completed_at, updated_at, scheduled_for)
                        ELSE NULL
                    END
                ) AS last_completed_at
            FROM task_occurrences
            WHERE task_id IN ({placeholders})
            GROUP BY task_id
            """,
            task_ids,
        ).fetchall()
    stats = {str(row["task_id"]): row for row in rows}
    enriched: list[dict[str, Any]] = []
    for task in tasks:
        item = dict(task)
        row = stats.get(str(item.get("id") or ""))
        item["pending_count"] = int(row["pending_count"] or 0) if row else 0
        item["completed_count"] = int(row["completed_count"] or 0) if row else 0
        item["last_completed_at"] = row["last_completed_at"] if row else None
        enriched.append(item)
    return enriched


def apply_v0934_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True
    base_execute = task_records.TaskRecordStore.execute
    base_enrich_tasks = task_records.TaskRecordStore.enrich_tasks

    async def enrich_tasks_v0934(self, tasks):
        enriched = await base_enrich_tasks(self, tasks)
        return await self._hass.async_add_executor_job(  # noqa: SLF001
            _enrich_task_completion_stats_sync,
            self._database_path,  # noqa: SLF001
            enriched,
        )

    async def execute_v0934(self, *args: Any, **kwargs: Any):
        result = await base_execute(self, *args, **kwargs)
        if (
            kwargs.get("expected_kind") != task_kinds.TASK_KIND_TREATMENT
            or not result.event
        ):
            return result
        repaired = await self._hass.async_add_executor_job(  # noqa: SLF001
            _repair_treatment_event_sync,
            self._database_path,  # noqa: SLF001
            str(result.event["id"]),
            _loads_dict(result.occurrence.get("planned")),
        )
        return task_records.TaskExecutionResult(
            result.occurrence,
            repaired or result.event,
        )

    task_records.TaskRecordStore.enrich_tasks = enrich_tasks_v0934  # type: ignore[method-assign]
    task_records.TaskRecordStore.execute = execute_v0934  # type: ignore[method-assign]


async def async_initialize_v0934_features(hass: HomeAssistant) -> None:
    path = Path(hass.config.path(DATABASE_NAME))
    await hass.async_add_executor_job(_repair_existing_treatment_events_sync, path)
