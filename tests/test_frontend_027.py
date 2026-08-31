from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_027_version_is_consistent() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    assert manifest["version"] == "0.9.27"
    assert 'const V="0.9.27",D="animal_health"' in part01


def test_027_gabe_backend_and_product_databases() -> None:
    backend = "".join((INTEGRATION / name).read_text(encoding="utf-8") for name in ("v0927_data.py", "v0927_gabe.py", "v0927_features.py"))
    init = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")
    task_kinds = (INTEGRATION / "task_kinds.py").read_text(encoding="utf-8")
    for marker in (
        'GABE_MEDICATION = "medication"',
        'GABE_VACCINATION = "vaccination"',
        'GABE_DEWORMING = "deworming"',
        'GABE_SUPPLEMENT = "supplement"',
        'GABE_FEED = "feed"',
        'CREATE TABLE IF NOT EXISTS v0927_products',
        '/v0927/gabe/record',
        '/v0927/task/gabe/execute',
        'active_amounts',
        'weight_snapshot',
        'backfill_gabe_events',
    ):
        assert marker in backend
    assert "async_initialize_v0927_features" in init
    assert "async_setup_v0927_features" in init
    assert "apply_v0927_patches" in init
    for marker in ('TASK_KIND_DEWORMING = "deworming"', 'TASK_KIND_SUPPLEMENT = "supplement"', 'TASK_KIND_FEED = "feed"'):
        assert marker in task_kinds


def test_027_frontend_structure_and_compact_timeline() -> None:
    frontend = "".join((FRONTEND / f"animal-health-panel.part{part}.js").read_text(encoding="utf-8") for part in (83, 84, 85, 86))
    for marker in (
        "groupOverviewTile027",
        "targetFieldLabel027",
        "defaultSelected027",
        "settingsGrid027",
        "vaccineDatabase027",
        "supplementDatabase027",
        "feedDatabase027",
        "gabeType027",
        "activeSummary027",
        "mg_per_kg",
        "taskSource027",
        "taskOriginDetail027",
        ".capturePlus016,.capturePlus019{display:none!important}",
        ".objectMenu025{z-index:5000!important",
    ):
        assert marker in frontend


def test_027_treatment_components_keep_default_selection() -> None:
    backend = "".join((INTEGRATION / name).read_text(encoding="utf-8") for name in ("v0927_gabe.py", "v0927_features.py"))
    frontend = "".join((FRONTEND / f"animal-health-panel.part{part}.js").read_text(encoding="utf-8") for part in (83, 84, 85, 86))
    assert 'item["default_selected"]' in backend
    assert "data-plan-default-selected027" in frontend
    assert "item.optional&&item.default_selected" in frontend
    assert "selectedOptional=(plan.components||[])" in frontend


def test_android_remains_frozen_after_027() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
