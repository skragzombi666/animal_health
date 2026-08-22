from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_011_manual_medication_entry() -> None:
    part55 = (FRONTEND / "animal-health-panel.part55.js").read_text(encoding="utf-8")
    part56 = (FRONTEND / "animal-health-panel.part56.js").read_text(encoding="utf-8")

    assert 'manualMedication011:["Medikament auswählen oder direkt eingeben"' in part55
    assert 'name="product_name_${index}"' in part55
    assert '<input name="product_name_${index}"' in part55
    assert '<datalist id="${listId}">' in part55
    assert 'name="planned_medication_name"' in part56
    assert 'list="${listId}"' in part56


def test_011_off_label_disabled_still_shows_all_medications() -> None:
    part55 = (FRONTEND / "animal-health-panel.part55.js").read_text(encoding="utf-8")

    assert 'querySelector:selector=>String(selector).includes("show_off_label")?{}:null' in part55
    assert 'const markOffLabel=Boolean(this.v0817?.off_label_enabled)' in part55
    assert 'custom=(this.v0817?.medications||[]).map' in part55
    assert 'plans=this.treatmentPlansFor011("medication").map' in part55
    assert 'offlabel:Boolean(markOffLabel&&item.species_id&&species&&item.species_id!==species)' in part55
    assert 'Alle Medikamente werden für jedes Tier angezeigt' in part55


def test_011_teilstrich_is_exposed_in_frontend() -> None:
    part55 = (FRONTEND / "animal-health-panel.part55.js").read_text(encoding="utf-8")

    assert 'mark:["Teilstrich","Graduation mark"]' in part55
    assert '"mark"' in (INTEGRATION / "const.py").read_text(encoding="utf-8")
    assert '"mark": "Teilstrich"' in (INTEGRATION / "v0817_patches.py").read_text(encoding="utf-8")


def test_011_treatment_plan_catalogue_surfaces() -> None:
    part55 = (FRONTEND / "animal-health-panel.part55.js").read_text(encoding="utf-8")

    assert 'treatmentPlans011:["Behandlungen & Behandlungspläne"' in part55
    assert 'data-form="v0911-treatment"' in part55
    assert 'name="list_as"' in part55
    assert 'value="medication"' in part55
    assert 'value="task"' in part55
    assert 'value="both"' in part55
    assert 'data-action="delete-treatment-011"' in part55
    assert 'data-treatment-plan011' in part55
    assert 'data-kind="treatment"' in part55
    assert 'this.treatmentPlansFor011("medication")' in part55
    assert 'this.treatmentPlansFor011("task")' in part55


def test_android_remains_frozen_after_011() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
