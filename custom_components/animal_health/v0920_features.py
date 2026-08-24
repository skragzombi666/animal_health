from __future__ import annotations

import asyncio
import json
import re
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DATABASE_NAME, DOMAIN
from .swissmedic_catalog import (
    SWISSMEDIC_DATASET_ID,
    SWISSMEDIC_LANDING_URL,
    SWISSMEDIC_OGD_URL,
    SWISSMEDIC_SOURCE_ID,
    parse_swissmedic_ogd_zip,
)

_STATE_COMMAND = f"{DOMAIN}/v0920/state"
_REFRESH_COMMAND = f"{DOMAIN}/v0920/catalog/refresh"
_FAVORITE_TOGGLE_COMMAND = f"{DOMAIN}/v0920/favorite/toggle"
_FAVORITE_ORDER_COMMAND = f"{DOMAIN}/v0920/favorite/order"
_SOURCE_NAME = "Swissmedic OGD – zugelassene Tierarzneimittel"


def _database_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(DATABASE_NAME))


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _normalise(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def _initialise_sync(path: Path) -> None:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS v0920_catalog_sources (
                source_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                scope TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
                dataset_id TEXT,
                source_url TEXT,
                landing_url TEXT,
                snapshot_date TEXT,
                item_count INTEGER NOT NULL DEFAULT 0,
                is_complete INTEGER NOT NULL DEFAULT 0 CHECK(is_complete IN (0,1)),
                last_attempt_at TEXT,
                last_success_at TEXT,
                last_error TEXT,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS v0920_catalog_products (
                source_id TEXT NOT NULL REFERENCES v0920_catalog_sources(source_id) ON DELETE CASCADE,
                item_id TEXT NOT NULL,
                authorisation_number TEXT,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                active_ingredient TEXT,
                active_ingredients_json TEXT NOT NULL DEFAULT '[]',
                concentration TEXT,
                dosage_form TEXT,
                target_species_json TEXT NOT NULL DEFAULT '[]',
                aliases_json TEXT NOT NULL DEFAULT '[]',
                authorisation_status TEXT,
                application_area TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(source_id,item_id)
            );
            CREATE INDEX IF NOT EXISTS idx_v0920_catalog_name
                ON v0920_catalog_products(normalized_name,source_id);
            CREATE TABLE IF NOT EXISTS v0920_favorites (
                favorite_key TEXT PRIMARY KEY,
                position INTEGER NOT NULL CHECK(position >= 0),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_v0920_favorites_position
                ON v0920_favorites(position,favorite_key);
            """
        )
        connection.execute(
            """
            INSERT INTO v0920_catalog_sources(
                source_id,name,scope,enabled,dataset_id,source_url,landing_url,
                snapshot_date,item_count,is_complete,last_attempt_at,last_success_at,last_error,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(source_id) DO UPDATE SET
                name=excluded.name,scope=excluded.scope,dataset_id=excluded.dataset_id,
                source_url=excluded.source_url,landing_url=excluded.landing_url,
                updated_at=excluded.updated_at
            """,
            (
                SWISSMEDIC_SOURCE_ID,
                _SOURCE_NAME,
                "CH",
                1,
                SWISSMEDIC_DATASET_ID,
                SWISSMEDIC_OGD_URL,
                SWISSMEDIC_LANDING_URL,
                None,
                0,
                0,
                None,
                None,
                None,
                now,
            ),
        )
        count = connection.execute(
            "SELECT COUNT(*) FROM v0920_catalog_products WHERE source_id=?",
            (SWISSMEDIC_SOURCE_ID,),
        ).fetchone()[0]
        if not count:
            _seed_fallback_sync(connection, now)


def _seed_fallback_sync(connection: sqlite3.Connection, now: str) -> None:
    path = Path(__file__).parent / "catalogs" / "medicines_ch.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        document = {"items": []}
    items = [dict(item) for item in document.get("items", [])]
    if not any("eradia" in str(item.get("name", "")).casefold() for item in items):
        items.append(
            {
                "id": "swissmedic.66759",
                "authorisation_number": "66759",
                "name": "Eradia 125 mg/ml ad us. vet., orale Suspension für Hunde",
                "active_ingredients": ["Metronidazol"],
                "concentration": "125 mg/ml",
                "dosage_form": "Orale Suspension",
                "target_species": ["dog"],
                "aliases": ["Eradia", "Eradia 125 mg/ml"],
            }
        )
    rows = []
    for item in items:
        name = str(item.get("name") or item.get("name_de") or item.get("id") or "").strip()
        if not name:
            continue
        ingredients = [str(value) for value in item.get("active_ingredients", [])]
        rows.append(
            (
                SWISSMEDIC_SOURCE_ID,
                str(item.get("id") or f"fallback.{_normalise(name)}"),
                str(item.get("authorisation_number") or ""),
                name,
                _normalise(name),
                ", ".join(ingredients),
                json.dumps(ingredients, ensure_ascii=False),
                str(item.get("concentration") or ""),
                str(item.get("dosage_form") or ""),
                json.dumps(item.get("target_species") or [], ensure_ascii=False),
                json.dumps(item.get("aliases") or [], ensure_ascii=False),
                "fallback",
                "",
                now,
            )
        )
    connection.executemany(
        """
        INSERT OR REPLACE INTO v0920_catalog_products(
            source_id,item_id,authorisation_number,name,normalized_name,
            active_ingredient,active_ingredients_json,concentration,dosage_form,
            target_species_json,aliases_json,authorisation_status,application_area,updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )
    connection.execute(
        """
        UPDATE v0920_catalog_sources
        SET snapshot_date=?,item_count=?,is_complete=0,last_error=?,updated_at=?
        WHERE source_id=?
        """,
        (
            str(document.get("source", {}).get("as_of") or ""),
            len(rows),
            "Offizieller Swissmedic-Abgleich steht noch aus; lokaler Fallback aktiv.",
            now,
            SWISSMEDIC_SOURCE_ID,
        ),
    )


def _source_sync(path: Path) -> dict[str, Any]:
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT * FROM v0920_catalog_sources WHERE source_id=?",
            (SWISSMEDIC_SOURCE_ID,),
        ).fetchone()
    if row is None:
        return {}
    return {
        "source_id": str(row["source_id"]),
        "name": str(row["name"]),
        "scope": str(row["scope"]),
        "enabled": bool(row["enabled"]),
        "dataset_id": str(row["dataset_id"] or ""),
        "source_url": str(row["source_url"] or ""),
        "landing_url": str(row["landing_url"] or ""),
        "snapshot_date": str(row["snapshot_date"] or ""),
        "item_count": int(row["item_count"] or 0),
        "is_complete": bool(row["is_complete"]),
        "last_attempt_at": str(row["last_attempt_at"] or ""),
        "last_success_at": str(row["last_success_at"] or ""),
        "last_error": str(row["last_error"] or ""),
    }


def _catalog_products_sync(path: Path) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT source_id,item_id,authorisation_number,name,active_ingredient,
                   active_ingredients_json,concentration,dosage_form,target_species_json,
                   aliases_json,authorisation_status,application_area
            FROM v0920_catalog_products
            WHERE source_id=?
            ORDER BY name COLLATE NOCASE,item_id
            """,
            (SWISSMEDIC_SOURCE_ID,),
        ).fetchall()
    result = []
    for row in rows:
        result.append(
            {
                "id": str(row["item_id"]),
                "source_id": str(row["source_id"]),
                "authorisation_number": str(row["authorisation_number"] or ""),
                "name": str(row["name"]),
                "active_ingredient": str(row["active_ingredient"] or ""),
                "active_ingredients": json.loads(str(row["active_ingredients_json"] or "[]")),
                "concentration": str(row["concentration"] or ""),
                "dosage_form": str(row["dosage_form"] or ""),
                "target_species": json.loads(str(row["target_species_json"] or "[]")),
                "aliases": json.loads(str(row["aliases_json"] or "[]")),
                "authorisation_status": str(row["authorisation_status"] or ""),
                "application_area": str(row["application_area"] or ""),
                "source": "catalog",
            }
        )
    return result


def _favorites_sync(path: Path) -> list[str]:
    with _connect(path) as connection:
        rows = connection.execute(
            "SELECT favorite_key FROM v0920_favorites ORDER BY position,favorite_key"
        ).fetchall()
    return [str(row["favorite_key"]) for row in rows]


def _state_sync(path: Path) -> dict[str, Any]:
    return {
        "sources": [_source_sync(path)],
        "catalog_products": _catalog_products_sync(path),
        "favorites": _favorites_sync(path),
    }


def _replace_catalog_sync(
    path: Path,
    snapshot_date: str,
    products: list[dict[str, Any]],
) -> None:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        connection.execute(
            "DELETE FROM v0920_catalog_products WHERE source_id=?",
            (SWISSMEDIC_SOURCE_ID,),
        )
        rows = []
        for item in products:
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            rows.append(
                (
                    SWISSMEDIC_SOURCE_ID,
                    str(item.get("id") or item.get("authorisation_number") or _normalise(name)),
                    str(item.get("authorisation_number") or ""),
                    name,
                    _normalise(name),
                    str(item.get("active_ingredient") or ""),
                    json.dumps(item.get("active_ingredients") or [], ensure_ascii=False),
                    str(item.get("concentration") or ""),
                    str(item.get("dosage_form") or ""),
                    json.dumps(item.get("target_species") or [], ensure_ascii=False),
                    json.dumps(item.get("aliases") or [], ensure_ascii=False),
                    str(item.get("authorisation_status") or ""),
                    str(item.get("application_area") or ""),
                    now,
                )
            )
        connection.executemany(
            """
            INSERT INTO v0920_catalog_products(
                source_id,item_id,authorisation_number,name,normalized_name,
                active_ingredient,active_ingredients_json,concentration,dosage_form,
                target_species_json,aliases_json,authorisation_status,application_area,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            rows,
        )
        connection.execute(
            """
            UPDATE v0920_catalog_sources
            SET snapshot_date=?,item_count=?,is_complete=1,last_success_at=?,last_error=NULL,updated_at=?
            WHERE source_id=?
            """,
            (snapshot_date, len(rows), now, now, SWISSMEDIC_SOURCE_ID),
        )


def _record_attempt_sync(path: Path, error: str | None = None) -> None:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        connection.execute(
            "UPDATE v0920_catalog_sources SET last_attempt_at=?,last_error=?,updated_at=? WHERE source_id=?",
            (now, error, now, SWISSMEDIC_SOURCE_ID),
        )


def _needs_refresh_sync(path: Path) -> bool:
    source = _source_sync(path)
    if not source.get("is_complete"):
        return True
    raw = str(source.get("last_attempt_at") or source.get("last_success_at") or "")
    if not raw:
        return True
    try:
        last = datetime.fromisoformat(raw)
    except ValueError:
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=UTC)
    return datetime.now(UTC) - last >= timedelta(hours=24)


def _toggle_favorite_sync(path: Path, favorite_key: str, favorite: bool) -> list[str]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    key = favorite_key.strip()
    if not key:
        raise ValueError("favorite_key is required")
    with _connect(path) as connection:
        if favorite:
            position = int(
                connection.execute(
                    "SELECT COALESCE(MAX(position),-1)+1 FROM v0920_favorites"
                ).fetchone()[0]
            )
            connection.execute(
                """
                INSERT INTO v0920_favorites(favorite_key,position,created_at,updated_at)
                VALUES(?,?,?,?)
                ON CONFLICT(favorite_key) DO UPDATE SET updated_at=excluded.updated_at
                """,
                (key, position, now, now),
            )
        else:
            connection.execute("DELETE FROM v0920_favorites WHERE favorite_key=?", (key,))
            rows = connection.execute(
                "SELECT favorite_key FROM v0920_favorites ORDER BY position,favorite_key"
            ).fetchall()
            connection.executemany(
                "UPDATE v0920_favorites SET position=?,updated_at=? WHERE favorite_key=?",
                [(index, now, str(row["favorite_key"])) for index, row in enumerate(rows)],
            )
    return _favorites_sync(path)


def _save_favorite_order_sync(path: Path, favorite_keys: list[str]) -> list[str]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    requested = []
    for value in favorite_keys:
        key = str(value or "").strip()
        if key and key not in requested:
            requested.append(key)
    with _connect(path) as connection:
        existing = [
            str(row["favorite_key"])
            for row in connection.execute(
                "SELECT favorite_key FROM v0920_favorites ORDER BY position,favorite_key"
            ).fetchall()
        ]
        order = [key for key in requested if key in existing]
        order.extend(key for key in existing if key not in order)
        connection.executemany(
            "UPDATE v0920_favorites SET position=?,updated_at=? WHERE favorite_key=?",
            [(index, now, key) for index, key in enumerate(order)],
        )
    return order


async def async_initialize_v0920_features(hass: HomeAssistant) -> None:
    await hass.async_add_executor_job(_initialise_sync, _database_path(hass))


async def async_refresh_v0920_catalog(hass: HomeAssistant, *, force: bool = False) -> dict[str, Any]:
    path = _database_path(hass)
    if not force and not await hass.async_add_executor_job(_needs_refresh_sync, path):
        return _source_sync(path)
    await hass.async_add_executor_job(_record_attempt_sync, path, None)
    try:
        session = async_get_clientsession(hass)
        async with asyncio.timeout(25):
            response = await session.get(SWISSMEDIC_OGD_URL)
            response.raise_for_status()
            payload = await response.read()
        snapshot_date, products = await hass.async_add_executor_job(parse_swissmedic_ogd_zip, payload)
        if len(products) < 100:
            raise ValueError(f"Swissmedic catalogue unexpectedly contains only {len(products)} veterinary products")
        await hass.async_add_executor_job(_replace_catalog_sync, path, snapshot_date, products)
    except Exception as err:  # noqa: BLE001
        await hass.async_add_executor_job(_record_attempt_sync, path, str(err))
    return _source_sync(path)


def async_setup_v0920_features(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command({vol.Required("type"): _STATE_COMMAND})
    @websocket_api.async_response
    async def websocket_state(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(_state_sync, _database_path(hass))
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0920_state_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command({vol.Required("type"): _REFRESH_COMMAND})
    @websocket_api.async_response
    async def websocket_refresh(hass, connection, msg) -> None:
        source = await async_refresh_v0920_catalog(hass, force=True)
        connection.send_result(msg["id"], {"source": source})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _FAVORITE_TOGGLE_COMMAND,
            vol.Required("favorite_key"): str,
            vol.Required("favorite"): bool,
        }
    )
    @websocket_api.async_response
    async def websocket_favorite_toggle(hass, connection, msg) -> None:
        try:
            favorites = await hass.async_add_executor_job(
                _toggle_favorite_sync,
                _database_path(hass),
                msg["favorite_key"],
                bool(msg["favorite"]),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0920_favorite_failed", str(err))
            return
        connection.send_result(msg["id"], {"favorites": favorites})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _FAVORITE_ORDER_COMMAND,
            vol.Required("favorite_keys"): [str],
        }
    )
    @websocket_api.async_response
    async def websocket_favorite_order(hass, connection, msg) -> None:
        try:
            favorites = await hass.async_add_executor_job(
                _save_favorite_order_sync,
                _database_path(hass),
                msg["favorite_keys"],
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0920_favorite_order_failed", str(err))
            return
        connection.send_result(msg["id"], {"favorites": favorites})

    websocket_api.async_register_command(hass, websocket_state)
    websocket_api.async_register_command(hass, websocket_refresh)
    websocket_api.async_register_command(hass, websocket_favorite_toggle)
    websocket_api.async_register_command(hass, websocket_favorite_order)
