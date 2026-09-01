from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"


def test_032_timeline_counts_share_header_row() -> None:
    frontend = (FRONTEND / "animal-health-panel.part91.js").read_text(encoding="utf-8")
    for marker in (
        ".timelinePeriod029>.dayHeader023",
        "display:flex!important",
        "flex-direction:row!important",
        "justify-content:space-between!important",
        "margin:0 0 0 auto!important",
        "text-align:right!important",
    ):
        assert marker in frontend
