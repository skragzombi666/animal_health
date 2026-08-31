from __future__ import annotations

import json
import re
import secrets
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import v0927_data

DATABASE_SWISSMEDIC = "swissmedic_ch"
DATABASE_DEWORMERS = "swissmedic_dewormers"
DATABASE_VACCINES = "animal_health_vaccines_ch"
DATABASE_SUPPLEMENTS = "animal_health_supplements"
DATABASE_FEEDS = "animal_health_feed_chicken"
DATABASE_USER = "user_default"
DATABASE_SCHEMA_VERSION = 1

PRODUCT_KINDS = (
    v0927_data.GABE_MEDICATION,
    v0927_data.GABE_VACCINATION,
    v0927_data.GABE_SUPPLEMENT,
    v0927_data.GABE_FEED,
)

_DEWORMING_WORDS = (
    "anthelm",
    "entwurm",
    "deworm",
    "worm",
    "wurm",
    "flubendazol",
    "fenbendazol",
    "febantel",
    "praziquantel",
    "pyrantel",
    "milbemycin",
    "milbemycinoxim",
    "moxidectin",
    "ivermectin",
    "emodepsid",
    "levamisol",
    "piperazin",
    "selamectin",
)

_SYSTEM_DATABASES: tuple[dict[str, Any], ...] = (
    {
        "id": DATABASE_SWISSMEDIC,
        "name": "Swissmedic – Tierarzneimittel",
        "description": "Offizielle Schweizer Tierarzneimittel-Datenbank.",
        "provider": "Swissmedic",
        "source_type": "official",
        "product_types": [v0927_data.GABE_MEDICATION, v0927_data.GABE_VACCINATION],
        "version": "OGD",
        "data_as_of": "",
        "source_url": "",
        "license": "Swissmedic Open Government Data",
        "priority": 100,
        "is_enabled": True,
        "is_system": True,
        "is_removable": False,
        "update_mode": "automatic",
        "parent_database_id": "",
        "filter_classification": "",
        "metadata": {"immutable_source": True, "supports_local_overrides": True},
    },
    {
        "id": DATABASE_DEWORMERS,
        "name": "Swissmedic – Entwurmungsmittel",
        "description": "Gefilterte Ansicht der als Entwurmungsmittel erkannten Tierarzneimittel.",
        "provider": "Swissmedic / Animal Health",
        "source_type": "view",
        "product_types": [v0927_data.GABE_MEDICATION],
        "version": "1",
        "data_as_of": "",
        "source_url": "",
        "license": "Ansicht auf Swissmedic Open Government Data",
        "priority": 95,
        "is_enabled": True,
        "is_system": True,
        "is_removable": False,
        "update_mode": "derived",
        "parent_database_id": DATABASE_SWISSMEDIC,
        "filter_classification": v0927_data.GABE_DEWORMING,
        "metadata": {"is_view": True},
    },
    {
        "id": DATABASE_VACCINES,
        "name": "Animal Health – Impfstoffe Schweiz",
        "description": "Mitgelieferter, kuratierter Startkatalog für Impfstoffe.",
        "provider": "Animal Health",
        "source_type": "curated",
        "product_types": [v0927_data.GABE_VACCINATION],
        "version": "2026.05",
        "data_as_of": "2026-05-31",
        "source_url": "",
        "license": "Quellenangaben pro Datenbank und Produkt",
        "priority": 80,
        "is_enabled": True,
        "is_system": True,
        "is_removable": False,
        "update_mode": "bundled",
        "parent_database_id": "",
        "filter_classification": "",
        "metadata": {"immutable_source": True, "supports_local_overrides": True},
    },
    {
        "id": DATABASE_SUPPLEMENTS,
        "name": "Animal Health – Ergänzungspräparate",
        "description": "Mitgelieferte, kuratierte Ergänzungspräparate mit mehreren aktiven Bestandteilen.",
        "provider": "Animal Health",
        "source_type": "curated",
        "product_types": [v0927_data.GABE_SUPPLEMENT],
        "version": "2026.08",
        "data_as_of": "2026-08-31",
        "source_url": "",
        "license": "Quellenangaben pro Produkt",
        "priority": 70,
        "is_enabled": True,
        "is_system": True,
        "is_removable": False,
        "update_mode": "bundled",
        "parent_database_id": "",
        "filter_classification": "",
        "metadata": {"immutable_source": True, "supports_local_overrides": True},
    },
    {
        "id": DATABASE_FEEDS,
        "name": "Animal Health – Futtermittel Geflügel",
        "description": "Mitgelieferter Startkatalog für Geflügelfutter mit Nährwerten und Fütterungshinweisen.",
        "provider": "Animal Health",
        "source_type": "curated",
        "product_types": [v0927_data.GABE_FEED],
        "version": "2026.08",
        "data_as_of": "2026-08-31",
        "source_url": "",
        "license": "Quellenangaben pro Produkt",
        "priority": 70,
        "is_enabled": True,
        "is_system": True,
        "is_removable": False,
        "update_mode": "bundled",
        "parent_database_id": "",
        "filter_classification": "",
        "metadata": {"immutable_source": True, "supports_local_overrides": True},
    },
    {
        "id": DATABASE_USER,
        "name": "Meine Produktdatenbank",
        "description": "Eigene, vollständig bearbeitbare Produktdatenbank.",
        "provider": "Lokal",
        "source_type": "user",
        "product_types": list(PRODUCT_KINDS),
        "version": "1",
        "data_as_of": "",
        "source_url": "",
        "license": "Privat",
        "priority": 120,
        "is_enabled": True,
        "is_system": True,
        "is_removable": False,
        "update_mode": "manual",
        "parent_database_id": "",
        "filter_classification": "",
        "metadata": {"editable": True, "immutable_source": False},
    },
)


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _required(value: Any, label: str = "value") -> str:
    cleaned = _text(value)
    if not cleaned:
        raise ValueError(f"{label} must not be empty")
    return cleaned


def _normal(value: Any) -> str:
    return _text(value).casefold()


def _json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if value in (None, ""):
        return []
    try:
        parsed = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return list(parsed) if isinstance(parsed, list) else []


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if value in (None, ""):
        return {}
    try:
        parsed = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return dict(parsed) if isinstance(parsed, dict) else {}


def _table_exists(connection: sqlite3.Connection, name: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        is not None
    )


def _column_names(connection: sqlite3.Connection, table: str) -> set[str]:
    if not _table_exists(connection, table):
        return set()
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}


def _database_payload(definition: dict[str, Any]) -> tuple[Any, ...]:
    return (
        definition["id"],
        definition["name"],
        definition["description"],
        definition["provider"],
        definition["source_type"],
        json.dumps(definition["product_types"], ensure_ascii=False),
        definition["version"],
        definition["data_as_of"],
        definition["source_url"],
        definition["license"],
        int(definition["priority"]),
        1 if definition["is_enabled"] else 0,
        1 if definition["is_system"] else 0,
        1 if definition["is_removable"] else 0,
        definition["update_mode"],
        definition["parent_database_id"],
        definition["filter_classification"],
        json.dumps(definition["metadata"], ensure_ascii=False, sort_keys=True),
    )


def _seed_database_rows(connection: sqlite3.Connection, now: str) -> None:
    for definition in _SYSTEM_DATABASES:
        connection.execute(
            """
            INSERT INTO v0928_product_databases(
                id,name,description,provider,source_type,product_types_json,version,
                data_as_of,source_url,license,priority,is_enabled,is_system,is_removable,
                update_mode,parent_database_id,filter_classification,metadata_json,
                created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                provider=excluded.provider,
                source_type=excluded.source_type,
                product_types_json=excluded.product_types_json,
                version=excluded.version,
                data_as_of=excluded.data_as_of,
                source_url=CASE WHEN excluded.source_url<>'' THEN excluded.source_url ELSE v0928_product_databases.source_url END,
                license=excluded.license,
                is_system=1,
                is_removable=excluded.is_removable,
                update_mode=excluded.update_mode,
                parent_database_id=excluded.parent_database_id,
                filter_classification=excluded.filter_classification,
                metadata_json=excluded.metadata_json,
                updated_at=excluded.updated_at
            """,
            (*_database_payload(definition), now, now),
        )


def _ensure_product_database_column(connection: sqlite3.Connection) -> None:
    columns = _column_names(connection, "v0927_products")
    if "database_id" not in columns:
        connection.execute(
            "ALTER TABLE v0927_products ADD COLUMN database_id TEXT NOT NULL DEFAULT ''"
        )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_v0928_products_database ON v0927_products(database_id,kind,normalized_name)"
    )
    connection.execute(
        "UPDATE v0927_products SET database_id=? WHERE source='vaccines_ch' AND database_id=''",
        (DATABASE_VACCINES,),
    )
    connection.execute(
        "UPDATE v0927_products SET database_id=? WHERE is_custom=1 AND database_id=''",
        (DATABASE_USER,),
    )
    connection.execute(
        "UPDATE v0927_products SET database_id=? WHERE kind=? AND database_id=''",
        (DATABASE_VACCINES, v0927_data.GABE_VACCINATION),
    )
    connection.execute(
        "UPDATE v0927_products SET database_id=? WHERE kind=? AND database_id=''",
        (DATABASE_SUPPLEMENTS, v0927_data.GABE_SUPPLEMENT),
    )
    connection.execute(
        "UPDATE v0927_products SET database_id=? WHERE kind=? AND database_id=''",
        (DATABASE_FEEDS, v0927_data.GABE_FEED),
    )


def _seed_curated_products(connection: sqlite3.Connection, now: str) -> None:
    path = Path(__file__).with_name("catalogs") / "product_databases_0928.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    for database in document.get("databases", []) if isinstance(document, dict) else []:
        if not isinstance(database, dict):
            continue
        database_id = _text(database.get("id"))
        if not database_id:
            continue
        for raw in database.get("products", []):
            if not isinstance(raw, dict):
                continue
            source_id = _text(raw.get("id"))
            kind = _text(raw.get("kind"))
            name = _text(raw.get("name"))
            if not source_id or kind not in PRODUCT_KINDS or not name:
                continue
            item_id = f"{database_id}:{source_id}"
            target_species = [
                _text(item) for item in raw.get("target_species", []) if _text(item)
            ]
            metadata = {
                key: value
                for key, value in raw.items()
                if key not in {"id", "kind", "name", "target_species"}
            }
            metadata.setdefault("source_database_id", database_id)
            connection.execute(
                """
                INSERT INTO v0927_products(
                    id,kind,source,source_id,name,normalized_name,species_json,
                    metadata_json,override_json,is_hidden,is_custom,created_at,updated_at,database_id
                ) VALUES(?,?,?,?,?,?,?,?,?,0,0,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    kind=excluded.kind,
                    source=excluded.source,
                    source_id=excluded.source_id,
                    name=excluded.name,
                    normalized_name=excluded.normalized_name,
                    species_json=excluded.species_json,
                    metadata_json=excluded.metadata_json,
                    database_id=excluded.database_id,
                    updated_at=excluded.updated_at
                """,
                (
                    item_id,
                    kind,
                    database_id,
                    source_id,
                    name,
                    _normal(name),
                    json.dumps(target_species, ensure_ascii=False),
                    json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                    "{}",
                    now,
                    now,
                    database_id,
                ),
            )


def _migrate_legacy_medications(connection: sqlite3.Connection, now: str) -> None:
    columns = _column_names(connection, "v0817_medications")
    if not columns or "id" not in columns or "name" not in columns:
        return
    wanted = (
        "id",
        "name",
        "species_id",
        "default_unit",
        "default_route",
        "active_ingredient",
        "concentration",
        "dosage_form",
        "is_archived",
        "product_category",
    )
    selected = [name for name in wanted if name in columns]
    rows = connection.execute(
        f"SELECT {','.join(selected)} FROM v0817_medications ORDER BY id"
    ).fetchall()
    for row in rows:
        row_data = {name: row[name] for name in selected}
        legacy_id = str(row_data["id"])
        name = _text(row_data.get("name"))
        if not name:
            continue
        kind = (
            v0927_data.GABE_SUPPLEMENT
            if _text(row_data.get("product_category")) == v0927_data.GABE_SUPPLEMENT
            else v0927_data.GABE_MEDICATION
        )
        species = [_text(row_data.get("species_id"))] if _text(row_data.get("species_id")) else []
        metadata = {
            "legacy_medication_id": legacy_id,
            "default_unit": _text(row_data.get("default_unit")) or "dose",
            "default_route": _text(row_data.get("default_route")),
            "active_ingredient": _text(row_data.get("active_ingredient")),
            "concentration": _text(row_data.get("concentration")),
            "dosage_form": _text(row_data.get("dosage_form")),
            "classifications": [kind],
        }
        connection.execute(
            """
            INSERT OR IGNORE INTO v0927_products(
                id,kind,source,source_id,name,normalized_name,species_json,
                metadata_json,override_json,is_hidden,is_custom,created_at,updated_at,database_id
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                f"legacy_medication:{legacy_id}",
                kind,
                "legacy_medication",
                legacy_id,
                name,
                _normal(name),
                json.dumps(species, ensure_ascii=False),
                json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                "{}",
                1 if bool(row_data.get("is_archived")) else 0,
                1,
                now,
                now,
                DATABASE_USER,
            ),
        )


def initialize_product_databases_sync(path: Path) -> None:
    v0927_data.initialize_products_sync(path)
    now = _now()
    with v0927_data.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS v0928_product_databases(
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                provider TEXT NOT NULL DEFAULT '',
                source_type TEXT NOT NULL,
                product_types_json TEXT NOT NULL DEFAULT '[]',
                version TEXT NOT NULL DEFAULT '',
                data_as_of TEXT NOT NULL DEFAULT '',
                source_url TEXT NOT NULL DEFAULT '',
                license TEXT NOT NULL DEFAULT '',
                priority INTEGER NOT NULL DEFAULT 50,
                is_enabled INTEGER NOT NULL DEFAULT 1 CHECK(is_enabled IN (0,1)),
                is_system INTEGER NOT NULL DEFAULT 0 CHECK(is_system IN (0,1)),
                is_removable INTEGER NOT NULL DEFAULT 1 CHECK(is_removable IN (0,1)),
                update_mode TEXT NOT NULL DEFAULT 'manual',
                parent_database_id TEXT NOT NULL DEFAULT '',
                filter_classification TEXT NOT NULL DEFAULT '',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_v0928_databases_enabled_priority
                ON v0928_product_databases(is_enabled,priority DESC,name);
            """
        )
        _seed_database_rows(connection, now)
        _ensure_product_database_column(connection)
        _seed_curated_products(connection, now)
        _migrate_legacy_medications(connection, now)


def _database_row(row: sqlite3.Row) -> dict[str, Any]:
    metadata = _json_object(row["metadata_json"])
    return {
        "id": str(row["id"]),
        "name": str(row["name"]),
        "description": str(row["description"] or ""),
        "provider": str(row["provider"] or ""),
        "source_type": str(row["source_type"]),
        "product_types": _json_list(row["product_types_json"]),
        "version": str(row["version"] or ""),
        "data_as_of": str(row["data_as_of"] or ""),
        "source_url": str(row["source_url"] or ""),
        "license": str(row["license"] or ""),
        "priority": int(row["priority"] or 0),
        "is_enabled": bool(row["is_enabled"]),
        "is_system": bool(row["is_system"]),
        "is_removable": bool(row["is_removable"]),
        "update_mode": str(row["update_mode"] or "manual"),
        "parent_database_id": str(row["parent_database_id"] or ""),
        "filter_classification": str(row["filter_classification"] or ""),
        "metadata": metadata,
        "is_editable": bool(metadata.get("editable")) or not bool(row["is_system"]),
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
    }


def _database_rows(path: Path) -> list[dict[str, Any]]:
    with v0927_data.connect(path) as connection:
        rows = connection.execute(
            "SELECT * FROM v0928_product_databases ORDER BY priority DESC,name COLLATE NOCASE,id"
        ).fetchall()
    return [_database_row(row) for row in rows]


def _database_by_id(connection: sqlite3.Connection, database_id: str) -> sqlite3.Row:
    row = connection.execute(
        "SELECT * FROM v0928_product_databases WHERE id=?", (database_id,)
    ).fetchone()
    if row is None:
        raise KeyError(database_id)
    return row
