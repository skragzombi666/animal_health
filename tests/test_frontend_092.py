from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_home_overview_092_polish() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    part43 = (FRONTEND / "animal-health-panel.part43.js").read_text(encoding="utf-8")

    assert manifest["version"] == "0.9.2"
    assert 'const V="0.9.2",D="animal_health"' in part01

    assert "homeAnimalsHead092" in part43
    assert "homeAnimalTools092" in part43
    assert "homeIconTool092" in part43
    assert 'mdi:account-group-outline' in part43
    assert 'mdi:tag-multiple-outline' in part43
    assert 'mdi:magnify' in part43

    assert "homeFilterOption092" in part43
    assert "selected092" in part43
    assert 'aria-pressed=' in part43
    assert 'mdi:check' in part43

    assert "homeUngroupedTiles092" in part43
    assert 'aria-label="${esc(this.t("ungrouped"))}"' in part43
    assert 'homeAnimalGroup091("ungrouped"' not in part43

    assert "homeAnimalVisualSlot092" in part43
    assert "grid-template-rows:48px minmax(18px,auto)" in part43
    assert "homeAnimalName092" in part43

    assert 'actionNowHead actionNowHead0816' in part43
    assert 'overviewScope0816||"today"' in part43
    assert ".homeAnimalsHead092 h2,.quickCaptureHead091 h2,.actionNowHead0816 h2" in part43


def test_release_092_is_explicitly_latest_without_android_build() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert '--latest' in workflow
    assert "gradle" not in workflow.lower()
    assert "apk" not in workflow.lower()
