from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "custom_components" / "animal_health" / "v0934_features.py"
INIT = ROOT / "custom_components" / "animal_health" / "__init__.py"
MANIFEST = ROOT / "custom_components" / "animal_health" / "manifest.json"
FRONTEND_VERSION = (
    ROOT
    / "custom_components"
    / "animal_health"
    / "frontend"
    / "animal-health-panel.part01.js"
)
FRONTEND = FRONTEND_VERSION.parent
LEGACY_MANIFEST = FRONTEND / "legacy" / "manifest.json"
DIST = FRONTEND / "dist" / "animal-health-panel.js"
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
    assert "await async_setup_v0927_features(hass)" in source
    assert "await async_setup_v0928_features(hass)" in source
    assert "\n    async_setup_v0928_features(hass)" not in source


def test_034_release_version_and_shared_bundle_count_are_consistent() -> None:
    version = str(json.loads(MANIFEST.read_text(encoding="utf-8"))["version"])
    assert f'const V="{version}"' in DIST.read_text(encoding="utf-8")

    legacy_manifest = json.loads(LEGACY_MANIFEST.read_text(encoding="utf-8"))
    parts = legacy_manifest["parts"]
    assert legacy_manifest["reference_version"] == "0.9.41"
    assert len(parts) == 99
    assert parts[0].endswith("animal-health-panel.part01.js")
    assert parts[-1].endswith("animal-health-panel.part99.js")

    android = ANDROID.read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in android
    assert "versionCode = 900007" in android
    assert 'resolve("dist/animal-health-panel.js")' in android
    assert "prepareSharedFrontendAssets" in android
    assert "animal-health-panel.part*.js" not in android
    assert "ordered.size ==" not in android
