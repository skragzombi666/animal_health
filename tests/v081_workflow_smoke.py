from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def read(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"{path} is empty"
    return text


def main() -> None:
    features = read(INTEGRATION / "v081_features.py")
    fixes = read(INTEGRATION / "v081_fixes.py")
    stt_source = read(INTEGRATION / "v081_stt.py")
    init_source = read(INTEGRATION / "__init__.py")
    manifest = json.loads(read(INTEGRATION / "manifest.json"))
    frontend = "".join(
        read(FRONTEND / f"animal-health-panel.part{index:02d}.js")
        for index in (17, 18)
    )
    docs = read(ROOT / "docs" / "version-0.8.1.md")
    latest_weight = read(INTEGRATION / "latest_weight.py")
    exports = read(INTEGRATION / "exports.py")

    for source in (features, fixes, stt_source):
        ast.parse(source)

    assert manifest["version"] == "0.8.1"
    assert 'const V="0.8.1"' in read(FRONTEND / "animal-health-panel.part01.js")
    for marker in (
        "async_initialize_v081_features",
        "async_setup_v081_features",
        "async_setup_v081_fixes",
        "async_setup_v081_stt",
    ):
        assert marker in init_source, marker

    for table in (
        "v081_settings",
        "group_events",
        "task_group_targets",
        "group_task_configs",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in features, table

    for command in (
        "/v081/state",
        "/v081/settings/update",
        "/v081/product/record",
        "/v081/weight/correct",
        "/v081/group_task/create",
        "/v081/group_task/execute",
        "/v081/group_pdf",
    ):
        assert command in features, command
    assert "/v081/group_event/create_safe" in fixes
    assert "partial(" in fixes
    assert "async_add_executor_job(operation)" in fixes

    assert '"product_type": msg["product_type"]' in features
    assert '"entry_mode": "spontaneous"' in features
    assert "correction_of_event_id=str(current[\"id\"])" in features
    assert "WITH RECURSIVE chain AS" in features
    assert "WITH RECURSIVE weight_versions AS" in latest_weight
    assert "later_correction.correction_of_event_id = version.id" in latest_weight

    assert "animal_ids=[None]" in features
    assert "task_group_targets" in features
    assert "group_task_occurrence" in features
    assert "gruppenchronik.pdf" in features
    assert "SELECT name" in exports and "sqlite_master" in exports

    for marker in (
        "de-CH",
        "de-DE",
        '_TRANSCRIBE_COMMAND = f"{DOMAIN}/v081/transcribe"',
        "requested_language",
        '"language": language',
    ):
        assert marker in stt_source, marker

    for marker in (
        "actionNow",
        "quickCaptureGrid",
        "record-product",
        "correct-weight",
        "groups081",
        "settings081",
        "group-detail-081",
        "create-group-task",
        "group-pdf",
        "v081/group_event/create_safe",
        "v081/transcribe",
        "ai_task_entity_id",
        "stt_entity_id",
        "operationalHeading",
    ):
        assert marker in frontend, marker

    assert "urgent.slice(0,3)" in frontend
    assert "3-Math.min(3,urgent.length)" in frontend
    assert "Weitere Angaben" in frontend
    assert "product_type" in frontend
    assert "supplement" in frontend
    assert "correctionBadge" in frontend
    assert "defaultBlock.querySelectorAll" in frontend
    assert "AH081STBase.handleSubmit.call" in frontend

    for phrase in (
        "Was muss ich jetzt tun?",
        "Medikament / Supplement",
        "Tiergruppen ohne Einzeltiere",
        "Gewicht korrigieren",
        "de-CH",
        "AI Task",
    ):
        assert phrase in docs, phrase

    print("Animal Health 0.8.1 workflow validation passed")


if __name__ == "__main__":
    main()
