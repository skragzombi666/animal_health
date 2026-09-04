from __future__ import annotations

import calendar
import importlib.util
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from types import ModuleType
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FEATURES = INTEGRATION / "v0941_features.py"
TIMEZONE = ZoneInfo("Europe/Zurich")


@dataclass(frozen=True, slots=True)
class TaskRecord:
    id: str
    animal_id: str | None
    animal_name: str | None
    title: str
    description: str | None
    recurrence_type: str
    recurrence_interval: int
    start_date: date
    end_date: date | None
    due_time: time | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    next_pending_at: datetime | None = None
    pending_count: int = 0
    overdue_count: int = 0


class TaskStore:
    def __init__(
        self,
        connection,
        *,
        today: date = date(2026, 9, 4),
        timezone: ZoneInfo = TIMEZONE,
    ) -> None:
        self.connection = connection
        self._today = today
        self._timezone = timezone

    @property
    def timezone(self) -> ZoneInfo:
        return self._timezone

    def local_today(self) -> date:
        return self._today

    @staticmethod
    def _add_months(anchor: date, months: int) -> date:
        month_index = anchor.year * 12 + anchor.month - 1 + months
        year, zero_based_month = divmod(month_index, 12)
        month = zero_based_month + 1
        return date(
            year,
            month,
            min(anchor.day, calendar.monthrange(year, month)[1]),
        )

    @staticmethod
    def _generate_record_id(prefix: str, existing_ids: set[str]) -> str:
        index = 1
        while f"{prefix}-{index}" in existing_ids:
            index += 1
        return f"{prefix}-{index}"

    def _scheduled_for_utc(
        self,
        occurrence_date: date,
        due_time: time | None,
    ) -> datetime:
        return datetime.combine(
            occurrence_date,
            due_time or time.min,
            tzinfo=self._timezone,
        ).astimezone(UTC).replace(microsecond=0)


def _period_bounds(
    recurrence_type: str,
    scheduled_date: date,
    *,
    week_start: str | None = None,
) -> tuple[date, date]:
    if recurrence_type == "weekly":
        names = (
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        )
        start_index = names.index(week_start or "monday")
        offset = (scheduled_date.weekday() - start_index) % 7
        start = scheduled_date - timedelta(days=offset)
        return start, start + timedelta(days=6)
    if recurrence_type == "monthly":
        return (
            scheduled_date.replace(day=1),
            date(
                scheduled_date.year,
                scheduled_date.month,
                calendar.monthrange(
                    scheduled_date.year,
                    scheduled_date.month,
                )[1],
            ),
        )
    return scheduled_date, scheduled_date


def load_feature_module() -> tuple[ModuleType, ModuleType, type[TaskStore]]:
    package = ModuleType("custom_components")
    package.__path__ = []  # type: ignore[attr-defined]
    animal_health = ModuleType("custom_components.animal_health")
    animal_health.__path__ = [str(INTEGRATION)]  # type: ignore[attr-defined]

    v0815 = ModuleType("custom_components.animal_health.v0815_features")
    v0815._ORIGINAL_ENSURE_OCCURRENCES = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    v0815._initialize_v0815_sync = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    v0815._insert_series_summary = lambda *args, **kwargs: None  # type: ignore[attr-defined]

    confirmation = ModuleType("custom_components.animal_health.confirmation_policy")
    confirmation.CONFIRMATION_REQUIRED = "required"  # type: ignore[attr-defined]
    confirmation.CONFIRMATION_ROUTINE = "routine"  # type: ignore[attr-defined]
    confirmation.OCCURRENCE_NOT_DOCUMENTED = "not_documented"  # type: ignore[attr-defined]
    confirmation.WEEK_START_KEYS = (  # type: ignore[attr-defined]
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    )
    confirmation.recurrence_period_bounds = _period_bounds  # type: ignore[attr-defined]

    task_store = ModuleType("custom_components.animal_health.task_store")
    task_store.MAX_GENERATED_OCCURRENCES = 10000  # type: ignore[attr-defined]
    task_store.OCCURRENCE_PENDING = "pending"  # type: ignore[attr-defined]
    task_store.RECURRENCE_ONCE = "once"  # type: ignore[attr-defined]
    task_store.TaskRecord = TaskRecord  # type: ignore[attr-defined]
    task_store.TaskStore = TaskStore  # type: ignore[attr-defined]
    animal_health.v0815_features = v0815  # type: ignore[attr-defined]

    stubs = {
        "custom_components": package,
        "custom_components.animal_health": animal_health,
        "custom_components.animal_health.v0815_features": v0815,
        "custom_components.animal_health.confirmation_policy": confirmation,
        "custom_components.animal_health.task_store": task_store,
    }
    feature_names = [
        "custom_components.animal_health.v0941_features",
        "custom_components.animal_health.v0941_migration",
        "custom_components.animal_health.v0941_occurrences",
        "custom_components.animal_health.v0941_recurrence",
    ]
    previous = {name: sys.modules.get(name) for name in [*stubs, *feature_names]}
    sys.modules.update(stubs)
    for name in feature_names:
        sys.modules.pop(name, None)
    try:
        spec = importlib.util.spec_from_file_location(feature_names[0], FEATURES)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    finally:
        for name, value in previous.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value
    return module, v0815, TaskStore
