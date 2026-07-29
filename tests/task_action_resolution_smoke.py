from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
COMPONENT_DIR = ROOT / "custom_components" / "animal_health"


def _load_task_kinds():
    path = COMPONENT_DIR / "task_kinds.py"
    spec = importlib.util.spec_from_file_location("animal_health_task_kinds", path)
    if spec is None or spec.loader is None:
        raise AssertionError("Could not load task_kinds.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _context_expected_kind(function: ast.AsyncFunctionDef) -> str:
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "_context":
            continue
        if len(node.args) != 2 or not isinstance(node.args[1], ast.Name):
            raise AssertionError(f"{function.name} does not pass an expected task kind")
        return node.args[1].id
    raise AssertionError(f"{function.name} does not call _context")


def main() -> None:
    task_kinds = _load_task_kinds()
    expected_labels = {
        "reminder": "Erinnerung",
        "weight": "Gewicht",
        "medication": "Medikament",
        "vaccination": "Impfung",
        "health_check": "Gesundheitskontrolle",
        "care": "Pflege",
        "veterinary_visit": "Tierarztbesuch",
    }
    for task_kind, label in expected_labels.items():
        assert task_kinds.task_kind_label(task_kind, "de") == label
    assert task_kinds.task_language("de-CH", "CH") == "de"
    for country in ("AT", "CH", "DE", "LI"):
        assert task_kinds.task_language("en", country) == "en"
        assert task_kinds.task_language(None, country) == "de"
    assert task_kinds.task_language("en", "US") == "en"
    assert task_kinds.task_language(None, "GB") == "en"
    assert task_kinds.task_language("de", "US") == "de"

    first = task_kinds.task_display_name(
        "Tiere wägen",
        "weight",
        "TK-AAAAAAA",
        "de",
    )
    second = task_kinds.task_display_name(
        "Tiere wägen",
        "weight",
        "TK-BBBBBBB",
        "de",
    )
    assert first == "Tiere wägen · Gewicht · TK-AAAAAAA"
    assert second == "Tiere wägen · Gewicht · TK-BBBBBBB"
    assert first != second

    services_path = COMPONENT_DIR / "task_record_services.py"
    tree = ast.parse(services_path.read_text(encoding="utf-8"))
    handlers = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
    }
    expected_handlers = {
        "handle_record_reminder": "TASK_KIND_REMINDER",
        "handle_record_weight": "TASK_KIND_WEIGHT",
        "handle_record_medication": "TASK_KIND_MEDICATION",
        "handle_record_vaccination": "TASK_KIND_VACCINATION",
        "handle_record_health_check": "TASK_KIND_HEALTH_CHECK",
        "handle_record_care": "TASK_KIND_CARE",
        "handle_record_veterinary_visit": "TASK_KIND_VETERINARY_VISIT",
    }
    for handler_name, expected_kind in expected_handlers.items():
        assert _context_expected_kind(handlers[handler_name]) == expected_kind

    service_source = services_path.read_text(encoding="utf-8")
    assert "translation_domain=DOMAIN" in service_source
    assert "translation_key=message_key" in service_source
    assert 'f"wrong_task_kind_{expected_kind}"' in service_source

    creation_source = (
        COMPONENT_DIR / "task_record_creation.py"
    ).read_text(encoding="utf-8")
    assert "translation_domain=DOMAIN" in creation_source
    assert "translation_key=message_key" in creation_source

    with (COMPONENT_DIR / "strings.json").open(encoding="utf-8") as file:
        english_exceptions = json.load(file)["exceptions"]
    with (COMPONENT_DIR / "translations" / "de.json").open(
        encoding="utf-8"
    ) as file:
        german_exceptions = json.load(file)["exceptions"]
    assert set(english_exceptions) == set(german_exceptions)
    assert german_exceptions["general_task_requires_reminder"]["message"] == (
        "Als allgemeine Aufgabe kann nur eine Erinnerung angelegt werden."
    )
    assert german_exceptions["invalid_animal_device"]["message"] == (
        "Das ausgewählte Gerät ist kein Animal-Health-Tier."
    )
    assert german_exceptions["wrong_task_kind_weight"]["message"] == (
        "Die ausgewählte Aufgabe ist keine Gewichtsaufgabe."
    )

    switch_source = (COMPONENT_DIR / "switch.py").read_text(encoding="utf-8")
    assert "task_display_name(" in switch_source
    assert "TASK_KIND_ICONS" in switch_source

    service_yaml = (COMPONENT_DIR / "services.yaml").read_text(encoding="utf-8")
    assert service_yaml.count("domain: sensor") == 10
    print("task action resolution smoke test passed")


if __name__ == "__main__":
    main()
