from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"
MANIFEST = INTEGRATION / "manifest.json"
ANDROID = ROOT / "android" / "app" / "build.gradle.kts"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
RELEASE_NOTES = ROOT / "docs" / "version-0.9.41.md"


def test_041_release_metadata_is_complete_and_consistent() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["version"] == "0.9.41"
    first_part = (FRONTEND / "animal-health-panel.part01.js").read_text(
        encoding="utf-8"
    )
    assert 'const V="0.9.41"' in first_part
    assert RELEASE_NOTES.is_file()
    assert RELEASE_NOTES.read_text(encoding="utf-8").startswith(
        "# Animal Health 0.9.41"
    )


def test_041_frontend_part_count_and_android_freeze_are_explicit() -> None:
    parts = sorted(FRONTEND.glob("animal-health-panel.part*.js"))
    assert len(parts) == 99
    assert parts[-1].name == "animal-health-panel.part99.js"
    android = ANDROID.read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in android
    assert "versionCode = 900007" in android
    assert "ordered.size == 99" in android
    assert "Expected 99 Animal Health frontend parts" in android


def test_041_repository_contains_no_temporary_probe_files() -> None:
    assert not list(ROOT.glob(".tmp*"))
    assert not list(ROOT.glob("__probe*"))


def test_041_release_waits_for_successful_validation() -> None:
    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_run:" in workflow
    assert "workflows:" in workflow
    assert "- Validate" in workflow
    assert "github.event.workflow_run.conclusion == 'success'" in workflow
    assert "github.event.workflow_run.head_branch == 'main'" in workflow
    assert "Missing release notes" in workflow
    assert "on:\n  push:" not in workflow
