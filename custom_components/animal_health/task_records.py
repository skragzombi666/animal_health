from __future__ import annotations

import json
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .catalog import product_event_metadata
from .const import (
    ADMINISTRATION_ROUTES,
    DATABASE_NAME,
    DOSE_UNITS,
    EVENT_TYPES,
    SYMPTOM_OTHER,
    SYMPTOM_SEVERITIES,
    SYMPTOMS,
    VACCINATION_TARGET_OTHER,
    VACCINATION_TARGETS,
    WEIGHT_UNITS,
)
from .models import HealthEvent
from .task_kinds import (
    TASK_KIND_CARE,
    TASK_KIND_HEALTH_CHECK,
    TASK_KIND_MEDICATION,
    TASK_KIND_REMINDER,
    TASK_KIND_VACCINATION,
    TASK_KIND_VETERINARY_VISIT,
    TASK_KIND_WEIGHT,
    TASK_KINDS,
)
from .task_store import TaskRecord, TaskStore

HEALTH_CHECK_NORMAL = "normal"
HEALTH_CHECK_CONCERN = "concern"
HEALTH_CHECK_SYMPTOM = "symptom"
HEALTH_CHECK_RESULTS = (
    HEALTH_CHECK_NORMAL,
    HEALTH_CHECK_CONCERN,
    HEALTH_CHECK_SYMPTOM,
)

TIMING_EARLY = "early"
TIMING_ON_TIME = "on_time"
TIMING_LATE = "late"

SERVICE_RECORD_TASK_REMINDER = "record_task_reminder"
SERVICE_RECORD_TASK_WEIGHT = "record_task_weight"
SERVICE_RECORD_TASK_MEDICATION = "record_task_medication"
SERVICE_RECORD_TASK_VACCINATION = "record_task_vaccination"
SERVICE_RECORD_TASK_HEALTH_CHECK = "record_task_health_check"
SERVICE_RECORD_TASK_CARE = "record_task_care"
SERVICE_RECORD_TASK_VETERINARY_VISIT = "record_task_veterinary_visit"

ATTR_TASK_KIND = "task_kind"
ATTR_TASK_ENTITY_ID = "task_entity_id"
ATTR_SCHEDULED_DATE = "scheduled_date"
ATTR_PERFORMED_AT = "performed_at"
ATTR_DEVIATION_REASON = "deviation_reason"
ATTR_CHECK_RESULT = "check_result"
ATTR_OUTCOME = "outcome"
ATTR_PROVIDER = "provider"
ATTR_DIAGNOSIS = "diagnosis"
ATTR_CARE_ACTION = "care_action"
ATTR_VISIT_REASON = "visit_reason"
ATTR_CHECK_FOCUS = "check_focus"

ATTR_PLANNED_MEDICATION_NAME = "planned_medication_name"
ATTR_PLANNED_DOSE = "planned_dose"
ATTR_PLANNED_DOSE_UNIT = "planned_dose_unit"
ATTR_PLANNED_ROUTE = "planned_route"
ATTR_PLANNED_VACCINATION_TARGETS = "planned_vaccination_targets"
ATTR_PLANNED_CUSTOM_VACCINATION_TARGET = "planned_custom_vaccination_target"
ATTR_PLANNED_VACCINE_NAME = "planned_vaccine_name"
ATTR_PLANNED_ANTIGEN = "planned_antigen"
ATTR_PLANNED_VACCINATION_DOSE = "planned_vaccination_dose"
ATTR_PLANNED_VACCINATION_DOSE_UNIT = "planned_vaccination_dose_unit"
ATTR_PLANNED_VACCINATION_ROUTE = "planned_vaccination_route"
ATTR_PLANNED_CHECK_FOCUS = "planned_check_focus"
ATTR_PLANNED_CARE_ACTION = "planned_care_action"
ATTR_PLANNED_VISIT_REASON = "planned_visit_reason"
ATTR_PLANNED_PROVIDER = "planned_provider"

TASK_RECORDING_FIELDS = {
    ATTR_TASK_KIND,
    ATTR_PLANNED_MEDICATION_NAME,
    ATTR_PLANNED_DOSE,
    ATTR_PLANNED_DOSE_UNIT,
    ATTR_PLANNED_ROUTE,
    ATTR_PLANNED_VACCINATION_TARGETS,
    ATTR_PLANNED_CUSTOM_VACCINATION_TARGET,
    ATTR_PLANNED_VACCINE_NAME,
    ATTR_PLANNED_ANTIGEN,
    ATTR_PLANNED_VACCINATION_DOSE,
    ATTR_PLANNED_VACCINATION_DOSE_UNIT,
    ATTR_PLANNED_VACCINATION_ROUTE,
    ATTR_PLANNED_CHECK_FOCUS,
    ATTR_PLANNED_CARE_ACTION,
    ATTR_PLANNED_VISIT_REASON,
    ATTR_PLANNED_PROVIDER,
}

_RECORD_ID_ALPHABET = "23456789ABCDEFGHJKMNPQRSTVWXYZ"
_RECORD_ID_LENGTH = 7


@dataclass(frozen=True, slots=True)
class TaskRecordingConfig:
    task_id: str
    task_kind: str
    template: dict[str, Any]


@dataclass(frozen=True, slots=True)
class TaskExecutionResult:
    occurrence: dict[str, Any]
    event: dict[str, Any] | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "occurrence": self.occurrence,
            "event": self.event,
        }


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _positive_number(value: Any, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as err:
        raise ValueError(f"{field_name} must be a number") from err
    if number <= 0:
        raise ValueError(f"{field_name} must be greater than zero")
    return number


def _unique_values(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    result: list[str] = []
    for item in values:
        text = _clean_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _set_or_clear(template: dict[str, Any], key: str, data: dict[str, Any], field: str) -> None:
    if field not in data:
        return
    value = data[field]
    if value in (None, "", []):
        template.pop(key, None)
    else:
        template[key] = value


def build_task_template(
    task_kind: str,
    data: dict[str, Any],
    *,
    title: str,
    current: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if task_kind not in TASK_KINDS:
        raise ValueError(f"Unsupported task kind: {task_kind}")

    template = dict(current or {})
    if task_kind == TASK_KIND_REMINDER:
        return {}
    if task_kind == TASK_KIND_WEIGHT:
        return {"measurement": "weight"}

    if task_kind == TASK_KIND_MEDICATION:
        _set_or_clear(
            template,
            "medication_name",
            data,
            ATTR_PLANNED_MEDICATION_NAME,
        )
        _set_or_clear(template, "dose", data, ATTR_PLANNED_DOSE)
        _set_or_clear(template, "dose_unit", data, ATTR_PLANNED_DOSE_UNIT)
        _set_or_clear(template, "route", data, ATTR_PLANNED_ROUTE)
        medication_input = _clean_text(template.get("medication_name"))
        if medication_input is None:
            raise ValueError("A planned medication is required for a medication task")
        medication_name, catalog_data = product_event_metadata(medication_input)
        template["medication_name"] = medication_name
        template["catalog"] = catalog_data
        template["dose"] = _positive_number(template.get("dose"), "Planned dose")
        dose_unit = _clean_text(template.get("dose_unit"))
        if dose_unit not in DOSE_UNITS:
            raise ValueError("A valid planned dose unit is required")
        template["dose_unit"] = dose_unit
        route = _clean_text(template.get("route"))
        if route is not None and route not in ADMINISTRATION_ROUTES:
            raise ValueError(f"Unsupported administration route: {route}")
        if route is None:
            template.pop("route", None)
        else:
            template["route"] = route
        return template

    if task_kind == TASK_KIND_VACCINATION:
        _set_or_clear(
            template,
            "vaccination_targets",
            data,
            ATTR_PLANNED_VACCINATION_TARGETS,
        )
        _set_or_clear(
            template,
            "custom_vaccination_target",
            data,
            ATTR_PLANNED_CUSTOM_VACCINATION_TARGET,
        )
        _set_or_clear(template, "vaccine_name", data, ATTR_PLANNED_VACCINE_NAME)
        _set_or_clear(template, "antigen", data, ATTR_PLANNED_ANTIGEN)
        _set_or_clear(template, "dose", data, ATTR_PLANNED_VACCINATION_DOSE)
        _set_or_clear(
            template,
            "dose_unit",
            data,
            ATTR_PLANNED_VACCINATION_DOSE_UNIT,
        )
        _set_or_clear(template, "route", data, ATTR_PLANNED_VACCINATION_ROUTE)

        targets = _unique_values(template.get("vaccination_targets"))
        if not targets or any(target not in VACCINATION_TARGETS for target in targets):
            raise ValueError("At least one valid planned vaccination target is required")
        custom_target = _clean_text(template.get("custom_vaccination_target"))
        if VACCINATION_TARGET_OTHER in targets and custom_target is None:
            raise ValueError(
                "A custom planned vaccination target is required when 'other' is selected"
            )
        if VACCINATION_TARGET_OTHER not in targets and custom_target is not None:
            raise ValueError(
                "A custom planned vaccination target may only be used with 'other'"
            )
        template["vaccination_targets"] = targets
        if custom_target is None:
            template.pop("custom_vaccination_target", None)
        else:
            template["custom_vaccination_target"] = custom_target

        vaccine_input = _clean_text(template.get("vaccine_name"))
        if vaccine_input is not None:
            vaccine_name, catalog_data = product_event_metadata(vaccine_input, vaccine=True)
            template["vaccine_name"] = vaccine_name
            template["catalog"] = catalog_data
        else:
            template.pop("vaccine_name", None)
            template.pop("catalog", None)

        dose = template.get("dose")
        dose_unit = _clean_text(template.get("dose_unit"))
        if dose is None and dose_unit is not None:
            raise ValueError("Planned vaccination dose and unit must be supplied together")
        if dose is not None and dose_unit is None:
            raise ValueError("Planned vaccination dose and unit must be supplied together")
        if dose is not None:
            template["dose"] = _positive_number(dose, "Planned vaccination dose")
            if dose_unit not in DOSE_UNITS:
                raise ValueError("Unsupported planned vaccination dose unit")
            template["dose_unit"] = dose_unit

        route = _clean_text(template.get("route"))
        if route is not None and route not in ADMINISTRATION_ROUTES:
            raise ValueError(f"Unsupported administration route: {route}")
        if route is None:
            template.pop("route", None)
        else:
            template["route"] = route
        antigen = _clean_text(template.get("antigen"))
        if antigen is None:
            template.pop("antigen", None)
        else:
            template["antigen"] = antigen
        return template

    if task_kind == TASK_KIND_HEALTH_CHECK:
        _set_or_clear(template, "check_focus", data, ATTR_PLANNED_CHECK_FOCUS)
        focus = _clean_text(template.get("check_focus"))
        if focus is None:
            template.pop("check_focus", None)
        else:
            template["check_focus"] = focus
        return template

    if task_kind == TASK_KIND_CARE:
        _set_or_clear(template, "care_action", data, ATTR_PLANNED_CARE_ACTION)
        template["care_action"] = _clean_text(template.get("care_action")) or title.strip()
        return template

    if task_kind == TASK_KIND_VETERINARY_VISIT:
        _set_or_clear(template, "visit_reason", data, ATTR_PLANNED_VISIT_REASON)
        _set_or_clear(template, "provider", data, ATTR_PLANNED_PROVIDER)
        template["visit_reason"] = _clean_text(template.get("visit_reason")) or title.strip()
        provider = _clean_text(template.get("provider"))
        if provider is None:
            template.pop("provider", None)
        else:
            template["provider"] = provider
        return template

    raise ValueError(f"Unsupported task kind: {task_kind}")


class TaskRecordStore:
    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._database_path = Path(hass.config.path(DATABASE_NAME))
        timezone = dt_util.get_time_zone(hass.config.time_zone)
        self._timezone = timezone if timezone is not None else ZoneInfo("UTC")

    @property
    def timezone(self) -> ZoneInfo:
        return self._timezone

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    @staticmethod
    def _generate_event_id(connection: sqlite3.Connection) -> str:
        existing_ids = {
            str(row[0]) for row in connection.execute("SELECT id FROM events").fetchall()
        }
        while True:
            suffix = "".join(
                secrets.choice(_RECORD_ID_ALPHABET) for _ in range(_RECORD_ID_LENGTH)
            )
            event_id = f"EV-{suffix}"
            if event_id not in existing_ids:
                return event_id

    @staticmethod
    def _loads(value: Any) -> dict[str, Any]:
        if value in (None, ""):
            return {}
        loaded = json.loads(str(value))
        return loaded if isinstance(loaded, dict) else {}

    async def create_configured_tasks(
        self,
        task_store: TaskStore,
        *,
        animal_ids: list[str | None],
        task_kind: str,
        template: dict[str, Any],
        title: str,
        description: str | None,
        recurrence_type: str,
        recurrence_interval: int,
        start_date: date,
        end_date: date | None,
        due_time: time | None,
    ) -> list[TaskRecord]:
        """Create and configure a batch of tasks in one transaction."""

        def configure_task(connection: sqlite3.Connection, task_id: str) -> None:
            self._configure_task_in_connection(
                connection,
                task_id,
                task_kind,
                template,
            )

        return await task_store.create_tasks(
            animal_ids=animal_ids,
            title=title,
            description=description,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
            start_date=start_date,
            end_date=end_date,
            due_time=due_time,
            configure_task=configure_task,
        )

    async def configure_task(
        self,
        task_id: str,
        task_kind: str,
        template: dict[str, Any],
    ) -> TaskRecordingConfig:
        return await self._hass.async_add_executor_job(
            self._configure_task_sync,
            task_id,
            task_kind,
            template,
        )

    def _configure_task_sync(
        self,
        task_id: str,
        task_kind: str,
        template: dict[str, Any],
    ) -> TaskRecordingConfig:
        if task_kind not in TASK_KINDS:
            raise ValueError(f"Unsupported task kind: {task_kind}")
        with self._connect() as connection:
            return self._configure_task_in_connection(
                connection,
                task_id,
                task_kind,
                template,
            )

    def _configure_task_in_connection(
        self,
        connection: sqlite3.Connection,
        task_id: str,
        task_kind: str,
        template: dict[str, Any],
    ) -> TaskRecordingConfig:
        if task_kind not in TASK_KINDS:
            raise ValueError(f"Unsupported task kind: {task_kind}")
        now = datetime.now(UTC).replace(microsecond=0).isoformat()
        template_json = json.dumps(template, ensure_ascii=False, sort_keys=True)
        task = connection.execute(
            "SELECT animal_id FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        if task is None:
            raise KeyError(task_id)
        if task_kind != TASK_KIND_REMINDER and task["animal_id"] is None:
            raise ValueError("Only reminder tasks may be general tasks")
        connection.execute(
            """
            INSERT INTO task_record_configs (
                task_id, task_kind, template_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                task_kind = excluded.task_kind,
                template_json = excluded.template_json,
                updated_at = excluded.updated_at
            """,
            (task_id, task_kind, template_json, now, now),
        )
        self._sync_occurrence_plans(connection, task_id, now)
        return TaskRecordingConfig(task_id, task_kind, dict(template))

    @staticmethod
    def _sync_occurrence_plans(
        connection: sqlite3.Connection,
        task_id: str,
        now: str,
    ) -> None:
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
            WHERE occurrence.task_id = ?
            """,
            (now, now, task_id),
        )

    async def get_task_config(self, task_id: str) -> TaskRecordingConfig:
        return await self._hass.async_add_executor_job(self._get_task_config_sync, task_id)

    def _get_task_config_sync(self, task_id: str) -> TaskRecordingConfig:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT task.id, config.task_kind, config.template_json
                FROM tasks AS task
                LEFT JOIN task_record_configs AS config ON config.task_id = task.id
                WHERE task.id = ?
                """,
                (task_id,),
            ).fetchone()
        if row is None:
            raise KeyError(task_id)
        return TaskRecordingConfig(
            task_id=str(row["id"]),
            task_kind=str(row["task_kind"] or TASK_KIND_REMINDER),
            template=self._loads(row["template_json"]),
        )

    async def resolve_occurrence(
        self,
        task_id: str,
        scheduled_date: date | None,
    ) -> str:
        return await self._hass.async_add_executor_job(
            self._resolve_occurrence_sync,
            task_id,
            scheduled_date,
        )

    def _resolve_occurrence_sync(
        self,
        task_id: str,
        scheduled_date: date | None,
    ) -> str:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT occurrence.id, occurrence.scheduled_for
                FROM task_occurrences AS occurrence
                WHERE occurrence.task_id = ?
                  AND occurrence.status = 'pending'
                ORDER BY occurrence.scheduled_for
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

    async def enrich_tasks(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return await self._hass.async_add_executor_job(self._enrich_tasks_sync, tasks)

    def _enrich_tasks_sync(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not tasks:
            return []
        now_utc = datetime.now(UTC).replace(microsecond=0)
        local_day_start = datetime.combine(
            now_utc.astimezone(self._timezone).date(),
            time.min,
            tzinfo=self._timezone,
        ).astimezone(UTC)
        enriched: list[dict[str, Any]] = []
        with self._connect() as connection:
            for task in tasks:
                row = connection.execute(
                    """
                    SELECT
                        COALESCE(config.task_kind, 'reminder') AS task_kind,
                        COALESCE(config.template_json, '{}') AS template_json,
                        (
                            SELECT COUNT(*)
                            FROM task_occurrences AS occurrence
                            JOIN tasks AS source_task ON source_task.id = occurrence.task_id
                            WHERE occurrence.task_id = ?
                              AND occurrence.status = 'pending'
                              AND (
                                  (source_task.due_time IS NOT NULL AND occurrence.scheduled_for < ?)
                                  OR
                                  (source_task.due_time IS NULL AND occurrence.scheduled_for < ?)
                              )
                        ) AS corrected_overdue_count
                    FROM tasks AS task
                    LEFT JOIN task_record_configs AS config ON config.task_id = task.id
                    WHERE task.id = ?
                    """,
                    (
                        task["id"],
                        now_utc.isoformat(),
                        local_day_start.isoformat(),
                        task["id"],
                    ),
                ).fetchone()
                item = dict(task)
                if row is not None:
                    item["task_kind"] = str(row["task_kind"])
                    item["planned"] = self._loads(row["template_json"])
                    item["overdue_count"] = int(row["corrected_overdue_count"] or 0)
                enriched.append(item)
        return enriched

    async def enrich_occurrences(
        self,
        occurrences: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return await self._hass.async_add_executor_job(
            self._enrich_occurrences_sync,
            occurrences,
        )

    def _enrich_occurrences_sync(
        self,
        occurrences: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not occurrences:
            return []
        now = datetime.now(UTC).replace(microsecond=0).isoformat()
        enriched: list[dict[str, Any]] = []
        with self._connect() as connection:
            task_ids = {str(item["task_id"]) for item in occurrences}
            for task_id in task_ids:
                self._sync_occurrence_plans(connection, task_id, now)
            for occurrence in occurrences:
                row = connection.execute(
                    """
                    SELECT
                        COALESCE(config.task_kind, 'reminder') AS task_kind,
                        COALESCE(plan.planned_json, config.template_json, '{}') AS planned_json,
                        plan.resolved_at
                    FROM task_occurrences AS occurrence
                    JOIN tasks AS task ON task.id = occurrence.task_id
                    LEFT JOIN task_record_configs AS config ON config.task_id = task.id
                    LEFT JOIN task_occurrence_plans AS plan ON plan.occurrence_id = occurrence.id
                    WHERE occurrence.id = ?
                    """,
                    (occurrence["id"],),
                ).fetchone()
                item = dict(occurrence)
                if row is not None:
                    item["task_kind"] = str(row["task_kind"])
                    item["planned"] = self._loads(row["planned_json"])
                    item["resolved_at"] = row["resolved_at"]
                enriched.append(item)
        return enriched

    async def mark_resolved(self, occurrence_id: str, resolved_at: datetime) -> None:
        await self._hass.async_add_executor_job(
            self._mark_resolved_sync,
            occurrence_id,
            resolved_at,
        )

    def _mark_resolved_sync(self, occurrence_id: str, resolved_at: datetime) -> None:
        resolved = resolved_at.astimezone(UTC).replace(microsecond=0).isoformat()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT task_id FROM task_occurrences WHERE id = ?",
                (occurrence_id,),
            ).fetchone()
            if row is None:
                raise KeyError(occurrence_id)
            self._sync_occurrence_plans(connection, str(row["task_id"]), resolved)
            connection.execute(
                """
                UPDATE task_occurrence_plans
                SET resolved_at = ?, updated_at = ?
                WHERE occurrence_id = ?
                """,
                (resolved, resolved, occurrence_id),
            )

    async def execute(
        self,
        *,
        occurrence_id: str,
        expected_kind: str,
        performed_at: datetime,
        actual: dict[str, Any],
        notes: str | None,
        deviation_reason: str | None,
        event_type: str | None,
        event_title: str | None,
        event_value: float | None = None,
        event_unit: str | None = None,
        event_data: dict[str, Any] | None = None,
    ) -> TaskExecutionResult:
        return await self._hass.async_add_executor_job(
            self._execute_sync,
            occurrence_id,
            expected_kind,
            performed_at,
            actual,
            notes,
            deviation_reason,
            event_type,
            event_title,
            event_value,
            event_unit,
            event_data,
        )

    def _execute_sync(
        self,
        occurrence_id: str,
        expected_kind: str,
        performed_at: datetime,
        actual: dict[str, Any],
        notes: str | None,
        deviation_reason: str | None,
        event_type: str | None,
        event_title: str | None,
        event_value: float | None,
        event_unit: str | None,
        event_data: dict[str, Any] | None,
    ) -> TaskExecutionResult:
        if expected_kind not in TASK_KINDS:
            raise ValueError(f"Unsupported task kind: {expected_kind}")
        if performed_at.tzinfo is None:
            performed_at = performed_at.replace(tzinfo=self._timezone)
        performed_at = performed_at.astimezone(UTC).replace(microsecond=0)
        now = datetime.now(UTC).replace(microsecond=0).isoformat()

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    occurrence.id,
                    occurrence.task_id,
                    occurrence.scheduled_for,
                    occurrence.status,
                    occurrence.completed_at,
                    occurrence.notes,
                    occurrence.created_at,
                    occurrence.updated_at,
                    task.animal_id,
                    animal.name AS animal_name,
                    task.title AS task_title,
                    task.due_time,
                    task.is_active AS task_is_active,
                    COALESCE(config.task_kind, 'reminder') AS task_kind,
                    COALESCE(config.template_json, '{}') AS template_json,
                    plan.planned_json,
                    plan.resolved_at
                FROM task_occurrences AS occurrence
                JOIN tasks AS task ON task.id = occurrence.task_id
                LEFT JOIN animals AS animal ON animal.id = task.animal_id
                LEFT JOIN task_record_configs AS config ON config.task_id = task.id
                LEFT JOIN task_occurrence_plans AS plan ON plan.occurrence_id = occurrence.id
                WHERE occurrence.id = ?
                """,
                (occurrence_id,),
            ).fetchone()
            if row is None:
                raise KeyError(occurrence_id)
            if str(row["status"]) != "pending":
                raise ValueError("Only pending task occurrences can be recorded")
            task_kind = str(row["task_kind"])
            if task_kind != expected_kind:
                raise ValueError(
                    f"This occurrence is a '{task_kind}' task, not a '{expected_kind}' task"
                )

            self._sync_occurrence_plans(connection, str(row["task_id"]), now)
            plan_row = connection.execute(
                "SELECT planned_json FROM task_occurrence_plans WHERE occurrence_id = ?",
                (occurrence_id,),
            ).fetchone()
            planned = self._loads(
                plan_row["planned_json"] if plan_row is not None else row["template_json"]
            )

            scheduled_for = datetime.fromisoformat(str(row["scheduled_for"]))
            scheduled_local = scheduled_for.astimezone(self._timezone)
            performed_local = performed_at.astimezone(self._timezone)
            if row["due_time"] is None:
                day_difference = (performed_local.date() - scheduled_local.date()).days
                timing_status = (
                    TIMING_EARLY
                    if day_difference < 0
                    else TIMING_LATE
                    if day_difference > 0
                    else TIMING_ON_TIME
                )
                deviation_minutes = day_difference * 1440
            else:
                difference_seconds = (performed_at - scheduled_for).total_seconds()
                timing_status = (
                    TIMING_EARLY
                    if difference_seconds < 0
                    else TIMING_LATE
                    if difference_seconds > 0
                    else TIMING_ON_TIME
                )
                deviation_minutes = round(difference_seconds / 60)

            event: HealthEvent | None = None
            if expected_kind != TASK_KIND_REMINDER:
                animal_id = row["animal_id"]
                if animal_id is None:
                    raise ValueError("A record-linked task must belong to an animal")
                if event_type not in EVENT_TYPES or event_title is None:
                    raise ValueError("A valid event type and title are required")
                if (event_value is None) != (event_unit is None):
                    raise ValueError("Event value and unit must be supplied together")
                linked = connection.execute(
                    "SELECT id FROM events WHERE task_occurrence_id = ?",
                    (occurrence_id,),
                ).fetchone()
                if linked is not None:
                    raise ValueError("This task occurrence already has a linked record")

                task_execution = {
                    "source": "task_occurrence",
                    "task_id": str(row["task_id"]),
                    "task_title": str(row["task_title"]),
                    "task_kind": task_kind,
                    "occurrence_id": occurrence_id,
                    "scheduled_for": scheduled_for.isoformat(),
                    "scheduled_local": scheduled_local.isoformat(),
                    "performed_at": performed_at.isoformat(),
                    "performed_local": performed_local.isoformat(),
                    "timing_status": timing_status,
                    "timing_deviation_minutes": deviation_minutes,
                    "deviation_reason": _clean_text(deviation_reason),
                    "planned": planned,
                    "actual": actual,
                }
                data = dict(event_data or {})
                data["task_execution"] = task_execution
                data["planned"] = planned
                data["actual"] = actual
                data["timing_status"] = timing_status
                data["timing_deviation_minutes"] = deviation_minutes
                if reason := _clean_text(deviation_reason):
                    data["deviation_reason"] = reason

                event_id = self._generate_event_id(connection)
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
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        str(animal_id),
                        event_type,
                        performed_at.isoformat(),
                        event_title.strip(),
                        _clean_text(notes),
                        event_value,
                        event_unit,
                        json.dumps(data, ensure_ascii=False, sort_keys=True),
                        str(row["task_id"]),
                        occurrence_id,
                        now,
                    ),
                )
                event_row = connection.execute(
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
                if event_row is None:
                    raise RuntimeError("Linked event could not be loaded")
                event = HealthEvent.from_mapping(event_row)

            connection.execute(
                """
                UPDATE task_occurrences
                SET status = 'completed',
                    completed_at = ?,
                    notes = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    performed_at.isoformat(),
                    _clean_text(notes),
                    now,
                    occurrence_id,
                ),
            )
            connection.execute(
                """
                UPDATE task_occurrence_plans
                SET resolved_at = ?, updated_at = ?
                WHERE occurrence_id = ?
                """,
                (performed_at.isoformat(), now, occurrence_id),
            )
            updated = connection.execute(
                """
                SELECT
                    occurrence.id,
                    occurrence.task_id,
                    occurrence.scheduled_for,
                    occurrence.status,
                    occurrence.completed_at,
                    occurrence.notes,
                    occurrence.created_at,
                    occurrence.updated_at,
                    task.animal_id,
                    animal.name AS animal_name,
                    task.title AS task_title,
                    task.is_active AS task_is_active,
                    COALESCE(config.task_kind, 'reminder') AS task_kind,
                    COALESCE(plan.planned_json, '{}') AS planned_json,
                    plan.resolved_at
                FROM task_occurrences AS occurrence
                JOIN tasks AS task ON task.id = occurrence.task_id
                LEFT JOIN animals AS animal ON animal.id = task.animal_id
                LEFT JOIN task_record_configs AS config ON config.task_id = task.id
                LEFT JOIN task_occurrence_plans AS plan ON plan.occurrence_id = occurrence.id
                WHERE occurrence.id = ?
                """,
                (occurrence_id,),
            ).fetchone()
            if updated is None:
                raise RuntimeError("Completed occurrence could not be loaded")

        local = datetime.fromisoformat(str(updated["scheduled_for"])).astimezone(
            self._timezone
        )
        occurrence = {
            "id": str(updated["id"]),
            "task_id": str(updated["task_id"]),
            "scope": "animal" if updated["animal_id"] is not None else "general",
            "animal_id": (
                str(updated["animal_id"]) if updated["animal_id"] is not None else None
            ),
            "animal_name": (
                str(updated["animal_name"])
                if updated["animal_name"] is not None
                else None
            ),
            "task_title": str(updated["task_title"]),
            "task_kind": str(updated["task_kind"]),
            "planned": self._loads(updated["planned_json"]),
            "actual": actual,
            "scheduled_for": str(updated["scheduled_for"]),
            "scheduled_local": local.isoformat(),
            "scheduled_date": local.date().isoformat(),
            "status": str(updated["status"]),
            "completed_at": updated["completed_at"],
            "resolved_at": updated["resolved_at"],
            "notes": updated["notes"],
            "task_is_active": bool(updated["task_is_active"]),
            "created_at": str(updated["created_at"]),
            "updated_at": str(updated["updated_at"]),
            "timing_status": timing_status,
            "timing_deviation_minutes": deviation_minutes,
            "deviation_reason": _clean_text(deviation_reason),
        }
        return TaskExecutionResult(
            occurrence=occurrence,
            event=event.as_dict() if event is not None else None,
        )


def actual_medication(
    planned: dict[str, Any],
    *,
    medication_name: str | None,
    dose: float | None,
    dose_unit: str | None,
    route: str | None,
) -> tuple[dict[str, Any], dict[str, Any], float, str, str]:
    selected_name = _clean_text(medication_name) or _clean_text(
        planned.get("medication_name")
    )
    if selected_name is None:
        raise ValueError("Medication name is required")
    canonical_name, catalog_data = product_event_metadata(selected_name)
    actual_dose = _positive_number(
        dose if dose is not None else planned.get("dose"),
        "Actual dose",
    )
    actual_unit = _clean_text(dose_unit) or _clean_text(planned.get("dose_unit"))
    if actual_unit not in DOSE_UNITS:
        raise ValueError("A valid actual dose unit is required")
    actual_route = _clean_text(route) or _clean_text(planned.get("route"))
    if actual_route is not None and actual_route not in ADMINISTRATION_ROUTES:
        raise ValueError(f"Unsupported administration route: {actual_route}")
    actual = {
        "medication_name": canonical_name,
        "dose": actual_dose,
        "dose_unit": actual_unit,
    }
    event_data = {"medication_name": canonical_name, **catalog_data}
    if actual_route is not None:
        actual["route"] = actual_route
        event_data["route"] = actual_route
    return actual, event_data, actual_dose, actual_unit, canonical_name


def actual_vaccination(
    planned: dict[str, Any],
    *,
    vaccination_targets: list[str] | None,
    custom_target: str | None,
    vaccine_name: str | None,
    antigen: str | None,
    dose: float | None,
    dose_unit: str | None,
    route: str | None,
    batch_number: str | None,
) -> tuple[dict[str, Any], dict[str, Any], float, str, str]:
    targets = _unique_values(vaccination_targets) or _unique_values(
        planned.get("vaccination_targets")
    )
    if not targets or any(target not in VACCINATION_TARGETS for target in targets):
        raise ValueError("At least one valid vaccination target is required")
    actual_custom = _clean_text(custom_target) or _clean_text(
        planned.get("custom_vaccination_target")
    )
    if VACCINATION_TARGET_OTHER in targets and actual_custom is None:
        raise ValueError("A custom vaccination target is required with 'other'")
    if VACCINATION_TARGET_OTHER not in targets and actual_custom is not None:
        raise ValueError("A custom vaccination target may only be used with 'other'")

    selected_vaccine = _clean_text(vaccine_name) or _clean_text(planned.get("vaccine_name"))
    if selected_vaccine is not None:
        canonical_vaccine, catalog_data = product_event_metadata(
            selected_vaccine,
            vaccine=True,
        )
    else:
        canonical_vaccine = None
        catalog_data = {
            "catalog_source": "not_specified",
            "catalog_scope": "not_specified",
            "catalog_id": None,
        }
    actual_dose = _positive_number(
        dose if dose is not None else planned.get("dose"),
        "Actual vaccination dose",
    )
    actual_unit = _clean_text(dose_unit) or _clean_text(planned.get("dose_unit"))
    if actual_unit not in DOSE_UNITS:
        raise ValueError("A valid actual vaccination dose unit is required")
    actual_route = _clean_text(route) or _clean_text(planned.get("route"))
    if actual_route is not None and actual_route not in ADMINISTRATION_ROUTES:
        raise ValueError(f"Unsupported administration route: {actual_route}")
    actual_antigen = _clean_text(antigen) or _clean_text(planned.get("antigen"))
    actual_batch = _clean_text(batch_number)

    actual: dict[str, Any] = {
        "vaccination_targets": targets,
        "dose": actual_dose,
        "dose_unit": actual_unit,
    }
    event_data: dict[str, Any] = {
        "vaccination_targets": targets,
        **catalog_data,
    }
    if actual_custom is not None:
        actual["custom_vaccination_target"] = actual_custom
        event_data["custom_vaccination_target"] = actual_custom
    if canonical_vaccine is not None:
        actual["vaccine_name"] = canonical_vaccine
        event_data["vaccine_name"] = canonical_vaccine
    if actual_antigen is not None:
        actual["antigen"] = actual_antigen
        event_data["antigen"] = actual_antigen
    if actual_route is not None:
        actual["route"] = actual_route
        event_data["route"] = actual_route
    if actual_batch is not None:
        actual["batch_number"] = actual_batch
        event_data["batch_number"] = actual_batch
    return (
        actual,
        event_data,
        actual_dose,
        actual_unit,
        canonical_vaccine or "vaccination",
    )


def actual_health_check(
    *,
    result: str,
    symptom: str | None,
    custom_symptom: str | None,
    severity: str | None,
    notes: str | None,
) -> tuple[dict[str, Any], str, str, dict[str, Any]]:
    if result not in HEALTH_CHECK_RESULTS:
        raise ValueError(f"Unsupported health-check result: {result}")
    actual: dict[str, Any] = {"result": result}
    if result == HEALTH_CHECK_SYMPTOM:
        selected_symptom = _clean_text(symptom)
        if selected_symptom not in SYMPTOMS:
            raise ValueError("A valid symptom is required")
        actual_symptom = (
            _clean_text(custom_symptom)
            if selected_symptom == SYMPTOM_OTHER
            else selected_symptom
        )
        if actual_symptom is None:
            raise ValueError("A custom symptom is required with 'other'")
        if selected_symptom != SYMPTOM_OTHER and _clean_text(custom_symptom) is not None:
            raise ValueError("A custom symptom may only be used with 'other'")
        actual_severity = _clean_text(severity) or "moderate"
        if actual_severity not in SYMPTOM_SEVERITIES:
            raise ValueError("A valid symptom severity is required")
        actual.update(
            {
                "symptom": actual_symptom,
                "severity": actual_severity,
            }
        )
        event_data = {
            "symptom": actual_symptom,
            "severity": actual_severity,
            "catalog_source": (
                "custom" if selected_symptom == SYMPTOM_OTHER else "builtin"
            ),
            "health_check_result": result,
        }
        if selected_symptom != SYMPTOM_OTHER:
            event_data["catalog_id"] = selected_symptom
        return actual, "symptom", actual_symptom, event_data

    if symptom is not None or custom_symptom is not None or severity is not None:
        raise ValueError("Symptom fields may only be used when a symptom was found")
    title = "health_check_normal" if result == HEALTH_CHECK_NORMAL else "health_check_concern"
    event_data = {"health_check_result": result}
    if note := _clean_text(notes):
        actual["notes"] = note
    return actual, "observation", title, event_data
