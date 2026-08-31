from __future__ import annotations

import json
import secrets
import sqlite3
from pathlib import Path
from typing import Any

from . import v0924_features, v0927_data
from .v0928_catalog import _parse_catalog_product_id, state_sync
from .v0928_schema import (
    DATABASE_USER,
    PRODUCT_KINDS,
    _database_by_id,
    _json_object,
    _normal,
    _now,
    _required,
    _text,
    initialize_product_databases_sync,
)


def save_database_sync(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    initialize_product_databases_sync(path)
    database_id = _text(payload.get("database_id"))
    fields = dict(payload.get("fields") or {})
    name = _required(fields.get("name") or payload.get("name"), "database name")
    product_types = fields.get("product_types") or payload.get("product_types") or list(PRODUCT_KINDS)
    if not isinstance(product_types, list):
        product_types = [product_types]
    product_types = [_text(value) for value in product_types if _text(value) in PRODUCT_KINDS]
    if not product_types:
        product_types = list(PRODUCT_KINDS)
    now = _now()
    with v0927_data.connect(path) as connection:
        if database_id:
            row = _database_by_id(connection, database_id)
            if bool(row["is_system"]):
                raise ValueError("System databases cannot be renamed or replaced")
        else:
            database_id = f"custom_db:{secrets.token_hex(8)}"
        metadata = _json_object(fields.get("metadata"))
        metadata["editable"] = True
        connection.execute(
            """
            INSERT INTO v0928_product_databases(
                id,name,description,provider,source_type,product_types_json,version,
                data_as_of,source_url,license,priority,is_enabled,is_system,is_removable,
                update_mode,parent_database_id,filter_classification,metadata_json,
                created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,0,1,'manual','','',?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                provider=excluded.provider,
                product_types_json=excluded.product_types_json,
                version=excluded.version,
                data_as_of=excluded.data_as_of,
                source_url=excluded.source_url,
                license=excluded.license,
                priority=excluded.priority,
                metadata_json=excluded.metadata_json,
                updated_at=excluded.updated_at
            """,
            (
                database_id,
                name,
                _text(fields.get("description")),
                _text(fields.get("provider")) or "Lokal",
                "user",
                json.dumps(product_types, ensure_ascii=False),
                _text(fields.get("version")) or "1",
                _text(fields.get("data_as_of")),
                _text(fields.get("source_url")),
                _text(fields.get("license")) or "Privat",
                int(fields.get("priority") or 100),
                1 if bool(fields.get("is_enabled", True)) else 0,
                json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                now,
                now,
            ),
        )
    return next(item for item in state_sync(path)["databases"] if item["id"] == database_id)


def toggle_database_sync(path: Path, database_id: str, enabled: bool) -> dict[str, Any]:
    initialize_product_databases_sync(path)
    with v0927_data.connect(path) as connection:
        cursor = connection.execute(
            "UPDATE v0928_product_databases SET is_enabled=?,updated_at=? WHERE id=?",
            (1 if enabled else 0, _now(), database_id),
        )
        if cursor.rowcount == 0:
            raise KeyError(database_id)
    return next(item for item in state_sync(path)["databases"] if item["id"] == database_id)


def delete_database_sync(path: Path, database_id: str) -> None:
    initialize_product_databases_sync(path)
    with v0927_data.connect(path) as connection:
        row = _database_by_id(connection, database_id)
        if bool(row["is_system"]) or not bool(row["is_removable"]):
            raise ValueError("This database cannot be removed")
        connection.execute("DELETE FROM v0927_products WHERE database_id=?", (database_id,))
        connection.execute("DELETE FROM v0928_product_databases WHERE id=?", (database_id,))


def _normalise_fields(fields: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in fields.items():
        if key in {"name", "kind", "database_id", "target_species"}:
            continue
        if isinstance(value, list):
            cleaned[key] = [dict(item) if isinstance(item, dict) else item for item in value]
        elif isinstance(value, dict):
            cleaned[key] = dict(value)
        elif value is None:
            cleaned[key] = ""
        else:
            cleaned[key] = value
    return cleaned


def _product_from_state(path: Path, item_id: str) -> dict[str, Any]:
    for item in state_sync(path)["products"]:
        if str(item.get("id")) == str(item_id):
            return item
    raise KeyError(item_id)


def _catalog_override_fields(fields: dict[str, Any], name: str, species: list[str]) -> dict[str, Any]:
    allowed = {
        "active_ingredient",
        "active_ingredients",
        "active_ingredient_details",
        "concentration",
        "dosage_form",
        "aliases",
        "default_route",
    }
    result = {key: value for key, value in fields.items() if key in allowed}
    result["name"] = name
    result["target_species"] = species
    return result


def save_product_sync(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    initialize_product_databases_sync(path)
    kind = _required(payload.get("kind"), "product kind")
    if kind not in PRODUCT_KINDS:
        raise ValueError(f"Unsupported product kind: {kind}")
    item_id = _text(payload.get("item_id"))
    database_id = _text(payload.get("database_id")) or DATABASE_USER
    fields = dict(payload.get("fields") or {})
    name = _required(fields.get("name") or payload.get("name"), "product name")
    species = fields.get("target_species", payload.get("target_species", []))
    if not isinstance(species, list):
        species = [species]
    species = [_text(value) for value in species if _text(value)]
    metadata = _normalise_fields(fields)
    catalog_key = _parse_catalog_product_id(item_id)
    if catalog_key:
        source_id, source_item_id = catalog_key
        current = _product_from_state(path, item_id)
        override = {"name": name, "target_species": species, **metadata}
        with v0927_data.connect(path) as connection:
            connection.execute(
                """
                INSERT INTO v0924_catalog_overrides(source_id,item_id,hidden,override_json,updated_at)
                VALUES(?,?,?,?,?)
                ON CONFLICT(source_id,item_id) DO UPDATE SET
                    hidden=excluded.hidden,override_json=excluded.override_json,updated_at=excluded.updated_at
                """,
                (
                    source_id,
                    source_item_id,
                    1 if bool(current.get("is_hidden")) else 0,
                    json.dumps(override, ensure_ascii=False, sort_keys=True),
                    _now(),
                ),
            )
        return _product_from_state(path, item_id)
    now = _now()
    with v0927_data.connect(path) as connection:
        if item_id:
            row = connection.execute(
                "SELECT * FROM v0927_products WHERE id=?", (item_id,)
            ).fetchone()
            if row is None:
                raise KeyError(item_id)
            if bool(row["is_custom"]):
                selected_database_id = database_id or str(row["database_id"] or DATABASE_USER)
                database = _database_by_id(connection, selected_database_id)
                database_meta = _json_object(database["metadata_json"])
                if bool(database["is_system"]) and not bool(database_meta.get("editable")):
                    raise ValueError("New products can only be stored in an editable database")
                connection.execute(
                    """
                    UPDATE v0927_products
                    SET kind=?,name=?,normalized_name=?,species_json=?,metadata_json=?,database_id=?,updated_at=?
                    WHERE id=?
                    """,
                    (
                        kind,
                        name,
                        _normal(name),
                        json.dumps(species, ensure_ascii=False),
                        json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                        selected_database_id,
                        now,
                        item_id,
                    ),
                )
            else:
                override = {"name": name, "target_species": species, **metadata}
                connection.execute(
                    "UPDATE v0927_products SET override_json=?,updated_at=? WHERE id=?",
                    (json.dumps(override, ensure_ascii=False, sort_keys=True), now, item_id),
                )
        else:
            database = _database_by_id(connection, database_id)
            database_meta = _json_object(database["metadata_json"])
            if bool(database["is_system"]) and not bool(database_meta.get("editable")):
                raise ValueError("New products can only be stored in an editable database")
            item_id = f"custom:{secrets.token_hex(12)}"
            connection.execute(
                """
                INSERT INTO v0927_products(
                    id,kind,source,source_id,name,normalized_name,species_json,
                    metadata_json,override_json,is_hidden,is_custom,created_at,updated_at,database_id
                ) VALUES(?,?,?,?,?,?,?,?,?,0,1,?,?,?)
                """,
                (
                    item_id,
                    kind,
                    "user",
                    None,
                    name,
                    _normal(name),
                    json.dumps(species, ensure_ascii=False),
                    json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                    "{}",
                    now,
                    now,
                    database_id,
                ),
            )
    return _product_from_state(path, item_id)


def archive_product_sync(path: Path, item_id: str, hidden: bool) -> dict[str, Any]:
    initialize_product_databases_sync(path)
    catalog_key = _parse_catalog_product_id(item_id)
    if catalog_key:
        source_id, source_item_id = catalog_key
        now = _now()
        with v0927_data.connect(path) as connection:
            row = connection.execute(
                "SELECT override_json FROM v0924_catalog_overrides WHERE source_id=? AND item_id=?",
                (source_id, source_item_id),
            ).fetchone()
            override = str(row["override_json"] if row is not None else "{}")
            connection.execute(
                """
                INSERT INTO v0924_catalog_overrides(source_id,item_id,hidden,override_json,updated_at)
                VALUES(?,?,?,?,?)
                ON CONFLICT(source_id,item_id) DO UPDATE SET
                    hidden=excluded.hidden,updated_at=excluded.updated_at
                """,
                (source_id, source_item_id, 1 if hidden else 0, override, now),
            )
        return _product_from_state(path, item_id)
    v0927_data.archive_product_sync(path, item_id, hidden)
    return _product_from_state(path, item_id)


def reset_product_sync(path: Path, item_id: str) -> dict[str, Any]:
    initialize_product_databases_sync(path)
    catalog_key = _parse_catalog_product_id(item_id)
    if catalog_key:
        source_id, source_item_id = catalog_key
        v0924_features._reset_catalog_override_sync(path, source_id, source_item_id)  # noqa: SLF001
        return _product_from_state(path, item_id)
    v0927_data.reset_product_sync(path, item_id)
    return _product_from_state(path, item_id)


def delete_product_sync(path: Path, item_id: str) -> None:
    initialize_product_databases_sync(path)
    if _parse_catalog_product_id(item_id):
        raise ValueError("Official source products cannot be deleted")
    with v0927_data.connect(path) as connection:
        row = connection.execute(
            "SELECT is_custom FROM v0927_products WHERE id=?", (item_id,)
        ).fetchone()
        if row is None:
            raise KeyError(item_id)
        if not bool(row["is_custom"]):
            raise ValueError("Supplied source products cannot be deleted")
        connection.execute("DELETE FROM v0927_products WHERE id=?", (item_id,))


def import_database_sync(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    document = payload.get("document") if isinstance(payload.get("document"), dict) else payload
    if not isinstance(document, dict):
        raise ValueError("Invalid database document")
    if document.get("format") not in (None, "animal-health-product-database"):
        raise ValueError("Unsupported database format")
    database_fields = dict(document.get("database") or {})
    database_fields.pop("id", None)
    database_fields["name"] = _required(database_fields.get("name"), "database name")
    database = save_database_sync(path, {"fields": database_fields})
    with v0927_data.connect(path) as connection:
        connection.execute(
            "UPDATE v0928_product_databases SET source_type='imported',updated_at=? WHERE id=?",
            (_now(), database["id"]),
        )
    imported = 0
    invalid: list[dict[str, Any]] = []
    for index, raw in enumerate(document.get("products", [])):
        if not isinstance(raw, dict):
            invalid.append({"index": index, "error": "Product is not an object"})
            continue
        fields = dict(raw)
        kind = _text(fields.pop("kind", ""))
        fields.pop("id", None)
        fields.pop("database_id", None)
        fields.pop("database_ids", None)
        fields.pop("original", None)
        try:
            save_product_sync(
                path,
                {
                    "kind": kind,
                    "database_id": database["id"],
                    "name": fields.get("name"),
                    "target_species": fields.get("target_species", []),
                    "fields": fields,
                },
            )
            imported += 1
        except (ValueError, KeyError, TypeError) as err:
            invalid.append({"index": index, "error": str(err)})
    return {"database": database, "imported": imported, "invalid": invalid}


def _connection_path(connection: sqlite3.Connection) -> Path | None:
    row = connection.execute("PRAGMA database_list").fetchone()
    if row is None:
        return None
    try:
        value = row["file"]
    except (IndexError, TypeError):
        value = row[2]
    return Path(str(value)) if value else None


def load_product_snapshot(connection: sqlite3.Connection, item_id: str) -> dict[str, Any] | None:
    stored = v0927_data.load_product_snapshot(connection, item_id)
    if stored is not None:
        row = connection.execute(
            "SELECT database_id FROM v0927_products WHERE id=?", (item_id,)
        ).fetchone()
        if row is not None:
            stored["database_id"] = str(row["database_id"] or DATABASE_USER)
        return stored
    catalog_key = _parse_catalog_product_id(item_id)
    if not catalog_key:
        return None
    path = _connection_path(connection)
    if path is None:
        return None
    try:
        item = _product_from_state(path, item_id)
    except KeyError:
        return None
    snapshot = dict(item)
    snapshot.pop("original", None)
    snapshot.pop("database_ids", None)
    return snapshot


def medication_snapshot_for_name(
    connection: sqlite3.Connection, product_name: str
) -> dict[str, Any]:
    path = _connection_path(connection)
    clean_name = _normal(product_name)
    if path is not None and clean_name:
        try:
            candidates = [
                item
                for item in state_sync(path)["products"]
                if item.get("kind") == v0927_data.GABE_MEDICATION
                and item.get("database_enabled") is not False
                and not item.get("is_hidden")
                and clean_name
                in {_normal(item.get("name")), *(_normal(alias) for alias in item.get("aliases", []))}
            ]
        except (sqlite3.Error, OSError):
            candidates = []
        if candidates:
            candidates.sort(
                key=lambda item: (
                    0 if item.get("is_custom") else 1,
                    -int(item.get("database_priority") or 0),
                    0 if item.get("is_modified") else 1,
                )
            )
            snapshot = dict(candidates[0])
            snapshot.pop("original", None)
            snapshot.pop("sources", None)
            snapshot.pop("database_ids", None)
            snapshot["product_name"] = snapshot.get("name", product_name)
            return snapshot
    return {
        "source": "free_text",
        "product_name": _text(product_name),
        "active_ingredient": "",
        "concentration": "",
        "dosage_form": "",
    }
