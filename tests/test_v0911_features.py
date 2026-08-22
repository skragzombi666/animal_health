from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"


def test_v0911_backend_registers_treatment_catalogue() -> None:
    source = (INTEGRATION / "v0911_features.py").read_text(encoding="utf-8")
    init_source = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")

    ast.parse(source)
    ast.parse(init_source)
    assert "CREATE TABLE IF NOT EXISTS v0911_treatment_plans" in source
    assert "CHECK (list_as IN ('medication', 'task', 'both'))" in source
    assert 'f"{DOMAIN}/v0911/state"' in source
    assert 'f"{DOMAIN}/v0911/treatment/save"' in source
    assert 'f"{DOMAIN}/v0911/treatment/delete"' in source
    assert "default_unit" in source
    assert "default_route" in source
    assert "description" in source
    assert "async_initialize_v0911_features" in init_source
    assert "async_setup_v0911_features" in init_source


def test_teilstrich_is_validated_and_exported() -> None:
    const_source = (INTEGRATION / "const.py").read_text(encoding="utf-8")
    patches = (INTEGRATION / "v0817_patches.py").read_text(encoding="utf-8")
    service_patch = (INTEGRATION / "v0911_patches.py").read_text(encoding="utf-8")

    ast.parse(service_patch)
    assert '"mark"' in const_source
    assert '"mark": "Teilstrich"' in patches
    assert '("mark", "Teilstrich" if german else "Graduation mark")' in service_patch
    assert 'options.append({"value": value, "label": label})' in service_patch


def test_v0911_state_contains_surface_metadata() -> None:
    source = (INTEGRATION / "v0911_features.py").read_text(encoding="utf-8")

    for marker in (
        '"name": str(row["name"])',
        '"species_id": str(row["species_id"] or "")',
        '"list_as": str(row["list_as"])',
        '"description": str(row["description"] or "")',
        '"default_unit": str(row["default_unit"] or "dose")',
        '"default_route": str(row["default_route"] or "")',
    ):
        assert marker in source
