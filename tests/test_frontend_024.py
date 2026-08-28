from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_024_version_is_consistent_and_android_stays_frozen() -> None:
    manifest = json.loads(_read(INTEGRATION / "manifest.json"))
    part01 = _read(FRONTEND / "animal-health-panel.part01.js")
    gradle = _read(ROOT / "android" / "app" / "build.gradle.kts")
    assert manifest["version"] == "0.9.24"
    assert 'const V="0.9.24",D="animal_health"' in part01
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle


def test_024_all_captured_chronology_families_have_edit_paths() -> None:
    frontend = _read(FRONTEND / "animal-health-panel.part77.js")
    final = _read(FRONTEND / "animal-health-panel.part78.js")
    backend = _read(INTEGRATION / "v0924_features.py")
    polish = _read(INTEGRATION / "v0924_polish.py")
    assert 'data-action="event-edit-024"' in frontend
    assert 'data-action="symptom-assessment-edit-024"' in frontend
    assert 'data-action="treatment-edit-024"' in frontend
    assert 'data-action="status-edit-024"' in final
    assert "openMedicationEdit015" in frontend
    assert "/v0924/event/edit" in backend
    assert "/v0924/symptom/assessment/edit" in backend
    assert "/v0924/treatment/edit" in backend
    assert "/v0924/status/edit" in polish
    assert "correction_of_event_id=str(row[\"id\"])" in backend


def test_024_global_attachment_draft_supports_multiple_files_preview_and_remove() -> None:
    frontend = _read(FRONTEND / "animal-health-panel.part77.js")
    backend = _read(INTEGRATION / "v0924_features.py")
    assert "attachmentDrafts024" in frontend
    assert "addAttachmentFiles024" in frontend
    assert "data-attachment-input024 multiple" in frontend
    assert "attachment-draft-remove-024" in frontend
    assert "URL.createObjectURL" in frontend
    assert "attachmentGallery024" in frontend
    assert "attachment-preview-024" in frontend
    assert "attachment-original-024" in frontend
    assert 'max_size = (360, 360) if variant == "thumbnail" else (1600, 1600)' in backend
    assert 'variant not in {"thumbnail", "preview", "original"}' in backend
    assert '"thumbnail": f"{base}/thumbnail?token={token}"' in backend
    assert '"preview": f"{base}/preview?token={token}"' in backend
    assert '"original": f"{base}/original?token={token}"' in backend


def test_024_timeline_keeps_date_only_first_and_sorts_timed_entries_newest_first() -> None:
    frontend = _read(FRONTEND / "animal-health-panel.part77.js")
    assert 'if(ad!==bd)return ad?-1:1' in frontend
    assert 'return bt.localeCompare(at)' in frontend
    assert '`${this.t("today023")} · `' in frontend


def test_024_treatment_execution_is_atomic_optional_idempotent_and_extensible() -> None:
    frontend = _read(FRONTEND / "animal-health-panel.part77.js")
    backend = _read(INTEGRATION / "v0924_features.py")
    polish = _read(INTEGRATION / "v0924_polish.py")
    assert "data-plan-optional024" in frontend
    assert 'name="optional_components"' in frontend
    assert "selected_optional" in backend
    assert "v0924_requests" in backend
    assert '_request_response(connection, request_id, "treatment_execute")' in backend
    assert '"treatment_execution_role": "parent"' in backend
    assert '"treatment_execution_role": "extra" if extra else "component"' in backend
    assert "_edit_treatment_sync" in backend
    assert "_delete_treatment_sync" in backend
    assert "_add_treatment_components_sync" in backend
    assert "_current_execution_rows" in backend
    assert "v0924_auto_deduplicated" in polish
    assert "_dedupe_legacy_treatment_components_sync" in polish
    assert "_treatmentSubmit024" in frontend
    assert "treatmentNotes024" in frontend
    assert "<small>– ${esc(item)}</small>" in frontend
    assert "extraLabel024" in frontend


def test_024_separate_same_time_medications_group_but_date_only_and_treatment_children_do_not() -> None:
    frontend = _read(FRONTEND / "animal-health-panel.part78.js")
    assert 'if(event?.data?.treatment_execution_id||event?.data?.treatment_plan_id)return""' in frontend
    assert 'if(event?.data?.time_precision==="date")return""' in frontend
    assert 'if(batch&&mode==="batch")return`batch:${batch}`' in frontend
    assert 'return animal&&when?`time:${animal}:${when}`:""' in frontend


def test_024_master_data_contains_control_and_reversible_overrides() -> None:
    backend = _read(INTEGRATION / "v0924_features.py")
    frontend = _read(FRONTEND / "animal-health-panel.part77.js")
    capture = _read(INTEGRATION / "v0924_capture.py")
    assert '("control", "Kontrolle", "Control", "observation")' in backend
    assert "CREATE TABLE IF NOT EXISTS v0924_master_items" in backend
    assert "/v0924/master/save" in backend
    assert "/v0924/master/archive" in backend
    assert "/v0924/master/reset" in backend
    assert "masterEditor024" in frontend
    assert "entry-type-save-new-024" in frontend
    assert "symptom-save-new-022" in frontend
    assert "/v0924/event/record" in capture


def test_024_swissmedic_uses_sequences_routes_overrides_and_metacam_fallback() -> None:
    parser = _read(INTEGRATION / "swissmedic_catalog.py")
    backend = _read(INTEGRATION / "v0924_features.py")
    polish = _read(INTEGRATION / "v0924_polish.py")
    assert '"Applikationsarten_pro_Sequenz.XML"' in parser
    assert 'item_id = f"swissmedic.{authorisation}.{sequence_number or \'00\'}"' in parser
    assert '"sequence_number": sequence_number' in parser
    assert '"default_route": route_ids[0] if len(route_ids) == 1 else ""' in parser
    assert "ABLAUFDATUM is not used as an additional filter" in parser
    assert "v0924_catalog_overrides" in backend
    assert '"56764"' in backend
    assert '"Metacam 15 mg/ml ad us. vet., Suspension für Pferde"' in backend
    assert "Deklarationen.XML" in polish
    assert "active_ingredient_details" in polish


def test_024_medication_route_and_active_ingredient_equivalent_are_used_in_ui() -> None:
    frontend = _read(FRONTEND / "animal-health-panel.part77.js")
    patches = _read(INTEGRATION / "v0924_patches.py")
    final = _read(INTEGRATION / "v0924_final.py")
    assert "activeIngredientEquivalent024" in frontend
    assert "equivalentActive024" in frontend
    assert "rich?.default_route" in frontend
    assert 'data["route"] = official["default_route"]' in patches
    assert "treatment_execution_id" in final
    assert "treatment_component_index" in final
