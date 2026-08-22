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
        label = "Teilstrich" if german else "Graduation mark"
        for description in result.values():
            fields = description.get("fields", {})
            for key in (
                "planned_dose_unit",
                "planned_vaccination_dose_unit",
                "dose_unit",
            ):
                select = (
                    fields.get(key, {})
                    .get("selector", {})
                    .get("select", {})
                )
                options = select.get("options")
                if not isinstance(options, list):
                    continue
                if any(
                    (item.get("value") if isinstance(item, dict) else item) == "mark"
                    for item in options
                ):
                    continue
                if options and isinstance(options[0], dict):
                    options.append({"value": "mark", "label": label})
                else:
                    options.append("mark")
        return result

    task_service_schema.task_record_descriptions = descriptions
    _PATCHED = True
