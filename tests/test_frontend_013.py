from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_013_version_and_navigation() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    part60 = (FRONTEND / "animal-health-panel.part60.js").read_text(encoding="utf-8")

    assert manifest["version"] in {"0.9.13", "0.9.14", "0.9.15", "0.9.16"}
    assert f'const V="{manifest["version"]}",D="animal_health"' in part01
    assert "brandHome013" in part60
    assert "brandName013" in part60
    assert "brandVersion013" in part60
    assert 'AH013.headerNav098=function(){' in part60
    assert 'data-view="settings081"' in part60
    assert "homeTimeline013" in part60
    assert "slice(0,10)" in part60
    assert 'data-view="timeline"' in part60


def test_013_deleted_entries_are_auditable() -> None:
    part60 = (FRONTEND / "animal-health-panel.part60.js").read_text(encoding="utf-8")
    backend = (INTEGRATION / "v0913_features.py").read_text(encoding="utf-8")
    patches = (INTEGRATION / "v0913_patches.py").read_text(encoding="utf-8")

    assert "toggle-deleted-events-013" in part60
    assert "/v0913/event/delete" in part60
    assert "deleted_events" in backend
    assert "is_deleted" in backend
    assert "deleted_at" in backend
    assert "_recompute_status_sync" in backend
    assert "WHERE animal_id=? AND is_deleted=0" in patches
    assert "later_correction.is_deleted=0" in patches


def test_013_medication_metadata_archive_and_snapshot() -> None:
    part60 = (FRONTEND / "animal-health-panel.part60.js").read_text(encoding="utf-8")
    backend = (INTEGRATION / "v0913_features.py").read_text(encoding="utf-8")
    patches = (INTEGRATION / "v0913_patches.py").read_text(encoding="utf-8")

    for marker in (
        "activeIngredient013",
        "concentration013",
        "dosageForm013",
        "archive-medication-013",
        "toggle-archived-medications-013",
        "medSuggest013",
        "medicationSearchText013",
    ):
        assert marker in part60
    assert '"name": "Baytril 10% ad us. vet."' in backend
    assert '"active_ingredients": ["Enrofloxacin"]' in backend
    assert '"concentration": "100 mg/ml"' in backend
    assert '"concentration": "50 mg/g"' in backend
    assert '"concentration": "44 mg/ml"' in backend
    assert "is_archived" in backend
    assert "medication_snapshot" in patches
    assert "medication_snapshot" in part60


def test_android_stays_frozen_for_013() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
