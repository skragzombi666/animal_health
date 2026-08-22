from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"


def test_010_confirmation_controls() -> None:
    part52 = (FRONTEND / "animal-health-panel.part52.js").read_text(encoding="utf-8")
    part54 = (FRONTEND / "animal-health-panel.part54.js").read_text(encoding="utf-8")

    assert 'confirmationMode010:["Bestätigungsmodus"' in part52
    assert 'confirmationRequired010:["Einzelbestätigung erforderlich"' in part52
    assert 'confirmationRoutine010:["Routine ohne Einzelbestätigung"' in part52
    assert 'name="confirmation_mode"' in part52
    assert 'confirmationDefault010' in part52
    assert '["reminder","care"]' in part52
    assert '/confirmation/mode/update' in part52
    assert "syncEditConfirmation010" in part54
    assert 'form?.dataset.form==="task-edit-097"' in part54
    assert '["recurrence_type","confirmation_mode"]' in part54


def test_010_period_based_relevance_and_neutral_undocumented_state() -> None:
    part52 = (FRONTEND / "animal-health-panel.part52.js").read_text(encoding="utf-8")
    part53 = (FRONTEND / "animal-health-panel.part53.js").read_text(encoding="utf-8")

    assert 'start:this.dateKey0815(bounds.start)' in part52
    assert 'day.getUTCMonth(),1' in part52
    assert 'mode==="required"?pending.filter' in part52
    assert 'bucket:this.currentBucket010(task)' in part52
    assert 'type==="weekly"?"thisWeek"' in part52
    assert 'type==="monthly"?"thisMonth"' in part52
    assert 'key:"undocumented"' in part52
    assert 'key:"overdue"' in part52
    assert 'calendarState-undocumented' in part53
    assert 'calendarState-overdue' in part53
    assert 'undocumented:"mdi:help"' in part53
    assert 'overdue:"mdi:alert-outline"' in part53


def test_010_undocumented_calendar_entries_remain_clickable() -> None:
    part53 = (FRONTEND / "animal-health-panel.part53.js").read_text(encoding="utf-8")

    assert '["due","overdue","undocumented"].includes(state.key)' in part53
    assert '["pending","not_documented"].includes(state.occurrence.status)' in part53
    assert 'status:"all"' in part53
    assert '["pending","not_documented"].includes(item.status)' in part53
    assert 'data-action="calendar-execute-099"' in part53


def test_010_week_start_is_shared_with_backend() -> None:
    part52 = (FRONTEND / "animal-health-panel.part52.js").read_text(encoding="utf-8")

    assert 'this.v081?.settings?.week_start' in part52
    assert '/confirmation/week_start/update' in part52
    assert 'this.v081.settings.week_start=value' in part52


def test_android_remains_frozen_after_010() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
