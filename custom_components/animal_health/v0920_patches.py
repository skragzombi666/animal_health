from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from .database import AnimalHealthDatabase

_PATCHED = False


def _normalise(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def _official_snapshot(connection: sqlite3.Connection, name: str) -> dict[str, Any] | None:
    tables = {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "v0920_catalog_products" not in tables:
        return None
    row = connection.execute(
        """
        SELECT source_id,item_id,authorisation_number,name,active_ingredient,
               active_ingredients_json,concentration,dosage_form,authorisation_status
        FROM v0920_catalog_products
        WHERE normalized_name=?
        ORDER BY source_id,item_id LIMIT 1
        """,
        (_normalise(name),),
    ).fetchone()
    if row is None:
        return None
    return {
        "source": "official_catalog",
        "catalog_source_id": str(row["source_id"]),
        "catalog_id": str(row["item_id"]),
        "authorisation_number": str(row["authorisation_number"] or ""),
        "product_name": str(row["name"]),
        "active_ingredient": str(row["active_ingredient"] or ""),
        "active_ingredients": json.loads(str(row["active_ingredients_json"] or "[]")),
        "concentration": str(row["concentration"] or ""),
        "dosage_form": str(row["dosage_form"] or ""),
        "authorisation_status": str(row["authorisation_status"] or ""),
    }


def apply_v0920_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True
    base_create = AnimalHealthDatabase._create_event_in_connection

    def _create_event_with_official_snapshot(
        database: AnimalHealthDatabase,
        connection: sqlite3.Connection,
        **kwargs: Any,
    ):
        if str(kwargs.get("event_type") or "") == "medication":
            data = dict(kwargs.get("data") or {})
            snapshot = data.get("medication_snapshot")
            current_source = str(snapshot.get("source") or "") if isinstance(snapshot, dict) else ""
            if not snapshot or current_source in {"free_text", "catalog"}:
                product_name = str(
                    data.get("medication_name")
                    or (snapshot.get("product_name") if isinstance(snapshot, dict) else "")
                    or kwargs.get("title")
                    or ""
                ).strip()
                official = _official_snapshot(connection, product_name)
                if official:
                    snapshot = official
                    data["medication_snapshot"] = snapshot
                    data["catalog_source"] = "official"
                    data["catalog_source_id"] = snapshot["catalog_source_id"]
                    data["authorisation_number"] = snapshot["authorisation_number"]
                    data.setdefault("product_category", "medication")
                    kwargs["title"] = snapshot["product_name"]
            kwargs["data"] = data
        return base_create(database, connection, **kwargs)

    AnimalHealthDatabase._create_event_in_connection = _create_event_with_official_snapshot  # type: ignore[method-assign]
