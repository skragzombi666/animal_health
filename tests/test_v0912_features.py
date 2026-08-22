from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"


def _read(name: str) -> str:
    source = (INTEGRATION / name).read_text(encoding="utf-8")
    ast.parse(source)
    return source


def test_v0912_off_label_policy_is_persistent_and_migrates_legacy_setting() -> None:
    source = _read("v0912_features.py")

    for value in ("show_all", "show_marked", "hide", "on_demand"):
        assert f'"{value}"' in source
    assert "off_label_mode" in source
    assert "off_label_enabled" in source
    assert "OFF_LABEL_SHOW_MARKED" in source
    assert "OFF_LABEL_SHOW_ALL" in source
    assert "_save_off_label_mode_sync" in source


def test_v0912_treatment_plan_schema_contains_component_json() -> None:
    source = _read("v0912_features.py")

    assert 'ADD COLUMN components_json TEXT NOT NULL DEFAULT \'[]\'' in source
    assert "COMPONENT_TYPES" in source
    assert 'COMPONENT_TYPES = ("medication", "supplement", "feed", "action")' in source
    assert "_validate_component" in source
    assert "_decode_components" in source
    assert '"components": _decode_components(row["components_json"])' in source
    assert "json.dumps(validated" in source


def test_v0912_plan_execution_creates_summary_and_component_records() -> None:
    source = _read("v0912_features.py")
    patches = _read("v0912_patches.py")

    assert "EVENT_TYPE_TREATMENT" in source
    assert '"source": "treatment_plan"' in source
    assert "EVENT_TYPE_MEDICATION" in source
    assert "EVENT_TYPE_CARE" in source
    assert 'item["type"] in {"medication", "supplement"}' in source
    assert 'item["type"] not in {"medication", "supplement", "feed"}' in source
    assert "treatment_plan_id" in patches
    assert 'expected_kind") or "") != TASK_KIND_TREATMENT' in patches
    assert "component_events" in patches


def test_v0912_status_changes_are_scheduled_without_premature_state_change() -> None:
    source = _read("v0912_features.py")

    assert "CREATE TABLE IF NOT EXISTS v0912_status_changes" in source
    assert "state IN ('scheduled','confirmed','cancelled')" in source
    assert "if effective_at <= now_dt" in source
    assert '"scheduled": False' in source
    assert '"scheduled": True' in source
    future_block = source[source.index("def _save_status_change_sync"):source.index("def _resolve_status_change_sync")]
    assert "UPDATE animals" not in future_block
    assert "INSERT INTO v0912_status_changes" in future_block
    assert 'action == "cancel"' in source
    assert 'action == "reschedule"' in source
    assert "_apply_status_change_sync" in source


def test_v0912_historical_status_change_supports_date_correction() -> None:
    source = _read("v0912_features.py")

    assert "if previous == status" in source
    assert "correction_of = str(previous_event[\"id\"])" in source
    assert "status_changed_at=?" in source
    assert "occurred_at=effective_at" in source
    assert "correction_of_event_id=correction_of" in source
    assert '"date_corrected": correction_of is not None' in source


def test_v0912_status_alert_and_setup_are_registered() -> None:
    alerts = _read("status_change_alerts.py")
    init = _read("__init__.py")

    assert "CHECK_INTERVAL = timedelta(minutes=15)" in alerts
    assert 'NOTIFICATION_ID = f"{DOMAIN}_status_changes_due"' in alerts
    assert 'EVENT_STATUS_CHANGE_DUE = f"{DOMAIN}_status_change_due"' in alerts
    assert "persistent_notification.async_create" in alerts
    assert "persistent_notification.async_dismiss" in alerts
    assert "async_setup_status_change_alerts" in init
    assert "await async_setup_status_change_alerts(hass, entry)" in init
    assert "async_setup_v0912_features(hass)" in init
    assert "async_setup_v0912_task_links(hass)" in init
