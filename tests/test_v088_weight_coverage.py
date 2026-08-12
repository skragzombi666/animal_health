from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "custom_components" / "animal_health" / "v088_features.py"


def _load_function(name: str):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    node = next(
        item
        for item in tree.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name
    )
    module = ast.Module(body=[node], type_ignores=[])
    namespace: dict[str, Any] = {"Any": Any}
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace[name]


def test_weight_prompt_requires_full_row_coverage() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "WEIGHT-LIST COMPLETENESS RULES" in source
    assert "twelve visible animal/weight rows" in source
    assert "twelve draft entries" in source
    assert "Never omit a row merely because" in source
    assert "second, completeness-only verification pass" in source
    assert "len(entries) > 1" in source
    assert "coverage_added_count" in source


def test_coverage_merge_adds_missing_named_animals_without_duplicates() -> None:
    merge = _load_function("_merge_weight_entries")
    primary = [
        {"animal_name": f"Tier {index}", "weight": str(1000 + index), "weight_unit": "g"}
        for index in range(1, 7)
    ]
    additions = [
        {"animal_name": "Tier 1", "weight": "1001", "weight_unit": "g"},
        *[
            {"animal_name": f"Tier {index}", "weight": str(1000 + index), "weight_unit": "g"}
            for index in range(7, 13)
        ],
    ]

    merged = merge(primary, additions)

    assert len(merged) == 12
    assert {entry["animal_name"] for entry in merged} == {
        f"Tier {index}" for index in range(1, 13)
    }


def test_coverage_merge_fills_missing_fields_in_existing_row() -> None:
    merge = _load_function("_merge_weight_entries")
    primary = [
        {
            "animal_name": "Tina",
            "weight": "",
            "weight_unit": "",
            "document_date": "",
            "due_time": "",
        }
    ]
    additions = [
        {
            "animal_name": "Tina",
            "weight": "2040",
            "weight_unit": "g",
            "document_date": "2026-08-12",
            "due_time": "19:30",
        }
    ]

    merged = merge(primary, additions)

    assert len(merged) == 1
    assert merged[0]["weight"] == "2040"
    assert merged[0]["weight_unit"] == "g"
    assert merged[0]["document_date"] == "2026-08-12"
    assert merged[0]["due_time"] == "19:30"
