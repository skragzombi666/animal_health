from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_028_version_is_consistent_and_android_stays_frozen() -> None:
    manifest = json.loads(_read(INTEGRATION / "manifest.json"))
    part01 = _read(FRONTEND / "animal-health-panel.part01.js")
    gradle = _read(ROOT / "android" / "app" / "build.gradle.kts")
    assert manifest["version"] == "0.9.28"
    assert 'const V="0.9.28",D="animal_health"' in part01
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert "versionCode = 900007" in gradle


def test_028_database_backend_is_registered() -> None:
    backend = "".join(
        _read(INTEGRATION / name)
        for name in (
            "v0928_schema.py",
            "v0928_catalog.py",
            "v0928_data.py",
            "v0928_features.py",
        )
    )
    init = _read(INTEGRATION / "__init__.py")
    for marker in (
        "CREATE TABLE IF NOT EXISTS v0928_product_databases",
        'DATABASE_SWISSMEDIC = "swissmedic_ch"',
        'DATABASE_DEWORMERS = "swissmedic_dewormers"',
        'DATABASE_SUPPLEMENTS = "animal_health_supplements"',
        'DATABASE_FEEDS = "animal_health_feed_chicken"',
        "supports_local_overrides",
        "/v0928/database/import",
        "/v0928/product/save",
        "medication_snapshot_for_name",
    ):
        assert marker in backend
    assert "async_initialize_v0928_features" in init
    assert "async_setup_v0928_features" in init
    assert "apply_v0928_patches" in init


def test_028_bundled_feed_and_supplement_data_are_structured() -> None:
    catalog = json.loads(
        _read(INTEGRATION / "catalogs" / "product_databases_0928.json")
    )
    products = {
        item["name"]: item
        for database in catalog["databases"]
        for item in database["products"]
    }
    assert products["UFA 505"]["kind"] == "feed"
    assert products["UFA 506"]["kind"] == "feed"
    assert products["UFA 505"]["feed_form"] == "Expandat"
    assert products["UFA 506"]["feed_form"] == "Körner"
    assert products["UFA Gallo-Fit"]["kind"] == "supplement"
    assert len(products["UFA Gallo-Fit"]["active_components"]) > 1
    assert products["UFA-Antifex"]["active_components"][0]["category"] == "probiotic"
    for name in ("UFA 505", "UFA 506"):
        assert products[name]["analytical_components"]
        assert "active_ingredient" not in products[name]


def test_028_frontend_is_database_centred_and_type_specific() -> None:
    frontend = "".join(
        _read(FRONTEND / f"animal-health-panel.part{part}.js")
        for part in (87, 88, 89, 90, 91, 92)
    )
    for marker in (
        "productDatabases028",
        "databaseExportDocument028",
        "database-import-file-028",
        "active_components",
        "analytical_components",
        "feed_type",
        "feed_form",
        "settingsCapture028",
        "classifySettingCard028",
        "legacySettingsBySection028",
        '.gabeDose027{font-weight:600!important}',
        '.capturePlus016,.capturePlus019,.capturePlus027',
    ):
        assert marker in frontend
    assert 'section==="medications"' in frontend
    assert 'return"danger"' in frontend
    assert 'return"data"' in frontend
    assert 'return"capture"' in frontend


def test_028_release_notes_exist() -> None:
    notes = _read(ROOT / "docs" / "version-0.9.28.md")
    for marker in (
        "Produktdatenbanken",
        "Swissmedic – Entwurmungsmittel",
        "UFA 505",
        "UFA 506",
        "Erfassung & Vorschläge",
        "Test & Gefahrenbereich",
    ):
        assert marker in notes
