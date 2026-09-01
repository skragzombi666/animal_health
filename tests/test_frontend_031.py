from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"


def test_031_animal_task_count_uses_task_definitions() -> None:
    frontend = (FRONTEND / "animal-health-panel.part90.js").read_text(encoding="utf-8")
    assert 'activeTasks031:["Aktive Aufgaben"' in frontend
    assert "animalTasks031=function" in frontend
    assert "activeAnimalTasks031=function" in frontend
    assert "task.is_active===false||recurring||pendingIds.has(id)" in frontend
    assert 'data-action="animal-tasks-031"' in frontend
    assert "decorateTaskStat031" in frontend
    assert 'this.t("openTasks")' in frontend
    assert 'this.t("activeTasks031")' in frontend


def test_031_animal_tasks_are_managed_in_a_popup() -> None:
    frontend = (FRONTEND / "animal-health-panel.part90.js").read_text(encoding="utf-8")
    for marker in (
        "animalTasksModal031",
        "animalTaskRow031",
        'data-action="edit-task-097"',
        'data-action="animal-task-toggle-031"',
        'data-action="create-task"',
        'mdi:clipboard-text-outline',
        'modal?.type==="animal-tasks-031"',
    ):
        assert marker in frontend


def test_031_upcoming_header_has_task_manager_and_separated_count() -> None:
    frontend = (FRONTEND / "animal-health-panel.part90.js").read_text(encoding="utf-8")
    assert "animalUpcomingHead031" in frontend
    assert "relevantGroupHead031" in frontend
    assert '<h3>${esc(group.label)}</h3><span>${group.items.length}</span>' in frontend
    assert "justify-content:space-between!important" in frontend
    assert "animalUpcomingRow029=function" in frontend
    assert "taskScope031" in frontend
