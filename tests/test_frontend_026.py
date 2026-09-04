from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_026_version_is_consistent_and_android_stays_frozen() -> None:
    manifest = json.loads(_read(INTEGRATION / "manifest.json"))
    part01 = _read(FRONTEND / "animal-health-panel.part01.js")
    gradle = _read(ROOT / "android" / "app" / "build.gradle.kts")
    assert tuple(map(int, manifest["version"].split("."))) >= (0, 9, 26)
    assert 'const V="0.9.41",D="animal_health"' in part01
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert "versionCode = 900007" in gradle


def test_026_uses_one_scope_selector_for_groups_and_multiple_animals() -> None:
    frontend = "".join(_read(FRONTEND / f"animal-health-panel.part{part}.js") for part in (80, 81, 82))
    backend = _read(INTEGRATION / "v0926_features.py")
    init = _read(INTEGRATION / "__init__.py")
    assert "targetSelector026" in frontend
    assert '[["group","targetGroup026"],["animals","targetAnimals026"]]' in frontend
    assert '[["general","targetGeneral026"],["group","targetGroup026"],["animals","targetAnimal026"]]' in frontend
    for form in ("task", "symptom", "medication", "treatment"):
        assert f'targetPayload026("{form}")' in frontend
    assert '"target_scope": _SCOPE_GROUP' in backend
    assert '"target_group_id"' in backend
    assert '"target_group_name"' in backend
    assert '"target_animal_ids"' in backend
    assert "async_setup_v0926_features" in init


def test_026_group_scope_is_persisted_in_events_and_tasks() -> None:
    frontend = "".join(_read(FRONTEND / f"animal-health-panel.part{part}.js") for part in (80, 81, 82))
    backend = _read(INTEGRATION / "v0926_features.py")
    assert "_annotate_events_sync" in backend
    assert "template.update(metadata)" in backend
    assert "scopeBadge026" in frontend
    assert "groupAction026" in frontend


def test_026_timeline_and_treatment_plan_are_compact_and_reorderable() -> None:
    frontend = "".join(_read(FRONTEND / f"animal-health-panel.part{part}.js") for part in (80, 81, 82))
    assert ".timelineAxisRow023.dateOnly023{grid-template-columns:minmax(0,1fr)!important}" in frontend
    assert ".timelineAxisRow023.dateOnly023>time{display:none!important}" in frontend
    assert "plan-component-up-026" in frontend
    assert "plan-component-down-026" in frontend
    assert "text-overflow:ellipsis!important" in frontend
    assert "white-space:nowrap!important" in frontend


def test_026_attachment_previews_and_true_multi_file_capture_are_available() -> None:
    frontend = "".join(_read(FRONTEND / f"animal-health-panel.part{part}.js") for part in (80, 81, 82))
    assert "attachmentStrip026" in frontend
    assert "timelineAttachments026" in frontend
    assert "attachment-preview-024" in frontend
    assert 'multiple="multiple"' in frontend
    assert "addAttachmentFiles024" in frontend
    assert "uploadFilesToTargets026" in frontend
