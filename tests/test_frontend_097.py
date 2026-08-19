from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"


def test_097_task_management_view() -> None:
    part49 = (FRONTEND / "animal-health-panel.part49.js").read_text(encoding="utf-8")

    assert 'taskManagement097:["Aufgaben & Serien"' in part49
    assert "taskDefinitionItems097" in part49
    assert "taskManagementRow097" in part49
    assert 'data-action="edit-task-097"' in part49
    assert 'data-action="toggle"' in part49
    assert 'data-form="task-edit-097"' in part49
    assert 'this.svc("update_task",payload,true)' in part49
    assert 'this.group("overdue"' not in part49
    assert 'this.group("completed"' not in part49


def test_097_due_series_move_into_dynamic_time_sections() -> None:
    part49 = (FRONTEND / "animal-health-panel.part49.js").read_text(encoding="utf-8")

    assert "seriesPendingItem097" in part49
    assert 'bucket:key===todayKey?"today":"overdue"' in part49
    assert 'state097:"unconfirmed"' in part49
    assert 'bucket:"today"' in part49
    assert 'overdueUnconfirmed097' in part49
    assert 'todayRelevant097' in part49
    assert 'item.series097?this.seriesRow097(item)' in part49
    assert "missedCount" in part49


def test_097_calendar_has_status_colours_and_direct_execution() -> None:
    part49 = (FRONTEND / "animal-health-panel.part49.js").read_text(encoding="utf-8")

    for marker in (
        "calendarState-planned",
        "calendarState-due",
        "calendarState-unconfirmed",
        "calendarState-completed",
        "calendarState-stopped",
        "calendarLegend097",
        'data-action="execute"',
    ):
        assert marker in part49
    assert '["skipped","cancelled"]' in part49
    assert 'occurrence?.status==="completed"' in part49


def test_097_animal_timeline_contains_compact_series_status() -> None:
    part49 = (FRONTEND / "animal-health-panel.part49.js").read_text(encoding="utf-8")

    assert "animalSeriesStatus097" in part49
    assert "animalSeriesStatusRow097" in part49
    assert 'seriesStatus097:["Serienstatus"' in part49
    assert "unconfirmed097" in part49
    assert "skippedOn097" in part49
    assert "cancelledOn097" in part49
    assert 'html.replace(marker,card+marker)' in part49


def test_android_remains_frozen_after_097() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
