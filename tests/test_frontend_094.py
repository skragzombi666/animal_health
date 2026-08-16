from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_overview_heading_and_global_search_are_removed_in_094() -> None:
    part45 = (FRONTEND / "animal-health-panel.part45.js").read_text(encoding="utf-8")

    assert 'if(key==="overview")return""' in part45
    assert "AH094Base.heading.call(this,key,action)" in part45


def test_094_keeps_contextual_searches_available() -> None:
    part42 = (FRONTEND / "animal-health-panel.part42.js").read_text(encoding="utf-8")
    part45 = (FRONTEND / "animal-health-panel.part45.js").read_text(encoding="utf-8")

    assert 'data-action="home-search-toggle-091"' in part42
    assert 'data-home-search091' in part42
    assert 'key==="animals"' not in part45


def test_filter_reset_is_inserted_before_stable_filter_controls() -> None:
    part44 = (FRONTEND / "animal-health-panel.part44.js").read_text(encoding="utf-8")

    assert "homeFilterReset093" in part44
    assert "html=html.replace('<div class=\"homeAnimalTools092\" role=\"toolbar\">','<div class=\"homeAnimalTools092\" role=\"toolbar\">'+reset)" in part44
    assert 'mdi:close-circle-outline' in part44
