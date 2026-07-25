from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .database import AnimalHealthDatabase
from .models import Animal

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
            always_update=False,
        )
        self.database = database

    async def _async_update_data(self) -> dict[str, Animal]:
        animals = await self.database.get_animals()
        return {animal.id: animal for animal in animals}
