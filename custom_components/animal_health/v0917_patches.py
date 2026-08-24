from __future__ import annotations

import sqlite3
from typing import Any

from .database import AnimalHealthDatabase
from .v0913_features import medication_snapshot_for_name

_PATCHED = False


def _snapshot_with_category(
    connection: sqlite3.Connection,
    product_name: str,
) -> dict[str, Any]:
    snapshot = medication_snapshot_for_name(connection, product_name)
    category = "medication"
    medication_id = snapshot.get("medication_id")
    if medication_id is not None:
        row = connection.execute(
            "SELECT category FROM v0917_product_categories WHERE medication_id=?",
            (int(medication_id),),
        ).fetchone()
        if row is not None:
            category = str(row["category"])
    snapshot["product_category"] = category
    return snapshot


def apply_v0917_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True
    base_create = AnimalHealthDatabase._create_event_in_connection

    def _create_event_with_product_category(
        database: AnimalHealthDatabase,
        connection: sqlite3.Connection,
        **kwargs: Any,
    ):
        if str(kwargs.get("event_type") or "") == "medication":
            data = dict(kwargs.get("data") or {})
            snapshot = data.get("medication_snapshot")
            if not isinstance(snapshot, dict):
                name = str(data.get("medication_name") or kwargs.get("title") or "").strip()
                snapshot = _snapshot_with_category(connection, name)
            elif "product_category" not in snapshot:
                snapshot = dict(snapshot)
                medication_id = snapshot.get("medication_id")
                category = "medication"
                if medication_id is not None:
                    row = connection.execute(
                        "SELECT category FROM v0917_product_categories WHERE medication_id=?",
                        (int(medication_id),),
                    ).fetchone()
                    if row is not None:
                        category = str(row["category"])
                snapshot["product_category"] = category
            data["medication_snapshot"] = snapshot
            data.setdefault("product_category", snapshot.get("product_category", "medication"))
            kwargs["data"] = data
        return base_create(database, connection, **kwargs)

    AnimalHealthDatabase._create_event_in_connection = _create_event_with_product_category  # type: ignore[method-assign]
