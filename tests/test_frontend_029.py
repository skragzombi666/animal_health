from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"


def test_029_task_editing_and_upcoming_groups() -> None:
    frontend = (FRONTEND / "animal-health-panel.part88.js").read_text(encoding="utf-8")
    for marker in (
        'T.seriesStatus097=T.tasks029',
        'data-task-plan-029',
        '/v0929/task/plan/update',
        'tomorrow029:["Morgen"',
        'dayAfterTomorrow029:["Übermorgen"',
        'AH029.animalSeriesStatus097=function()',
        'data-action="edit-task-097"',
    ):
        assert marker in frontend


def test_029_timeline_and_quick_capture_polish() -> None:
    frontend = (FRONTEND / "animal-health-panel.part88.js").read_text(encoding="utf-8")
    for marker in (
        'yesterday029:["Gestern"',
        'dayBeforeYesterday029:["Vorgestern"',
        'lastWeek029:["Letzte Woche"',
        'lastMonth029:["Letzter Monat"',
        'gabeAnimal029',
        'mergeDose029',
        'taskSource027',
        'cleanupHomeQuickCapture029',
        '[data-action="record-product"]::after',
    ):
        assert marker in frontend


def test_029_attachment_preview_refresh() -> None:
    frontend = (FRONTEND / "animal-health-panel.part88.js").read_text(encoding="utf-8")
    backend = (ROOT / "custom_components" / "animal_health" / "v0929_features.py").read_text(encoding="utf-8")
    assert 'attachment-preview-024' in frontend
    assert 'previewRetry029' in frontend
    assert 'HTTPGone' in backend
    assert 'no-store' in backend
    assert '_update_pending_plans_sync' in backend
