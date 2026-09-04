from __future__ import annotations

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


def test_phase0_inventory_is_machine_readable_and_complete() -> None:
    assert INVENTORY_SCRIPT.is_file()
    assert BASELINE.is_file()
    module = _load_inventory_module()
    inventory = module.collect_inventory(ROOT)
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))

    assert inventory["reference_version"] == "0.9.41"
    assert inventory["frontend"]["part_count"] == 99
    assert inventory["frontend"]["parts"][0]["path"].endswith("part01.js")
    assert inventory["frontend"]["parts"][-1]["path"].endswith("part99.js")
    assert inventory["frontend"]["prototype_mutations"]
    assert inventory["frontend"]["actions"]
    assert inventory["frontend"]["dialogs"]
    assert inventory["backend"]["patch_registration_order"]
    assert inventory["backend"]["runtime_method_assignments"]
    assert baseline == inventory


def test_phase0_guardrails_accept_the_frozen_baseline() -> None:
    result = subprocess.run(
        [sys.executable, str(INVENTORY_SCRIPT), "--check", "--root", str(ROOT)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
