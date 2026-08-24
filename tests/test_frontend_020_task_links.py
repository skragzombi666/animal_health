from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_020_task_treatment_parent_link_is_persisted() -> None:
    patches = (INTEGRATION / "v0920_patches.py").read_text(encoding="utf-8")
    assert "TaskRecordStore.execute" in patches
    assert "_persist_treatment_parent_sync" in patches
    assert "UPDATE events SET data_json=? WHERE id=?" in patches
    for key in (
        '"treatment_plan_id"',
        '"treatment_plan_name"',
        '"treatment_plan_components"',
    ):
        assert key in patches


def test_020_legacy_task_treatment_parent_can_be_matched_by_name() -> None:
    frontend = (FRONTEND / "animal-health-panel.part72.js").read_text(encoding="utf-8")
    assert "treatmentParentMatches020" in frontend
    assert "sameTreatmentOccurrence020" in frontend
    assert "child?.data?.treatment_plan_name" in frontend
    assert "parent?.title" in frontend
    assert "parentPlanId!=null" in frontend
    assert 'event?.event_type==="treatment"' in frontend
    assert "this.treatmentChildren020(event,list).length" in frontend
