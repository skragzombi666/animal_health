from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"


def test_series_alert_monitor_is_registered_and_aggregated() -> None:
    source = (INTEGRATION / "series_alerts.py").read_text(encoding="utf-8")
    init_source = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))

    ast.parse(source)
    assert "persistent_notification" in manifest["dependencies"]
    assert "async_setup_series_alerts" in init_source
    assert "await async_setup_series_alerts(hass, entry)" in init_source
    assert "CHECK_INTERVAL = timedelta(minutes=15)" in source
    assert 'NOTIFICATION_ID = f"{DOMAIN}_overdue_series"' in source
    assert 'EVENT_SERIES_OVERDUE = f"{DOMAIN}_series_overdue"' in source
    assert "persistent_notification.async_create" in source
    assert "persistent_notification.async_dismiss" in source
    assert "hass.bus.async_fire" in source
    assert "signature != previous_signature" in source
    assert "current_occurrence_ids - previous_occurrence_ids" in source
    assert 'task.recurrence_type != "once"' in source


def test_overdue_rules_respect_all_day_and_timed_tasks() -> None:
    source = (INTEGRATION / "series_alerts.py").read_text(encoding="utf-8")

    assert "scheduled_local.date() < today" in source
    assert "occurrence.scheduled_for < now_utc" in source
    assert "status=OCCURRENCE_PENDING" in source
    assert "fire_events=False" in source
    assert "fire_events=True" in source
