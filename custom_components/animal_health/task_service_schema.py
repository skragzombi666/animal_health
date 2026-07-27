from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.service import async_set_service_schema

from .const import DOMAIN
from .task_service_descriptions import task_service_descriptions

_GERMAN_COUNTRIES = {"AT", "CH", "DE", "LI"}


def _task_language(hass: HomeAssistant) -> str:
    language = str(getattr(hass.config, "language", "en") or "en")
    country = str(getattr(hass.config, "country", "") or "").upper()
    if language.startswith("de") or country in _GERMAN_COUNTRIES:
        return "de"
    return language


def _multiple_animal_selector() -> dict[str, object]:
    return {
        "device": {
            "filter": [{"integration": DOMAIN}],
            "multiple": True,
        }
    }


def _multiple_task_switch_selector() -> dict[str, object]:
    return {
        "entity": {
            "filter": [{"integration": DOMAIN, "domain": "switch"}],
            "multiple": True,
        }
    }


def async_setup_task_service_descriptions(hass: HomeAssistant) -> None:
    language = _task_language(hass)
    descriptions = task_service_descriptions(language)
    german = language.startswith("de")

    create_fields = descriptions["create_task"]["fields"]
    create_fields.pop("device_id", None)
    create_fields["device_ids"] = {
        "name": "Tiere" if german else "Animals",
        "description": (
            "Für eine tierbezogene Aufgabe ein oder mehrere Tiere auswählen. "
            "Für eine allgemeine Aufgabe leer lassen."
            if german
            else "Select one or more animals for an animal-specific task. "
            "Leave empty for a general task."
        ),
        "selector": _multiple_animal_selector(),
    }

    due_fields = descriptions["list_due_tasks"]["fields"]
    due_fields.pop("device_id", None)
    due_fields["device_ids"] = {
        "name": "Tiere" if german else "Animals",
        "description": (
            "Optional auf ein oder mehrere Tiere filtern."
            if german
            else "Optionally filter by one or more animals."
        ),
        "selector": _multiple_animal_selector(),
    }

    active_fields = descriptions["set_task_active"]["fields"]
    active_fields.pop("task_id", None)
    active_fields["entity_ids"] = {
        "name": "Aufgaben" if german else "Tasks",
        "description": (
            "Eine oder mehrere Aufgaben anhand ihres Namens auswählen."
            if german
            else "Select one or more tasks by name."
        ),
        "required": True,
        "selector": _multiple_task_switch_selector(),
    }

    for service_name, description in descriptions.items():
        async_set_service_schema(hass, DOMAIN, service_name, description)
