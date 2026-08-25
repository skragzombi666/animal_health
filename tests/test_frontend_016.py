from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_016_version_is_consistent() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    part01 = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")

    assert manifest["version"] in {"0.9.16", "0.9.17", "0.9.18", "0.9.19", "0.9.20", "0.9.21"}
    assert f'const V="{manifest["version"]}",D="animal_health"' in part01


def test_016_treatment_task_kind_is_migrated_before_schema_init() -> None:
    schema = (INTEGRATION / "task_record_schema.py").read_text(encoding="utf-8")
    migration = (INTEGRATION / "v0916_migration.py").read_text(encoding="utf-8")
    init = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")

    assert "'treatment'" in schema
    assert "task_record_configs_v0916" in migration
    assert "DROP TABLE task_record_configs" in migration
    assert "ALTER TABLE task_record_configs_v0916 RENAME TO task_record_configs" in migration
    assert "async_migrate_v0916_task_kinds" in init
    assert init.index("await async_migrate_v0916_task_kinds(hass)") < init.index(
        "await async_initialize_task_record_schema(hass)"
    )


def test_016_quick_capture_uses_one_shared_plus_badge() -> None:
    part65 = (FRONTEND / "animal-health-panel.part65.js").read_text(encoding="utf-8")

    assert '"record-weight":{icon:"mdi:scale"' in part65
    assert '"record-symptom":{icon:"mdi:alert-circle-outline"' in part65
    assert '"record-product":{icon:"mdi:pill"' in part65
    assert '"record-event":{icon:"mdi:file-document-outline"' in part65
    assert '"create-task":{icon:"mdi:clipboard-outline"' in part65
    assert '"ai-assist":{icon:"mdi:creation-outline"' in part65
    assert '"attach-document":{icon:"mdi:paperclip"' in part65
    assert '<span class="capturePlus016"><ha-icon icon="mdi:plus"></ha-icon></span>' in part65
    assert ".quickCaptureCard091 [data-action]" in part65
    assert ".animalCaptureIcons090A7 [data-action]" in part65
    assert "mdi:note-plus-outline" not in part65
    assert "mdi:clipboard-plus-outline" not in part65
    assert "mdi:alert-plus" not in part65


def test_android_remains_frozen_after_016() -> None:
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in gradle
    assert 'versionCode = 900007' in gradle
