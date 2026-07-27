from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .database import AnimalHealthDatabase
from .latest_weight import LatestWeight, async_get_latest_weights
from .models import Animal
from .task_store import TASK_ACTIVE_ALL, TASK_SCOPE_ALL, TaskRecord, TaskStore

_LOGGER = logging.getLogger(__name__)


class AnimalHealthCoordinator(DataUpdateCoordinator[dict[str, Animal]]):
    def __init__(
        self,
        hass: HomeAssistant,
        database: AnimalHealthDatabase,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,
            always_update=True,
        )
        self.database = database
        self.task_store = TaskStore(hass)
        self.latest_weights: dict[str, LatestWeight] = {}
        self.tasks: dict[str, TaskRecord] = {}

    async def _async_update_data(self) -> dict[str, Animal]:
        animals = await self.database.get_animals()
        self.latest_weights = await async_get_latest_weights(self.hass)
        tasks = await self.task_store.list_tasks(
            scope=TASK_SCOPE_ALL,
            animal_id=None,
            active_state=TASK_ACTIVE_ALL,
            limit=10000,
        )
        self.tasks = {task.id: task for task in tasks}
        return {animal.id: animal for animal in animals}
