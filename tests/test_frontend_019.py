from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_019_version_is_consistent() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    assert manifest["version"] == "0.9.19"
    assert 'const V="0.9.19",D="animal_health"' in part01


def test_019_compact_quick_capture_is_icon_only() -> None:
    frontend = (FRONTEND / "animal-health-panel.part70.js").read_text(encoding="utf-8")
    assert "quickCaptureCompact019" in frontend
    assert 'role="toolbar"' in frontend
    assert 'title="${esc(this.t(label))}"' in frontend
    compact = frontend.split('const content=compact?', 1)[1].split(':`<div class="quickCaptureGrid', 1)[0]
    assert "quickCaptureLabel019" not in compact
    assert "capturePlus019" in compact
    assert "repeat(6,minmax(0,1fr))" in frontend


def test_019_expanded_quick_capture_is_separate_full_view() -> None:
    frontend = (FRONTEND / "animal-health-panel.part70.js").read_text(encoding="utf-8")
    assert "quickCaptureExpanded019" in frontend
    assert "quickCaptureLabel019" in frontend
    assert "grid-template-columns:repeat(3,minmax(0,1fr))" in frontend
    assert "@media(max-width:700px)" in frontend
    assert "grid-template-columns:repeat(2,minmax(0,1fr))" in frontend
    assert "min-height:78px" in frontend


def test_019_animal_detail_capture_stays_icon_only() -> None:
    frontend = (FRONTEND / "animal-health-panel.part70.js").read_text(encoding="utf-8")
    assert 'querySelectorAll(".animalCaptureIcons090A7 [data-action]")' in frontend
    assert 'button.innerHTML=this.captureIcon019(definition.icon)' in frontend
    assert "animalCaptureButton019" in frontend
    assert ".animalCaptureIcons090A7 .captureLabel016" in frontend


def test_019_shared_add_badge_has_no_embedded_plus_icons() -> None:
    frontend = (FRONTEND / "animal-health-panel.part70.js").read_text(encoding="utf-8")
    for icon in (
        '"mdi:scale"',
        '"mdi:alert-circle-outline"',
        '"mdi:pill"',
        '"mdi:file-document-outline"',
        '"mdi:clipboard-outline"',
        '"mdi:creation-outline"',
    ):
        assert icon in frontend
    assert '<ha-icon icon="mdi:plus"></ha-icon>' in frontend
    assert "mdi:note-plus-outline" not in frontend
    assert "mdi:clipboard-plus-outline" not in frontend
    assert "mdi:alert-plus" not in frontend


def test_android_remains_frozen_after_019() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
