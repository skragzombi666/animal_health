from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, tzinfo
import logging
from typing import Any, cast

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval

from .confirmation_policy import (
    CONFIRMATION_REQUIRED,
    async_resolve_routine_occurrences,
    recurrence_period_bounds,
)
from .const import DOMAIN
from .runtime import AnimalHealthRuntimeData
from .task_store import (
    OCCURRENCE_PENDING,
    TASK_ACTIVE_ALL,
    TASK_SCOPE_ALL,
    TaskOccurrenceRecord,
    TaskRecord,
)

_LOGGER = logging.getLogger(__name__)

CHECK_INTERVAL = timedelta(minutes=15)
EVENT_SERIES_OVERDUE = f"{DOMAIN}_series_overdue"
NOTIFICATION_ID = f"{DOMAIN}_overdue_series"
_STATE_KEY = f"{DOMAIN}_series_alerts"
_LOOKBACK_DAYS = 3650
_MAX_OCCURRENCES = 10000
_MAX_NOTIFICATION_ROWS = 20


def _is_recurring_required(
    task: TaskRecord,
    metadata: dict[str, Any],
) -> bool:
    return (
        task.is_active
        and task.recurrence_type != "once"
        and metadata.get("confirmation_mode", CONFIRMATION_REQUIRED)
        == CONFIRMATION_REQUIRED
    )


def _is_overdue(
    task: TaskRecord,
    occurrence: TaskOccurrenceRecord,
    *,
    today: date,
    timezone: tzinfo,
) -> bool:
    scheduled_date = occurrence.scheduled_for.astimezone(timezone).date()
    _, period_end = recurrence_period_bounds(
        task.recurrence_type,
        scheduled_date,
    )
    return period_end < today


def _task_target(
    task: TaskRecord,
    metadata: dict[str, Any],
    *,
    german: bool,
) -> str:
    if metadata.get("group_name"):
        return str(metadata["group_name"])
    if task.animal_name:
        return task.animal_name
    return "Allgemein" if german else "General"


def _format_local_date(value: datetime, timezone: tzinfo, *, german: bool) -> str:
    local = value.astimezone(timezone)
    return local.strftime("%d.%m.%Y") if german else local.strftime("%Y-%m-%d")


def _notification_text(
    grouped: dict[str, list[TaskOccurrenceRecord]],
    tasks: dict[str, TaskRecord],
    metadata: dict[str, dict[str, Any]],
    *,
    timezone: tzinfo,
    german: bool,
) -> tuple[str, str]:
    count = sum(len(items) for items in grouped.values())
    series_count = len(grouped)
    if german:
        title = "Animal Health: Überfällige Serienbestätigungen"
        intro = (
            f"{count} wirklich überfällige Bestätigung(en) aus "
            f"{series_count} Serie(n)."
        )
    else:
        title = "Animal Health: Overdue recurring confirmations"
        intro = (
            f"{count} confirmation(s) are genuinely overdue across "
            f"{series_count} recurring task(s)."
        )

    rows: list[str] = []
    ordered = sorted(
        grouped.items(),
        key=lambda item: (
            min(occurrence.scheduled_for for occurrence in item[1]),
            tasks[item[0]].title.casefold(),
        ),
    )
    for task_id, occurrences in ordered[:_MAX_NOTIFICATION_ROWS]:
        task = tasks[task_id]
        earliest = min(occurrence.scheduled_for for occurrence in occurrences)
        date_text = _format_local_date(earliest, timezone, german=german)
        target = _task_target(
            task,
            metadata.get(task_id, {}),
            german=german,
        )
        if german:
            rows.append(
                f"- **{task.title}** · {target}: {len(occurrences)} überfällig "
                f"(seit {date_text})"
            )
        else:
            rows.append(
                f"- **{task.title}** · {target}: {len(occurrences)} overdue "
                f"(since {date_text})"
            )
    remaining = max(0, len(ordered) - _MAX_NOTIFICATION_ROWS)
    if remaining:
        rows.append(
            f"- … und {remaining} weitere Serie(n)"
            if german
            else f"- … and {remaining} more recurring task(s)"
        )
    return title, "\n\n".join((intro, "\n".join(rows)))


async def async_check_series_alerts(
    hass: HomeAssistant,
    runtime: AnimalHealthRuntimeData,
    *,
    fire_events: bool,
) -> None:
    state: dict[str, Any] = hass.data.setdefault(_STATE_KEY, {})
    if state.get("running"):
        return
    state["running"] = True
    try:
        store = runtime.coordinator.task_store
        await async_resolve_routine_occurrences(store)
        tasks = await store.list_tasks(
            scope=TASK_SCOPE_ALL,
            animal_id=None,
            active_state=TASK_ACTIVE_ALL,
            limit=10000,
        )
        metadata = runtime.coordinator.task_metadata
        recurring = {
            task.id: task
            for task in tasks
            if _is_recurring_required(task, metadata.get(task.id, {}))
        }
        today = store.local_today()
        grouped: dict[str, list[TaskOccurrenceRecord]] = defaultdict(list)
        if recurring:
            occurrences = await store.list_occurrences(
                task_id=None,
                scope=TASK_SCOPE_ALL,
                animal_id=None,
                status=OCCURRENCE_PENDING,
                start_date=today - timedelta(days=_LOOKBACK_DAYS),
                end_date=today,
                include_general=True,
                limit=_MAX_OCCURRENCES,
            )
            for occurrence in occurrences:
                task = recurring.get(occurrence.task_id)
                if task is None:
                    continue
                if _is_overdue(
                    task,
                    occurrence,
                    today=today,
                    timezone=store.timezone,
                ):
                    grouped[task.id].append(occurrence)

        signature = tuple(
            sorted(
                (
                    task_id,
                    recurring[task_id].title,
                    tuple(sorted(occurrence.id for occurrence in occurrences)),
                )
                for task_id, occurrences in grouped.items()
            )
        )
        previous_signature = state.get("signature")
        current_occurrence_ids = {
            occurrence.id
            for occurrences in grouped.values()
            for occurrence in occurrences
        }
        previous_occurrence_ids = set(state.get("occurrence_ids", ()))
        german = str(getattr(hass.config, "language", "de") or "de").startswith("de")

        if grouped:
            if signature != previous_signature:
                title, message = _notification_text(
                    grouped,
                    recurring,
                    metadata,
                    timezone=store.timezone,
                    german=german,
                )
                persistent_notification.async_create(
                    hass,
                    message,
                    title,
                    NOTIFICATION_ID,
                )
        else:
            persistent_notification.async_dismiss(hass, NOTIFICATION_ID)

        if fire_events and state.get("initialized"):
            new_ids = current_occurrence_ids - previous_occurrence_ids
            if new_ids:
                for task_id, occurrences in grouped.items():
                    new_occurrences = [
                        occurrence for occurrence in occurrences if occurrence.id in new_ids
                    ]
                    if not new_occurrences:
                        continue
                    task = recurring[task_id]
                    item_metadata = metadata.get(task_id, {})
                    hass.bus.async_fire(
                        EVENT_SERIES_OVERDUE,
                        {
                            "task_id": task.id,
                            "title": task.title,
                            "animal_id": task.animal_id,
                            "animal_name": task.animal_name,
                            "group_id": item_metadata.get("group_id"),
                            "group_name": item_metadata.get("group_name"),
                            "confirmation_mode": CONFIRMATION_REQUIRED,
                            "occurrence_ids": [
                                occurrence.id for occurrence in new_occurrences
                            ],
                            "new_overdue_count": len(new_occurrences),
                            "total_overdue_count": len(occurrences),
                            "earliest_scheduled_for": min(
                                occurrence.scheduled_for for occurrence in occurrences
                            ).isoformat(),
                        },
                    )

        state["signature"] = signature
        state["occurrence_ids"] = tuple(sorted(current_occurrence_ids))
        state["initialized"] = True
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Failed to update recurring-series alerts")
    finally:
        state["running"] = False


async def async_setup_series_alerts(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    runtime = cast(AnimalHealthRuntimeData, entry.runtime_data)
    await async_check_series_alerts(hass, runtime, fire_events=False)

    async def _scheduled_check(_now: datetime) -> None:
        await async_check_series_alerts(hass, runtime, fire_events=True)

    entry.async_on_unload(
        async_track_time_interval(hass, _scheduled_check, CHECK_INTERVAL)
    )

    @callback
    def _coordinator_updated() -> None:
        hass.async_create_task(
            async_check_series_alerts(hass, runtime, fire_events=True),
            f"{DOMAIN} recurring-series alert refresh",
        )

    entry.async_on_unload(runtime.coordinator.async_add_listener(_coordinator_updated))
