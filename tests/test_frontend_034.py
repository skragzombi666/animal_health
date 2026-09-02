from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"
SOURCE = FRONTEND / "animal-health-panel.part93.js"


def source() -> str:
    return SOURCE.read_text(encoding="utf-8")


def test_034_timeline_uses_one_inline_flow_without_measurement_patch() -> None:
    frontend = source()
    for marker in (
        'class="gabeFlow034"',
        'class="gabeDose034"',
        "gabeTitle034",
        'class="taskSource034',
        ".gabeFlow034{display:block",
        ".gabeTitle034{display:inline",
        "AH033Base.render.call(this)",
        "rawCompact021",
    ):
        assert marker in frontend
    assert "layoutGabe033" not in frontend


def test_034_treatment_plan_task_keeps_snapshot_and_source_marker() -> None:
    frontend = source()
    for marker in (
        "treatmentComponents034",
        "treatment_plan_components",
        "treatmentTaskSource034",
        "treatmentPlanComponents034",
        "isTaskSource034",
        "treatmentBundle021",
    ):
        assert marker in frontend


def test_034_multiple_choice_is_chip_dropdown_plus_component() -> None:
    frontend = source()
    for marker in (
        "multiChoiceMarkup034",
        "multiChips034",
        "data-multi-add034",
        "multi-remove-034",
        "multi-custom-034",
        "animalPickerMarkup034",
        "data-target-animal-add034",
        "target-animal-create-034",
        "taskPlanEditor029",
        "AH034.checks=function",
    ):
        assert marker in frontend
    assert '<div class="animalChecks026">' not in frontend


def test_034_completed_tasks_can_be_duplicated_or_rescheduled() -> None:
    frontend = source()
    for marker in (
        "completed_count",
        "taskCompleted034",
        "task-duplicate-034",
        "task-continue-034",
        "openTaskCopy034",
        "taskDraft034",
        "taskCompletedHint034",
    ):
        assert marker in frontend


def test_034_android_product_database_commands_are_locally_available() -> None:
    frontend = source()
    for marker in (
        "androidV0928Command034",
        "androidV0928State034",
        "product_databases_0928.json",
        "medicines_ch.json",
        "vaccines_ch.json",
        "/database/import",
        "/product/save",
        "databaseLoadUnavailable034",
    ):
        assert marker in frontend
    assert 'String(type).startsWith(`${D}/v0928/`)' in frontend


def test_034_browser_history_has_one_authoritative_back_path() -> None:
    frontend = source()
    for marker in (
        "__animalHealthNav034",
        "restoreNavSnapshot034",
        "bindInternalHistory034",
        "requestBack034",
        "_ahBackPending034",
        "history.pushState",
        "history.replaceState",
        "history.back()",
        "__animalHealthHandleBack034",
    ):
        assert marker in frontend
    assert "AH033Base.handleClick.call(this,event)" in frontend
