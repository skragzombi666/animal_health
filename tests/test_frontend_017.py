from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_017_version_is_consistent() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    assert tuple(map(int, manifest["version"].split("."))) >= (0, 9, 17)
    assert 'const V="0.9.41",D="animal_health"' in part01


def test_017_persistent_group_and_animal_ordering() -> None:
    backend = (INTEGRATION / "v0917_features.py").read_text(encoding="utf-8")
    frontend = (FRONTEND / "animal-health-panel.part66.js").read_text(encoding="utf-8")
    polish = (FRONTEND / "animal-health-panel.part67.js").read_text(encoding="utf-8")
    init = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS v0917_group_order" in backend
    assert "CREATE TABLE IF NOT EXISTS v0917_animal_order" in backend
    assert "/v0917/group_order/save" in backend
    assert "/v0917/animal_order/save" in backend
    assert "groupOrderSettings017" in frontend
    assert "groupAnimalTiles017" in frontend
    assert "animal-order-up-017" in frontend
    assert "home-groups-017" in frontend
    assert "reorderAnimalSelects017" in polish
    assert "reorderAnimalCheckboxes017" in polish
    assert "reorderGroupSelects017" in polish
    assert "async_initialize_v0917_features" in init
    assert "async_setup_v0917_features" in init


def test_017_quick_capture_is_responsive_and_uses_one_plus_badge() -> None:
    frontend = (FRONTEND / "animal-health-panel.part66.js").read_text(encoding="utf-8")
    assert "capturePlus016" in frontend
    assert "right:-4px!important;bottom:-2px!important" in frontend
    assert "repeat(6,minmax(82px,108px))" in frontend
    assert "@media(max-width:720px)" in frontend
    assert "repeat(6,minmax(0,1fr))" in frontend


def test_017_tasks_without_time_do_not_show_implicit_midnight() -> None:
    frontend = (FRONTEND / "animal-health-panel.part66.js").read_text(encoding="utf-8")
    assert "stripImplicitMidnight017" in frontend
    assert "if(task?.due_time)return html" in frontend
    assert "taskCompact=function" in frontend
    assert "occRow=function" in frontend
    assert "taskManagementRow097=function" in frontend


def test_017_required_recurring_tasks_keep_overdue_and_current_due() -> None:
    frontend = (FRONTEND / "animal-health-panel.part66.js").read_text(encoding="utf-8")
    polish = (FRONTEND / "animal-health-panel.part67.js").read_text(encoding="utf-8")
    assert "AH017.dynamicRelevantGroups095=function" in frontend
    assert 'mode!=="required"' in frontend
    assert "overdue.length" in frontend
    assert "if(current)" in frontend
    assert 'ensureGroup("overdue","overdueUnconfirmed097")' in frontend
    assert "overdueFollowup017" in polish


def test_017_unified_product_model() -> None:
    frontend = (FRONTEND / "animal-health-panel.part66.js").read_text(encoding="utf-8")
    polish = (FRONTEND / "animal-health-panel.part67.js").read_text(encoding="utf-8")
    backend = (INTEGRATION / "v0917_features.py").read_text(encoding="utf-8")
    patches = (INTEGRATION / "v0917_patches.py").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS v0917_product_categories" in backend
    assert "/v0917/product/category" in backend
    assert "productManagement017" in frontend
    assert '[["product","componentProduct017"],["feed","componentFeed012"],["action","componentAction012"]]' in frontend
    assert 'return["medication","supplement","product"].includes' in frontend
    for legacy in ('"medication"', '"supplement"'):
        assert legacy in patches
    assert '"product"' in patches
    assert 'snapshot["product_category"]' in patches
    assert "Produkte und Futter" in polish


def test_android_remains_frozen_after_017() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
