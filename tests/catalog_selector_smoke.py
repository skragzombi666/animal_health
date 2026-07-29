from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).parents[1]
COMPONENT_DIR = ROOT / "custom_components" / "animal_health"
PACKAGE = "custom_components.animal_health"


def _package(name: str, path: Path) -> None:
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    sys.modules[name] = module


def _load(name: str, path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _stub(name: str, **attributes: str) -> None:
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module


def _catalog_names(filename: str) -> list[str]:
    path = COMPONENT_DIR / "catalogs" / filename
    document = json.loads(path.read_text(encoding="utf-8"))
    return sorted((str(item["name"]) for item in document["items"]), key=str.casefold)


def _selector_options(field: dict) -> list[str]:
    selector = field["selector"]["select"]
    assert selector["custom_value"] is True
    assert selector["mode"] == "dropdown"
    assert selector["sort"] is True
    return selector["options"]


def main() -> None:
    _package("custom_components", ROOT / "custom_components")
    _package(PACKAGE, COMPONENT_DIR)
    _load(f"{PACKAGE}.const", COMPONENT_DIR / "const.py")
    catalog = _load(f"{PACKAGE}.catalog", COMPONENT_DIR / "catalog.py")
    _stub(
        f"{PACKAGE}.task_record_creation",
        SERVICE_CREATE_RECORD_TASK="create_record_task",
    )
    _stub(
        f"{PACKAGE}.task_records",
        SERVICE_RECORD_TASK_CARE="record_task_care",
        SERVICE_RECORD_TASK_HEALTH_CHECK="record_task_health_check",
        SERVICE_RECORD_TASK_MEDICATION="record_task_medication",
        SERVICE_RECORD_TASK_REMINDER="record_task_reminder",
        SERVICE_RECORD_TASK_VACCINATION="record_task_vaccination",
        SERVICE_RECORD_TASK_VETERINARY_VISIT="record_task_veterinary_visit",
        SERVICE_RECORD_TASK_WEIGHT="record_task_weight",
    )
    descriptions_module = _load(
        f"{PACKAGE}.task_record_descriptions",
        COMPONENT_DIR / "task_record_descriptions.py",
    )

    expected_medicines = _catalog_names("medicines_ch.json")
    expected_vaccines = _catalog_names("vaccines_ch.json")
    assert len(expected_medicines) == 27
    assert len(expected_vaccines) == 14
    assert catalog.medicine_catalog_names() == expected_medicines
    assert catalog.vaccine_catalog_names() == expected_vaccines

    descriptions = descriptions_module.task_record_descriptions("de")
    planned_medication = descriptions["create_record_task"]["fields"][
        "planned_medication_name"
    ]
    actual_medication = descriptions["record_task_medication"]["fields"][
        "medication_name"
    ]
    planned_vaccine = descriptions["create_record_task"]["fields"][
        "planned_vaccine_name"
    ]
    actual_vaccine = descriptions["record_task_vaccination"]["fields"][
        "vaccine_name"
    ]

    assert _selector_options(planned_medication) == expected_medicines
    assert _selector_options(actual_medication) == expected_medicines
    assert _selector_options(planned_vaccine) == expected_vaccines
    assert _selector_options(actual_vaccine) == expected_vaccines

    animal_selector = descriptions["create_record_task"]["fields"]["device_ids"][
        "selector"
    ]["device"]
    assert animal_selector["entity"] == [
        {"integration": "animal_health", "domain": "sensor"}
    ]
    print("catalog selector smoke test passed")


if __name__ == "__main__":
    main()
