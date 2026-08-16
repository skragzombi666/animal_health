from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_overview_heading_and_global_search_are_removed_in_094() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    part45 = (FRONTEND / "animal-health-panel.part45.js").read_text(encoding="utf-8")

    assert manifest["version"] == "0.9.4"
    assert 'const V="0.9.4",D="animal_health"' in part01
    assert 'if(key==="overview")return""' in part45
    assert "AH094Base.heading.call(this,key,action)" in part45


def test_094_keeps_contextual_searches_available() -> None:
    part42 = (FRONTEND / "animal-health-panel.part42.js").read_text(encoding="utf-8")
    part45 = (FRONTEND / "animal-health-panel.part45.js").read_text(encoding="utf-8")

    assert 'data-action="home-search-toggle-091"' in part42
    assert 'data-home-search091' in part42
    assert 'key==="animals"' not in part45
