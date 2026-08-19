from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_095_multi_select_filters() -> None:
    part46 = (FRONTEND / "animal-health-panel.part46.js").read_text(encoding="utf-8")

    assert "homeGroupFilters095" in part46
    assert "homeTagFilters095" in part46
    assert "new Set(state.groupFilters)" in part46
    assert "animalTags.some(id=>tagSet.has(id))" in part46
    assert 'id==="all"' in part46
    assert "set.has(id)?set.delete(id):set.add(id)" in part46
    assert "homeFilterReset093" in part46
    assert "groups:this.homeGroupFilters095" in part46
    assert "tags:this.homeTagFilters095" in part46


def test_095_relevance_is_dynamic_without_scope_dropdown() -> None:
    part46 = (FRONTEND / "animal-health-panel.part46.js").read_text(encoding="utf-8")

    assert "seriesRelevantItems095" in part46
    assert "isSeriesTask095" in part46
    assert 'recurrence_type||"once")!=="once"' in part46
    assert "dynamicRelevantGroups095" in part46
    assert 'this.t("scopeToday0816")' in part46
    assert 'this.t("thisWeekRelevant095")' in part46
    assert 'this.t("nextWeekRelevant095")' in part46
    assert 'this.t("thisMonthRelevant095")' in part46
    assert 'this.t("nextMonthRelevant095")' in part46
    assert ".filter(group=>group.items.length)" in part46
    assert 'data-overview-scope' not in part46


def test_095_week_start_setting_defaults_to_monday_and_drives_calendar() -> None:
    part46 = (FRONTEND / "animal-health-panel.part46.js").read_text(encoding="utf-8")

    assert 'let value="monday"' in part46
    assert 'animal_health.week_start' in part46
    assert "weekStartIndex095" in part46
    assert "weekBounds095" in part46
    assert 'data-week-start095' in part46
    assert "calendar=function" in part46
    assert "monthStart.getUTCDay()-weekStart+7" in part46
    assert "weekdayMonday095" in part46
    assert "weekdaySunday095" in part46


def test_android_remains_frozen_after_095() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
