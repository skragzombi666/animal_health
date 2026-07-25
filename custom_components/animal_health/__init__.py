from __future__ import annotations

from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATABASE_NAME, DOMAIN
from .database import AnimalHealthDatabase


type AnimalHealthConfigEntry = ConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AnimalHealthConfigEntry,
) -> bool:
    database_path = Path(hass.config.path(DATABASE_NAME))
    database = AnimalHealthDatabase(hass, database_path)
    await database.initialize()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = database
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AnimalHealthConfigEntry,
) -> bool:
    domain_data = hass.data.get(DOMAIN)
    if domain_data is None:
        return True

    domain_data.pop(entry.entry_id, None)
    if not domain_data:
        hass.data.pop(DOMAIN, None)
    return True
