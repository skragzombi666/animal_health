from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"
SOURCE = FRONTEND / "src"
DIST = FRONTEND / "dist" / "animal-health-panel.js"
MANIFEST = FRONTEND / "legacy" / "manifest.json"
PACKAGE = ROOT / "package.json"
CHECKER = ROOT / "scripts" / "check_frontend_modules.mjs"
EXPECTED_SOURCE_FILES = {
    "entry.js",
    "platform/transport.js",
    "platform/home-assistant-adapter.js",
    "platform/android-adapter.js",
    "api/commands.js",
    "api/errors.js",
    "api/client.js",
    "api/normalizers/common.js",
    "api/normalizers/animals.js",
    "api/normalizers/tasks.js",
    "api/normalizers/timeline.js",
    "api/normalizers/catalog.js",
    "api/normalizers/features.js",
    "api/normalizers/dashboard.js",
    "api/normalizers/products.js",
    "api/normalizers/treatments.js",
    "api/normalizers/settings.js",
    "api/normalizers/index.js",
}


def _existing_sources() -> dict[str, str]:
    return {
        path.relative_to(SOURCE).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(SOURCE.rglob("*.js"))
    } if SOURCE.exists() else {}


def test_phase2_source_boundary_files_exist() -> None:
    sources = _existing_sources()
    assert EXPECTED_SOURCE_FILES.issubset(sources), (
        "Missing Phase 2 source files: "
        + ", ".join(sorted(EXPECTED_SOURCE_FILES - sources.keys()))
    )
    assert CHECKER.is_file()


def test_phase2_host_calls_are_confined_to_platform_adapters() -> None:
    sources = _existing_sources()
    for relative, source in sources.items():
        if ".callWS" in source or ".callService" in source:
            assert relative == "platform/home-assistant-adapter.js", relative
        if any(
            marker in source
            for marker in ("bridge.call", "bridge.toast", "bridge.exportData")
        ):
            assert relative == "platform/android-adapter.js", relative


def test_phase2_versioned_commands_are_confined_to_the_registry() -> None:
    sources = _existing_sources()
    pattern = re.compile(r"animal_health/v0\d+")
    offenders = [
        relative
        for relative, source in sources.items()
        if pattern.search(source) and relative != "api/commands.js"
    ]
    assert offenders == []


def test_phase2_source_has_no_legacy_or_runtime_side_effects() -> None:
    forbidden = (
        "AnimalHealthPanel.prototype",
        "shadowRoot.innerHTML +=",
        "customElements.define",
    )
    global_assignment = re.compile(r"\b(?:globalThis|window)\.[A-Za-z_$][\w$]*\s*=")
    for relative, source in _existing_sources().items():
        for marker in forbidden:
            assert marker not in source, f"{relative}: {marker}"
        assert global_assignment.search(source) is None, relative
    for path in sorted((SOURCE / "api" / "normalizers").glob("*.js")) if SOURCE.exists() else []:
        assert "new Date(" not in path.read_text(encoding="utf-8"), path


def test_phase2_dist_bundle_remains_the_exact_legacy_reference() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = "".join(
        (MANIFEST.parent / relative).resolve().read_text(encoding="utf-8")
        for relative in manifest["parts"]
    )
    assert DIST.read_text(encoding="utf-8") == expected


def test_phase2_package_scripts_use_permanent_dependency_free_checks() -> None:
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert package["private"] is True
    assert package["type"] == "module"
    assert package["scripts"] == {
        "check:frontend": "node scripts/check_frontend_modules.mjs",
        "test:frontend": "node --test tests/frontend/*.test.mjs",
    }
    assert "dependencies" not in package
    assert "devDependencies" not in package
