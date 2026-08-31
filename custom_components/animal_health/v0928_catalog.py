from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from . import v0924_features, v0927_data
from .v0928_schema import (
    DATABASE_DEWORMERS,
    DATABASE_SWISSMEDIC,
    DATABASE_USER,
    DATABASE_SCHEMA_VERSION,
    PRODUCT_KINDS,
    _DEWORMING_WORDS,
    _json_object,
    _normal,
    _table_exists,
    _text,
    _database_rows,
    initialize_product_databases_sync,
)


def _classifications(item: dict[str, Any]) -> list[str]:
    raw = item.get("classifications") or item.get("classification") or []
    if isinstance(raw, str):
        values = [raw]
    elif isinstance(raw, list):
        values = list(raw)
    else:
        values = []
    result = [_text(value) for value in values if _text(value)]
    kind = _text(item.get("kind"))
    if kind and kind not in result:
        result.append(kind)
    haystack = " ".join(
        [
            _text(item.get("name")),
            _text(item.get("active_ingredient")),
            " ".join(_text(value) for value in item.get("active_ingredients", []) if _text(value)),
            _text(item.get("application_area")),
        ]
    ).casefold()
    if any(word in haystack for word in _DEWORMING_WORDS):
        if v0927_data.GABE_DEWORMING not in result:
            result.append(v0927_data.GABE_DEWORMING)
    return result


def _canonical_key(item: dict[str, Any]) -> str:
    authorisation = _text(item.get("authorisation_number"))
    if authorisation:
        return f"authorisation:{authorisation.casefold()}"
    gtin = _text(item.get("gtin") or item.get("ean"))
    if gtin:
        return f"gtin:{gtin}"
    name = _normal(item.get("name"))
    manufacturer = _normal(item.get("manufacturer") or item.get("provider"))
    concentration = _normal(item.get("concentration"))
    return f"name:{name}|manufacturer:{manufacturer}|concentration:{concentration}"


def _stored_products(path: Path) -> list[dict[str, Any]]:
    with v0927_data.connect(path) as connection:
        rows = connection.execute(
            "SELECT * FROM v0927_products ORDER BY kind,normalized_name,id"
        ).fetchall()
    products: list[dict[str, Any]] = []
    for row in rows:
        item = v0927_data.product_row(row)
        database_id = str(row["database_id"] or DATABASE_USER)
        item["database_id"] = database_id
        item["database_ids"] = [database_id]
        item["classifications"] = _classifications(item)
        if v0927_data.GABE_DEWORMING in item["classifications"]:
            item["database_ids"].append(DATABASE_DEWORMERS)
        item["canonical_key"] = _canonical_key(item)
        item["record_type"] = "stored"
        products.append(item)
    return products


def _catalog_product_id(source_id: str, item_id: str) -> str:
    return f"catalog::{source_id}::{item_id}"


def _parse_catalog_product_id(item_id: str) -> tuple[str, str] | None:
    if not str(item_id).startswith("catalog::"):
        return None
    parts = str(item_id).split("::", 2)
    if len(parts) != 3 or not parts[1] or not parts[2]:
        return None
    return parts[1], parts[2]


def _catalog_products(path: Path) -> list[dict[str, Any]]:
    try:
        source_items = v0924_features._catalog_state_sync(path)  # noqa: SLF001
    except (sqlite3.Error, OSError):
        source_items = []
    products: list[dict[str, Any]] = []
    for source in source_items:
        source_id = _text(source.get("source_id")) or DATABASE_SWISSMEDIC
        source_item_id = _text(source.get("id"))
        if not source_item_id:
            continue
        original = dict(source.get("original") or {})
        item = dict(source)
        item.update(
            {
                "id": _catalog_product_id(source_id, source_item_id),
                "source_record_id": source_item_id,
                "kind": v0927_data.GABE_MEDICATION,
                "database_id": DATABASE_SWISSMEDIC,
                "database_ids": [DATABASE_SWISSMEDIC],
                "source": "official",
                "is_custom": False,
                "record_type": "catalog",
            }
        )
        item["classifications"] = _classifications(item)
        if v0927_data.GABE_DEWORMING in item["classifications"]:
            item["database_ids"].append(DATABASE_DEWORMERS)
        item["canonical_key"] = _canonical_key(item)
        if original:
            item["original"] = {
                **original,
                "id": item["id"],
                "source_record_id": source_item_id,
                "database_id": DATABASE_SWISSMEDIC,
                "kind": v0927_data.GABE_MEDICATION,
            }
        products.append(item)
    return products


def _swissmedic_source(path: Path) -> dict[str, Any]:
    with v0927_data.connect(path) as connection:
        if not _table_exists(connection, "v0920_catalog_sources"):
            return {}
        row = connection.execute(
            "SELECT * FROM v0920_catalog_sources WHERE source_id=?",
            (DATABASE_SWISSMEDIC,),
        ).fetchone()
    if row is None:
        return {}
    return {
        "name": str(row["name"] or "Swissmedic – Tierarzneimittel"),
        "source_url": str(row["landing_url"] or row["source_url"] or ""),
        "data_as_of": str(row["snapshot_date"] or ""),
        "version": str(row["dataset_id"] or "OGD"),
        "source_enabled": bool(row["enabled"]),
        "source_item_count": int(row["item_count"] or 0),
        "is_complete": bool(row["is_complete"]),
        "last_success_at": str(row["last_success_at"] or ""),
        "last_error": str(row["last_error"] or ""),
    }


def state_sync(path: Path) -> dict[str, Any]:
    initialize_product_databases_sync(path)
    databases = _database_rows(path)
    products = [*_catalog_products(path), *_stored_products(path)]
    swissmedic = _swissmedic_source(path)
    database_by_id = {database["id"]: database for database in databases}
    if swissmedic and DATABASE_SWISSMEDIC in database_by_id:
        database_by_id[DATABASE_SWISSMEDIC].update(swissmedic)
    if swissmedic and DATABASE_DEWORMERS in database_by_id:
        database_by_id[DATABASE_DEWORMERS]["data_as_of"] = swissmedic.get("data_as_of", "")
        database_by_id[DATABASE_DEWORMERS]["last_success_at"] = swissmedic.get("last_success_at", "")
    for product in products:
        physical = database_by_id.get(str(product.get("database_id") or ""), {})
        product["database_name"] = physical.get("name", product.get("database_id", ""))
        product["database_priority"] = int(physical.get("priority", 0))
        product["database_enabled"] = bool(physical.get("is_enabled", True))
    for database in databases:
        matching = [
            product
            for product in products
            if database["id"] in (product.get("database_ids") or [])
        ]
        database["item_count"] = len(matching)
        database["hidden_count"] = sum(bool(item.get("is_hidden")) for item in matching)
        database["modified_count"] = sum(bool(item.get("is_modified")) for item in matching)
    databases.sort(key=lambda item: (-int(item.get("priority", 0)), _normal(item.get("name"))))
    return {
        "schema_version": DATABASE_SCHEMA_VERSION,
        "database_export_format": "animal-health-product-database",
        "databases": databases,
        "products": products,
        "product_kinds": list(PRODUCT_KINDS),
        "classifications": [v0927_data.GABE_DEWORMING],
    }
