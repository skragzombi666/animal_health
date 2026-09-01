from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_030_version_and_patch_registration() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    init = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")

    assert tuple(map(int, manifest["version"].split("."))) >= (0, 9, 30)
    assert f'const V="{manifest["version"]}",D="animal_health"' in part01
    assert "from .v0930_features import apply_v0930_patches" in init
    assert "apply_v0930_patches()" in init


def test_030_product_database_catalogue_has_required_starters() -> None:
    payload = json.loads(
        (INTEGRATION / "catalogs" / "product_databases_0928.json").read_text(
            encoding="utf-8"
        )
    )
    databases = {item["id"]: item for item in payload["databases"]}

    vaccines = json.loads(
        (INTEGRATION / "catalogs" / "vaccines_ch.json").read_text(encoding="utf-8")
    )["items"]
    supplements = databases["animal_health_supplements"]["products"]
    feeds = databases["animal_health_feed_chicken"]["products"]

    assert len(vaccines) >= 14
    assert len(supplements) >= 8
    assert len(feeds) >= 42

    vaccine_names = {item["name"] for item in vaccines}
    supplement_names = {item["name"] for item in supplements}
    feed_names = {item["name"] for item in feeds}

    assert {"Nobivac DHPPi ad us. vet.", "Nobilis IB Ma5 ad us. vet."} <= vaccine_names
    assert {
        "UFA Gallo-Fit",
        "UFA-Antifex",
        "UFA-Antifex Natur",
        "UFA-Mixgrit",
        "AviPro Avian",
        "Anima-Strath® flüssig",
        "Anima-Strath® Granulat",
        "Vetark Nutrobal",
    } <= supplement_names
    assert {"UFA 505", "UFA 506"} <= feed_names


def test_030_all_product_sources_are_visible_and_self_healing() -> None:
    backend = (INTEGRATION / "v0930_features.py").read_text(encoding="utf-8")
    frontend = (FRONTEND / "animal-health-panel.part89.js").read_text(
        encoding="utf-8"
    )

    for marker in (
        "DATABASE_MEDICATION_STARTER",
        "DATABASE_HISTORY",
        "_reconcile_legacy",
        "_seed_history",
        "_assign_unassigned",
        "initialize_product_databases_v0930",
        "state_sync_v0930",
        "v0928_features.state_sync = state_sync_v0930",
    ):
        assert marker in backend

    for marker in (
        "databaseLoadFailed030",
        "databaseEmpty030",
        "db-retry-030",
        "databaseList030",
        "local_history_suggestions",
        "animal_health_medications_ch",
        "databaseCard030",
    ):
        assert marker in frontend
