from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import v0912_features as treatment_features
from .const import DATABASE_NAME, DOMAIN
from .runtime import AnimalHealthRuntimeData

_STATE_COMMAND = f"{DOMAIN}/v0918/state"
_SAVE_COMMAND = f"{DOMAIN}/v0918/treatment/save"
_ARCHIVE_COMMAND = f"{DOMAIN}/v0918/treatment/archive"
_LIST_TARGETS = ("medication", "task", "both")


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


def _required_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if not text:
        raise vol.Invalid("value must not be empty")
    return text


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _initialise_sync(path: Path) -> None:
    with _connect(path) as connection:
        columns = {
            str(row[1])
            for row in connection.execute(
                "PRAGMA table_info(v0911_treatment_plans)"
            ).fetchall()
        }
        if not columns:
            return
        if "is_archived" not in columns:
            connection.execute(
                "ALTER TABLE v0911_treatment_plans ADD COLUMN is_archived "
                "INTEGER NOT NULL DEFAULT 0 CHECK (is_archived IN (0,1))"
            )
        if "archived_at" not in columns:
            connection.execute(
                "ALTER TABLE v0911_treatment_plans ADD COLUMN archived_at TEXT"
            )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_v0918_treatment_archived "
            "ON v0911_treatment_plans(is_archived,name,species_id,id)"
        )


def _plan_dict(row: sqlite3.Row) -> dict[str, Any]:
    try:
        components = treatment_features._decode_components(row["components_json"])
    except Exception:  # noqa: BLE001
        try:
            raw = json.loads(str(row["components_json"] or "[]"))
        except (TypeError, json.JSONDecodeError):
            raw = []
        components = raw if isinstance(raw, list) else []
    return {
        "id": int(row["id"]),
        "name": str(row["name"]),
        "species_id": str(row["species_id"] or ""),
        "list_as": str(row["list_as"] or "both"),
        "description": str(row["description"] or ""),
        "default_unit": str(row["default_unit"] or "dose"),
        "default_route": str(row["default_route"] or ""),
        "components": components,
        "is_archived": bool(row["is_archived"]),
        "archived_at": str(row["archived_at"] or ""),
    }


def _plans_sync(path: Path) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT id,name,species_id,list_as,description,default_unit,
                   default_route,components_json,is_archived,archived_at
            FROM v0911_treatment_plans
            ORDER BY is_archived,name COLLATE NOCASE,species_id,id
            """
        ).fetchall()
    return [_plan_dict(row) for row in rows]


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def _validated_components(components: list[Any]) -> list[dict[str, Any]]:
    validated = [treatment_features._validate_component(item) for item in components]
    if not validated:
        raise ValueError("A treatment plan needs at least one component or action")
    return validated


def _save_sync(
    path: Path,
    plan_id: int | None,
    name: str,
    species_id: str | None,
    list_as: str,
    description: str | None,
    components: list[Any],
) -> dict[str, Any]:
    clean_name = _required_text(name)
    species = str(species_id or "").strip().casefold()
    if list_as not in _LIST_TARGETS:
        raise ValueError(f"Unsupported treatment list target: {list_as}")
    validated = _validated_components(components)
    default = next((item for item in validated if item.get("type") != "action"), None)
    default_unit = str(default.get("unit") if default else "dose")
    default_route = str(default.get("route") or "") if default else ""
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    encoded = json.dumps(validated, ensure_ascii=False, sort_keys=True)
    normalized = _normalise(clean_name)

    with _connect(path) as connection:
        if plan_id is not None:
            current = connection.execute(
                "SELECT id FROM v0911_treatment_plans WHERE id=?",
                (plan_id,),
            ).fetchone()
            if current is None:
                raise KeyError(plan_id)
            conflict = connection.execute(
                """
                SELECT id FROM v0911_treatment_plans
                WHERE normalized_name=? AND species_id=? AND id<>?
                LIMIT 1
                """,
                (normalized, species, plan_id),
            ).fetchone()
            if conflict is not None:
                raise ValueError("A treatment plan with this name already exists for this species")
            connection.execute(
                """
                UPDATE v0911_treatment_plans
                SET name=?,normalized_name=?,species_id=?,list_as=?,description=?,
                    default_unit=?,default_route=?,components_json=?,updated_at=?
                WHERE id=?
                """,
                (
                    clean_name,
                    normalized,
                    species,
                    list_as,
                    description,
                    default_unit,
                    default_route or None,
                    encoded,
                    now,
                    plan_id,
                ),
            )
            saved_id = plan_id
        else:
            connection.execute(
                """
                INSERT INTO v0911_treatment_plans(
                    name,normalized_name,species_id,list_as,description,
                    default_unit,default_route,components_json,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(normalized_name,species_id) DO UPDATE SET
                    name=excluded.name,
                    list_as=excluded.list_as,
                    description=excluded.description,
                    default_unit=excluded.default_unit,
                    default_route=excluded.default_route,
                    components_json=excluded.components_json,
                    updated_at=excluded.updated_at
                """,
                (
                    clean_name,
                    normalized,
                    species,
                    list_as,
                    description,
                    default_unit,
                    default_route or None,
                    encoded,
                    now,
                    now,
                ),
            )
            row = connection.execute(
                "SELECT id FROM v0911_treatment_plans WHERE normalized_name=? AND species_id=?",
                (normalized, species),
            ).fetchone()
            if row is None:
                raise RuntimeError("Saved treatment plan could not be loaded")
            saved_id = int(row["id"])

        row = connection.execute(
            """
            SELECT id,name,species_id,list_as,description,default_unit,
                   default_route,components_json,is_archived,archived_at
            FROM v0911_treatment_plans WHERE id=?
            """,
            (saved_id,),
        ).fetchone()
    if row is None:
        raise RuntimeError("Saved treatment plan could not be loaded")
    return _plan_dict(row)


def _archive_sync(path: Path, plan_id: int, archived: bool) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    archived_at = now if archived else None
    with _connect(path) as connection:
        cursor = connection.execute(
            """
            UPDATE v0911_treatment_plans
            SET is_archived=?,archived_at=?,updated_at=?
            WHERE id=?
            """,
            (1 if archived else 0, archived_at, now, plan_id),
        )
        if cursor.rowcount == 0:
            raise KeyError(plan_id)
        row = connection.execute(
            """
            SELECT id,name,species_id,list_as,description,default_unit,
                   default_route,components_json,is_archived,archived_at
            FROM v0911_treatment_plans WHERE id=?
            """,
            (plan_id,),
        ).fetchone()
    if row is None:
        raise KeyError(plan_id)
    return _plan_dict(row)


async def async_initialize_v0918_features(hass: HomeAssistant) -> None:
    await hass.async_add_executor_job(_initialise_sync, _database_path(hass))


def async_setup_v0918_features(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command({vol.Required("type"): _STATE_COMMAND})
    @websocket_api.async_response
    async def websocket_state(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(_plans_sync, _database_path(hass))
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0918_state_failed", str(err))
            return
        connection.send_result(msg["id"], {"treatment_plans": result})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SAVE_COMMAND,
            vol.Optional("plan_id"): vol.Coerce(int),
            vol.Required("name"): _required_text,
            vol.Optional("species_id"): _optional_text,
            vol.Optional("list_as", default="both"): vol.In(_LIST_TARGETS),
            vol.Optional("description"): _optional_text,
            vol.Required("components"): list,
        }
    )
    @websocket_api.async_response
    async def websocket_save(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _save_sync,
                _database_path(hass),
                int(msg["plan_id"]) if msg.get("plan_id") is not None else None,
                str(msg["name"]),
                msg.get("species_id"),
                str(msg.get("list_as") or "both"),
                msg.get("description"),
                msg["components"],
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0918_treatment_save_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _ARCHIVE_COMMAND,
            vol.Required("plan_id"): vol.Coerce(int),
            vol.Required("archived"): bool,
        }
    )
    @websocket_api.async_response
    async def websocket_archive(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _archive_sync,
                _database_path(hass),
                int(msg["plan_id"]),
                bool(msg["archived"]),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0918_treatment_archive_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    websocket_api.async_register_command(hass, websocket_state)
    websocket_api.async_register_command(hass, websocket_save)
    websocket_api.async_register_command(hass, websocket_archive)
