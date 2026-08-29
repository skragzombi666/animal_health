from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_022_version_is_consistent() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    assert manifest["version"] in {"0.9.22", "0.9.23", "0.9.24", "0.9.25", "0.9.26"}
    assert f'const V="{manifest["version"]}",D="animal_health"' in part01


def test_022_quick_capture_has_no_plus_badges_and_no_primary_weight_tile() -> None:
    frontend = (FRONTEND / "animal-health-panel.part70.js").read_text(encoding="utf-8")
    assert '["record-weight","mdi:scale","recordWeight",false]' in frontend
    assert 'captureIcon019=function(icon){return`<span class="captureIcon019"><ha-icon icon="${icon}"></ha-icon></span>`}' in frontend
    assert ".capturePlus019,.capturePlus016{display:none!important}" in frontend
    assert '<ha-icon icon="mdi:plus"></ha-icon>' not in frontend
    assert 'button.classList.remove("captureTile016","primary")' in frontend


def test_022_event_actions_are_icon_only_on_mobile_and_icon_plus_text_on_desktop() -> None:
    frontend = (FRONTEND / "animal-health-panel.part74.js").read_text(encoding="utf-8")
    assert "actionLabel022" in frontend
    assert ".actionLabel022{display:inline}" in frontend
    assert ":host([narrow]) .actionLabel022{display:none!important}" in frontend
    assert "@media(max-width:700px)" in frontend
    assert ".actionLabel022{display:none!important}" in frontend
    assert '"med-edit-0817","mdi:pencil-outline"' in frontend
    assert '"med-repeat-0817","mdi:repeat"' in frontend
    assert '"delete-event-013","mdi:delete-outline"' in frontend


def test_022_copy_actions_are_removed_from_runtime_ui() -> None:
    frontend = (FRONTEND / "animal-health-panel.part74.js").read_text(encoding="utf-8")
    assert "removeCopyActions022" in frontend
    assert "med-copy-0817|treatment-copy-021|batch-copy-021" in frontend
    assert '["med-copy-0817","treatment-copy-021","batch-copy-021"].includes(action)' in frontend


def test_022_unknown_symptoms_can_be_saved_without_losing_form_state() -> None:
    frontend = (FRONTEND / "animal-health-panel.part74.js").read_text(encoding="utf-8")
    assert "saveNewSymptom022" in frontend
    assert 'data-action="symptom-save-new-022"' in frontend
    assert '`${D}/v0915/symptom/save`' in frontend
    assert "refreshSymptomChips022" in frontend
    assert "AH022.addSymptomChoice015=function" in frontend
    assert "this.refreshSymptomChips022()" in frontend
    assert 'if(action==="symptom-remove-015")' in frontend
    add_body = frontend.split("AH022.addSymptomChoice015=function", 1)[1].split(";\nAH022.handleClick", 1)[0]
    assert "this.render()" not in add_body


def test_022_unknown_products_can_be_saved_from_medication_capture() -> None:
    frontend = (FRONTEND / "animal-health-panel.part74.js").read_text(encoding="utf-8")
    assert "saveNewProduct022" in frontend
    assert "renderMedicationSuggestions013=function" in frontend
    assert 'data-action="product-save-new-022"' in frontend
    assert '`${D}/v0913/medication/save`' in frontend
    assert "productExactKnown022" in frontend
    assert "applyMedicationChoice013(input,name)" in frontend


def test_android_remains_frozen_after_022() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
