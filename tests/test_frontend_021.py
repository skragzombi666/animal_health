from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_021_version_is_consistent() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    assert manifest["version"] in {"0.9.21", "0.9.22", "0.9.23", "0.9.24"}
    assert f'const V="{manifest["version"]}",D="animal_health"' in part01


def test_021_treatment_summary_uses_standard_chronology_row_and_chevron() -> None:
    frontend = (FRONTEND / "animal-health-panel.part73.js").read_text(encoding="utf-8")
    assert "treatmentBundle021" in frontend
    assert 'class="row event eventCompact0817 bundleRow021 treatmentSummary021"' in frontend
    assert "bundleMeta021" in frontend
    assert "this.fmt(event.occurred_at,true)" in frontend
    assert "bundlePreview021" in frontend
    assert "bundleChevron021" in frontend
    assert 'data-action="toggle-treatment-021"' in frontend
    assert "align-self:center!important" in frontend


def test_021_treatment_plan_can_repeat_or_copy_as_a_whole() -> None:
    frontend = (FRONTEND / "animal-health-panel.part73.js").read_text(encoding="utf-8")
    assert "treatment-repeat-021" in frontend
    assert "treatment-copy-021" in frontend
    assert "openTreatmentFromHistory021" in frontend
    assert "openTreatmentPlanExecution012" in frontend
    assert "treatmentRepeat021" in frontend
    assert "treatmentCopy021" in frontend
    assert "eventDetail=function" in frontend


def test_021_treatment_steps_and_child_events_are_indented() -> None:
    frontend = (FRONTEND / "animal-health-panel.part73.js").read_text(encoding="utf-8")
    assert "treatmentComponents021" in frontend
    assert "bundleActionStep021" in frontend
    assert "bundleChild021" in frontend
    assert "AH020Base.eventCompact0817.call(this,event)" in frontend
    assert "border-left:2px solid var(--divider-color)" in frontend


def test_021_multi_medication_batches_are_grouped_and_repeatable() -> None:
    frontend = (FRONTEND / "animal-health-panel.part73.js").read_text(encoding="utf-8")
    backend = (INTEGRATION / "v0817_features.py").read_text(encoding="utf-8")
    assert '"batch_id": batch_id' in backend
    assert '"entry_mode": "correction" if correction else "batch" if len(validated) > 1 else "spontaneous"' in backend
    assert "batchMembers021" in frontend
    assert "isMedicationBatch021" in frontend
    assert "isMedicationBatchChild021" in frontend
    assert "medicationBatchBundle021" in frontend
    assert "batch-repeat-021" in frontend
    assert "batch-copy-021" in frontend
    assert "openMedicationBatchFromHistory021" in frontend
    assert "eventToMedication0817" in frontend


def test_021_home_timeline_counts_groups_before_limiting_to_ten() -> None:
    frontend = (FRONTEND / "animal-health-panel.part73.js").read_text(encoding="utf-8")
    assert "visibleTimelineEvents021" in frontend
    assert "visible.slice(0,10)" in frontend
    assert "isMedicationBatchChild021" in frontend
    assert "treatmentSummaryForChild020" in frontend


def test_android_remains_frozen_after_021() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
