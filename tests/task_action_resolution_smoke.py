from __future__ import annotations

import ast
import importlib.util
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


def _literal_assignment(tree: ast.Module, name: str) -> dict:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, dict):
                return value
    raise AssertionError(f"Could not find literal assignment {name}")


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
    assert task_kinds.task_language("en", "CH") == "en"
    assert task_kinds.task_language(None, "CH") == "de"
    assert task_kinds.task_language("en", "US") == "en"

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

    messages = _literal_assignment(tree, "_ERROR_MESSAGES")
    expected_german = {
        "invalid_task_switch": (
            "Die ausgewählte Entität ist kein Animal-Health-Aufgabenschalter."
        ),
        "task_and_occurrence_mutually_exclusive": (
            "Entweder eine Aufgabe oder eine Fälligkeits-ID angeben, nicht beides."
        ),
        "choose_task_or_occurrence": (
            "Eine Aufgabe auswählen oder eine Fälligkeits-ID eingeben."
        ),
        "no_matching_open_occurrence": (
            "Für die ausgewählte Aufgabe gibt es keine passende offene Fälligkeit."
        ),
        "occurrence_missing": (
            "Die ausgewählte Aufgabenfälligkeit existiert nicht mehr."
        ),
    }
    for key, message in expected_german.items():
        assert messages[key]["de"] == message
    assert "{actual_kind}" in messages["wrong_task_kind"]["de"]
    assert "{expected_kind}" in messages["wrong_task_kind"]["de"]

    creation_tree = ast.parse(
        (COMPONENT_DIR / "task_record_creation.py").read_text(encoding="utf-8")
    )
    creation_messages = _literal_assignment(creation_tree, "_ERROR_MESSAGES")
    assert creation_messages["general_task_requires_reminder"]["de"] == (
        "Als allgemeine Aufgabe kann nur eine Erinnerung angelegt werden."
    )
    assert creation_messages["invalid_animal_device"]["de"] == (
        "Das ausgewählte Gerät ist kein Animal-Health-Tier."
    )

    switch_source = (COMPONENT_DIR / "switch.py").read_text(encoding="utf-8")
    assert "task_display_name(" in switch_source
    assert "TASK_KIND_ICONS" in switch_source

    service_yaml = (COMPONENT_DIR / "services.yaml").read_text(encoding="utf-8")
    assert service_yaml.count("domain: sensor") == 10
    print("task action resolution smoke test passed")


if __name__ == "__main__":
    main()
