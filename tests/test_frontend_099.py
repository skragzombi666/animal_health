from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"


def test_099_pull_refresh_binding() -> None:
    part51 = (FRONTEND / "animal-health-panel.part51.js").read_text(encoding="utf-8")

    assert "bindPullRefresh099" in part51
    assert 'this.addEventListener("touchstart"' in part51
    assert 'this.addEventListener("touchmove"' in part51
    assert '{passive:false,capture:true}' in part51
    assert 'AH099.render=function(){AH099Base.render.call(this);this.bindPullRefresh099()' in part51
    assert "connectedCallback" not in part51
    assert "dy>=76" in part51


def test_099_virtual_past_calendar_items_are_executable() -> None:
    part51 = (FRONTEND / "animal-health-panel.part51.js").read_text(encoding="utf-8")

    for marker in (
        'data-action="calendar-execute-099"',
        'data-task-id=',
        'data-date=',
        'this.svc("list_task_occurrences"',
        'task_scope:"all"',
        'status:"pending"',
        "findOccurrenceResponse099",
        "decorateOccurrence099",
        "upsertOccurrence099",
        'this.open("execute",{occurrenceId:occurrence.id})',
    ):
        assert marker in part51
    assert '["due","unconfirmed"].includes(state.key)&&!state.occurrence' in part51


def test_android_remains_frozen_after_099() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
