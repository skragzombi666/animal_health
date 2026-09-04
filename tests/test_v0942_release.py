from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"
MANIFEST = INTEGRATION / "manifest.json"
LEGACY_MANIFEST = FRONTEND / "legacy" / "manifest.json"
DIST = FRONTEND / "dist" / "animal-health-panel.js"
PANEL = INTEGRATION / "panel.py"
README = ROOT / "README.md"
ANDROID = ROOT / "android" / "app" / "build.gradle.kts"
ANDROID_WORKFLOW = ROOT / ".github" / "workflows" / "android.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
RELEASE_NOTES = ROOT / "docs" / "version-0.9.42.md"


def test_042_release_metadata_is_complete_and_consistent() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["version"] == "0.9.42"
    assert RELEASE_NOTES.is_file()
    notes = RELEASE_NOTES.read_text(encoding="utf-8")
    assert notes.startswith("# Animal Health 0.9.42")
    assert "Konsolidierungs-Checkpoint" in notes
    assert "overview" in notes
    assert "animals" in notes
    assert "animal-detail" in notes

    readme = README.read_text(encoding="utf-8")
    assert "Die aktuelle Version ist **0.9.42**" in readme
    assert "modulare" in readme.lower()


def test_042_current_release_and_frozen_legacy_reference_are_separate() -> None:
    legacy_manifest = json.loads(LEGACY_MANIFEST.read_text(encoding="utf-8"))
    assert legacy_manifest["reference_version"] == "0.9.41"
    assert len(legacy_manifest["parts"]) == 99

    bundle = DIST.read_text(encoding="utf-8")
    assert 'const V="0.9.41",D="animal_health"' in bundle
    assert bundle.count("ANIMAL_HEALTH_MODERN_RUNTIME") == 1

    panel = PANEL.read_text(encoding="utf-8")
    assert "version = _integration_version()" in panel
    assert "f'const V=\"{version}\",D=\"animal_health\";'" in panel
    assert "FRONTEND_REVISION = _frontend_revision()" in panel


def test_042_android_remains_a_separate_alpha_but_runs_for_release_changes() -> None:
    android = ANDROID.read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in android
    assert "versionCode = 900007" in android

    workflow = ANDROID_WORKFLOW.read_text(encoding="utf-8")
    assert '"custom_components/animal_health/manifest.json"' in workflow
    assert '"docs/version-*.md"' in workflow
    assert "npm run test:frontend" in workflow
    assert "gradle -p android :app:assembleDebug" in workflow


def test_042_release_requires_successful_main_validation() -> None:
    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_run:" in workflow
    assert "- Validate" in workflow
    assert "github.event.workflow_run.conclusion == 'success'" in workflow
    assert "github.event.workflow_run.head_branch == 'main'" in workflow
    assert "Missing release notes" in workflow
    assert 'TAG="v${VERSION}"' in workflow


def test_042_repository_contains_no_temporary_release_automation() -> None:
    assert not (ROOT / ".github/workflows/prepare-0942.yml").exists()
    assert not (ROOT / "scripts/prepare_release_0942.py").exists()
