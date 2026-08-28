from __future__ import annotations

import json
from typing import Any

from . import v0923_features

_PATCHED = False
_TREATMENT_KEYS = (
    "source",
    "treatment_plan_id",
    "treatment_plan_name",
    "treatment_execution_id",
    "treatment_execution_role",
    "treatment_parent_event_id",
    "treatment_component_index",
    "treatment_component_optional",
    "treatment_component_extra",
    "component_type",
)


def _event_data(database, event_id: str) -> dict[str, Any]:
    with database._connect() as connection:  # noqa: SLF001
        row = connection.execute("SELECT data_json FROM events WHERE id=?", (event_id,)).fetchone()
    if row is None:
        return {}
    try:
        value = json.loads(str(row["data_json"] or "{}"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _persist_data(database, event_id: str, data: dict[str, Any]) -> None:
    with database._connect() as connection:  # noqa: SLF001
        connection.execute(
            "UPDATE events SET data_json=? WHERE id=?",
            (json.dumps(data, ensure_ascii=False, sort_keys=True), event_id),
        )


def apply_v0924_final() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True
    base = v0923_features._record_medications_sync

    def record_medications_preserving_treatment_group(
        database,
        animal_id,
        occurred_at,
        common_notes,
        items,
    ):
        raw_items = [dict(item) for item in items]
        old_data: list[dict[str, Any]] = []
        for item in raw_items:
            correction_id = str(item.get("correction_event_id") or "").strip()
            old_data.append(_event_data(database, correction_id) if correction_id else {})
        result = base(database, animal_id, occurred_at, common_notes, raw_items)
        for original, event in zip(old_data, result, strict=False):
            tx_id = str(original.get("treatment_execution_id") or "")
            event_id = str(event.get("id") or "")
            if not tx_id or not event_id:
                continue
            current = dict(event.get("data") or {})
            for key in _TREATMENT_KEYS:
                if key in original:
                    current[key] = original[key]
            _persist_data(database, event_id, current)
            event["data"] = current
        return result

    v0923_features._record_medications_sync = record_medications_preserving_treatment_group
