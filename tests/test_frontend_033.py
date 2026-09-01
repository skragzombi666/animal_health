from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"


def test_033_medication_dose_exists_only_once_and_moves_when_title_wraps() -> None:
    frontend = (FRONTEND / "animal-health-panel.part92.js").read_text(encoding="utf-8")

    assert 'class="gabeDose033"' in frontend
    assert 'class="gabeDoseTop033"' not in frontend
    assert 'class="gabeDoseInline033"' not in frontend
    assert "titleLine.insertBefore(dose,title)" in frontend
    assert "title.getClientRects().length>1" in frontend
    assert 'row.classList.add("doseInline033")' in frontend
    assert ".doseInline033 .gabeTopSep033{display:none}" in frontend
    assert ".doseInline033.local033 .gabeTop033" in frontend


def test_033_internal_navigation_uses_browser_history() -> None:
    frontend = (FRONTEND / "animal-health-panel.part92.js").read_text(encoding="utf-8")

    for marker in (
        "__animalHealthNav033",
        'addEventListener("popstate"',
        'removeEventListener("popstate"',
        "history.pushState",
        "history.replaceState",
        "history.back()",
        "restoreNavSnapshot033",
        "loadDetail(snapshot.animalId,false)",
        "groupDetailId",
        "settingsSection027",
    ):
        assert marker in frontend


def test_033_root_history_entry_stays_at_depth_zero() -> None:
    frontend = (FRONTEND / "animal-health-panel.part92.js").read_text(encoding="utf-8")

    assert "this.writeNavEntry033(this.navSnapshot033(),{depth:0})" in frontend
    assert "if(backward&&depth>0)" in frontend
    assert "depth:depth+1" in frontend
    assert "if(marker)void this.restoreNavSnapshot033(marker)" in frontend
