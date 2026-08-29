from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_018_version_is_consistent() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    assert manifest["version"] in {"0.9.18", "0.9.19", "0.9.20", "0.9.21", "0.9.22", "0.9.23", "0.9.24", "0.9.25", "0.9.26"}
    assert f'const V="{manifest["version"]}",D="animal_health"' in part01


def test_018_treatment_plan_lifecycle_is_persistent() -> None:
    backend = (INTEGRATION / "v0918_features.py").read_text(encoding="utf-8")
    init = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")
    assert "ALTER TABLE v0911_treatment_plans ADD COLUMN is_archived" in backend
    assert "ALTER TABLE v0911_treatment_plans ADD COLUMN archived_at" in backend
    assert '/v0918/treatment/save' in backend
    assert '/v0918/treatment/archive' in backend
    assert 'vol.Optional("plan_id")' in backend
    assert 'vol.Optional("list_as", default="both")' in backend
    assert "UPDATE v0911_treatment_plans" in backend
    assert "SET is_archived=?,archived_at=?,updated_at=?" in backend
    assert "async_initialize_v0918_features" in init
    assert "async_setup_v0918_features" in init


def test_018_new_treatment_plans_default_to_both() -> None:
    frontend = (FRONTEND / "animal-health-panel.part69.js").read_text(encoding="utf-8")
    assert 'list_as:"both"' in frontend
    assert 'draft.list_as||"both"' in frontend
    assert 'list_as:draft.list_as||"both"' in frontend
    assert 'value="both" ${draft.list_as==="both"?"selected":""}' in frontend


def test_018_treatment_plans_edit_archive_restore_without_delete_ui() -> None:
    frontend = (FRONTEND / "animal-health-panel.part69.js").read_text(encoding="utf-8")
    for marker in (
        "edit-treatment-018",
        "archive-treatment-018",
        "toggle-archived-treatments-018",
        "cancel-treatment-edit-018",
        "showArchivedTreatmentPlans018",
        "treatmentPlanEdit018",
    ):
        assert marker in frontend
    assert 'data-action="delete-treatment-012"' not in frontend
    assert '`${D}/v0918/treatment/archive`' in frontend
    assert '`${D}/v0918/treatment/save`' in frontend


def test_018_archived_plans_are_excluded_from_normal_selection() -> None:
    frontend = (FRONTEND / "animal-health-panel.part69.js").read_text(encoding="utf-8")
    assert "const active=(this.v0918?.treatment_plans||[]).filter(plan=>!plan.is_archived)" in frontend
    assert "this.v0912.treatment_plans=active" in frontend
    assert "filter(plan=>!plan.is_archived)" in frontend


def test_android_remains_frozen_after_018() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
