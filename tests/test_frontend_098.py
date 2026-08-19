from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_098_version_and_compact_header_navigation() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    part50 = (FRONTEND / "animal-health-panel.part50.js").read_text(encoding="utf-8")

    assert manifest["version"] == "0.9.8"
    assert 'const V="0.9.8",D="animal_health"' in part01
    assert '[["overview","mdi:view-dashboard"],["timeline","mdi:timeline-clock"],["settings081","mdi:cog-outline"]]' in part50
    assert 'data-view="groups081"' not in part50
    assert 'data-action="refresh"' not in part50
    assert "headerNav098" in part50


def test_098_pull_to_refresh_replaces_visible_refresh_button() -> None:
    part50 = (FRONTEND / "animal-health-panel.part50.js").read_text(encoding="utf-8")

    for marker in (
        "pullToRefresh098",
        "releaseToRefresh098",
        "refreshing098",
        'addEventListener("touchstart"',
        'addEventListener("touchmove"',
        'addEventListener("touchend"',
        "refreshFromPull098",
        "await this.load()",
        "pullRefresh098",
    ):
        assert marker in part50
    assert '{passive:false}' in part50
    assert "dy>=84" in part50


def test_098_home_group_heading_opens_group_detail() -> None:
    part50 = (FRONTEND / "animal-health-panel.part50.js").read_text(encoding="utf-8")

    assert 'action==="home-open-group-091"' in part50
    assert 'this.groupDetailId=id;this.view="group-detail"' in part50
    assert 'this.groupFilter="ungrouped"' in part50


def test_android_remains_frozen_after_098() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
