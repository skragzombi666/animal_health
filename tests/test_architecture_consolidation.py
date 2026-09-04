from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_SCRIPT = ROOT / "scripts" / "architecture_inventory.py"
BASELINE = ROOT / "docs" / "architecture" / "inventory" / "legacy-baseline.json"


def _load_inventory_module():
    spec = importlib.util.spec_from_file_location(
        "architecture_inventory", INVENTORY_SCRIPT
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _baseline() -> dict:
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def test_phase0_inventory_is_machine_readable_and_complete() -> None:
    assert INVENTORY_SCRIPT.is_file()
    assert BASELINE.is_file()
    module = _load_inventory_module()
    inventory = module.collect_inventory(ROOT)
    baseline = _baseline()

    assert inventory["reference_version"] == "0.9.41"
    assert inventory["frontend"]["part_count"] == 99
    assert inventory["frontend"]["parts"][0]["path"].endswith("part01.js")
    assert inventory["frontend"]["parts"][-1]["path"].endswith("part99.js")
    assert inventory["frontend"]["prototype_mutations"]
    assert inventory["frontend"]["actions"]
    assert inventory["frontend"]["dialogs"]
    assert inventory["backend"]["patch_registration_order"]
    assert inventory["backend"]["runtime_method_assignments"]
    assert module.check_guardrails(inventory, baseline) == []


def test_phase0_guardrails_allow_reduction_but_reject_frontend_growth() -> None:
    module = _load_inventory_module()
    baseline = _baseline()

    reduced = deepcopy(baseline)
    reduced["frontend"]["prototype_mutations"].pop()
    reduced["frontend"]["actions"].pop()
    reduced["frontend"]["style_block_count"] -= 1
    assert module.check_guardrails(reduced, baseline) == []

    grown = deepcopy(baseline)
    grown["frontend"]["actions"].append("phase01-unapproved-action")
    grown["frontend"]["new_source_forbidden_patterns"].append(
        {
            "path": "custom_components/animal_health/frontend/src/example.js",
            "pattern": "direct_prototype_patch",
            "ordinal": 1,
        }
    )
    errors = module.check_guardrails(grown, baseline)
    assert any("actions" in error for error in errors)
    assert any("new_source_forbidden_patterns" in error for error in errors)


def test_phase0_guardrails_reject_backend_runtime_growth_and_reordering() -> None:
    module = _load_inventory_module()
    baseline = _baseline()

    grown = deepcopy(baseline)
    grown["backend"]["runtime_method_assignments"].append(
        {
            "path": "custom_components/animal_health/new_patch.py",
            "target": "TaskRecordStore.execute",
            "statement_sha256": "unapproved",
        }
    )
    grown["backend"]["patch_registration_order"].append(
        "apply_unapproved_patches"
    )
    errors = module.check_guardrails(grown, baseline)
    assert any("runtime_method_assignments" in error for error in errors)
    assert any("patch registration order" in error for error in errors)


def test_phase0_source_scanner_blocks_direct_and_aliased_prototype_patches() -> None:
    module = _load_inventory_module()
    path = "custom_components/animal_health/frontend/src/example.js"
    source = """
AnimalHealthPanel.prototype.render = function() {};
const AHNext = AnimalHealthPanel.prototype;
AHNext.handleClick = function() {};
Object.assign(AHNext, { handleSubmit() {} });
shadowRoot.innerHTML += '<style></style>';
"""
    violations = module.find_frontend_source_violations(source, path)
    patterns = {item["pattern"] for item in violations}
    assert "direct_prototype_patch" in patterns
    assert "prototype_alias_patch" in patterns
    assert "prototype_object_assign" in patterns
    assert "shadow_root_append" in patterns

    bridge = (
        "custom_components/animal_health/frontend/src/legacy/"
        "compatibility-bridge.js"
    )
    bridge_patterns = {
        item["pattern"]
        for item in module.find_frontend_source_violations(source, bridge)
    }
    assert bridge_patterns == {"shadow_root_append"}


def test_phase0_guardrails_accept_the_frozen_baseline() -> None:
    result = subprocess.run(
        [sys.executable, str(INVENTORY_SCRIPT), "--check", "--root", str(ROOT)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_phase0_has_no_temporary_generation_workflow_or_migration_script() -> None:
    assert not (ROOT / ".github/workflows/phase01-generate.yml").exists()
    assert not (ROOT / "scripts/phase01_migrate_release_tests.py").exists()
