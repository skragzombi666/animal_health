from __future__ import annotations

from typing import Any

from . import v0912_features as treatment_features
from . import v0923_features

_PATCHED = False


def apply_v0923_patches() -> None:
    """Bind 0.9.23 to the final product/treatment logic after legacy patch layers."""
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True
    v0923_features._execute_treatment_sync = treatment_features._execute_treatment_sync

    base_record_medications = v0923_features._record_medications_sync

    def _record_medications_with_unified_product_type(
        database,
        animal_id: str,
        occurred_at,
        common_notes: str | None,
        items: list[dict[str, Any]],
    ):
        normalized: list[dict[str, Any]] = []
        for raw in items:
            item = dict(raw)
            if str(item.get("product_type") or "").strip() == "product":
                item["product_type"] = "medication"
            normalized.append(item)
        return base_record_medications(
            database,
            animal_id,
            occurred_at,
            common_notes,
            normalized,
        )

    v0923_features._record_medications_sync = _record_medications_with_unified_product_type
