from __future__ import annotations

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"
LEGACY_MANIFEST = FRONTEND / "legacy" / "manifest.json"
DIST = FRONTEND / "dist" / "animal-health-panel.js"
BUILD_SCRIPT = ROOT / "scripts" / "build_frontend.mjs"


def test_phase1_manifest_names_exactly_the_frozen_99_parts() -> None:
    manifest = json.loads(LEGACY_MANIFEST.read_text(encoding="utf-8"))
    expected = [
        f"../animal-health-panel.part{index:02d}.js" for index in range(1, 100)
    ]
    assert manifest == {
        "schema_version": 1,
        "reference_version": "0.9.41",
        "parts": expected,
    }


def test_phase1_dist_bundle_is_reproducible_and_valid_javascript() -> None:
    check = subprocess.run(
        ["node", str(BUILD_SCRIPT), "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert check.returncode == 0, check.stderr or check.stdout
    subprocess.run(["node", "--check", str(DIST)], check=True)


def test_phase1_dist_is_exact_legacy_concatenation() -> None:
    manifest = json.loads(LEGACY_MANIFEST.read_text(encoding="utf-8"))
    expected = "".join(
        (LEGACY_MANIFEST.parent / relative)
        .resolve()
        .read_text(encoding="utf-8")
        for relative in manifest["parts"]
    )
    assert DIST.read_text(encoding="utf-8") == expected


def test_phase1_home_assistant_and_android_reference_only_the_dist_bundle() -> None:
    panel = (
        ROOT / "custom_components" / "animal_health" / "panel.py"
    ).read_text(encoding="utf-8")
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(
        encoding="utf-8"
    )

    assert '"dist" / "animal-health-panel.js"' in panel
    assert 'glob("animal-health-panel.part*.js")' not in panel
    assert 'resolve("dist/animal-health-panel.js")' in gradle
    assert "animal-health-panel.part*.js" not in gradle
    assert "ordered.size == 99" not in gradle
