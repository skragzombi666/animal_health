from __future__ import annotations

from typing import Any

from . import task_service_schema

_PATCHED = False


def apply_v0911_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    original = task_service_schema.task_record_descriptions

    def descriptions(language: str) -> dict[str, dict[str, Any]]:
        result = original(language)
        german = language.startswith("de")
        additions = (
            ("mark", "Teilstrich" if german else "Graduation mark"),
            ("pinch", "Messerspitze" if german else "Pinch"),
            ("coffee_spoon", "Kaffeelöffel" if german else "Coffee spoon"),
        )
        for description in result.values():
            fields = description.get("fields", {})
            for key in (
                "planned_dose_unit",
                "planned_vaccination_dose_unit",
                "dose_unit",
            ):
                select = fields.get(key, {}).get("selector", {}).get("select", {})
                options = select.get("options")
                if not isinstance(options, list):
                    continue
                existing = {
                    item.get("value") if isinstance(item, dict) else item
                    for item in options
                }
                for value, label in additions:
                    if value in existing:
                        continue
                    if options and isinstance(options[0], dict):
                        options.append({"value": value, "label": label})
                    else:
                        options.append(value)
        return result

    task_service_schema.task_record_descriptions = descriptions
    _PATCHED = True
