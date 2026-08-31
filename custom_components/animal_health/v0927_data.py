from __future__ import annotations

import json
import re
import secrets
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import voluptuous as vol

GABE_MEDICATION = "medication"
GABE_VACCINATION = "vaccination"
GABE_DEWORMING = "deworming"
GABE_SUPPLEMENT = "supplement"
GABE_FEED = "feed"
GABE_TYPES = (
    GABE_MEDICATION,
    GABE_VACCINATION,
    GABE_DEWORMING,
    GABE_SUPPLEMENT,
    GABE_FEED,
)
PRODUCT_KINDS = (GABE_VACCINATION, GABE_SUPPLEMENT, GABE_FEED)

_VACCINE_TARGETS: dict[str, list[str]] = {
    "ch.nobivac_dhppi": ["distemper", "canine_adenovirus", "canine_parvovirus", "parainfluenza"],
    "ch.nobivac_dhp": ["distemper", "canine_adenovirus", "canine_parvovirus"],
    "ch.nobivac_pi": ["parainfluenza"],
    "ch.nobivac_lepto_6": ["leptospirosis"],
    "ch.nobivac_rabies": ["rabies"],
    "ch.nobivac_kc": ["kennel_cough"],
    "ch.nobivac_tricat_iii": ["feline_panleukopenia", "feline_herpesvirus", "feline_calicivirus"],
    "ch.purevax_felv": ["feline_leukemia"],
    "ch.nobilis_ib_4_91": ["infectious_bronchitis"],
    "ch.nobilis_ib_ma5": ["infectious_bronchitis"],
    "ch.poulvac_procerta_hvt_ibd": ["marek", "gumboro"],
    "ch.bultavo_3": ["bluetongue"],
    "ch.nobilis_paramyxo_p201": ["paramyxovirus"],
}


def connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def required_text(value: Any) -> str:
    cleaned = text(value)
    if not cleaned:
        raise vol.Invalid("value must not be empty")
    return cleaned


def normal(value: Any) -> str:
    return text(value).casefold()


def json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if value in (None, ""):
        return {}
    try:
        loaded = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return dict(loaded) if isinstance(loaded, dict) else {}


def json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if value in (None, ""):
        return []
    try:
        loaded = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return list(loaded) if isinstance(loaded, list) else []


def initialize_products_sync(path: Path) -> None:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS v0927_products (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                source TEXT NOT NULL,
                source_id TEXT,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                species_json TEXT NOT NULL DEFAULT '[]',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                override_json TEXT NOT NULL DEFAULT '{}',
                is_hidden INTEGER NOT NULL DEFAULT 0 CHECK (is_hidden IN (0,1)),
                is_custom INTEGER NOT NULL DEFAULT 0 CHECK (is_custom IN (0,1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_v0927_products_kind_name
                ON v0927_products(kind, normalized_name);
            """
        )
        seed_vaccines(connection, now)


def seed_vaccines(connection: sqlite3.Connection, now: str) -> None:
    catalog_path = Path(__file__).with_name("catalogs") / "vaccines_ch.json"
    try:
        payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    source = dict(payload.get("source") or {}) if isinstance(payload, dict) else {}
    for item in payload.get("items", []) if isinstance(payload, dict) else []:
        if not isinstance(item, dict) or not text(item.get("id")):
            continue
        source_id = text(item["id"])
        product_id = f"vaccines_ch:{source_id}"
        metadata = {
            "aliases": list(item.get("aliases") or []),
            "authorisation_number": text(item.get("authorisation_number")),
            "target_species": list(item.get("target_species") or []),
            "targets": list(_VACCINE_TARGETS.get(source_id, [])),
            "source_name": text(source.get("name")),
            "source_as_of": text(source.get("as_of")),
            "source_url": text(source.get("url")),
        }
        name = required_text(item.get("name"))
        species = list(item.get("target_species") or [])
        connection.execute(
            """
            INSERT INTO v0927_products (
                id,kind,source,source_id,name,normalized_name,species_json,
                metadata_json,override_json,is_hidden,is_custom,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,0,0,?,?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                normalized_name=excluded.normalized_name,
                species_json=excluded.species_json,
                metadata_json=excluded.metadata_json,
                updated_at=excluded.updated_at
            """,
            (
                product_id,
                GABE_VACCINATION,
                "vaccines_ch",
                source_id,
                name,
                normal(name),
                json.dumps(species, ensure_ascii=False),
                json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                "{}",
                now,
                now,
            ),
        )


def product_row(row: sqlite3.Row) -> dict[str, Any]:
    metadata = json_object(row["metadata_json"])
    override = json_object(row["override_json"])
    base = {
        "id": str(row["id"]),
        "kind": str(row["kind"]),
        "source": str(row["source"]),
        "source_id": row["source_id"],
        "name": str(row["name"]),
        "target_species": json_list(row["species_json"]),
        **metadata,
    }
    merged = {**base, **override}
    merged["is_hidden"] = bool(row["is_hidden"])
    merged["is_custom"] = bool(row["is_custom"])
    merged["is_modified"] = bool(override)
    merged["original"] = base
    return merged


def state_sync(path: Path) -> dict[str, Any]:
    with connect(path) as connection:
        rows = connection.execute(
            "SELECT * FROM v0927_products ORDER BY kind,normalized_name,id"
        ).fetchall()
    products = [product_row(row) for row in rows]
    return {
        "gabe_types": list(GABE_TYPES),
        "products": products,
        "vaccines": [item for item in products if item["kind"] == GABE_VACCINATION],
        "supplements": [item for item in products if item["kind"] == GABE_SUPPLEMENT],
        "feeds": [item for item in products if item["kind"] == GABE_FEED],
    }


def save_product_sync(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    kind = required_text(payload.get("kind"))
    if kind not in PRODUCT_KINDS:
        raise ValueError(f"Unsupported product kind: {kind}")
    item_id = text(payload.get("item_id"))
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    fields = dict(payload.get("fields") or {})
    name = required_text(fields.get("name") or payload.get("name"))
    target_species = fields.pop("target_species", payload.get("target_species", []))
    if not isinstance(target_species, list):
        target_species = [target_species] if target_species else []
    target_species = [text(value) for value in target_species if text(value)]
    with connect(path) as connection:
        if item_id:
            row = connection.execute(
                "SELECT * FROM v0927_products WHERE id=? AND kind=?",
                (item_id, kind),
            ).fetchone()
            if row is None:
                raise KeyError(item_id)
            if bool(row["is_custom"]):
                metadata = json_object(row["metadata_json"])
                metadata.update({key: value for key, value in fields.items() if key != "name"})
                connection.execute(
                    """
                    UPDATE v0927_products
                    SET name=?,normalized_name=?,species_json=?,metadata_json=?,updated_at=?
                    WHERE id=?
                    """,
                    (
                        name,
                        normal(name),
                        json.dumps(target_species, ensure_ascii=False),
                        json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                        now,
                        item_id,
                    ),
                )
            else:
                override = {"name": name, "target_species": target_species}
                override.update({key: value for key, value in fields.items() if key != "name"})
                connection.execute(
                    "UPDATE v0927_products SET override_json=?,updated_at=? WHERE id=?",
                    (json.dumps(override, ensure_ascii=False, sort_keys=True), now, item_id),
                )
        else:
            item_id = f"custom:{kind}:{secrets.token_hex(8)}"
            metadata = {key: value for key, value in fields.items() if key != "name"}
            connection.execute(
                """
                INSERT INTO v0927_products (
                    id,kind,source,source_id,name,normalized_name,species_json,
                    metadata_json,override_json,is_hidden,is_custom,created_at,updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,0,1,?,?)
                """,
                (
                    item_id,
                    kind,
                    "manual",
                    None,
                    name,
                    normal(name),
                    json.dumps(target_species, ensure_ascii=False),
                    json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                    "{}",
                    now,
                    now,
                ),
            )
        row = connection.execute("SELECT * FROM v0927_products WHERE id=?", (item_id,)).fetchone()
    if row is None:
        raise RuntimeError("Product could not be loaded after save")
    return product_row(row)


def archive_product_sync(path: Path, item_id: str, hidden: bool) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with connect(path) as connection:
        connection.execute(
            "UPDATE v0927_products SET is_hidden=?,updated_at=? WHERE id=?",
            (1 if hidden else 0, now, item_id),
        )
        row = connection.execute("SELECT * FROM v0927_products WHERE id=?", (item_id,)).fetchone()
    if row is None:
        raise KeyError(item_id)
    return product_row(row)


def reset_product_sync(path: Path, item_id: str) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with connect(path) as connection:
        row = connection.execute("SELECT * FROM v0927_products WHERE id=?", (item_id,)).fetchone()
        if row is None:
            raise KeyError(item_id)
        if bool(row["is_custom"]):
            raise ValueError("Custom products have no official source to reset to")
        connection.execute(
            "UPDATE v0927_products SET override_json='{}',is_hidden=0,updated_at=? WHERE id=?",
            (now, item_id),
        )
        row = connection.execute("SELECT * FROM v0927_products WHERE id=?", (item_id,)).fetchone()
    if row is None:
        raise KeyError(item_id)
    return product_row(row)


def load_product_snapshot(connection: sqlite3.Connection, item_id: str) -> dict[str, Any] | None:
    if not item_id:
        return None
    row = connection.execute("SELECT * FROM v0927_products WHERE id=?", (item_id,)).fetchone()
    if row is None:
        return None
    item = product_row(row)
    item.pop("original", None)
    return item
