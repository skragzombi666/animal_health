from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_012_version_and_off_label_modes() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    part57 = (FRONTEND / "animal-health-panel.part57.js").read_text(encoding="utf-8")

    assert manifest["version"] in {"0.9.12", "0.9.13", "0.9.14", "0.9.15"}
    assert f'const V="{manifest["version"]}",D="animal_health"' in part01
    for mode in ("show_all", "show_marked", "hide", "on_demand"):
        assert f'"{mode}"' in part57
    assert "allowOffLabel012" in part57
    assert "markOffLabel012" in part57
    assert 'mode==="on_demand"' in part57
    assert 'name="show_off_label"' in part57
    assert 'data-off-label-med012' in part57
    assert '⚠ ${this.t("offLabel011")}' in part57
    assert '/v0912/off_label/update' in part57


def test_012_treatment_plans_support_multiple_fixed_components() -> None:
    part57 = (FRONTEND / "animal-health-panel.part57.js").read_text(encoding="utf-8")
    backend = (INTEGRATION / "v0912_features.py").read_text(encoding="utf-8")

    for component in ("medication", "supplement", "feed", "action"):
        assert f'"{component}"' in part57
        assert f'"{component}"' in backend
    assert "planComponents012" in part57
    assert "plan-component-add-012" in part57
    assert "plan-component-remove-012" in part57
    assert "components_json" in backend
    assert "_validate_component" in backend
    assert "_execute_treatment_sync" in backend
    assert 'data-form="treatment-plan-execute-012"' in part57
    assert '/v0912/treatment/execute' in part57
    assert 'pinch:["Messerspitze","Pinch"]' in part57
    assert '"pinch"' in (INTEGRATION / "const.py").read_text(encoding="utf-8")


def test_012_treatment_plan_can_be_linked_to_tasks() -> None:
    part57 = (FRONTEND / "animal-health-panel.part57.js").read_text(encoding="utf-8")
    creation = (INTEGRATION / "task_record_creation.py").read_text(encoding="utf-8")
    links = (INTEGRATION / "v0912_task_links.py").read_text(encoding="utf-8")
    patches = (INTEGRATION / "v0912_patches.py").read_text(encoding="utf-8")

    assert 'name="planned_treatment_plan_id"' in part57
    assert '/v0912/task_plan/link' in part57
    assert "ATTR_PLANNED_TREATMENT_PLAN_ID" in creation
    assert '"treatment": {ATTR_PLANNED_TREATMENT_PLAN_ID}' in creation
    assert "treatment_plan_id" in links
    assert "task_occurrence_plans" in links
    assert "_record_plan_components_sync" in patches
    assert "TaskRecordStore.execute" in patches


def test_012_status_change_has_effective_time_and_future_confirmation() -> None:
    part58 = (FRONTEND / "animal-health-panel.part58.js").read_text(encoding="utf-8")
    part59 = (FRONTEND / "animal-health-panel.part59.js").read_text(encoding="utf-8")
    backend = (INTEGRATION / "v0912_features.py").read_text(encoding="utf-8")
    alerts = (INTEGRATION / "status_change_alerts.py").read_text(encoding="utf-8")

    assert 'name="effective_at"' in part58
    assert '/v0912/status_change/save' in part58
    assert '/v0912/status_change/resolve' in part58
    assert 'status-change-confirm-012' in part58
    assert 'status-change-alternative-012' in part58
    assert 'status-change-cancel-012' in part58
    assert 'value="confirm"' in part58
    assert 'value="reschedule"' in part58
    assert "statusChangesDue012" in part58
    assert "plannedStatusChanges012" in part58
    assert "datetimeLocal012" in part59
    assert "v0912_status_changes" in backend
    assert "effective_at <= now_dt" in backend
    assert "correction_of_event_id=correction_of" in backend
    assert "status_changed_at" in backend
    assert "EVENT_STATUS_CHANGE_DUE" in alerts
    assert "persistent_notification.async_create" in alerts


def test_android_remains_frozen_after_012() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
