from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .const import DATABASE_NAME, DOMAIN
from .runtime import AnimalHealthRuntimeData

_STATE_COMMAND = f"{DOMAIN}/v0917/state"
_SAVE_GROUP_ORDER_COMMAND = f"{DOMAIN}/v0917/group_order/save"
_SAVE_ANIMAL_ORDER_COMMAND = f"{DOMAIN}/v0917/animal_order/save"
_SAVE_PRODUCT_CATEGORY_COMMAND = f"{DOMAIN}/v0917/product/category"
PRODUCT_CATEGORIES = ("medication", "supplement", "care", "other")


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _database_path(hass: HomeAssistant) -> Path:
    try:
        return _runtime_data(hass).feature_store.database_path
    except RuntimeError:
        return Path(hass.config.path(DATABASE_NAME))


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _initialise_sync(path: Path) -> None:
    with _connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS v0917_group_order (
                group_id TEXT PRIMARY KEY REFERENCES animal_groups(id) ON DELETE CASCADE,
                position INTEGER NOT NULL CHECK(position >= 0),
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_v0917_group_order_position
                ON v0917_group_order(position, group_id);

            CREATE TABLE IF NOT EXISTS v0917_animal_order (
                animal_id TEXT PRIMARY KEY REFERENCES animals(id) ON DELETE CASCADE,
                group_id TEXT NOT NULL REFERENCES animal_groups(id) ON DELETE CASCADE,
                position INTEGER NOT NULL CHECK(position >= 0),
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_v0917_animal_order_group_position
                ON v0917_animal_order(group_id, position, animal_id);

            CREATE TABLE IF NOT EXISTS v0917_product_categories (
                medication_id INTEGER PRIMARY KEY
                    REFERENCES v0817_medications(id) ON DELETE CASCADE,
                category TEXT NOT NULL DEFAULT 'medication'
                    CHECK(category IN ('medication','supplement','care','other')),
                updated_at TEXT NOT NULL
            );
            """
        )


def _ordered_group_ids(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute(
        """
        SELECT g.id
        FROM animal_groups AS g
        LEFT JOIN v0917_group_order AS o ON o.group_id=g.id
        ORDER BY CASE WHEN o.position IS NULL THEN 1 ELSE 0 END,
                 o.position,
                 g.name COLLATE NOCASE,
                 g.id
        """
    ).fetchall()
    return [str(row["id"]) for row in rows]


def _ordered_animal_ids(connection: sqlite3.Connection, group_id: str) -> list[str]:
    rows = connection.execute(
        """
        SELECT a.id
        FROM animal_group_memberships AS m
        JOIN animals AS a ON a.id=m.animal_id
        LEFT JOIN v0917_animal_order AS o
          ON o.animal_id=a.id AND o.group_id=m.group_id
        WHERE m.group_id=?
        ORDER BY CASE WHEN o.position IS NULL THEN 1 ELSE 0 END,
                 o.position,
                 a.name COLLATE NOCASE,
                 a.id
        """,
        (group_id,),
    ).fetchall()
    return [str(row["id"]) for row in rows]


def _product_categories(connection: sqlite3.Connection) -> dict[str, str]:
    rows = connection.execute(
        "SELECT medication_id,category FROM v0917_product_categories"
    ).fetchall()
    return {str(row["medication_id"]): str(row["category"]) for row in rows}


def _state_sync(path: Path) -> dict[str, Any]:
    with _connect(path) as connection:
        groups = _ordered_group_ids(connection)
        animals = {
            group_id: _ordered_animal_ids(connection, group_id)
            for group_id in groups
        }
        categories = _product_categories(connection)
    return {
        "group_order": groups,
        "animal_order": animals,
        "product_categories": categories,
    }


def _unique_ids(values: Any) -> list[str]:
    if not isinstance(values, list):
        raise vol.Invalid("value must be a list")
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return result


def _save_group_order_sync(path: Path, requested: list[str]) -> list[str]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        valid = {
            str(row["id"])
            for row in connection.execute("SELECT id FROM animal_groups").fetchall()
        }
        order = [group_id for group_id in requested if group_id in valid]
        for group_id in _ordered_group_ids(connection):
            if group_id not in order:
                order.append(group_id)
        connection.execute("DELETE FROM v0917_group_order")
        connection.executemany(
            "INSERT INTO v0917_group_order(group_id,position,updated_at) VALUES(?,?,?)",
            [(group_id, position, now) for position, group_id in enumerate(order)],
        )
    return order


def _save_animal_order_sync(
    path: Path,
    group_id: str,
    requested: list[str],
) -> list[str]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        if connection.execute(
            "SELECT 1 FROM animal_groups WHERE id=?", (group_id,)
        ).fetchone() is None:
            raise KeyError(group_id)
        valid = {
            str(row["animal_id"])
            for row in connection.execute(
                "SELECT animal_id FROM animal_group_memberships WHERE group_id=?",
                (group_id,),
            ).fetchall()
        }
        order = [animal_id for animal_id in requested if animal_id in valid]
        for animal_id in _ordered_animal_ids(connection, group_id):
            if animal_id not in order:
                order.append(animal_id)
        connection.execute("DELETE FROM v0917_animal_order WHERE group_id=?", (group_id,))
        connection.executemany(
            """
            INSERT INTO v0917_animal_order(animal_id,group_id,position,updated_at)
            VALUES(?,?,?,?)
            ON CONFLICT(animal_id) DO UPDATE SET
                group_id=excluded.group_id,
                position=excluded.position,
                updated_at=excluded.updated_at
            """,
            [
                (animal_id, group_id, position, now)
                for position, animal_id in enumerate(order)
            ],
        )
    return order


def _save_product_category_sync(
    path: Path,
    medication_id: int,
    category: str,
) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT id,name FROM v0817_medications WHERE id=?", (medication_id,)
        ).fetchone()
        if row is None:
            raise KeyError(medication_id)
        connection.execute(
            """
            INSERT INTO v0917_product_categories(medication_id,category,updated_at)
            VALUES(?,?,?)
            ON CONFLICT(medication_id) DO UPDATE SET
                category=excluded.category,
                updated_at=excluded.updated_at
            """,
            (medication_id, category, now),
        )
    return {"medication_id": medication_id, "category": category, "name": str(row["name"])}


async def async_initialize_v0917_features(hass: HomeAssistant) -> None:
    await hass.async_add_executor_job(_initialise_sync, _database_path(hass))


def async_setup_v0917_features(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command({vol.Required("type"): _STATE_COMMAND})
    @websocket_api.async_response
    async def websocket_state(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(_state_sync, _database_path(hass))
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0917_state_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SAVE_GROUP_ORDER_COMMAND,
            vol.Required("group_ids"): _unique_ids,
        }
    )
    @websocket_api.async_response
    async def websocket_group_order(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _save_group_order_sync,
                _database_path(hass),
                msg["group_ids"],
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0917_group_order_failed", str(err))
            return
        connection.send_result(msg["id"], {"group_order": result})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SAVE_ANIMAL_ORDER_COMMAND,
            vol.Required("group_id"): str,
            vol.Required("animal_ids"): _unique_ids,
        }
    )
    @websocket_api.async_response
    async def websocket_animal_order(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _save_animal_order_sync,
                _database_path(hass),
                str(msg["group_id"]),
                msg["animal_ids"],
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0917_animal_order_failed", str(err))
            return
        connection.send_result(msg["id"], {"animal_order": result})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SAVE_PRODUCT_CATEGORY_COMMAND,
            vol.Required("medication_id"): vol.Coerce(int),
            vol.Required("category"): vol.In(PRODUCT_CATEGORIES),
        }
    )
    @websocket_api.async_response
    async def websocket_product_category(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _save_product_category_sync,
                _database_path(hass),
                int(msg["medication_id"]),
                str(msg["category"]),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0917_product_category_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    websocket_api.async_register_command(hass, websocket_state)
    websocket_api.async_register_command(hass, websocket_group_order)
    websocket_api.async_register_command(hass, websocket_animal_order)
    websocket_api.async_register_command(hass, websocket_product_category)
