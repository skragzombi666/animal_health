from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable

REFERENCE_VERSION = "0.9.41"
BASELINE_RELATIVE_PATH = Path(
    "docs/architecture/inventory/legacy-baseline.json"
)
FRONTEND_RELATIVE_PATH = Path("custom_components/animal_health/frontend")
INTEGRATION_RELATIVE_PATH = Path("custom_components/animal_health")
PART_NAME_PATTERN = re.compile(r"animal-health-panel\.part(\d+)\.js$")
PROTOTYPE_ALIAS_PATTERN = re.compile(
    r"\bconst\s+(AH[A-Za-z0-9_$]*)\s*=\s*AnimalHealthPanel\.prototype\s*;"
)
SOURCE_PROTOTYPE_ALIAS_PATTERN = re.compile(
    r"\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)"
    r"\s*=\s*AnimalHealthPanel\.prototype\s*;"
)
DIRECT_PROTOTYPE_PATTERN = re.compile(
    r"\bAnimalHealthPanel\.prototype\.([A-Za-z_$][A-Za-z0-9_$]*)\s*=(?!=)"
)
DIRECT_PROTOTYPE_ACCESS_PATTERN = re.compile(
    r"\bAnimalHealthPanel\.prototype\s*\."
)
DIRECT_PROTOTYPE_OBJECT_ASSIGN_PATTERN = re.compile(
    r"\bObject\.assign\(\s*AnimalHealthPanel\.prototype\s*,"
)
SHADOW_ROOT_APPEND_PATTERN = re.compile(r"shadowRoot\.innerHTML\s*\+=")


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def _collapse(value: str) -> str:
    return " ".join(value.split())


def _stable_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sorted_unique(values: Iterable[str]) -> list[str]:
    return sorted({value for value in values if value})


def _assignment_kind(text: str, offset: int) -> str:
    tail = text[offset:].lstrip()
    if tail.startswith("async function"):
        return "async_function"
    if tail.startswith("function"):
        return "function"
    if tail.startswith("async ") or tail.startswith("async("):
        return "async_value"
    return "value"


def _violation_records(
    relative: str,
    pattern_name: str,
    positions: Iterable[int],
) -> list[dict[str, Any]]:
    return [
        {"path": relative, "pattern": pattern_name, "ordinal": ordinal}
        for ordinal, _position in enumerate(sorted(positions), start=1)
    ]


def find_frontend_source_violations(
    text: str,
    relative: str,
) -> list[dict[str, Any]]:
    """Return forbidden architecture patterns in one new frontend source file."""
    violations: list[dict[str, Any]] = []
    is_legacy_bridge = relative.endswith(
        "frontend/src/legacy/compatibility-bridge.js"
    )

    if not is_legacy_bridge:
        violations.extend(
            _violation_records(
                relative,
                "direct_prototype_patch",
                (match.start() for match in DIRECT_PROTOTYPE_ACCESS_PATTERN.finditer(text)),
            )
        )
        violations.extend(
            _violation_records(
                relative,
                "prototype_object_assign",
                (
                    match.start()
                    for match in DIRECT_PROTOTYPE_OBJECT_ASSIGN_PATTERN.finditer(text)
                ),
            )
        )

        aliases = sorted(set(SOURCE_PROTOTYPE_ALIAS_PATTERN.findall(text)))
        alias_assignment_positions: list[int] = []
        alias_object_assign_positions: list[int] = []
        for alias in aliases:
            assignment = re.compile(
                rf"\b{re.escape(alias)}\.([A-Za-z_$][A-Za-z0-9_$]*)\s*=(?!=)"
            )
            object_assign = re.compile(
                rf"\bObject\.assign\(\s*{re.escape(alias)}\s*,"
            )
            alias_assignment_positions.extend(
                match.start() for match in assignment.finditer(text)
            )
            alias_object_assign_positions.extend(
                match.start() for match in object_assign.finditer(text)
            )

        violations.extend(
            _violation_records(
                relative,
                "prototype_alias_patch",
                alias_assignment_positions,
            )
        )
        violations.extend(
            _violation_records(
                relative,
                "prototype_object_assign",
                alias_object_assign_positions,
            )
        )

    violations.extend(
        _violation_records(
            relative,
            "shadow_root_append",
            (match.start() for match in SHADOW_ROOT_APPEND_PATTERN.finditer(text)),
        )
    )
    return sorted(violations, key=_stable_key)


def _frontend_inventory(root: Path) -> dict[str, Any]:
    frontend = root / FRONTEND_RELATIVE_PATH
    parts = sorted(
        frontend.glob("animal-health-panel.part*.js"),
        key=lambda path: path.name,
    )
    part_records: list[dict[str, Any]] = []
    prototype_mutations: list[dict[str, Any]] = []
    actions: set[str] = set()
    views: set[str] = set()
    dialogs: set[str] = set()
    websocket_commands: set[str] = set()
    services: set[str] = set()
    translation_keys: set[Any] = set()
    style_block_count = 0

    for path in parts:
        data = path.read_bytes()
        text = data.decode("utf-8")
        match = PART_NAME_PATTERN.fullmatch(path.name)
        part_records.append(
            {
                "path": _relative(root, path),
                "index": int(match.group(1)) if match else None,
                "bytes": len(data),
                "sha256": _sha256(data),
                "git_blob_sha1": _git_blob_sha1(data),
            }
        )

        aliases = sorted(set(PROTOTYPE_ALIAS_PATTERN.findall(text)))
        mutation_ordinals: dict[tuple[str, str], int] = {}
        for alias in aliases:
            pattern = re.compile(
                rf"\b{re.escape(alias)}\.([A-Za-z_$][A-Za-z0-9_$]*)\s*=(?!=)"
            )
            for mutation in pattern.finditer(text):
                member = mutation.group(1)
                key = (alias, member)
                ordinal = mutation_ordinals.get(key, 0) + 1
                mutation_ordinals[key] = ordinal
                prototype_mutations.append(
                    {
                        "path": _relative(root, path),
                        "alias": alias,
                        "member": member,
                        "ordinal": ordinal,
                        "kind": _assignment_kind(text, mutation.end()),
                    }
                )

        for mutation in DIRECT_PROTOTYPE_PATTERN.finditer(text):
            member = mutation.group(1)
            key = ("AnimalHealthPanel.prototype", member)
            ordinal = mutation_ordinals.get(key, 0) + 1
            mutation_ordinals[key] = ordinal
            prototype_mutations.append(
                {
                    "path": _relative(root, path),
                    "alias": "AnimalHealthPanel.prototype",
                    "member": member,
                    "ordinal": ordinal,
                    "kind": _assignment_kind(text, mutation.end()),
                }
            )

        actions.update(re.findall(r"data-action=[\"']([^\"']+)[\"']", text))
        actions.update(
            re.findall(r"\baction\s*={2,3}\s*[\"']([^\"']+)[\"']", text)
        )
        actions.update(
            re.findall(
                r"dataset\.action\s*={2,3}\s*[\"']([^\"']+)[\"']", text
            )
        )
        views.update(re.findall(r"data-view=[\"']([^\"']+)[\"']", text))
        views.update(re.findall(r"this\.view\s*=\s*[\"']([^\"']+)[\"']", text))
        views.update(
            re.findall(r"this\.view\s*={2,3}\s*[\"']([^\"']+)[\"']", text)
        )
        dialogs.update(re.findall(r"this\.open\(\s*[\"']([^\"']+)[\"']", text))
        dialogs.update(
            re.findall(
                r"(?:this\.)?modal(?:\?\.)?\.type\s*={2,3}\s*[\"']([^\"']+)[\"']",
                text,
            )
        )
        dialogs.update(
            re.findall(
                r"this\.modal\s*=\s*\{\s*type\s*:\s*[\"']([^\"']+)[\"']",
                text,
            )
        )
        websocket_commands.update(
            re.findall(r"(?:animal_health|\$\{D\})/[A-Za-z0-9_./-]+", text)
        )
        services.update(
            re.findall(r"callService\(\s*[\"']([^\"']+)[\"']", text)
        )
        style_block_count += text.count("<style")

        for block in re.finditer(
            r"(?:const\s+T\s*=|Object\.assign\(T\s*,)\s*\{([\s\S]*?)\}\s*\)?\s*;",
            text,
        ):
            translation_keys.update(
                re.findall(
                    r"(?:^|[,\n])\s*(?:[\"']([^\"']+)[\"']|([A-Za-z_$][A-Za-z0-9_$]*))\s*:",
                    block.group(1),
                )
            )

    flattened_translation_keys = {
        quoted or bare
        for quoted, bare in translation_keys
        if quoted or bare
    }

    new_source_forbidden_patterns: list[dict[str, Any]] = []
    source_root = frontend / "src"
    if source_root.exists():
        for path in sorted(source_root.rglob("*.js")):
            relative = _relative(root, path)
            text = path.read_text(encoding="utf-8")
            new_source_forbidden_patterns.extend(
                find_frontend_source_violations(text, relative)
            )

    return {
        "part_count": len(part_records),
        "parts": part_records,
        "prototype_mutations": sorted(
            prototype_mutations, key=_stable_key
        ),
        "actions": sorted(actions),
        "views": sorted(views),
        "dialogs": sorted(dialogs),
        "websocket_commands": sorted(websocket_commands),
        "services": sorted(services),
        "translation_keys": sorted(flattened_translation_keys),
        "style_block_count": style_block_count,
        "new_source_forbidden_patterns": sorted(
            new_source_forbidden_patterns, key=_stable_key
        ),
    }


def _dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return None


def _iter_assignment_targets(node: ast.AST) -> Iterable[ast.AST]:
    if isinstance(node, ast.Assign):
        yield from node.targets
    elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        yield node.target


def _backend_inventory(root: Path) -> dict[str, Any]:
    integration = root / INTEGRATION_RELATIVE_PATH
    patch_definitions: list[dict[str, str]] = []
    runtime_method_assignments: list[dict[str, str]] = []
    migration_modules: list[str] = []
    version_runtime_modules: list[str] = []

    for path in sorted(integration.glob("*.py")):
        relative = _relative(root, path)
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=relative)

        if "migration" in path.stem:
            migration_modules.append(relative)
        if re.fullmatch(r"v\d+.*", path.stem) and "migration" not in path.stem:
            version_runtime_modules.append(relative)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("apply_"):
                patch_definitions.append({"path": relative, "function": node.name})

            for target in _iter_assignment_targets(node):
                dotted = _dotted_name(target)
                if not dotted or "." not in dotted:
                    continue
                root_name = dotted.split(".", 1)[0]
                if root_name in {
                    "self",
                    "cls",
                    "result",
                    "event",
                    "data",
                    "payload",
                    "item",
                    "task",
                    "occurrence",
                    "record",
                    "entry",
                    "state",
                    "row",
                }:
                    continue
                segment = ast.get_source_segment(text, node) or dotted
                runtime_method_assignments.append(
                    {
                        "path": relative,
                        "target": dotted,
                        "statement_sha256": _sha256(_collapse(segment).encode())[:16],
                    }
                )

            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "setattr"
                and len(node.args) >= 2
            ):
                owner = _dotted_name(node.args[0])
                attribute = (
                    node.args[1].value
                    if isinstance(node.args[1], ast.Constant)
                    and isinstance(node.args[1].value, str)
                    else None
                )
                if owner and attribute:
                    segment = (
                        ast.get_source_segment(text, node)
                        or f"setattr({owner},{attribute})"
                    )
                    runtime_method_assignments.append(
                        {
                            "path": relative,
                            "target": f"{owner}.{attribute}",
                            "statement_sha256": _sha256(
                                _collapse(segment).encode()
                            )[:16],
                        }
                    )

    init_path = integration / "__init__.py"
    init_text = init_path.read_text(encoding="utf-8")
    init_tree = ast.parse(init_text, filename=_relative(root, init_path))
    patch_registration_order: list[str] = []
    for node in init_tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "_apply_all_patches"
        ):
            for statement in node.body:
                if not isinstance(statement, ast.Expr) or not isinstance(
                    statement.value, ast.Call
                ):
                    continue
                called = _dotted_name(statement.value.func)
                if called:
                    patch_registration_order.append(called)
            break

    return {
        "patch_definitions": sorted(patch_definitions, key=_stable_key),
        "patch_registration_order": patch_registration_order,
        "runtime_method_assignments": sorted(
            runtime_method_assignments, key=_stable_key
        ),
        "migration_modules": sorted(migration_modules),
        "version_runtime_modules": sorted(version_runtime_modules),
    }


def collect_inventory(root: Path) -> dict[str, Any]:
    root = root.resolve()
    return {
        "schema_version": 1,
        "reference_version": REFERENCE_VERSION,
        "frontend": _frontend_inventory(root),
        "backend": _backend_inventory(root),
    }


def _is_subsequence(current: list[str], baseline: list[str]) -> bool:
    iterator = iter(baseline)
    return all(any(candidate == value for candidate in iterator) for value in current)


def _added_records(current: list[Any], baseline: list[Any]) -> list[Any]:
    baseline_keys = {_stable_key(value) for value in baseline}
    return [value for value in current if _stable_key(value) not in baseline_keys]


def check_guardrails(
    current: dict[str, Any], baseline: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if current.get("reference_version") != baseline.get("reference_version"):
        errors.append("The legacy reference version changed")

    current_frontend = current["frontend"]
    baseline_frontend = baseline["frontend"]
    if current_frontend["parts"] != baseline_frontend["parts"]:
        errors.append(
            "The frozen legacy frontend parts changed; create a dedicated migration instead"
        )

    for key in (
        "prototype_mutations",
        "actions",
        "views",
        "dialogs",
        "websocket_commands",
        "services",
        "translation_keys",
        "new_source_forbidden_patterns",
    ):
        added = _added_records(current_frontend[key], baseline_frontend[key])
        if added:
            errors.append(f"Frontend architecture grew in {key}: {added}")

    if current_frontend["style_block_count"] > baseline_frontend["style_block_count"]:
        errors.append(
            "Legacy frontend style block count increased: "
            f"{current_frontend['style_block_count']} > {baseline_frontend['style_block_count']}"
        )

    current_backend = current["backend"]
    baseline_backend = baseline["backend"]
    for key in (
        "patch_definitions",
        "runtime_method_assignments",
        "version_runtime_modules",
    ):
        added = _added_records(current_backend[key], baseline_backend[key])
        if added:
            errors.append(f"Backend runtime architecture grew in {key}: {added}")

    if not _is_subsequence(
        current_backend["patch_registration_order"],
        baseline_backend["patch_registration_order"],
    ):
        errors.append("Backend patch registration order gained or reordered entries")

    return errors


def _baseline_path(root: Path) -> Path:
    return root / BASELINE_RELATIVE_PATH


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inventory and guard the Animal Health legacy architecture"
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--stdout", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    inventory = collect_inventory(root)
    baseline_path = _baseline_path(root)

    if args.write:
        _write_json(baseline_path, inventory)
        print(f"Wrote {baseline_path.relative_to(root)}")
        return 0

    if args.stdout:
        print(json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if not baseline_path.is_file():
        print(
            f"Missing architecture baseline: {baseline_path.relative_to(root)}",
            file=sys.stderr,
        )
        return 1
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    errors = check_guardrails(inventory, baseline)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Architecture guardrails match or reduce the 0.9.41 baseline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
