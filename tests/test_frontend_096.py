from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_096_version_and_upcoming_section_links() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    part48 = (FRONTEND / "animal-health-panel.part48.js").read_text(encoding="utf-8")

    assert manifest["version"] == "0.9.6"
    assert 'const V="0.9.6",D="animal_health"' in part01
    assert 'upcoming096:["Anstehend","Upcoming"]' in part48
    assert 'data-view="tasks"' in part48
    assert 'data-view="calendar"' in part48
    assert 'mdi:clipboard-check' in part48
    assert 'mdi:calendar' in part48
    assert "upcomingLinks096" in part48


def test_096_settings_show_installed_version_next_to_updates() -> None:
    part48 = (FRONTEND / "animal-health-panel.part48.js").read_text(encoding="utf-8")

    assert 'currentVersion096:["Aktuelle Version","Current version"]' in part48
    assert 'this.d?.version||V' in part48
    assert '<button data-action="open-updates-084">' in part48
    assert "currentVersion096" in part48


def test_096_top_navigation_keeps_only_overview_and_timeline_core_links() -> None:
    part03 = (FRONTEND / "animal-health-panel.part03.js").read_text(encoding="utf-8")

    assert '[["overview","mdi:view-dashboard"],["timeline","mdi:timeline-clock"]]' in part03
    assert '[["overview","mdi:view-dashboard"],["animals","mdi:paw"]' not in part03
    assert '["tasks","mdi:clipboard-check"]' not in part03
    assert '["calendar","mdi:calendar"]' not in part03


def test_android_remains_frozen_for_096() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
