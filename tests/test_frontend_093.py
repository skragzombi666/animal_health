from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_dashboard_cleanup_093() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    part44 = (FRONTEND / "animal-health-panel.part44.js").read_text(encoding="utf-8")

    assert manifest["version"] == "0.9.3"
    assert 'const V="0.9.3",D="animal_health"' in part01

    assert 'animal_health.home_animal_filters' in part44
    assert "restoreHomeFilters093" in part44
    assert "persistHomeFilters093" in part44
    assert 'home-group-select-091' in part44
    assert 'home-tag-select-091' in part44

    assert "home-filter-reset-093" in part44
    assert "homeFilterReset093" in part44
    assert 'mdi:close-circle-outline' in part44
    assert 'var(--error-color,#db4437)' in part44
    assert 'this.homeGroupFilter091="all"' in part44
    assert 'this.homeTagFilter091="all"' in part44
    assert 'this.homeAnimalSearch091=""' in part44

    assert 'class="heading"' in part44
    assert 'label class="search"' in part44
    assert ".homeAnimalTile092{place-items:center!important" in part44
    assert ".homeAnimalName092{width:100%!important;text-align:center!important" in part44


def test_android_remains_frozen_for_093() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
