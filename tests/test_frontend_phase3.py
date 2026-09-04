from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"
SOURCE = FRONTEND / "src"
ENTRY = SOURCE / "entry.js"
CHECKER = ROOT / "scripts" / "check_frontend_modules.mjs"
MANIFEST = FRONTEND / "legacy" / "manifest.json"
DIST = FRONTEND / "dist" / "animal-health-panel.js"

EXPECTED_APP_FILES = {
    "app/application.js",
    "app/animal-health-panel.js",
    "app/controller.js",
    "app/router.js",
    "app/state.js",
    "app/store.js",
    "legacy/compatibility-bridge.js",
}

EXPECTED_PHASE3_EXPORTS = {
    "createAnimalHealthApplication",
    "createAnimalHealthPanelClass",
    "createCompatibilityBridge",
    "createController",
    "createInitialState",
    "createRoute",
    "createRouter",
    "createStore",
    "renderApplicationShell",
}


def _sources() -> dict[str, str]:
    return {
        path.relative_to(SOURCE).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(SOURCE.rglob("*.js"))
    }


def test_phase3_application_shell_files_exist() -> None:
    sources = _sources()
    assert EXPECTED_APP_FILES <= sources.keys(), (
        "Missing Phase 3 source files: "
        + ", ".join(sorted(EXPECTED_APP_FILES - sources.keys()))
    )


def test_phase3_app_modules_remain_host_neutral_and_unpatched() -> None:
    forbidden = (
        "hass.",
        "bridge.call",
        "bridge.toast",
        "bridge.exportData",
        "window.history",
        "customElements.define",
        "AnimalHealthPanel.prototype",
        "shadowRoot.innerHTML +=",
    )
    for relative, source in _sources().items():
        if relative.startswith("app/"):
            for marker in forbidden:
                assert marker not in source, f"{relative}: {marker}"


def test_phase3_entry_exports_are_side_effect_free() -> None:
    entry = ENTRY.read_text(encoding="utf-8")
    for name in EXPECTED_PHASE3_EXPORTS:
        assert name in entry, name
    assert "customElements.define" not in entry
    assert "createAnimalHealthApplication(" not in entry
    assert "installLegacyReadOnlyAnimalsSlice(" not in entry


def test_phase3_checker_permanently_enforces_public_shell_exports() -> None:
    checker = CHECKER.read_text(encoding="utf-8")
    for name in EXPECTED_PHASE3_EXPORTS:
        assert f'"{name}"' in checker, name
    assert "Phase 2 entry" not in checker
    assert "modular frontend entry" in checker


def test_phase3_productive_bundle_keeps_the_exact_99_part_prefix() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    parts = list(manifest["parts"])
    assert len(parts) == 99
    legacy = "".join(
        (MANIFEST.parent / relative).resolve().read_text(encoding="utf-8")
        for relative in parts
    )
    bundle = DIST.read_text(encoding="utf-8")
    assert bundle.startswith(legacy)
    assert bundle[len(legacy) :].startswith(
        "\n/* ANIMAL_HEALTH_MODERN_RUNTIME */\n"
    )
    assert all("src/" not in relative for relative in parts)
