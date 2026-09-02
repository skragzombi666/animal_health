from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"
SOURCE = FRONTEND / "animal-health-panel.part95.js"
BASE = FRONTEND / "animal-health-panel.part07.js"


def test_035_overrides_global_block_span_rule_inside_medication_flow() -> None:
    base = BASE.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")

    assert ".stat span,.row span,.row small,.animal span{display:block" in base
    assert ".row.event.gabeCompact034 .gabeFlow034>span{display:inline!important}" in source
    assert ".gabeTypeBadge027" in source
    assert ".scopeBadge026" in source
    assert ".taskSource034{display:inline-flex!important}" in source


def test_035_medication_row_has_one_icon_column_and_one_text_flow() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    for marker in (
        "display:grid!important",
        "grid-template-columns:24px minmax(0,1fr)!important",
        "row-gap:0!important",
        "width:auto!important",
        "white-space:normal!important",
        "word-break:normal!important",
        "overflow-wrap:break-word!important",
    ):
        assert marker in source


def test_035_notes_are_the_only_forced_follow_up_line() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert ".gabeContent034>small{display:block!important" in source
    assert ".gabeFlow034>span{display:block" not in source
