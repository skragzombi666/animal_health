from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"


def test_batch_layout_uses_vertical_flow_without_visible_overflow_hack() -> None:
    source = (FRONTEND / "animal-health-panel.part32.js").read_text(encoding="utf-8")

    assert "display:flex!important" in source
    assert "flex-direction:column!important" in source
    assert ".aiBatchCard086,.aiBatchCard086.expanded" in source
    assert "overflow:hidden!important" in source
    assert "position:static!important" in source


def test_unmatched_weight_batch_entries_do_not_inherit_context_animal() -> None:
    source = (FRONTEND / "animal-health-panel.part32.js").read_text(encoding="utf-8")

    assert "prepareBatchAssociations0812" in source
    assert 'entry?.capture_mode!=="weight"' in source
    assert "matched_animal_id" in source
    assert 'if(contextIds.has(current))entry.animal_id=""' in source


def test_weight_ai_stays_on_original_single_pass() -> None:
    route = (FRONTEND / "animal-health-panel.part29.js").read_text(encoding="utf-8")

    assert 'p?.mode==="weight"?`${D}/v083/ai/analyze`:type' in route
    assert 'p?.mode==="weight"?`${D}/v088/ai/analyze`:type' not in route
