from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_015_version_and_ha_menu_are_restored() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    part63 = (FRONTEND / "animal-health-panel.part63.js").read_text(encoding="utf-8")

    assert manifest["version"] in {"0.9.15", "0.9.16", "0.9.17", "0.9.18", "0.9.19", "0.9.20"}
    assert f'const V="{manifest["version"]}",D="animal_health"' in part01
    assert 'class="menuButton" data-action="menu"' in part63
    assert "hass-toggle-menu" in (FRONTEND / "animal-health-panel.part08.js").read_text(encoding="utf-8")


def test_015_medication_search_does_not_rerender_per_character() -> None:
    part63 = (FRONTEND / "animal-health-panel.part63.js").read_text(encoding="utf-8")

    assert '"medSearch013" in input.dataset' in part63
    assert "state.items[index].product_name=input.value" in part63
    assert "renderMedicationSuggestions013(input,true)" in part63
    assert "input.focus({preventScroll:true})" in part63
    assert "planMedOption014" in part63
    assert "medSuggestion013" in part63
    assert "pointer-events:none" in part63


def test_015_medication_edit_preserves_original_event_time() -> None:
    part63 = (FRONTEND / "animal-health-panel.part63.js").read_text(encoding="utf-8")

    assert "localEventFields015" in part63
    assert "openMedicationEdit015" in part63
    assert "date:when.date,time:when.time" in part63
    assert 'if(action==="med-edit-0817")' in part63


def test_015_symptoms_have_master_data_and_multi_capture() -> None:
    part63 = (FRONTEND / "animal-health-panel.part63.js").read_text(encoding="utf-8")
    backend = (INTEGRATION / "v0915_features.py").read_text(encoding="utf-8")
    init = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")

    for marker in (
        "symptomManagement015",
        "symptomChips015",
        "data-symptom-search015",
        "symptom-option-015",
        "symptom-add-free-015",
        "/v0915/symptoms/record",
        "/v0915/symptom/save",
        "/v0915/symptom/archive",
    ):
        assert marker in part63
    assert "CREATE TABLE IF NOT EXISTS v0915_symptoms" in backend
    assert 'event_type="symptom"' in backend
    assert '"symptoms": symptoms' in backend
    assert "async_initialize_v0915_features" in init
    assert "async_setup_v0915_features" in init


def test_015_animal_detail_uses_overlays_and_local_audit() -> None:
    part63 = (FRONTEND / "animal-health-panel.part63.js").read_text(encoding="utf-8")

    for marker in (
        "animal-master-015",
        "animal-photo-015",
        "weight-history-015",
        "task-detail-015",
        "animal-timeline-menu-015",
        "toggle-animal-deleted-015",
        "toggle-animal-changes-015",
        "eventChangeSummary015",
    ):
        assert marker in part63
    assert 'masterDetails082' in part63
    assert "weightChart015" in part63
    assert "taskHistory015" in part63


def test_015_timeline_uses_medication_snapshot_and_multi_symptoms() -> None:
    part63 = (FRONTEND / "animal-health-panel.part63.js").read_text(encoding="utf-8")

    assert "medication_snapshot" in part63
    assert "active_ingredient" in part63
    assert "concentration" in part63
    assert "dosage_form" in part63
    assert 'Array.isArray(event.data?.symptoms)' in part63


def test_015_add_icons_and_animal_menu_state() -> None:
    part63 = (FRONTEND / "animal-health-panel.part63.js").read_text(encoding="utf-8")

    assert "medAddPlus015" in part63
    assert 'icon","mdi:plus-circle"' in part63
    assert "this.animalMenuOpen=false" in part63
    assert 'action==="animal-master-015"' in part63


def test_android_remains_frozen_after_015() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
