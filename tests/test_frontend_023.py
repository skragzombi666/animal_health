from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_023_version_is_consistent() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    assert manifest["version"] == "0.9.23"
    assert 'const V="0.9.23",D="animal_health"' in part01


def test_023_date_precision_is_explicit_and_date_only_is_supported() -> None:
    backend = (INTEGRATION / "v0923_features.py").read_text(encoding="utf-8")
    frontend = (FRONTEND / "animal-health-panel.part75.js").read_text(encoding="utf-8")
    assert '"time_precision": precision' in backend
    assert 'result["occurred_date"] = occurred_date' in backend
    assert 'return local_value.astimezone(UTC), "date", day.isoformat()' in backend
    assert "optionalTime023" in frontend
    assert "temporalPair023" in frontend
    assert 'event?.data?.time_precision==="date"' in frontend
    assert 'occurred_date' in frontend
    assert 'occurred_time' in frontend


def test_023_manual_capture_paths_support_date_without_time() -> None:
    backend = (INTEGRATION / "v0923_features.py").read_text(encoding="utf-8")
    frontend = (FRONTEND / "animal-health-panel.part75.js").read_text(encoding="utf-8")
    for command in (
        "/v0923/weight/record",
        "/v0923/event/record",
        "/v0923/medications/record",
        "/v0923/treatment/execute",
    ):
        assert command in backend
        assert command in frontend
    assert "occurred_time" in frontend
    assert "timeHint023" in frontend


def test_023_symptoms_are_persistent_episodes_with_assessments() -> None:
    backend = (INTEGRATION / "v0923_features.py").read_text(encoding="utf-8")
    frontend = (FRONTEND / "animal-health-panel.part75.js").read_text(encoding="utf-8")
    init = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS v0923_symptom_episodes" in backend
    assert "CREATE TABLE IF NOT EXISTS v0923_symptom_assessments" in backend
    assert "/v0923/symptoms/start" in backend
    assert "/v0923/symptom/reassess" in backend
    assert "/v0923/symptom/resolve" in backend
    assert "symptom_episode_id" in backend
    assert "currentSymptoms023" in frontend
    assert "symptom-reassess-023" in frontend
    assert "symptom-resolve-023" in frontend
    assert "episodePeriod023" in frontend
    assert "episodeAssessment023" in frontend
    assert "async_initialize_v0923_features" in init
    assert "async_setup_v0923_features" in init


def test_023_active_symptoms_are_carried_forward_without_daily_database_rows() -> None:
    frontend = (FRONTEND / "animal-health-panel.part76.js").read_text(encoding="utf-8")
    backend = (INTEGRATION / "v0923_features.py").read_text(encoding="utf-8")
    assert "activeEpisodesForTimeline023" in frontend
    assert "episodeCarryEvent023" in frontend
    assert "episode_carry_forward:true" in frontend
    assert "timelineEntry023(this.episodeCarryEvent023" in frontend
    assert "alreadyShown" in frontend
    assert "episode_carry_forward" not in backend


def test_023_symptom_prefix_is_removed() -> None:
    frontend = (FRONTEND / "animal-health-panel.part75.js").read_text(encoding="utf-8")
    assert "legacySymptomCompact023" in frontend
    assert 'symptoms.join(" · ")' not in frontend
    assert 'this.t("symptomsRecorded015")' not in frontend


def test_023_timeline_uses_today_date_only_first_and_time_axis() -> None:
    frontend = (FRONTEND / "animal-health-panel.part75.js").read_text(encoding="utf-8")
    assert "timelineDaySections023" in frontend
    assert "timelineAxisRow023" in frontend
    assert "dayHeader023" in frontend
    assert '`${this.t("today023")} · `' in frontend
    assert "if(ad!==bd)return ad?-1:1" in frontend
    assert "return at.localeCompare(bt)" in frontend
    assert "grid-template-columns:54px minmax(0,1fr)" in frontend
    assert "dateOnly023>time{color:transparent}" in frontend


def test_023_legacy_symptoms_are_not_migrated_to_active_episodes() -> None:
    backend = (INTEGRATION / "v0923_features.py").read_text(encoding="utf-8")
    assert "INSERT INTO v0923_symptom_episodes" in backend
    assert "FROM events WHERE event_type='symptom'" not in backend


def test_android_remains_frozen_after_023() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
