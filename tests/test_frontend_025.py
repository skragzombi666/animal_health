from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_025_version_is_consistent_and_android_stays_frozen() -> None:
    manifest = json.loads(_read(INTEGRATION / "manifest.json"))
    part01 = _read(FRONTEND / "animal-health-panel.part01.js")
    gradle = _read(ROOT / "android" / "app" / "build.gradle.kts")
    assert manifest["version"] == "0.9.25"
    assert 'const V="0.9.25",D="animal_health"' in part01
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle


def test_025_simultaneously_captured_symptoms_are_grouped_without_merging_records() -> None:
    backend = _read(INTEGRATION / "v0925_features.py")
    frontend = _read(FRONTEND / "animal-health-panel.part79.js")
    init = _read(INTEGRATION / "__init__.py")
    assert "symptom_capture_batch_id" in backend
    assert "episode[\"symptom_capture_batch_id\"]" in backend
    assert "/v0925/symptoms/group/update" in backend
    assert '_GROUP_ACTIONS = ("continue", "reassess", "resolve")' in backend
    assert "database._connect()" in backend
    assert "_episode_event" in backend
    assert "_insert_assessment" in backend
    assert "origin_batch_values" in backend
    assert "any(not batch for batch in origin_batch_values)" in backend
    assert "apply_v0925_patches" in init
    assert "async_setup_v0925_features" in init
    assert "symptomGroups025" in frontend
    assert "activeSymptomsCard023" in frontend
    assert "symptom-group-continue-025" in frontend
    assert "symptom-group-reassess-025" in frontend
    assert "symptom-group-resolve-025" in frontend
    assert "toggle-symptom-group-025" in frontend
    assert "symptom_group_episode_ids" in frontend
    assert "visibleTimelineEvents023" in frontend
    assert "timelineDaySections023" in frontend


def test_025_treatment_plans_and_manual_medications_can_be_duplicated_compactly() -> None:
    frontend = _read(FRONTEND / "animal-health-panel.part79.js")
    for marker in (
        "duplicate-treatment-025",
        "duplicate-treatment-edit-025",
        "duplicate-medication-025",
        "duplicate-med-edit-025",
        "createCopy025",
        "saveCopy025",
        "mdi:dots-vertical",
    ):
        assert marker in frontend
    assert "draft.plan_id=null" in frontend
    assert "id:null" in frontend
    assert "copyName025" in frontend
    assert 'this.planDraft012=draft' in frontend
    assert 'this.medicationEdit013={' in frontend
    assert "history" not in frontend.lower()


def test_025_copy_paths_reuse_existing_master_save_apis() -> None:
    frontend = _read(FRONTEND / "animal-health-panel.part79.js")
    treatment = _read(INTEGRATION / "v0918_features.py")
    medication = _read(INTEGRATION / "v0913_features.py")
    assert 'form?.dataset.form==="v0912-treatment"' in frontend
    assert 'form?.dataset.form==="v0913-medication"' in frontend
    assert '/v0918/treatment/save' in treatment
    assert 'vol.Optional("plan_id")' in treatment
    assert '/v0913/medication/save' in medication
    assert 'vol.Optional("medication_id")' in medication
