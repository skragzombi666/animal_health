from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"


def test_096_upcoming_section_links() -> None:
    part48 = (FRONTEND / "animal-health-panel.part48.js").read_text(encoding="utf-8")

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


def test_android_remains_frozen_after_096() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
