from __future__ import annotations

from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .ai_assist import async_setup_ai_assist
from .const import DATABASE_NAME, DOMAIN
from .coordinator import AnimalHealthCoordinator
from .dashboard_api import async_setup_dashboard_api
from .database import AnimalHealthDatabase
from .download_stabilization import apply_download_stabilization
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
from .v080_features import async_initialize_v080_features, async_setup_v080_features
from .v080_task_policy import async_setup_v080_task_policy
from .v080_weight import async_setup_v080_weight_api
from .v081_features import _initialize_sync, async_setup_v081_features
from .v081_fixes import async_setup_v081_fixes
from .v081_stt import async_setup_v081_stt
from .v0815_features import apply_v0815_patches, async_initialize_v0815_features
from .v0816_features import apply_v0816_patches
from .v082_features import apply_v082_patches, async_setup_v082_features
from .v083_features import async_initialize_v083_features, async_setup_v083_features
from .v084_features import async_setup_v084_features
from .v086_features import async_setup_v086_features
from .v088_features import async_setup_v088_features

PLATFORMS = [
    Platform.SENSOR,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.SWITCH,
]

type AnimalHealthConfigEntry = ConfigEntry[AnimalHealthRuntimeData]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    apply_v082_patches()
    apply_v0815_patches()
    apply_v0816_patches()
    apply_task_stabilization()
    apply_download_stabilization()
    async_setup_services(hass)
    async_setup_task_services(hass)
    async_setup_task_record_creation(hass)
    async_setup_task_record_services(hass)
    async_setup_v080_task_policy(hass)
    async_setup_task_service_descriptions(hass)
    async_setup_dashboard_api(hass)
    async_setup_feature_api(hass)
    async_setup_group_lifecycle_api(hass)
    async_setup_v080_features(hass)
    async_setup_v080_weight_api(hass)
    async_setup_v081_features(hass)
    async_setup_v081_fixes(hass)
    async_setup_v081_stt(hass)
    async_setup_v082_features(hass)
    async_setup_v083_features(hass)
    async_setup_v084_features(hass)
    async_setup_v086_features(hass)
    async_setup_v088_features(hass)
    async_setup_ai_assist(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: AnimalHealthConfigEntry) -> bool:
    apply_v082_patches()
    apply_v0815_patches()
    apply_v0816_patches()
    apply_task_stabilization()
    apply_download_stabilization()
    database_path = Path(hass.config.path(DATABASE_NAME))
    database = AnimalHealthDatabase(hass, database_path)
    await database.initialize()
    await async_initialize_task_record_schema(hass)
    await async_initialize_v0815_features(hass)

    feature_store = AnimalHealthFeatureStore(
        hass,
        database_path,
        Path(hass.config.path(".storage", DOMAIN, "attachments")),
    )
    await feature_store.initialize()
    await async_initialize_group_lifecycle_store(feature_store)
    await async_initialize_v080_features(feature_store)
    await hass.async_add_executor_job(_initialize_sync, database_path)
    await async_initialize_v083_features(feature_store)

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
