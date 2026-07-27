from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AnimalHealthConfigEntry
from .const import DOMAIN, NAME
from .coordinator import AnimalHealthCoordinator
from .task_store import TASK_SCOPE_ANIMAL, TASK_SCOPE_GENERAL, TaskRecord

GENERAL_TASKS_DEVICE_ID = "general_tasks"
TASK_SWITCH_UNIQUE_ID_PREFIX = "task_active_"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AnimalHealthConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    known_task_ids: set[str] = set()

    @callback
    def add_new_task_entities() -> None:
        new_task_ids = set(coordinator.tasks) - known_task_ids
        if not new_task_ids:
            return
        known_task_ids.update(new_task_ids)
        async_add_entities(
            TaskActiveSwitch(coordinator, task_id)
            for task_id in sorted(new_task_ids)
        )

    add_new_task_entities()
    entry.async_on_unload(coordinator.async_add_listener(add_new_task_entities))


class TaskActiveSwitch(
    CoordinatorEntity[AnimalHealthCoordinator],
    SwitchEntity,
):
    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-check"

    def __init__(
        self,
        coordinator: AnimalHealthCoordinator,
        task_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._task_id = task_id
        self._attr_unique_id = f"{TASK_SWITCH_UNIQUE_ID_PREFIX}{task_id}"

    @property
    def task(self) -> TaskRecord | None:
        return self.coordinator.tasks.get(self._task_id)

    @property
    def task_metadata(self) -> dict[str, Any]:
        return self.coordinator.task_metadata.get(self._task_id, {})

    @property
    def available(self) -> bool:
        return super().available and self.task is not None

    @property
    def name(self) -> str | None:
        task = self.task
        return task.title if task else None

    @property
    def is_on(self) -> bool | None:
        task = self.task
        return task.is_active if task else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.task_store.set_task_active(self._task_id, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.task_store.set_task_active(self._task_id, False)
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self) -> DeviceInfo | None:
        task = self.task
        if task is None:
            return None
        if task.animal_id is not None:
            return DeviceInfo(identifiers={(DOMAIN, task.animal_id)})
        return DeviceInfo(
            identifiers={(DOMAIN, GENERAL_TASKS_DEVICE_ID)},
            name="Allgemeine Aufgaben",
            manufacturer=NAME,
            model="Aufgaben",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        task = self.task
        if task is None:
            return {"task_id": self._task_id}
        metadata = self.task_metadata
        return {
            "task_id": task.id,
            "task_kind": metadata.get("task_kind", "reminder"),
            "planned": metadata.get("planned", {}),
            "scope": TASK_SCOPE_ANIMAL if task.animal_id else TASK_SCOPE_GENERAL,
            "animal_id": task.animal_id,
            "animal_name": task.animal_name,
            "description": task.description,
            "recurrence_type": task.recurrence_type,
            "recurrence_interval": task.recurrence_interval,
            "start_date": task.start_date.isoformat(),
            "end_date": task.end_date.isoformat() if task.end_date else None,
            "due_time": (
                task.due_time.isoformat(timespec="minutes")
                if task.due_time
                else None
            ),
            "next_pending_local": (
                task.next_pending_at.astimezone(
                    self.coordinator.task_store.timezone
                ).isoformat()
                if task.next_pending_at
                else None
            ),
            "pending_count": task.pending_count,
            "overdue_count": metadata.get("overdue_count", task.overdue_count),
        }
