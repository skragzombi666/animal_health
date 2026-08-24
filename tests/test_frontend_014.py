from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_014_version_and_settings_alignment() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    part62 = (FRONTEND / "animal-health-panel.part62.js").read_text(encoding="utf-8")

    assert manifest["version"] in {"0.9.14", "0.9.15", "0.9.16", "0.9.17", "0.9.18"}
    assert f'const V="{manifest["version"]}",D="animal_health"' in part01
    assert "header nav{flex:1 1 auto!important" in part62
    assert "justify-content:flex-end!important" in part62
    assert "padding-right:0!important" in part62


def test_014_treatment_plan_uses_medication_picker() -> None:
    part62 = (FRONTEND / "animal-health-panel.part62.js").read_text(encoding="utf-8")

    assert "data-plan-med-search014" in part62
    assert "planMedSuggest014" in part62
    assert "medicationOptionsForSpecies012" in part62
    assert "medicationOptionMarkup013" in part62
    assert "medicationSearchText013" in part62
    assert "plan-med-option-014" in part62


def test_014_routes_are_localised() -> None:
    part62 = (FRONTEND / "animal-health-panel.part62.js").read_text(encoding="utf-8")

    expected = {
        'topical:["Topisch","Topical"]',
        'subcutaneous:["Subkutan","Subcutaneous"]',
        'intramuscular:["Intramuskulär","Intramuscular"]',
        'intravenous:["Intravenös","Intravenous"]',
        'eye:["Auge","Eye"]',
        'ear:["Ohr","Ear"]',
    }
    for marker in expected:
        assert marker in part62


def test_014_coffee_spoon_is_a_supported_dose_unit() -> None:
    const = (INTEGRATION / "const.py").read_text(encoding="utf-8")
    exports = (INTEGRATION / "v0817_patches.py").read_text(encoding="utf-8")
    selectors = (INTEGRATION / "v0911_patches.py").read_text(encoding="utf-8")
    part62 = (FRONTEND / "animal-health-panel.part62.js").read_text(encoding="utf-8")

    assert '"coffee_spoon"' in const
    assert '"coffee_spoon": "Kaffeelöffel"' in exports
    assert '("coffee_spoon", "Kaffeelöffel" if german else "Coffee spoon")' in selectors
    assert 'coffee_spoon:["Kaffeelöffel","Coffee spoon"]' in part62


def test_014_recurring_overdue_and_current_occurrence_are_both_visible() -> None:
    part62 = (FRONTEND / "animal-health-panel.part62.js").read_text(encoding="utf-8")

    assert "latestOverdue=overdue.length?overdue[overdue.length-1]:null" in part62
    assert "if(latestOverdue)result.push" in part62
    assert "key>=todayKey&&key<=endKey" in part62
    assert "if(key&&(!latestOverdue||key!==this.occurrenceDate0816(latestOverdue)))result.push" in part62


def test_android_remains_frozen_after_014() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
