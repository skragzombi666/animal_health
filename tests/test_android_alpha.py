from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "android"
APP = ANDROID / "app"


def test_android_alpha_project_is_version_aligned_and_standalone() -> None:
    manifest = json.loads(
        (ROOT / "custom_components" / "animal_health" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    version = manifest["version"]
    assert version == "0.9.0-alpha.1"

    gradle = (APP / "build.gradle.kts").read_text(encoding="utf-8")
    android_manifest = (APP / "src" / "main" / "AndroidManifest.xml").read_text(
        encoding="utf-8"
    )
    activity = (
        APP / "src" / "main" / "java" / "ch" / "animalhealth" / "app" / "MainActivity.java"
    ).read_text(encoding="utf-8")
    database = (
        APP
        / "src"
        / "main"
        / "java"
        / "ch"
        / "animalhealth"
        / "app"
        / "AnimalHealthDatabase.java"
    ).read_text(encoding="utf-8")

    assert f'versionName = "{version}"' in gradle
    assert 'applicationId = "ch.animalhealth.app"' in gradle
    assert "android.intent.action.MAIN" in android_manifest
    assert "Home Assistant" in activity
    assert "Medikationen dieses Tages erneut vorbereiten" in activity
    assert "Nochmals verabreichen" in activity
    assert "Kopieren" in activity
    assert "Bearbeiten" in activity
    assert "+ Weiteres Medikament" in activity
    assert "CREATE TABLE animals" in database
    assert "CREATE TABLE events" in database
    assert "CREATE TABLE tasks" in database
    assert "CREATE TABLE medications" in database
    assert "addMedicationBatch" in database
    assert "exportJson" in database


def test_android_release_workflow_builds_and_attaches_apk() -> None:
    release = (ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    android_workflow = (ROOT / ".github" / "workflows" / "android.yml").read_text(
        encoding="utf-8"
    )
    assert "gradle -p android :app:assembleDebug" in release
    assert "Standalone Android APK" in release
    assert "--prerelease" in release
    assert "gradle -p android :app:assembleDebug" in android_workflow
    assert "actions/upload-artifact@v4" in android_workflow
