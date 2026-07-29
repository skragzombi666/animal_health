from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.service import async_set_service_schema

from .const import DOMAIN
from .task_kinds import task_language
from .task_record_descriptions import task_record_descriptions
from .task_service_descriptions import task_service_descriptions


def _task_language(hass: HomeAssistant) -> str:
    return task_language(
        getattr(hass.config, "language", None),
        getattr(hass.config, "country", None),
    )


def _multiple_animal_selector() -> dict[str, object]:
    return {
        "device": {
            "filter": [{"integration": DOMAIN}],
            "entity": [{"integration": DOMAIN, "domain": "sensor"}],
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


def _replace_field(
    fields: dict[str, Any],
    old_key: str,
    new_key: str,
    new_value: dict[str, Any],
) -> None:
    ordered: dict[str, Any] = {}
    for key, value in fields.items():
        if key == old_key:
            ordered[new_key] = new_value
        else:
            ordered[key] = value
    if old_key not in fields:
        ordered[new_key] = new_value
    fields.clear()
    fields.update(ordered)


def async_setup_task_service_descriptions(hass: HomeAssistant) -> None:
    language = _task_language(hass)
    descriptions = task_service_descriptions(language)
    descriptions.update(task_record_descriptions(language))
    german = language.startswith("de")

    _replace_field(
        descriptions["create_task"]["fields"],
        "device_id",
        "device_ids",
        {
            "name": "Tiere" if german else "Animals",
            "description": (
                "Für eine tierbezogene Erinnerungsaufgabe ein oder mehrere Tiere auswählen. "
                "Für fachlich verknüpfte Aufgaben die Aktion «Strukturierte Aufgabe anlegen» verwenden."
                if german
                else "Select one or more animals for an animal-specific reminder. "
                "Use Create structured task for record-linked tasks."
            ),
            "selector": _multiple_animal_selector(),
        },
    )

    _replace_field(
        descriptions["list_due_tasks"]["fields"],
        "device_id",
        "device_ids",
        {
            "name": "Tiere" if german else "Animals",
            "description": (
                "Optional auf ein oder mehrere Tiere filtern."
                if german
                else "Optionally filter by one or more animals."
            ),
            "selector": _multiple_animal_selector(),
        },
    )

    _replace_field(
        descriptions["set_task_active"]["fields"],
        "task_id",
        "entity_ids",
        {
            "name": "Aufgaben" if german else "Tasks",
            "description": (
                "Eine oder mehrere Aufgaben anhand ihres Namens auswählen."
                if german
                else "Select one or more tasks by name."
            ),
            "required": True,
            "selector": _multiple_task_switch_selector(),
        },
    )

    for service_name, description in descriptions.items():
        async_set_service_schema(hass, DOMAIN, service_name, description)
