from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

from custom_components.animal_health.swissmedic_catalog import (
    SWISSMEDIC_DATASET_ID,
    SWISSMEDIC_OGD_URL,
    parse_swissmedic_ogd_zip,
)

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def _xml(rows: list[dict[str, str]]) -> bytes:
    items = []
    for row in rows:
        fields = "".join(f"<{key}>{value}</{key}>" for key, value in row.items())
        items.append(f"<ROW>{fields}</ROW>")
    return ("<DATA>" + "".join(items) + "</DATA>").encode()


def _swissmedic_fixture() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(
            "Praeparate.XML",
            _xml(
                [
                    {
                        "VERWENDUNG": "TAM",
                        "ZULASSUNGSNUMMER": "66759",
                        "PRAEPARATENAME": "Eradia 125 mg/ml ad us. vet., orale Suspension für Hunde",
                        "ARZNEIFORM": "SUSP",
                        "ZULASSUNGSSTATUS": "A",
                        "ANWENDUNGSGEBIET": "Hunde",
                        "ABLAUFDATUM": "2030-12-31",
                    },
                    {
                        "VERWENDUNG": "HAM",
                        "ZULASSUNGSNUMMER": "100001",
                        "PRAEPARATENAME": "Human Test",
                        "ARZNEIFORM": "TAB",
                        "ZULASSUNGSSTATUS": "A",
                    },
                ]
            ),
        )
        archive.writestr(
            "Sequenzen.XML",
            _xml(
                [
                    {
                        "ZULASSUNGSNUMMER": "66759",
                        "SEQUENZNUMMER": "01",
                        "SEQUENZNAME": "Eradia 125 mg/ml",
                    }
                ]
            ),
        )
        archive.writestr(
            "Deklarationen.XML",
            _xml(
                [
                    {
                        "ZULASSUNGSNUMMER": "66759",
                        "SEQUENZNUMMER": "01",
                        "STOFF_ID": "metronidazol",
                        "STOFFKATEGORIE": "W",
                    }
                ]
            ),
        )
        archive.writestr(
            "Stoff-Synonyme.XML",
            _xml(
                [
                    {
                        "STOFF_ID": "metronidazol",
                        "SYNONYM_CODE": "LN",
                        "STOFFSYNONYM": "Metronidazol",
                    }
                ]
            ),
        )
        archive.writestr(
            "User-Defined-Codes.XML",
            _xml(
                [
                    {
                        "USER_DEFINED_CODE": "MA_STATUS",
                        "CODE_VALUE": "A",
                        "BESCHREIBUNG_1": "zugelassen",
                    },
                    {
                        "USER_DEFINED_CODE": "DF",
                        "CODE_VALUE": "SUSP",
                        "BESCHREIBUNG_2": "Suspension",
                    },
                    {
                        "USER_DEFINED_CODE": "SUBSTANCE_CATEGORY",
                        "CODE_VALUE": "W",
                        "BESCHREIBUNG_1": "Wirkstoff",
                    },
                ]
            ),
        )
        archive.writestr("Export-Datum.XML", _xml([{"EXPORT_DATUM": "2026-07-31"}]))
    return output.getvalue()


def test_020_version_is_consistent() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    assert manifest["version"] == "0.9.20"
    assert 'const V="0.9.20",D="animal_health"' in part01


def test_020_swissmedic_parser_filters_tam_and_keeps_eradia_metadata() -> None:
    snapshot, products = parse_swissmedic_ogd_zip(_swissmedic_fixture())
    assert snapshot == "2026-07-31"
    assert len(products) == 1
    eradia = products[0]
    assert eradia["authorisation_number"] == "66759"
    assert eradia["name"].startswith("Eradia 125 mg/ml")
    assert eradia["active_ingredient"] == "Metronidazol"
    assert eradia["concentration"] == "125 mg/ml"
    assert eradia["dosage_form"] == "Suspension"
    assert eradia["source_id"] == "swissmedic_ch"


def test_020_official_catalog_is_persistent_and_refreshed() -> None:
    backend = (INTEGRATION / "v0920_features.py").read_text(encoding="utf-8")
    parser = (INTEGRATION / "swissmedic_catalog.py").read_text(encoding="utf-8")
    init = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")
    assert SWISSMEDIC_DATASET_ID == "ZL172@swissmedic"
    assert SWISSMEDIC_OGD_URL in parser
    assert "CREATE TABLE IF NOT EXISTS v0920_catalog_sources" in backend
    assert "CREATE TABLE IF NOT EXISTS v0920_catalog_products" in backend
    assert "VERWENDUNG" in parser and '!= "TAM"' in parser
    assert "len(products) < 100" in backend
    assert "Eradia 125 mg/ml ad us. vet." in backend
    assert "async_refresh_v0920_catalog(hass)" in init
    assert "async_track_time_interval" in init
    assert "timedelta(hours=24)" in init


def test_020_favorites_cover_catalog_manual_and_treatment_plans() -> None:
    backend = (INTEGRATION / "v0920_features.py").read_text(encoding="utf-8")
    frontend = (FRONTEND / "animal-health-panel.part71.js").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS v0920_favorites" in backend
    assert "/v0920/favorite/toggle" in backend
    assert "/v0920/favorite/order" in backend
    assert 'catalog:${item.source_id||"swissmedic_ch"}:${item.id}' in frontend
    assert "manual:${item.id}" in frontend
    assert "treatment:${plan.id}" in frontend
    assert "favoriteRank020" in frontend
    assert "medicationOptionsForSpecies012=function" in frontend
    assert "treatmentPlansForSpecies012=function" in frontend
    assert "favorite-up-020" in frontend and "favorite-down-020" in frontend
    assert "favoriteStar020" in frontend


def test_020_swissmedic_catalog_replaces_curated_selector_source() -> None:
    frontend = (FRONTEND / "animal-health-panel.part71.js").read_text(encoding="utf-8")
    assert "this.v083.medicines=official" in frontend
    assert "this.v0913.catalog_products=official" in frontend
    assert '`${D}/v0920/state`' in frontend
    assert "catalogSourceCard020" in frontend
    assert "ZL172" not in frontend  # source metadata comes from backend state, not duplicated UI constants


def test_020_treatment_timeline_is_collapsed_with_indented_children() -> None:
    frontend = (FRONTEND / "animal-health-panel.part71.js").read_text(encoding="utf-8")
    assert "treatmentSummaryForChild020" in frontend
    assert "treatmentChildren020" in frontend
    assert "toggle-treatment-020" in frontend
    assert "expandedTreatments020" in frontend
    assert "treatmentChildren020" in frontend
    assert "margin:2px 0 6px 26px" in frontend
    assert "border-left:2px solid var(--divider-color)" in frontend
    assert 'if(this.treatmentSummaryForChild020(event,list))return""' in frontend
    assert "AH020Base.eventCompact0817.call(this,child)" in frontend


def test_020_official_metadata_is_snapshotted_for_history() -> None:
    patches = (INTEGRATION / "v0920_patches.py").read_text(encoding="utf-8")
    assert '"source": "official_catalog"' in patches
    assert '"authorisation_number"' in patches
    assert '"catalog_source_id"' in patches
    assert 'data["medication_snapshot"] = snapshot' in patches


def test_android_remains_frozen_after_020() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
