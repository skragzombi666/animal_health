from __future__ import annotations

from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DATABASE_NAME
from .coordinator import AnimalHealthCoordinator
from .database import AnimalHealthDatabase
from .runtime import AnimalHealthRuntimeData
from .services import async_setup_services
from .task_records import (
    async_initialize_task_records,
    async_setup_task_record_services,
)
from .task_service_schema import async_setup_task_service_descriptions
from .task_services import async_setup_task_services

PLATFORMS = [
    Platform.SENSOR,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.SWITCH,
]

type AnimalHealthConfigEntry = ConfigEntry[AnimalHealthRuntimeData]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    async_setup_services(hass)
    async_setup_task_services(hass)
    async_setup_task_service_descriptions(hass)
    async_setup_task_record_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: AnimalHealthConfigEntry) -> bool:
    database_path = Path(hass.config.path(DATABASE_NAME))
    database = AnimalHealthDatabase(hass, database_path)
    await database.initialize()
    await async_initialize_task_records(hass)

    coordinator = AnimalHealthCoordinator(hass, database)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = AnimalHealthRuntimeData(
        database=database,
        coordinator=coordinator,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AnimalHealthConfigEntry,
) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
