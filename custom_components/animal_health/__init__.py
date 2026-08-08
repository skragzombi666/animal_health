from __future__ import annotations

from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DATABASE_NAME, DOMAIN
from .coordinator import AnimalHealthCoordinator
from .dashboard_api import async_setup_dashboard_api
from .database import AnimalHealthDatabase
from .feature_api import async_setup_feature_api
from .feature_store import AnimalHealthFeatureStore
from .group_lifecycle import (
    async_initialize_group_lifecycle_store,
    async_setup_group_lifecycle_api,
)
from .panel import async_register_panel, async_unregister_panel
from .runtime import AnimalHealthRuntimeData
from .services import async_setup_services
from .task_record_creation import async_setup_task_record_creation
from .task_record_schema import async_initialize_task_record_schema
from .task_record_services import async_setup_task_record_services
from .task_service_schema import async_setup_task_service_descriptions
from .task_services import async_setup_task_services
from .task_stabilization import apply_task_stabilization

PLATFORMS = [
    Platform.SENSOR,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.SWITCH,
]

type AnimalHealthConfigEntry = ConfigEntry[AnimalHealthRuntimeData]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    apply_task_stabilization()
    async_setup_services(hass)
    async_setup_task_services(hass)
    async_setup_task_record_creation(hass)
    async_setup_task_record_services(hass)
    async_setup_task_service_descriptions(hass)
    async_setup_dashboard_api(hass)
    async_setup_feature_api(hass)
    async_setup_group_lifecycle_api(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: AnimalHealthConfigEntry) -> bool:
    apply_task_stabilization()
    database_path = Path(hass.config.path(DATABASE_NAME))
    database = AnimalHealthDatabase(hass, database_path)
    await database.initialize()
    await async_initialize_task_record_schema(hass)

    feature_store = AnimalHealthFeatureStore(
        hass,
        database_path,
        Path(hass.config.path(".storage", DOMAIN, "attachments")),
    )
    await feature_store.initialize()
    await async_initialize_group_lifecycle_store(feature_store)

    coordinator = AnimalHealthCoordinator(hass, database)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = AnimalHealthRuntimeData(
        database=database,
        coordinator=coordinator,
        feature_store=feature_store,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_register_panel(hass)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AnimalHealthConfigEntry,
) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        async_unregister_panel(hass)
    return unload_ok
