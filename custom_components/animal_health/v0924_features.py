from __future__ import annotations

import io
import json
import re
import secrets
import sqlite3
from datetime import UTC, date, datetime, time as dt_time, timedelta
from pathlib import Path
from typing import Any, cast

import voluptuous as vol
from aiohttp import web

from homeassistant.components import websocket_api
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.http import KEY_HASS
from homeassistant.util import dt as dt_util

from .const import DATABASE_NAME, DOMAIN, DOSE_UNITS, ADMINISTRATION_ROUTES
from .runtime import AnimalHealthRuntimeData
from . import v0912_features as treatment_features

_STATE_COMMAND = f"{DOMAIN}/v0924/state"
_MASTER_SAVE_COMMAND = f"{DOMAIN}/v0924/master/save"
_MASTER_ARCHIVE_COMMAND = f"{DOMAIN}/v0924/master/archive"
_MASTER_RESET_COMMAND = f"{DOMAIN}/v0924/master/reset"
_CATALOG_OVERRIDE_COMMAND = f"{DOMAIN}/v0924/catalog/override"
_CATALOG_RESET_COMMAND = f"{DOMAIN}/v0924/catalog/reset"
_EVENT_EDIT_COMMAND = f"{DOMAIN}/v0924/event/edit"
_EVENT_DELETE_COMMAND = f"{DOMAIN}/v0924/event/delete"
_SYMPTOM_EDIT_COMMAND = f"{DOMAIN}/v0924/symptom/assessment/edit"
_TREATMENT_EXECUTE_COMMAND = f"{DOMAIN}/v0924/treatment/execute"
_TREATMENT_EDIT_COMMAND = f"{DOMAIN}/v0924/treatment/edit"
_TREATMENT_DELETE_COMMAND = f"{DOMAIN}/v0924/treatment/delete"
_TREATMENT_ADD_COMMAND = f"{DOMAIN}/v0924/treatment/add"
_ATTACHMENT_URLS_COMMAND = f"{DOMAIN}/v0924/attachment/urls"
_TOKEN_KEY = f"{DOMAIN}_v0924_attachment_tokens"
_VIEW_STATE_KEY = f"{DOMAIN}_v0924_views"

_EVENT_TYPES = (
    ("observation", "Beobachtung", "Observation", "observation"),
    ("control", "Kontrolle", "Control", "observation"),
    ("diagnosis", "Diagnose", "Diagnosis", "diagnosis"),
    ("treatment", "Behandlung", "Treatment", "treatment"),
    ("veterinary_visit", "Tierarztbesuch", "Veterinary visit", "veterinary_visit"),
    ("care", "Pflege", "Care", "care"),
    ("other", "Andere", "Other", "other"),
)
_SYMPTOMS = (
    ("reduced_appetite", "Verminderter Appetit", "Reduced appetite"),
    ("lethargy", "Lethargie", "Lethargy"),
    ("diarrhea", "Durchfall", "Diarrhea"),
    ("coughing", "Husten", "Coughing"),
    ("sneezing", "Niesen", "Sneezing"),
    ("lameness", "Lahmheit", "Lameness"),
    ("weight_loss", "Gewichtsverlust", "Weight loss"),
)


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _database_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(DATABASE_NAME))


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _required_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if not text:
        raise vol.Invalid("value must not be empty")
    return text


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalise(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def _record_id(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(6).upper()}"


def _json(value: Any, fallback: Any) -> Any:
    try:
        decoded = json.loads(str(value or ""))
    except (TypeError, json.JSONDecodeError):
        return fallback
    return decoded


def _event_when(hass: HomeAssistant, raw_date: Any, raw_time: Any) -> tuple[datetime, str, str]:
    timezone = dt_util.get_time_zone(hass.config.time_zone) or UTC
    date_text = str(raw_date or "").strip()
    time_text = str(raw_time or "").strip()
    if not date_text:
        now_local = datetime.now(UTC).astimezone(timezone).replace(microsecond=0)
        return now_local.astimezone(UTC), "datetime", now_local.date().isoformat()
    day = date.fromisoformat(date_text)
    if time_text:
        local_time = dt_time.fromisoformat(time_text)
        local_value = datetime.combine(day, local_time, tzinfo=timezone).replace(microsecond=0)
        return local_value.astimezone(UTC), "datetime", day.isoformat()
    local_value = datetime.combine(day, dt_time(12, 0), tzinfo=timezone)
    return local_value.astimezone(UTC), "date", day.isoformat()


def _precision_data(precision: str, day: str) -> dict[str, Any]:
    result: dict[str, Any] = {"time_precision": precision}
    if precision == "date":
        result["occurred_date"] = day
    else:
        result.pop("occurred_date", None)
    return result


def _table_exists(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _seed_master_items(connection: sqlite3.Connection) -> None:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    for item_id, de, en, storage in _EVENT_TYPES:
        connection.execute(
            """
            INSERT INTO v0924_master_items(
                kind,item_id,base_label_de,base_label_en,override_label,storage_value,
                is_custom,is_hidden,created_at,updated_at
            ) VALUES('entry_type',?,?,?,?,?,0,0,?,?)
            ON CONFLICT(kind,item_id) DO UPDATE SET
                base_label_de=excluded.base_label_de,base_label_en=excluded.base_label_en,
                storage_value=excluded.storage_value,updated_at=excluded.updated_at
            """,
            (item_id, de, en, None, storage, now, now),
        )
    for item_id, de, en in _SYMPTOMS:
        connection.execute(
            """
            INSERT INTO v0924_master_items(
                kind,item_id,base_label_de,base_label_en,override_label,storage_value,
                is_custom,is_hidden,created_at,updated_at
            ) VALUES('symptom',?,?,?,?,?,0,0,?,?)
            ON CONFLICT(kind,item_id) DO UPDATE SET
                base_label_de=excluded.base_label_de,base_label_en=excluded.base_label_en,
                updated_at=excluded.updated_at
            """,
            (item_id, de, en, None, item_id, now, now),
        )
    if _table_exists(connection, "v0915_symptoms"):
        rows = connection.execute(
            "SELECT id,name,is_archived FROM v0915_symptoms"
        ).fetchall()
        for row in rows:
            item_id = f"custom.v0915.{row['id']}"
            connection.execute(
                """
                INSERT INTO v0924_master_items(
                    kind,item_id,base_label_de,base_label_en,override_label,storage_value,
                    is_custom,is_hidden,created_at,updated_at
                ) VALUES('symptom',?,?,?,?,?,1,?,?,?)
                ON CONFLICT(kind,item_id) DO UPDATE SET
                    base_label_de=excluded.base_label_de,base_label_en=excluded.base_label_en,
                    is_hidden=MAX(v0924_master_items.is_hidden,excluded.is_hidden),updated_at=excluded.updated_at
                """,
                (
                    item_id,
                    str(row["name"]),
                    str(row["name"]),
                    None,
                    str(row["name"]),
                    1 if bool(row["is_archived"]) else 0,
                    now,
                    now,
                ),
            )


def _initialise_sync(path: Path) -> None:
    with _connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS v0924_master_items(
                kind TEXT NOT NULL CHECK(kind IN ('entry_type','symptom')),
                item_id TEXT NOT NULL,
                base_label_de TEXT NOT NULL,
                base_label_en TEXT NOT NULL,
                override_label TEXT,
                storage_value TEXT NOT NULL,
                is_custom INTEGER NOT NULL DEFAULT 0 CHECK(is_custom IN (0,1)),
                is_hidden INTEGER NOT NULL DEFAULT 0 CHECK(is_hidden IN (0,1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(kind,item_id)
            );
            CREATE INDEX IF NOT EXISTS idx_v0924_master_kind_hidden
                ON v0924_master_items(kind,is_hidden,item_id);
            CREATE TABLE IF NOT EXISTS v0924_catalog_meta(
                source_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                sequence_number TEXT,
                official_product_name TEXT,
                active_ingredient_details_json TEXT NOT NULL DEFAULT '[]',
                routes_json TEXT NOT NULL DEFAULT '[]',
                route_descriptions_json TEXT NOT NULL DEFAULT '[]',
                default_route TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(source_id,item_id)
            );
            CREATE TABLE IF NOT EXISTS v0924_catalog_overrides(
                source_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                hidden INTEGER NOT NULL DEFAULT 0 CHECK(hidden IN (0,1)),
                override_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL,
                PRIMARY KEY(source_id,item_id)
            );
            CREATE TABLE IF NOT EXISTS v0924_requests(
                request_id TEXT PRIMARY KEY,
                command TEXT NOT NULL,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS v0924_meta(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        _seed_master_items(connection)
        marker = connection.execute(
            "SELECT value FROM v0924_meta WHERE key='sequence_catalog_refresh'"
        ).fetchone()
        if marker is None and _table_exists(connection, "v0920_catalog_sources"):
            now = datetime.now(UTC).replace(microsecond=0).isoformat()
            connection.execute(
                "UPDATE v0920_catalog_sources SET is_complete=0,last_attempt_at=NULL,updated_at=? WHERE source_id='swissmedic_ch'",
                (now,),
            )
            connection.execute(
                "INSERT INTO v0924_meta(key,value,updated_at) VALUES('sequence_catalog_refresh','1',?)",
                (now,),
            )
        _seed_metacam_fallback(connection)
    _assign_treatment_execution_ids_sync(path)


def _seed_metacam_fallback(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "v0920_catalog_products"):
        return
    source = connection.execute(
        "SELECT is_complete FROM v0920_catalog_sources WHERE source_id='swissmedic_ch'"
    ).fetchone()
    if source is None or bool(source["is_complete"]):
        return
    exists = connection.execute(
        "SELECT 1 FROM v0920_catalog_products WHERE source_id='swissmedic_ch' AND normalized_name LIKE '%metacam 15 mg/ml%' LIMIT 1"
    ).fetchone()
    if exists is not None:
        return
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    name = "Metacam 15 mg/ml ad us. vet., Suspension für Pferde"
    connection.execute(
        """
        INSERT OR REPLACE INTO v0920_catalog_products(
            source_id,item_id,authorisation_number,name,normalized_name,active_ingredient,
            active_ingredients_json,concentration,dosage_form,target_species_json,aliases_json,
            authorisation_status,application_area,updated_at
        ) VALUES('swissmedic_ch','swissmedic.56764.fallback','56764',?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            name,
            _normalise(name),
            "Meloxicam",
            json.dumps(["Meloxicam"]),
            "15 mg/ml",
            "Suspension",
            json.dumps(["horse"]),
            json.dumps(["Metacam 15 mg/ml"]),
            "fallback",
            "Pferde",
            now,
        ),
    )
    connection.execute(
        """
        INSERT OR REPLACE INTO v0924_catalog_meta(
            source_id,item_id,sequence_number,official_product_name,
            active_ingredient_details_json,routes_json,route_descriptions_json,default_route,updated_at
        ) VALUES('swissmedic_ch','swissmedic.56764.fallback','',?,?,'["oral"]','["Oral"]','oral',?)
        """,
        (
            name,
            json.dumps([{"name": "Meloxicam", "amount": 15.0, "unit": "mg", "per": 1.0, "per_unit": "ml"}]),
            now,
        ),
    )


def _store_catalog_meta_sync(path: Path, products: list[dict[str, Any]]) -> None:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        connection.execute("DELETE FROM v0924_catalog_meta WHERE source_id='swissmedic_ch'")
        rows = []
        for item in products:
            item_id = str(item.get("id") or "").strip()
            if not item_id:
                continue
            rows.append(
                (
                    str(item.get("source_id") or "swissmedic_ch"),
                    item_id,
                    str(item.get("sequence_number") or ""),
                    str(item.get("official_product_name") or item.get("name") or ""),
                    json.dumps(item.get("active_ingredient_details") or [], ensure_ascii=False),
                    json.dumps(item.get("routes") or [], ensure_ascii=False),
                    json.dumps(item.get("route_descriptions") or [], ensure_ascii=False),
                    str(item.get("default_route") or ""),
                    now,
                )
            )
        connection.executemany(
            """
            INSERT OR REPLACE INTO v0924_catalog_meta(
                source_id,item_id,sequence_number,official_product_name,
                active_ingredient_details_json,routes_json,route_descriptions_json,default_route,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?)
            """,
            rows,
        )


def _master_state_sync(path: Path) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT kind,item_id,base_label_de,base_label_en,override_label,storage_value,
                   is_custom,is_hidden,created_at,updated_at
            FROM v0924_master_items
            ORDER BY kind,is_custom,base_label_de COLLATE NOCASE,item_id
            """
        ).fetchall()
    return [
        {
            "kind": str(row["kind"]),
            "id": str(row["item_id"]),
            "base_label_de": str(row["base_label_de"]),
            "base_label_en": str(row["base_label_en"]),
            "label": str(row["override_label"] or row["base_label_de"]),
            "override_label": str(row["override_label"] or ""),
            "storage_value": str(row["storage_value"]),
            "is_custom": bool(row["is_custom"]),
            "is_hidden": bool(row["is_hidden"]),
            "is_modified": bool(row["override_label"]),
        }
        for row in rows
    ]


def _catalog_state_sync(path: Path) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        if not _table_exists(connection, "v0920_catalog_products"):
            return []
        rows = connection.execute(
            """
            SELECT p.source_id,p.item_id,p.authorisation_number,p.name,p.active_ingredient,
                   p.active_ingredients_json,p.concentration,p.dosage_form,p.target_species_json,
                   p.aliases_json,p.authorisation_status,p.application_area,
                   m.sequence_number,m.official_product_name,m.active_ingredient_details_json,
                   m.routes_json,m.route_descriptions_json,m.default_route,
                   o.hidden,o.override_json
            FROM v0920_catalog_products AS p
            LEFT JOIN v0924_catalog_meta AS m
              ON m.source_id=p.source_id AND m.item_id=p.item_id
            LEFT JOIN v0924_catalog_overrides AS o
              ON o.source_id=p.source_id AND o.item_id=p.item_id
            ORDER BY p.name COLLATE NOCASE,p.item_id
            """
        ).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        original = {
            "id": str(row["item_id"]),
            "source_id": str(row["source_id"]),
            "authorisation_number": str(row["authorisation_number"] or ""),
            "sequence_number": str(row["sequence_number"] or ""),
            "name": str(row["name"]),
            "official_product_name": str(row["official_product_name"] or row["name"]),
            "active_ingredient": str(row["active_ingredient"] or ""),
            "active_ingredients": _json(row["active_ingredients_json"], []),
            "active_ingredient_details": _json(row["active_ingredient_details_json"], []),
            "concentration": str(row["concentration"] or ""),
            "dosage_form": str(row["dosage_form"] or ""),
            "target_species": _json(row["target_species_json"], []),
            "aliases": _json(row["aliases_json"], []),
            "authorisation_status": str(row["authorisation_status"] or ""),
            "application_area": str(row["application_area"] or ""),
            "routes": _json(row["routes_json"], []),
            "route_descriptions": _json(row["route_descriptions_json"], []),
            "default_route": str(row["default_route"] or ""),
            "source": "catalog",
        }
        override = _json(row["override_json"], {}) if row["override_json"] else {}
        merged = {**original, **(override if isinstance(override, dict) else {})}
        merged["original"] = original
        merged["is_hidden"] = bool(row["hidden"] or 0)
        merged["is_modified"] = bool(override)
        result.append(merged)
    return result


def _state_sync(path: Path) -> dict[str, Any]:
    masters = _master_state_sync(path)
    return {
        "entry_types": [item for item in masters if item["kind"] == "entry_type"],
        "symptoms": [item for item in masters if item["kind"] == "symptom"],
        "catalog_products": _catalog_state_sync(path),
    }


def _save_master_sync(path: Path, kind: str, item_id: str | None, label: str) -> dict[str, Any]:
    clean = _required_text(label)
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        if item_id:
            row = connection.execute(
                "SELECT * FROM v0924_master_items WHERE kind=? AND item_id=?",
                (kind, item_id),
            ).fetchone()
            if row is None:
                raise KeyError(item_id)
            if bool(row["is_custom"]):
                connection.execute(
                    "UPDATE v0924_master_items SET base_label_de=?,base_label_en=?,storage_value=?,override_label=NULL,updated_at=? WHERE kind=? AND item_id=?",
                    (clean, clean, clean if kind == "symptom" else str(row["storage_value"]), now, kind, item_id),
                )
            else:
                base = str(row["base_label_de"])
                connection.execute(
                    "UPDATE v0924_master_items SET override_label=?,updated_at=? WHERE kind=? AND item_id=?",
                    (None if clean == base else clean, now, kind, item_id),
                )
        else:
            new_id = f"custom.{kind}.{secrets.token_hex(5)}"
            storage = clean if kind == "symptom" else "other"
            connection.execute(
                """
                INSERT INTO v0924_master_items(
                    kind,item_id,base_label_de,base_label_en,override_label,storage_value,
                    is_custom,is_hidden,created_at,updated_at
                ) VALUES(?,?,?,?,NULL,?,1,0,?,?)
                """,
                (kind, new_id, clean, clean, storage, now, now),
            )
            item_id = new_id
    return next(item for item in _master_state_sync(path) if item["kind"] == kind and item["id"] == item_id)


def _archive_master_sync(path: Path, kind: str, item_id: str, hidden: bool) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        cursor = connection.execute(
            "UPDATE v0924_master_items SET is_hidden=?,updated_at=? WHERE kind=? AND item_id=?",
            (1 if hidden else 0, now, kind, item_id),
        )
        if cursor.rowcount == 0:
            raise KeyError(item_id)
    return next(item for item in _master_state_sync(path) if item["kind"] == kind and item["id"] == item_id)


def _reset_master_sync(path: Path, kind: str, item_id: str) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT is_custom FROM v0924_master_items WHERE kind=? AND item_id=?",
            (kind, item_id),
        ).fetchone()
        if row is None:
            raise KeyError(item_id)
        if bool(row["is_custom"]):
            raise ValueError("Custom items have no original definition")
        connection.execute(
            "UPDATE v0924_master_items SET override_label=NULL,is_hidden=0,updated_at=? WHERE kind=? AND item_id=?",
            (now, kind, item_id),
        )
    return next(item for item in _master_state_sync(path) if item["kind"] == kind and item["id"] == item_id)


def _save_catalog_override_sync(path: Path, source_id: str, item_id: str, hidden: bool, fields: dict[str, Any]) -> dict[str, Any]:
    allowed = {"name", "active_ingredient", "active_ingredients", "active_ingredient_details", "concentration", "dosage_form", "target_species", "aliases", "default_route"}
    clean_fields = {key: value for key, value in fields.items() if key in allowed}
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        exists = connection.execute(
            "SELECT 1 FROM v0920_catalog_products WHERE source_id=? AND item_id=?",
            (source_id, item_id),
        ).fetchone()
        if exists is None:
            raise KeyError(item_id)
        connection.execute(
            """
            INSERT INTO v0924_catalog_overrides(source_id,item_id,hidden,override_json,updated_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(source_id,item_id) DO UPDATE SET
                hidden=excluded.hidden,override_json=excluded.override_json,updated_at=excluded.updated_at
            """,
            (source_id, item_id, 1 if hidden else 0, json.dumps(clean_fields, ensure_ascii=False, sort_keys=True), now),
        )
    return next(item for item in _catalog_state_sync(path) if item["source_id"] == source_id and item["id"] == item_id)


def _reset_catalog_override_sync(path: Path, source_id: str, item_id: str) -> dict[str, Any]:
    with _connect(path) as connection:
        connection.execute(
            "DELETE FROM v0924_catalog_overrides WHERE source_id=? AND item_id=?",
            (source_id, item_id),
        )
    return next(item for item in _catalog_state_sync(path) if item["source_id"] == source_id and item["id"] == item_id)


def _parse_event_data(row: sqlite3.Row) -> dict[str, Any]:
    data = _json(row["data_json"], {})
    return data if isinstance(data, dict) else {}


def _assign_treatment_execution_ids_sync(path: Path) -> None:
    with _connect(path) as connection:
        parents = connection.execute(
            "SELECT rowid,id,animal_id,occurred_at,data_json FROM events WHERE event_type='treatment' ORDER BY rowid"
        ).fetchall()
        parsed = []
        for row in parents:
            data = _parse_event_data(row)
            plan_id = data.get("treatment_plan_id") or data.get("task_execution", {}).get("treatment_plan_id") if isinstance(data.get("task_execution"), dict) else data.get("treatment_plan_id")
            if plan_id in (None, ""):
                continue
            parsed.append((row, data, str(plan_id)))
        for index, (parent, data, plan_id) in enumerate(parsed):
            tx_id = str(data.get("treatment_execution_id") or f"TX-{parent['id']}")
            data["treatment_execution_id"] = tx_id
            data["treatment_execution_role"] = "parent"
            connection.execute(
                "UPDATE events SET data_json=? WHERE id=?",
                (json.dumps(data, ensure_ascii=False, sort_keys=True), parent["id"]),
            )
            next_rowid: int | None = None
            for later, later_data, later_plan in parsed[index + 1 :]:
                if (
                    str(later["animal_id"]) == str(parent["animal_id"])
                    and str(later["occurred_at"]) == str(parent["occurred_at"])
                    and later_plan == plan_id
                ):
                    next_rowid = int(later["rowid"])
                    break
            sql = "SELECT rowid,id,event_type,data_json FROM events WHERE rowid>? AND animal_id=? AND occurred_at=?"
            params: list[Any] = [parent["rowid"], parent["animal_id"], parent["occurred_at"]]
            if next_rowid is not None:
                sql += " AND rowid<?"
                params.append(next_rowid)
            sql += " ORDER BY rowid"
            for child in connection.execute(sql, params).fetchall():
                if str(child["event_type"]) == "treatment":
                    continue
                child_data = _parse_event_data(child)
                child_plan = child_data.get("treatment_plan_id")
                if child_plan in (None, "") or str(child_plan) != plan_id:
                    continue
                if child_data.get("treatment_execution_id"):
                    continue
                child_data["treatment_execution_id"] = tx_id
                child_data["treatment_execution_role"] = "component"
                child_data["treatment_parent_event_id"] = str(parent["id"])
                connection.execute(
                    "UPDATE events SET data_json=? WHERE id=?",
                    (json.dumps(child_data, ensure_ascii=False, sort_keys=True), child["id"]),
                )


def _event_rows_for_execution(connection: sqlite3.Connection, tx_id: str) -> list[sqlite3.Row]:
    rows = connection.execute(
        "SELECT rowid,* FROM events ORDER BY rowid"
    ).fetchall()
    return [row for row in rows if str(_parse_event_data(row).get("treatment_execution_id") or "") == tx_id]


def _current_execution_rows(connection: sqlite3.Connection, tx_id: str) -> list[sqlite3.Row]:
    rows = _event_rows_for_execution(connection, tx_id)
    corrected = {str(row["correction_of_event_id"]) for row in rows if row["correction_of_event_id"]}
    return [row for row in rows if str(row["id"]) not in corrected and not bool(row["is_deleted"])]


def _move_attachments(connection: sqlite3.Connection, old_id: str, new_id: str) -> None:
    if _table_exists(connection, "attachments"):
        connection.execute("UPDATE attachments SET event_id=? WHERE event_id=?", (new_id, old_id))


def _create_correction(database, connection: sqlite3.Connection, row: sqlite3.Row, *, occurred_at: datetime, data: dict[str, Any], title: str | None = None, notes: str | None | object = ..., event_type: str | None = None, value: float | None | object = ..., unit: str | None | object = ...):
    actual_notes = row["notes"] if notes is ... else notes
    actual_value = row["value"] if value is ... else value
    actual_unit = row["unit"] if unit is ... else unit
    event = database._create_event_in_connection(  # noqa: SLF001
        connection,
        animal_id=str(row["animal_id"]),
        event_type=event_type or str(row["event_type"]),
        occurred_at=occurred_at,
        title=title if title is not None else str(row["title"]),
        notes=actual_notes,
        value=actual_value,
        unit=actual_unit,
        correction_of_event_id=str(row["id"]),
        data=data,
    )
    if row["task_id"] or row["task_occurrence_id"]:
        connection.execute(
            "UPDATE events SET task_id=?,task_occurrence_id=? WHERE id=?",
            (row["task_id"], row["task_occurrence_id"], event.id),
        )
    _move_attachments(connection, str(row["id"]), event.id)
    return event


def _master_item(connection: sqlite3.Connection, kind: str, item_id: str) -> sqlite3.Row | None:
    return connection.execute(
        "SELECT * FROM v0924_master_items WHERE kind=? AND item_id=?", (kind, item_id)
    ).fetchone()


def _edit_event_sync(database, path: Path, event_id: str, occurred_at: datetime, day: str, precision: str, title: str | None, notes: str | None, entry_type_id: str | None, value: float | None, unit: str | None) -> dict[str, Any]:
    with database._connect() as connection:  # noqa: SLF001
        row = connection.execute("SELECT rowid,* FROM events WHERE id=?", (event_id,)).fetchone()
        if row is None:
            raise KeyError(event_id)
        data = _parse_event_data(row)
        if data.get("symptom_episode_id"):
            raise ValueError("Use symptom assessment editing for symptom episodes")
        if str(row["event_type"]) == "treatment" and data.get("treatment_execution_id"):
            raise ValueError("Use treatment execution editing for treatment groups")
        storage_event_type = str(row["event_type"])
        if entry_type_id:
            master = _master_item(connection, "entry_type", entry_type_id)
            if master is None:
                raise KeyError(entry_type_id)
            storage_event_type = str(master["storage_value"])
            data["entry_type_id"] = entry_type_id
            data["entry_type_label"] = str(master["override_label"] or master["base_label_de"])
        data.update(_precision_data(precision, day))
        new_event = _create_correction(
            database,
            connection,
            row,
            occurred_at=occurred_at,
            data=data,
            title=title if title is not None else str(row["title"]),
            notes=notes,
            event_type=storage_event_type,
            value=row["value"] if value is None else value,
            unit=row["unit"] if unit is None else unit,
        )
    return new_event.as_dict()


def _delete_event_sync(path: Path, event_id: str) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        row = connection.execute("SELECT id,data_json FROM events WHERE id=?", (event_id,)).fetchone()
        if row is None:
            raise KeyError(event_id)
        data = _parse_event_data(row)
        tx_id = str(data.get("treatment_execution_id") or "")
        if tx_id and str(data.get("treatment_execution_role") or "") == "parent":
            ids = [str(item["id"]) for item in _event_rows_for_execution(connection, tx_id)]
            connection.executemany(
                "UPDATE events SET is_deleted=1,deleted_at=? WHERE id=?",
                [(now, item_id) for item_id in ids],
            )
            return {"event_id": event_id, "deleted_at": now, "group_event_ids": ids}
        connection.execute("UPDATE events SET is_deleted=1,deleted_at=? WHERE id=?", (now, event_id))
    return {"event_id": event_id, "deleted_at": now}


def _component_event(database, connection: sqlite3.Connection, *, parent_id: str, tx_id: str, plan_id: int, plan_name: str, animal_id: str, occurred_at: datetime, component: dict[str, Any], index: int | None, extra: bool, precision: str, day: str):
    component_type = str(component.get("type") or "product")
    product = component_type in {"product", "medication", "supplement"}
    action = component_type == "action"
    event_type = "medication" if product else "care"
    data = {
        "source": "treatment_plan_extra" if extra else "treatment_plan",
        "treatment_plan_id": plan_id,
        "treatment_plan_name": plan_name,
        "treatment_execution_id": tx_id,
        "treatment_execution_role": "extra" if extra else "component",
        "treatment_parent_event_id": parent_id,
        "treatment_component_index": index,
        "treatment_component_optional": bool(component.get("optional")),
        "treatment_component_extra": extra,
        "component_type": component_type,
        **_precision_data(precision, day),
    }
    if component.get("route"):
        data["route"] = str(component["route"])
    return database._create_event_in_connection(  # noqa: SLF001
        connection,
        animal_id=animal_id,
        event_type=event_type,
        occurred_at=occurred_at,
        title=str(component.get("name") or "Behandlungsschritt"),
        notes=str(component.get("instructions") or "").strip() or None,
        value=None if action else float(component.get("dose")),
        unit=None if action else str(component.get("unit")),
        data=data,
    )


def _request_response(connection: sqlite3.Connection, request_id: str, command: str) -> dict[str, Any] | None:
    if not request_id:
        return None
    row = connection.execute(
        "SELECT response_json FROM v0924_requests WHERE request_id=? AND command=?",
        (request_id, command),
    ).fetchone()
    decoded = _json(row["response_json"], None) if row is not None else None
    return decoded if isinstance(decoded, dict) else None


def _save_request(connection: sqlite3.Connection, request_id: str, command: str, response: dict[str, Any]) -> None:
    if not request_id:
        return
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    connection.execute(
        "INSERT OR REPLACE INTO v0924_requests(request_id,command,response_json,created_at) VALUES(?,?,?,?)",
        (request_id, command, json.dumps(response, ensure_ascii=False, sort_keys=True), now),
    )


def _execute_treatment_sync(database, plan_id: int, animal_id: str, occurred_at: datetime, day: str, precision: str, notes: str | None, selected_optional: list[int], extras: list[dict[str, Any]], request_id: str) -> dict[str, Any]:
    with database._connect() as connection:  # noqa: SLF001
        cached = _request_response(connection, request_id, "treatment_execute")
        if cached is not None:
            return cached
        row = connection.execute(
            """
            SELECT id,name,species_id,list_as,description,default_unit,default_route,components_json
            FROM v0911_treatment_plans WHERE id=? AND COALESCE(is_archived,0)=0
            """,
            (plan_id,),
        ).fetchone()
        if row is None:
            raise KeyError(plan_id)
        template = treatment_features._decode_components(row["components_json"])
        selected_set = {int(value) for value in selected_optional}
        executed: list[tuple[int | None, dict[str, Any], bool]] = []
        for index, component in enumerate(template):
            if bool(component.get("optional")) and index not in selected_set:
                continue
            executed.append((index, component, False))
        for raw in extras:
            component = treatment_features._validate_component(raw)
            component["optional"] = False
            executed.append((None, component, True))
        tx_id = _record_id("TX")
        plan_name = str(row["name"])
        parent_data = {
            "source": "treatment_plan",
            "treatment_plan_id": plan_id,
            "treatment_plan_name": plan_name,
            "treatment_execution_id": tx_id,
            "treatment_execution_role": "parent",
            "template_components": template,
            "components": [component for _, component, _ in executed],
            "selected_optional_indexes": sorted(selected_set),
            **_precision_data(precision, day),
        }
        parent = database._create_event_in_connection(  # noqa: SLF001
            connection,
            animal_id=animal_id,
            event_type="treatment",
            occurred_at=occurred_at,
            title=plan_name,
            notes=notes or str(row["description"] or "") or None,
            data=parent_data,
        )
        events = [parent.as_dict()]
        for index, component, extra in executed:
            events.append(
                _component_event(
                    database,
                    connection,
                    parent_id=parent.id,
                    tx_id=tx_id,
                    plan_id=plan_id,
                    plan_name=plan_name,
                    animal_id=animal_id,
                    occurred_at=occurred_at,
                    component=component,
                    index=index,
                    extra=extra,
                    precision=precision,
                    day=day,
                ).as_dict()
            )
        response = {"execution_id": tx_id, "events": events}
        _save_request(connection, request_id, "treatment_execute", response)
        return response


def _edit_treatment_sync(database, parent_event_id: str, occurred_at: datetime, day: str, precision: str, notes: str | None) -> dict[str, Any]:
    with database._connect() as connection:  # noqa: SLF001
        parent_row = connection.execute("SELECT rowid,* FROM events WHERE id=?", (parent_event_id,)).fetchone()
        if parent_row is None:
            raise KeyError(parent_event_id)
        parent_data = _parse_event_data(parent_row)
        tx_id = str(parent_data.get("treatment_execution_id") or "")
        if not tx_id:
            raise ValueError("Treatment execution grouping is missing")
        current = _current_execution_rows(connection, tx_id)
        current_parent = next((row for row in current if str(row["event_type"]) == "treatment"), None)
        if current_parent is None:
            raise ValueError("Treatment parent is missing")
        data = _parse_event_data(current_parent)
        data.update(_precision_data(precision, day))
        corrected_parent = _create_correction(
            database,
            connection,
            current_parent,
            occurred_at=occurred_at,
            data=data,
            notes=notes,
        )
        events = [corrected_parent.as_dict()]
        for child in current:
            if str(child["id"]) == str(current_parent["id"]):
                continue
            child_data = _parse_event_data(child)
            child_data["treatment_parent_event_id"] = corrected_parent.id
            child_data.update(_precision_data(precision, day))
            corrected = _create_correction(
                database,
                connection,
                child,
                occurred_at=occurred_at,
                data=child_data,
            )
            events.append(corrected.as_dict())
        return {"execution_id": tx_id, "events": events}


def _delete_treatment_sync(path: Path, parent_event_id: str) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        row = connection.execute("SELECT data_json FROM events WHERE id=?", (parent_event_id,)).fetchone()
        if row is None:
            raise KeyError(parent_event_id)
        tx_id = str(_parse_event_data(row).get("treatment_execution_id") or "")
        if not tx_id:
            raise ValueError("Treatment execution grouping is missing")
        ids = [str(item["id"]) for item in _event_rows_for_execution(connection, tx_id)]
        connection.executemany(
            "UPDATE events SET is_deleted=1,deleted_at=? WHERE id=?",
            [(now, item_id) for item_id in ids],
        )
    return {"execution_id": tx_id, "deleted_event_ids": ids, "deleted_at": now}


def _add_treatment_components_sync(database, parent_event_id: str, components: list[dict[str, Any]]) -> dict[str, Any]:
    with database._connect() as connection:  # noqa: SLF001
        row = connection.execute("SELECT rowid,* FROM events WHERE id=?", (parent_event_id,)).fetchone()
        if row is None:
            raise KeyError(parent_event_id)
        data = _parse_event_data(row)
        tx_id = str(data.get("treatment_execution_id") or "")
        if not tx_id:
            raise ValueError("Treatment execution grouping is missing")
        current = _current_execution_rows(connection, tx_id)
        parent = next((item for item in current if str(item["event_type"]) == "treatment"), row)
        parent_data = _parse_event_data(parent)
        plan_id = int(parent_data.get("treatment_plan_id") or 0)
        plan_name = str(parent_data.get("treatment_plan_name") or parent["title"])
        precision = str(parent_data.get("time_precision") or "datetime")
        day = str(parent_data.get("occurred_date") or str(parent["occurred_at"])[:10])
        events = []
        for raw in components:
            component = treatment_features._validate_component(raw)
            component["optional"] = False
            events.append(
                _component_event(
                    database,
                    connection,
                    parent_id=str(parent["id"]),
                    tx_id=tx_id,
                    plan_id=plan_id,
                    plan_name=plan_name,
                    animal_id=str(parent["animal_id"]),
                    occurred_at=datetime.fromisoformat(str(parent["occurred_at"])),
                    component=component,
                    index=None,
                    extra=True,
                    precision=precision,
                    day=day,
                ).as_dict()
            )
        return {"execution_id": tx_id, "events": events}


def _assessment_edit_sync(database, assessment_id: str, symptom: str, severity: str, occurred_at: datetime, day: str, precision: str, notes: str | None) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with database._connect() as connection:  # noqa: SLF001
        assessment = connection.execute(
            """
            SELECT s.*,e.animal_id,e.title,e.data_json,e.notes AS event_notes,e.value,e.unit,
                   e.task_id,e.task_occurrence_id,ep.symptom AS episode_symptom,ep.state
            FROM v0923_symptom_assessments AS s
            JOIN events AS e ON e.id=s.event_id
            JOIN v0923_symptom_episodes AS ep ON ep.id=s.episode_id
            WHERE s.id=?
            """,
            (assessment_id,),
        ).fetchone()
        if assessment is None:
            raise KeyError(assessment_id)
        episode_id = str(assessment["episode_id"])
        ordered = connection.execute(
            "SELECT id,action,assessed_at FROM v0923_symptom_assessments WHERE episode_id=? ORDER BY assessed_at,created_at,id",
            (episode_id,),
        ).fetchall()
        position = next(index for index, item in enumerate(ordered) if str(item["id"]) == assessment_id)
        if position > 0 and occurred_at < datetime.fromisoformat(str(ordered[position - 1]["assessed_at"])):
            raise ValueError("Assessment cannot be before the previous assessment")
        if position + 1 < len(ordered) and occurred_at > datetime.fromisoformat(str(ordered[position + 1]["assessed_at"])):
            raise ValueError("Assessment cannot be after the next assessment")
        old_event = connection.execute("SELECT rowid,* FROM events WHERE id=?", (assessment["event_id"],)).fetchone()
        if old_event is None:
            raise KeyError(str(assessment["event_id"]))
        data = _parse_event_data(old_event)
        data["symptom"] = symptom
        data["symptoms"] = [symptom]
        data["severity"] = severity
        data.update(_precision_data(precision, day))
        new_event = _create_correction(
            database,
            connection,
            old_event,
            occurred_at=occurred_at,
            data=data,
            title=symptom,
            notes=notes,
        )
        connection.execute(
            """
            UPDATE v0923_symptom_assessments
            SET event_id=?,assessed_at=?,assessed_date=?,time_precision=?,severity=?,notes=?,created_at=?
            WHERE id=?
            """,
            (new_event.id, occurred_at.isoformat(), day, precision, severity, notes, now, assessment_id),
        )
        connection.execute(
            "UPDATE v0923_symptom_episodes SET symptom=?,normalized_symptom=?,updated_at=? WHERE id=?",
            (symptom, _normalise(symptom), now, episode_id),
        )
        current = connection.execute(
            "SELECT action,event_id,assessed_at,assessed_date,severity FROM v0923_symptom_assessments WHERE episode_id=? ORDER BY assessed_at,created_at,id",
            (episode_id,),
        ).fetchall()
        first = current[0]
        last = current[-1]
        ended = next((item for item in reversed(current) if str(item["action"]) == "resolved"), None)
        connection.execute(
            """
            UPDATE v0923_symptom_episodes
            SET started_at=?,started_date=?,start_event_id=?,latest_severity=?,
                ended_at=?,ended_date=?,state=?,updated_at=? WHERE id=?
            """,
            (
                first["assessed_at"], first["assessed_date"], first["event_id"], last["severity"],
                ended["assessed_at"] if ended else None, ended["assessed_date"] if ended else None,
                "resolved" if ended else "active", now, episode_id,
            ),
        )
    return new_event.as_dict()


def _attachment_token(hass: HomeAssistant, attachment_id: str) -> str:
    token = secrets.token_urlsafe(24)
    records = hass.data.setdefault(_TOKEN_KEY, {})
    now = datetime.now(UTC)
    for old, item in list(records.items()):
        if item["expires"] < now:
            records.pop(old, None)
    records[token] = {"attachment_id": attachment_id, "expires": now + timedelta(minutes=20)}
    return token


def _verify_attachment_token(request: web.Request, attachment_id: str) -> None:
    hass: HomeAssistant = request.app[KEY_HASS]
    token = request.query.get("token", "")
    record = hass.data.setdefault(_TOKEN_KEY, {}).get(token)
    if not record or record["expires"] < datetime.now(UTC) or record["attachment_id"] != attachment_id:
        raise web.HTTPUnauthorized()


def _image_variant(path: Path, attachment_id: str, variant: str) -> tuple[bytes, str]:
    if variant == "original":
        return path.read_bytes(), "application/octet-stream"
    from PIL import Image, ImageOps
    max_size = (360, 360) if variant == "thumbnail" else (1600, 1600)
    quality = 72 if variant == "thumbnail" else 84
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        if image.mode not in {"RGB", "L"}:
            background = Image.new("RGB", image.size, "white")
            if "A" in image.getbands():
                background.paste(image, mask=image.getchannel("A"))
            else:
                background.paste(image.convert("RGB"))
            image = background
        elif image.mode == "L":
            image = image.convert("RGB")
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=quality, optimize=True)
        return output.getvalue(), "image/jpeg"


class AnimalHealthV0924AttachmentView(HomeAssistantView):
    url = f"/api/{DOMAIN}/v0924/attachments/{{attachment_id}}/{{variant}}"
    name = f"api:{DOMAIN}:v0924_attachment"
    requires_auth = False

    async def get(self, request: web.Request, attachment_id: str, variant: str) -> web.Response:
        if variant not in {"thumbnail", "preview", "original"}:
            raise web.HTTPNotFound()
        _verify_attachment_token(request, attachment_id)
        hass: HomeAssistant = request.app[KEY_HASS]
        try:
            item, path = await _runtime_data(hass).feature_store.attachment_file(attachment_id)
        except (KeyError, FileNotFoundError):
            raise web.HTTPNotFound() from None
        media_type = str(item.get("media_type") or "application/octet-stream")
        if variant != "original" and not media_type.startswith("image/"):
            raise web.HTTPUnsupportedMediaType()
        if variant == "original":
            body = await hass.async_add_executor_job(path.read_bytes)
            content_type = media_type
        else:
            body, content_type = await hass.async_add_executor_job(_image_variant, path, attachment_id, variant)
        return web.Response(body=body, content_type=content_type, headers={"Cache-Control": "private, max-age=900"})


async def async_initialize_v0924_features(hass: HomeAssistant) -> None:
    await hass.async_add_executor_job(_initialise_sync, _database_path(hass))


def async_setup_v0924_features(hass: HomeAssistant) -> None:
    state = hass.data.setdefault(_VIEW_STATE_KEY, {})
    if not state.get("registered"):
        hass.http.register_view(AnimalHealthV0924AttachmentView())
        state["registered"] = True

    @websocket_api.websocket_command({vol.Required("type"): _STATE_COMMAND})
    @websocket_api.async_response
    async def websocket_state(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(_state_sync, _database_path(hass))
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0924_state_failed", str(err)); return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({vol.Required("type"): _MASTER_SAVE_COMMAND, vol.Required("kind"): vol.In(("entry_type", "symptom")), vol.Optional("item_id"): _optional_text, vol.Required("label"): _required_text})
    @websocket_api.async_response
    async def websocket_master_save(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(_save_master_sync, _database_path(hass), msg["kind"], msg.get("item_id"), msg["label"])
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0924_master_save_failed", str(err)); return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({vol.Required("type"): _MASTER_ARCHIVE_COMMAND, vol.Required("kind"): vol.In(("entry_type", "symptom")), vol.Required("item_id"): _required_text, vol.Required("hidden"): bool})
    @websocket_api.async_response
    async def websocket_master_archive(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(_archive_master_sync, _database_path(hass), msg["kind"], msg["item_id"], bool(msg["hidden"]))
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0924_master_archive_failed", str(err)); return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({vol.Required("type"): _MASTER_RESET_COMMAND, vol.Required("kind"): vol.In(("entry_type", "symptom")), vol.Required("item_id"): _required_text})
    @websocket_api.async_response
    async def websocket_master_reset(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(_reset_master_sync, _database_path(hass), msg["kind"], msg["item_id"])
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0924_master_reset_failed", str(err)); return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({vol.Required("type"): _CATALOG_OVERRIDE_COMMAND, vol.Required("source_id"): _required_text, vol.Required("item_id"): _required_text, vol.Optional("hidden", default=False): bool, vol.Optional("fields", default={}): dict})
    @websocket_api.async_response
    async def websocket_catalog_override(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(_save_catalog_override_sync, _database_path(hass), msg["source_id"], msg["item_id"], bool(msg.get("hidden")), msg.get("fields") or {})
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0924_catalog_override_failed", str(err)); return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({vol.Required("type"): _CATALOG_RESET_COMMAND, vol.Required("source_id"): _required_text, vol.Required("item_id"): _required_text})
    @websocket_api.async_response
    async def websocket_catalog_reset(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(_reset_catalog_override_sync, _database_path(hass), msg["source_id"], msg["item_id"])
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0924_catalog_reset_failed", str(err)); return
        connection.send_result(msg["id"], result)

    temporal = {vol.Optional("occurred_date"): _optional_text, vol.Optional("occurred_time"): _optional_text}

    @websocket_api.websocket_command({vol.Required("type"): _EVENT_EDIT_COMMAND, vol.Required("event_id"): _required_text, vol.Optional("title"): _optional_text, vol.Optional("notes"): _optional_text, vol.Optional("entry_type_id"): _optional_text, vol.Optional("value"): vol.Any(None, vol.Coerce(float)), vol.Optional("unit"): _optional_text, **temporal})
    @websocket_api.async_response
    async def websocket_event_edit(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            when, precision, day = _event_when(hass, msg.get("occurred_date"), msg.get("occurred_time"))
            result = await hass.async_add_executor_job(_edit_event_sync, runtime.database, _database_path(hass), msg["event_id"], when, day, precision, msg.get("title"), msg.get("notes"), msg.get("entry_type_id"), msg.get("value"), msg.get("unit"))
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0924_event_edit_failed", str(err)); return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({vol.Required("type"): _EVENT_DELETE_COMMAND, vol.Required("event_id"): _required_text})
    @websocket_api.async_response
    async def websocket_event_delete(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            result = await hass.async_add_executor_job(_delete_event_sync, _database_path(hass), msg["event_id"])
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0924_event_delete_failed", str(err)); return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({vol.Required("type"): _SYMPTOM_EDIT_COMMAND, vol.Required("assessment_id"): _required_text, vol.Required("symptom"): _required_text, vol.Required("severity"): _required_text, vol.Optional("notes"): _optional_text, **temporal})
    @websocket_api.async_response
    async def websocket_symptom_edit(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            when, precision, day = _event_when(hass, msg.get("occurred_date"), msg.get("occurred_time"))
            result = await hass.async_add_executor_job(_assessment_edit_sync, runtime.database, msg["assessment_id"], msg["symptom"], msg["severity"], when, day, precision, msg.get("notes"))
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0924_symptom_edit_failed", str(err)); return
        connection.send_result(msg["id"], result)

    component_schema = dict
    @websocket_api.websocket_command({vol.Required("type"): _TREATMENT_EXECUTE_COMMAND, vol.Required("plan_id"): vol.Coerce(int), vol.Required("animal_id"): _required_text, vol.Optional("notes"): _optional_text, vol.Optional("selected_optional", default=[]): [vol.Coerce(int)], vol.Optional("extras", default=[]): [component_schema], vol.Required("request_id"): _required_text, **temporal})
    @websocket_api.async_response
    async def websocket_treatment_execute(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            when, precision, day = _event_when(hass, msg.get("occurred_date"), msg.get("occurred_time"))
            result = await hass.async_add_executor_job(_execute_treatment_sync, runtime.database, int(msg["plan_id"]), msg["animal_id"], when, day, precision, msg.get("notes"), list(msg.get("selected_optional") or []), list(msg.get("extras") or []), msg["request_id"])
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0924_treatment_execute_failed", str(err)); return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({vol.Required("type"): _TREATMENT_EDIT_COMMAND, vol.Required("event_id"): _required_text, vol.Optional("notes"): _optional_text, **temporal})
    @websocket_api.async_response
    async def websocket_treatment_edit(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            when, precision, day = _event_when(hass, msg.get("occurred_date"), msg.get("occurred_time"))
            result = await hass.async_add_executor_job(_edit_treatment_sync, runtime.database, msg["event_id"], when, day, precision, msg.get("notes"))
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0924_treatment_edit_failed", str(err)); return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({vol.Required("type"): _TREATMENT_DELETE_COMMAND, vol.Required("event_id"): _required_text})
    @websocket_api.async_response
    async def websocket_treatment_delete(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            result = await hass.async_add_executor_job(_delete_treatment_sync, _database_path(hass), msg["event_id"])
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0924_treatment_delete_failed", str(err)); return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({vol.Required("type"): _TREATMENT_ADD_COMMAND, vol.Required("event_id"): _required_text, vol.Required("components"): [component_schema]})
    @websocket_api.async_response
    async def websocket_treatment_add(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            result = await hass.async_add_executor_job(_add_treatment_components_sync, runtime.database, msg["event_id"], list(msg["components"]))
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0924_treatment_add_failed", str(err)); return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({vol.Required("type"): _ATTACHMENT_URLS_COMMAND, vol.Required("attachment_ids"): vol.All([_required_text], vol.Length(max=100))})
    @websocket_api.async_response
    async def websocket_attachment_urls(hass, connection, msg) -> None:
        result: dict[str, Any] = {}
        for attachment_id in msg["attachment_ids"]:
            token = _attachment_token(hass, attachment_id)
            base = f"/api/{DOMAIN}/v0924/attachments/{attachment_id}"
            result[attachment_id] = {
                "thumbnail": f"{base}/thumbnail?token={token}",
                "preview": f"{base}/preview?token={token}",
                "original": f"{base}/original?token={token}",
            }
        connection.send_result(msg["id"], {"urls": result})

    for command in (
        websocket_state, websocket_master_save, websocket_master_archive, websocket_master_reset,
        websocket_catalog_override, websocket_catalog_reset, websocket_event_edit, websocket_event_delete,
        websocket_symptom_edit, websocket_treatment_execute, websocket_treatment_edit,
        websocket_treatment_delete, websocket_treatment_add, websocket_attachment_urls,
    ):
        websocket_api.async_register_command(hass, command)
