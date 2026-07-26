from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.service import async_set_service_schema

from .const import DOMAIN
from .task_service_descriptions import task_service_descriptions


def async_setup_task_service_descriptions(hass: HomeAssistant) -> None:
    language = getattr(hass.config, "language", "en")
    for service_name, description in task_service_descriptions(language).items():
        async_set_service_schema(hass, DOMAIN, service_name, description)
