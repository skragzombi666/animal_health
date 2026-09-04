from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"
SOURCE = FRONTEND / "src"
MANIFEST = FRONTEND / "legacy" / "manifest.json"
DIST = FRONTEND / "dist" / "animal-health-panel.js"
README = SOURCE / "README.md"
CHECKER = ROOT / "scripts" / "check_frontend_modules.mjs"
PACKAGE = ROOT / "package.json"
MODERN_SEPARATOR = "\n/* ANIMAL_HEALTH_MODERN_RUNTIME */\n"

EXPECTED_PHASE4_FILES = {
    "app/read-only-animals.js",
    "domain/animals/selectors.js",
    "legacy/compatibility-bridge.js",
    "runtime-entry.js",
    "ui/read-only/components.js",
    "ui/read-only/format.js",
    "ui/read-only/i18n.js",
    "ui/read-only/styles.js",
    "ui/views/animal-detail.js",
    "ui/views/animals.js",
    "ui/views/overview.js",
}

EXPECTED_PHASE4_EXPORTS = {
    "createReadOnlyAnimalsRuntime",
    "installLegacyReadOnlyAnimalsSlice",
    "renderReadOnlyAnimalsRoute",
    "selectUrgentOccurrences",
    "selectVisibleAnimals",
}

BACKEND_ALIAS_MARKERS = {
    "animal_id",
    "group_id",
    "tag_ids",
    "latest_weight",
    "occurred_at",
    "scheduled_for",
    "task_id",
    "target_scope",
    "is_overdue",
}


def _sources() -> dict[str, str]:
    return {
        path.relative_to(SOURCE).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(SOURCE.rglob("*.js"))
    }


def _legacy_prelude() -> str:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return "".join(
        (MANIFEST.parent / relative).resolve().read_text(encoding="utf-8")
        for relative in manifest["parts"]
    )


def test_phase4_files_exist_without_a_new_numbered_fragment() -> None:
    sources = _sources()
    assert EXPECTED_PHASE4_FILES <= sources.keys(), (
        "Missing Phase 4 source files: "
        + ", ".join(sorted(EXPECTED_PHASE4_FILES - sources.keys()))
    )
    parts = sorted(FRONTEND.glob("animal-health-panel.part*.js"))
    assert len(parts) == 99
    assert parts[-1].name == "animal-health-panel.part99.js"
    assert not (FRONTEND / "animal-health-panel.part100.js").exists()


def test_phase4_has_exactly_one_legacy_prototype_integration_point() -> None:
    offenders = [
        relative
        for relative, source in _sources().items()
        if "LegacyPanelClass.prototype" in source
    ]
    assert offenders == ["legacy/compatibility-bridge.js"]


def test_phase4_runtime_activation_is_isolated_from_side_effect_free_entry() -> None:
    sources = _sources()
    activation_files = [
        relative
        for relative, source in sources.items()
        if re.search(r"\bAnimalHealthPanel\b", source)
    ]
    assert activation_files == ["runtime-entry.js"]
    assert "installLegacyReadOnlyAnimalsSlice(AnimalHealthPanel" in sources[
        "runtime-entry.js"
    ]
    assert "runtime-entry.js" not in sources["entry.js"]
    assert "installLegacyReadOnlyAnimalsSlice(" not in sources["entry.js"]


def test_phase4_views_are_canonical_read_only_and_host_neutral() -> None:
    sources = _sources()
    for relative, source in sources.items():
        if not relative.startswith("ui/views/"):
            continue
        for marker in BACKEND_ALIAS_MARKERS:
            assert marker not in source, f"{relative}: {marker}"
        for marker in (
            "hass.",
            "callService",
            "callWS",
            "bridge.",
            "window.",
            "globalThis.",
            "localStorage",
        ):
            assert marker not in source, f"{relative}: {marker}"


def test_phase4_runtime_declares_only_the_three_approved_routes_and_no_writes() -> None:
    runtime = (SOURCE / "app/read-only-animals.js").read_text(encoding="utf-8")
    route_block = re.search(
        r"MIGRATED_READ_ROUTES\s*=\s*Object\.freeze\(\[([\s\S]*?)\]\)",
        runtime,
    )
    assert route_block is not None
    routes = re.findall(r'"([a-z-]+)"', route_block.group(1))
    assert routes == ["overview", "animals", "animal-detail"]
    assert "callService" not in runtime
    assert "callWS" not in runtime
    assert "createHomeAssistantTransport" in runtime
    assert "getAnimalDirectory" in runtime
    assert "getAnimalDetail" in runtime


def test_phase4_bundle_keeps_exact_legacy_prefix_and_one_runtime_marker() -> None:
    legacy = _legacy_prelude()
    bundle = DIST.read_text(encoding="utf-8")
    assert bundle.startswith(legacy)
    suffix = bundle[len(legacy) :]
    assert suffix.startswith(MODERN_SEPARATOR)
    assert bundle.count("ANIMAL_HEALTH_MODERN_RUNTIME") == 1
    assert "installLegacyReadOnlyAnimalsSlice" in suffix
    assert "createReadOnlyAnimalsRuntime" in suffix


def test_phase4_checker_enforces_the_public_active_slice_exports() -> None:
    checker = CHECKER.read_text(encoding="utf-8")
    for name in EXPECTED_PHASE4_EXPORTS:
        assert f'"{name}"' in checker, name
    assert "runtime-entry.js" not in checker


def test_phase4_readme_declares_active_routes_and_legacy_writes() -> None:
    readme = README.read_text(encoding="utf-8")
    assert "## Status in Phase 4" in readme
    for route in ("overview", "animals", "animal-detail"):
        assert f"`{route}`" in readme
    assert "Schreib" in readme and "Legacy" in readme
    assert "99" in readme and "Präfix" in readme


def test_phase4_build_dependency_is_exactly_pinned_and_generator_is_temporary() -> None:
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert package["devDependencies"] == {"esbuild": "0.25.9"}
    assert package["scripts"]["build:frontend"] == "node scripts/build_frontend.mjs"
    assert not (ROOT / ".github/workflows/phase4-generate.yml").exists()
    assert not (ROOT / "package-lock.json").exists()
