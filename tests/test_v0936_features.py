from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "custom_components" / "animal_health" / "v0936_features.py"
INIT = ROOT / "custom_components" / "animal_health" / "__init__.py"
MANIFEST = ROOT / "custom_components" / "animal_health" / "manifest.json"
FRONTEND_VERSION = (
    ROOT
    / "custom_components"
    / "animal_health"
    / "frontend"
    / "animal-health-panel.part01.js"
)
ANDROID = ROOT / "android" / "app" / "build.gradle.kts"


def _load_feature_module():
    package = ModuleType("custom_components")
    package.__path__ = []  # type: ignore[attr-defined]
    animal_health = ModuleType("custom_components.animal_health")
    animal_health.__path__ = []  # type: ignore[attr-defined]
    creation = ModuleType("custom_components.animal_health.task_record_creation")
    records = ModuleType("custom_components.animal_health.task_records")

    def base_builder(
        task_kind_value: str,
        data: dict[str, Any],
        *,
        title: str,
        current: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {"kind": task_kind_value, "title": title, **dict(current or {})}

    creation.build_task_template = base_builder  # type: ignore[attr-defined]
    records.build_task_template = base_builder  # type: ignore[attr-defined]
    animal_health.task_record_creation = creation  # type: ignore[attr-defined]
    animal_health.task_records = records  # type: ignore[attr-defined]
    modules = {
        "custom_components": package,
        "custom_components.animal_health": animal_health,
        "custom_components.animal_health.task_record_creation": creation,
        "custom_components.animal_health.task_records": records,
    }
    previous = {name: sys.modules.get(name) for name in modules}
    sys.modules.update(modules)
    try:
        spec = importlib.util.spec_from_file_location(
            "custom_components.animal_health.v0936_features",
            FEATURES,
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module, creation, records, previous
    except Exception:
        for name, value in previous.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value
        raise


def _restore_modules(previous: dict[str, ModuleType | None]) -> None:
    sys.modules.pop("custom_components.animal_health.v0936_features", None)
    for name, value in previous.items():
        if value is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = value


def test_036_task_copy_origin_is_persisted_by_the_shared_template_builder() -> None:
    module, creation, records, previous = _load_feature_module()
    try:
        module.apply_v0936_patches()
        assert creation.build_task_template is records.build_task_template
        duplicate = creation.build_task_template(
            "medication",
            {
                "copy_mode": "duplicate",
                "source_task_id": "TK-1",
                "source_task_title": "Metacam",
            },
            title="Metacam copy",
        )
        assert duplicate["task_origin"] == {
            "mode": "duplicate",
            "source_task_id": "TK-1",
            "source_task_title": "Metacam",
        }
        replan = creation.build_task_template(
            "medication",
            {
                "copy_mode": "replan",
                "source_task_id": "TK-2",
                "source_task_title": "Metacam",
                "source_root_task_id": "TK-ROOT",
            },
            title="Metacam again",
        )
        assert replan["task_origin"]["root_task_id"] == "TK-ROOT"
        preserved = creation.build_task_template(
            "medication",
            {},
            title="Edited",
            current={"task_origin": replan["task_origin"]},
        )
        assert preserved["task_origin"] == replan["task_origin"]
    finally:
        _restore_modules(previous)


def test_036_task_copy_origin_rejects_incomplete_or_unknown_modes() -> None:
    module, creation, _records, previous = _load_feature_module()
    try:
        module.apply_v0936_patches()
        for payload in (
            {"copy_mode": "replan"},
            {"copy_mode": "unknown", "source_task_id": "TK-1"},
        ):
            try:
                creation.build_task_template("reminder", payload, title="Invalid")
            except ValueError:
                pass
            else:
                raise AssertionError("invalid copy metadata was accepted")
    finally:
        _restore_modules(previous)


def test_036_patch_is_wired_after_existing_task_template_patches() -> None:
    source = INIT.read_text(encoding="utf-8")
    assert "from .v0936_features import apply_v0936_patches" in source
    assert source.index("apply_v0934_patches()") < source.index("apply_v0936_patches()")


def test_036_release_version_and_shared_bundle_count_are_updated() -> None:
    assert '"version": "0.9.37"' in MANIFEST.read_text(encoding="utf-8")
    assert 'const V="0.9.37"' in FRONTEND_VERSION.read_text(encoding="utf-8")
    android = ANDROID.read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in android
    assert "versionCode = 900007" in android
    assert "ordered.size == 97" in android
    assert "Expected 97 Animal Health frontend parts" in android
