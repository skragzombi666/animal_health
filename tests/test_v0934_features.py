from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "custom_components" / "animal_health" / "v0934_features.py"
INIT = ROOT / "custom_components" / "animal_health" / "__init__.py"
MANIFEST = ROOT / "custom_components" / "animal_health" / "manifest.json"
ANDROID = ROOT / "android" / "app" / "build.gradle.kts"


def test_034_treatment_task_repair_persists_complete_event_identity() -> None:
    source = FEATURES.read_text(encoding="utf-8")
    for marker in (
        "_repair_treatment_event_sync",
        "task_occurrence_plans",
        '"source": "task"',
        '"treatment_execution_role": "parent"',
        '"treatment_execution_role": "component"',
        '"treatment_plan_components"',
        '"treatment_parent_event_id"',
        "task_id=COALESCE(task_id, ?)",
        "task_occurrence_id=COALESCE(task_occurrence_id, ?)",
        "_repair_existing_treatment_events_sync",
    ):
        assert marker in source


def test_034_task_completion_history_is_enriched_from_database() -> None:
    source = FEATURES.read_text(encoding="utf-8")
    for marker in (
        "_enrich_task_completion_stats_sync",
        "pending_count",
        "completed_count",
        "last_completed_at",
        "TaskRecordStore.enrich_tasks",
    ):
        assert marker in source


def test_034_backend_patch_is_wired_after_earlier_versions() -> None:
    source = INIT.read_text(encoding="utf-8")
    assert "from .v0934_features import" in source
    assert source.index("apply_v0930_patches()") < source.index("apply_v0934_patches()")
    assert "await async_initialize_v0934_features(hass)" in source


def test_034_versions_and_android_bundle_count_are_updated() -> None:
    assert '"version": "0.9.34"' in MANIFEST.read_text(encoding="utf-8")
    android = ANDROID.read_text(encoding="utf-8")
    assert "versionCode = 8" in android
    assert 'versionName = "0.9.34"' in android
    assert "ordered.size == 42" in android
