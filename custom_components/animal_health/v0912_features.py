from __future__ import annotations

import json
import re
import secrets
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    ADMINISTRATION_ROUTES,
    ANIMAL_STATUSES,
    DATABASE_NAME,
    DOMAIN,
    DOSE_UNITS,
    EVENT_TYPE_CARE,
    EVENT_TYPE_MEDICATION,
    EVENT_TYPE_STATUS_CHANGE,
    EVENT_TYPE_TREATMENT,
)
from .runtime import AnimalHealthRuntimeData

_STATE_COMMAND = f"{DOMAIN}/v0912/state"
_SAVE_OFF_LABEL_COMMAND = f"{DOMAIN}/v0912/off_label/update"
_SAVE_TREATMENT_COMMAND = f"{DOMAIN}/v0912/treatment/save"
_EXECUTE_TREATMENT_COMMAND = f"{DOMAIN}/v0912/treatment/execute"
_SAVE_STATUS_CHANGE_COMMAND = f"{DOMAIN}/v0912/status_change/save"
_RESOLVE_STATUS_CHANGE_COMMAND = f"{DOMAIN}/v0912/status_change/resolve"

OFF_LABEL_SHOW_ALL = "show_all"
OFF_LABEL_SHOW_MARKED = "show_marked"
OFF_LABEL_HIDE = "hide"
OFF_LABEL_ON_DEMAND = "on_demand"
OFF_LABEL_MODES = (
    OFF_LABEL_SHOW_ALL,
    OFF_LABEL_SHOW_MARKED,
    OFF_LABEL_HIDE,
    OFF_LABEL_ON_DEMAND,
)

COMPONENT_TYPES = ("medication", "supplement", "feed", "action")
LIST_TARGETS = ("medication", "task", "both")


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


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def _event_datetime_utc(hass: HomeAssistant, raw: Any) -> datetime:
    if raw in (None, ""):
        return datetime.now(UTC).replace(microsecond=0)
    value = raw if isinstance(raw, datetime) else datetime.fromisoformat(str(raw))
    if value.tzinfo is None:
        timezone = dt_util.get_time_zone(hass.config.time_zone) or UTC
        value = value.replace(tzinfo=timezone)
    return value.astimezone(UTC).replace(microsecond=0)


def _initialise_sync(path: Path) -> None:
    with _connect(path) as connection:
        columns = {
            str(row[1])
            for row in connection.execute(
                "PRAGMA table_info(v0911_treatment_plans)"
            ).fetchall()
        }
        if columns and "components_json" not in columns:
            connection.execute(
                "ALTER TABLE v0911_treatment_plans "
                "ADD COLUMN components_json TEXT NOT NULL DEFAULT '[]'"
            )
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS v0912_status_changes (
                id TEXT PRIMARY KEY,
                animal_id TEXT NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
                target_status TEXT NOT NULL,
                planned_for TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'scheduled'
                    CHECK (state IN ('scheduled','confirmed','cancelled')),
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                resolved_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_v0912_status_changes_due
                ON v0912_status_changes(state, planned_for);
            CREATE INDEX IF NOT EXISTS idx_v0912_status_changes_animal
                ON v0912_status_changes(animal_id, state, planned_for);
            """
        )
        current = connection.execute(
            "SELECT value FROM v081_settings WHERE key='off_label_mode'"
        ).fetchone()
        if current is None:
            legacy = connection.execute(
                "SELECT value FROM v081_settings WHERE key='off_label_enabled'"
            ).fetchone()
            mode = (
                OFF_LABEL_SHOW_MARKED
                if legacy is not None and str(legacy["value"]).strip() == "1"
                else OFF_LABEL_SHOW_ALL
            )
            now = datetime.now(UTC).replace(microsecond=0).isoformat()
            connection.execute(
                "INSERT INTO v081_settings(key,value,updated_at) VALUES('off_label_mode',?,?)",
                (mode, now),
            )


def _off_label_mode_sync(path: Path) -> str:
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT value FROM v081_settings WHERE key='off_label_mode'"
        ).fetchone()
    value = str(row["value"] if row is not None else OFF_LABEL_SHOW_ALL)
    return value if value in OFF_LABEL_MODES else OFF_LABEL_SHOW_ALL


def _save_off_label_mode_sync(path: Path, mode: str) -> str:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        connection.execute(
            """
            INSERT INTO v081_settings(key,value,updated_at)
            VALUES('off_label_mode',?,?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at
            """,
            (mode, now),
        )
        connection.execute(
            """
            INSERT INTO v081_settings(key,value,updated_at)
            VALUES('off_label_enabled',?,?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at
            """,
            ("1" if mode == OFF_LABEL_SHOW_MARKED else "0", now),
        )
    return mode


def _validate_component(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("Treatment plan components must be objects")
    component_type = str(raw.get("type") or "").strip()
    if component_type not in COMPONENT_TYPES:
        raise ValueError(f"Unsupported treatment component type: {component_type}")
    name = _required_text(raw.get("name"))
    instructions = _optional_text(raw.get("instructions"))
    if component_type == "action":
        return {
            "type": component_type,
            "name": name,
            "dose": None,
            "unit": None,
            "route": None,
            "instructions": instructions,
        }
    try:
        dose = float(raw.get("dose"))
    except (TypeError, ValueError) as err:
        raise ValueError(f"A dose/amount is required for {name}") from err
    if dose <= 0:
        raise ValueError(f"Dose/amount for {name} must be greater than zero")
    unit = str(raw.get("unit") or "").strip()
    if unit not in DOSE_UNITS:
        raise ValueError(f"Unsupported unit for {name}: {unit}")
    route = str(raw.get("route") or "").strip() or None
    if route is not None and route not in ADMINISTRATION_ROUTES:
        raise ValueError(f"Unsupported route for {name}: {route}")
    return {
        "type": component_type,
        "name": name,
        "dose": dose,
        "unit": unit,
        "route": route,
        "instructions": instructions,
    }


def _decode_components(value: Any) -> list[dict[str, Any]]:
    try:
        raw = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    if not isinstance(raw, list):
        return []
    result: list[dict[str, Any]] = []
    for item in raw:
        try:
            result.append(_validate_component(item))
        except (ValueError, vol.Invalid):
            continue
    return result


def _plan_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "name": str(row["name"]),
        "species_id": str(row["species_id"] or ""),
        "list_as": str(row["list_as"]),
        "description": str(row["description"] or ""),
        "default_unit": str(row["default_unit"] or "dose"),
        "default_route": str(row["default_route"] or ""),
        "components": _decode_components(row["components_json"]),
    }


def _plans_sync(path: Path) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT id,name,species_id,list_as,description,default_unit,
                   default_route,components_json
            FROM v0911_treatment_plans
            ORDER BY name COLLATE NOCASE,species_id,id
            """
        ).fetchall()
    return [_plan_dict(row) for row in rows]


def _save_treatment_sync(
    path: Path,
    name: str,
    species_id: str | None,
    list_as: str,
    description: str | None,
    components: list[Any],
) -> dict[str, Any]:
    clean_name = _required_text(name)
    species = str(species_id or "").strip().casefold()
    validated = [_validate_component(item) for item in components]
    if not validated:
        raise ValueError("A treatment plan needs at least one component or action")
    default = next((item for item in validated if item["type"] != "action"), None)
    default_unit = str(default["unit"] if default else "dose")
    default_route = str(default["route"] or "") if default else ""
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    encoded = json.dumps(validated, ensure_ascii=False, sort_keys=True)
    with _connect(path) as connection:
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
                _normalise(clean_name),
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
            """
            SELECT id,name,species_id,list_as,description,default_unit,
                   default_route,components_json
            FROM v0911_treatment_plans
            WHERE normalized_name=? AND species_id=?
            """,
            (_normalise(clean_name), species),
        ).fetchone()
    if row is None:
        raise RuntimeError("Saved treatment plan could not be loaded")
    return _plan_dict(row)


def _execute_treatment_sync(
    runtime: AnimalHealthRuntimeData,
    plan_id: int,
    animal_id: str,
    occurred_at: datetime,
    notes: str | None,
) -> list[dict[str, Any]]:
    database = runtime.database
    results: list[dict[str, Any]] = []
    with database._connect() as connection:  # noqa: SLF001
        animal = database._get_animal_from_connection(connection, animal_id)  # noqa: SLF001
        if animal is None:
            raise KeyError(animal_id)
        row = connection.execute(
            """
            SELECT id,name,species_id,list_as,description,default_unit,
                   default_route,components_json
            FROM v0911_treatment_plans WHERE id=?
            """,
            (plan_id,),
        ).fetchone()
        if row is None:
            raise KeyError(plan_id)
        plan = _plan_dict(row)
        components = plan["components"]
        action_steps = [
            item for item in components if item["type"] == "action"
        ]
        summary = database._create_event_in_connection(  # noqa: SLF001
            connection,
            animal_id=animal_id,
            event_type=EVENT_TYPE_TREATMENT,
            occurred_at=occurred_at,
            title=plan["name"],
            notes=notes or plan["description"] or None,
            data={
                "source": "treatment_plan",
                "treatment_plan_id": plan_id,
                "treatment_plan_name": plan["name"],
                "components": components,
                "action_steps": action_steps,
            },
        )
        results.append(summary.as_dict())
        for item in components:
            if item["type"] not in {"medication", "supplement", "feed"}:
                continue
            event_type = (
                EVENT_TYPE_MEDICATION
                if item["type"] in {"medication", "supplement"}
                else EVENT_TYPE_CARE
            )
            event = database._create_event_in_connection(  # noqa: SLF001
                connection,
                animal_id=animal_id,
                event_type=event_type,
                occurred_at=occurred_at,
                title=item["name"],
                notes=item["instructions"],
                value=float(item["dose"]),
                unit=str(item["unit"]),
                data={
                    "source": "treatment_plan",
                    "treatment_plan_id": plan_id,
                    "treatment_plan_name": plan["name"],
                    "component_type": item["type"],
                    "product_type": item["type"],
                    **({"route": item["route"]} if item["route"] else {}),
                },
            )
            results.append(event.as_dict())
    return results


def _status_change_id(connection: sqlite3.Connection) -> str:
    existing = {
        str(row[0])
        for row in connection.execute("SELECT id FROM v0912_status_changes").fetchall()
    }
    while True:
        value = "SC-" + secrets.token_hex(4).upper()
        if value not in existing:
            return value


def _apply_status_change_sync(
    runtime: AnimalHealthRuntimeData,
    animal_id: str,
    status: str,
    effective_at: datetime,
    notes: str | None,
    scheduled_change_id: str | None = None,
) -> dict[str, Any]:
    database = runtime.database
    effective_at = effective_at.astimezone(UTC).replace(microsecond=0)
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with database._connect() as connection:  # noqa: SLF001
        current = database._get_animal_from_connection(connection, animal_id)  # noqa: SLF001
        if current is None:
            raise KeyError(animal_id)
        previous = current.status
        correction_of: str | None = None
        if previous == status:
            previous_event = connection.execute(
                """
                SELECT id,data_json FROM events
                WHERE animal_id=? AND event_type='status_change'
                ORDER BY occurred_at DESC,created_at DESC LIMIT 1
                """,
                (animal_id,),
            ).fetchone()
            if previous_event is not None:
                correction_of = str(previous_event["id"])
                try:
                    previous_data = json.loads(str(previous_event["data_json"] or "{}"))
                    previous = str(previous_data.get("previous_status") or previous)
                except json.JSONDecodeError:
                    pass
        connection.execute(
            """
            UPDATE animals
            SET status=?,status_changed_at=?,updated_at=?
            WHERE id=?
            """,
            (status, effective_at.isoformat(), now, animal_id),
        )
        event = database._create_event_in_connection(  # noqa: SLF001
            connection,
            animal_id=animal_id,
            event_type=EVENT_TYPE_STATUS_CHANGE,
            occurred_at=effective_at,
            title="status_change",
            notes=notes,
            correction_of_event_id=correction_of,
            data={
                "previous_status": previous,
                "new_status": status,
                "effective_at": effective_at.isoformat(),
                "scheduled_change_id": scheduled_change_id,
                "date_corrected": correction_of is not None,
            },
        )
    return {
        "animal_id": animal_id,
        "status": status,
        "effective_at": effective_at.isoformat(),
        "event": event.as_dict(),
    }


def _save_status_change_sync(
    runtime: AnimalHealthRuntimeData,
    animal_id: str,
    status: str,
    effective_at: datetime,
    notes: str | None,
) -> dict[str, Any]:
    now_dt = datetime.now(UTC).replace(microsecond=0)
    if effective_at <= now_dt:
        return {
            "scheduled": False,
            **_apply_status_change_sync(
                runtime,
                animal_id,
                status,
                effective_at,
                notes,
            ),
        }
    path = runtime.feature_store.database_path
    now = now_dt.isoformat()
    with _connect(path) as connection:
        animal = connection.execute(
            "SELECT id,name,status FROM animals WHERE id=?", (animal_id,)
        ).fetchone()
        if animal is None:
            raise KeyError(animal_id)
        existing = connection.execute(
            """
            SELECT id FROM v0912_status_changes
            WHERE animal_id=? AND state='scheduled'
            ORDER BY planned_for LIMIT 1
            """,
            (animal_id,),
        ).fetchone()
        change_id = str(existing["id"]) if existing is not None else _status_change_id(connection)
        if existing is None:
            connection.execute(
                """
                INSERT INTO v0912_status_changes(
                    id,animal_id,target_status,planned_for,state,notes,
                    created_at,updated_at,resolved_at
                ) VALUES(?,?,?,?, 'scheduled', ?, ?, ?, NULL)
                """,
                (
                    change_id,
                    animal_id,
                    status,
                    effective_at.isoformat(),
                    notes,
                    now,
                    now,
                ),
            )
        else:
            connection.execute(
                """
                UPDATE v0912_status_changes
                SET target_status=?,planned_for=?,notes=?,updated_at=?
                WHERE id=?
                """,
                (status, effective_at.isoformat(), notes, now, change_id),
            )
    return {
        "scheduled": True,
        "id": change_id,
        "animal_id": animal_id,
        "target_status": status,
        "planned_for": effective_at.isoformat(),
    }


def _resolve_status_change_sync(
    runtime: AnimalHealthRuntimeData,
    change_id: str,
    action: str,
    effective_at: datetime | None,
) -> dict[str, Any]:
    path = runtime.feature_store.database_path
    now_dt = datetime.now(UTC).replace(microsecond=0)
    now = now_dt.isoformat()
    with _connect(path) as connection:
        row = connection.execute(
            """
            SELECT id,animal_id,target_status,planned_for,state,notes
            FROM v0912_status_changes WHERE id=?
            """,
            (change_id,),
        ).fetchone()
        if row is None:
            raise KeyError(change_id)
        if str(row["state"]) != "scheduled":
            raise ValueError("The status change is already resolved")
        if action == "cancel":
            connection.execute(
                "UPDATE v0912_status_changes SET state='cancelled',resolved_at=?,updated_at=? WHERE id=?",
                (now, now, change_id),
            )
            return {"id": change_id, "state": "cancelled"}
        if action == "reschedule":
            if effective_at is None:
                raise ValueError("A new date/time is required")
            connection.execute(
                "UPDATE v0912_status_changes SET planned_for=?,updated_at=? WHERE id=?",
                (effective_at.isoformat(), now, change_id),
            )
            return {
                "id": change_id,
                "state": "scheduled",
                "planned_for": effective_at.isoformat(),
            }
        animal_id = str(row["animal_id"])
        status = str(row["target_status"])
        planned = datetime.fromisoformat(str(row["planned_for"]))
        notes = str(row["notes"] or "") or None
    actual = effective_at or planned
    result = _apply_status_change_sync(
        runtime,
        animal_id,
        status,
        actual,
        notes,
        scheduled_change_id=change_id,
    )
    with _connect(path) as connection:
        connection.execute(
            "UPDATE v0912_status_changes SET state='confirmed',resolved_at=?,updated_at=? WHERE id=?",
            (now, now, change_id),
        )
    return {"id": change_id, "state": "confirmed", **result}


def _status_changes_sync(path: Path) -> list[dict[str, Any]]:
    now = datetime.now(UTC).replace(microsecond=0)
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT change.id,change.animal_id,animal.name AS animal_name,
                   change.target_status,change.planned_for,change.state,
                   change.notes,change.created_at,change.updated_at
            FROM v0912_status_changes AS change
            JOIN animals AS animal ON animal.id=change.animal_id
            WHERE change.state='scheduled'
            ORDER BY change.planned_for,animal.name COLLATE NOCASE
            """
        ).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        planned = datetime.fromisoformat(str(row["planned_for"]))
        if planned.tzinfo is None:
            planned = planned.replace(tzinfo=UTC)
        result.append(
            {
                "id": str(row["id"]),
                "animal_id": str(row["animal_id"]),
                "animal_name": str(row["animal_name"]),
                "target_status": str(row["target_status"]),
                "planned_for": planned.astimezone(UTC).replace(microsecond=0).isoformat(),
                "state": "due" if planned <= now else "scheduled",
                "is_due": planned <= now,
                "notes": str(row["notes"] or ""),
            }
        )
    return result


def _state_sync(path: Path) -> dict[str, Any]:
    return {
        "off_label_mode": _off_label_mode_sync(path),
        "treatment_plans": _plans_sync(path),
        "status_changes": _status_changes_sync(path),
    }


async def async_initialize_v0912_features(hass: HomeAssistant) -> None:
    await hass.async_add_executor_job(_initialise_sync, _database_path(hass))


def async_setup_v0912_features(hass: HomeAssistant) -> None:
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
            connection.send_error(msg["id"], "v0912_state_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SAVE_OFF_LABEL_COMMAND,
            vol.Required("mode"): vol.In(OFF_LABEL_MODES),
        }
    )
    @websocket_api.async_response
    async def websocket_save_off_label(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            mode = await hass.async_add_executor_job(
                _save_off_label_mode_sync,
                _database_path(hass),
                str(msg["mode"]),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0912_off_label_failed", str(err))
            return
        connection.send_result(msg["id"], {"off_label_mode": mode})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SAVE_TREATMENT_COMMAND,
            vol.Required("name"): _required_text,
            vol.Optional("species_id"): _optional_text,
            vol.Required("list_as"): vol.In(LIST_TARGETS),
            vol.Optional("description"): _optional_text,
            vol.Required("components"): list,
        }
    )
    @websocket_api.async_response
    async def websocket_save_treatment(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _save_treatment_sync,
                _database_path(hass),
                msg["name"],
                msg.get("species_id"),
                msg["list_as"],
                msg.get("description"),
                msg["components"],
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0912_treatment_save_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _EXECUTE_TREATMENT_COMMAND,
            vol.Required("plan_id"): vol.Coerce(int),
            vol.Required("animal_id"): _required_text,
            vol.Optional("occurred_at"): _optional_text,
            vol.Optional("notes"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_execute_treatment(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        runtime = _runtime_data(hass)
        try:
            occurred_at = _event_datetime_utc(hass, msg.get("occurred_at"))
            events = await hass.async_add_executor_job(
                _execute_treatment_sync,
                runtime,
                int(msg["plan_id"]),
                str(msg["animal_id"]),
                occurred_at,
                msg.get("notes"),
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0912_treatment_execute_failed", str(err))
            return
        connection.send_result(msg["id"], {"events": events})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SAVE_STATUS_CHANGE_COMMAND,
            vol.Required("animal_id"): _required_text,
            vol.Required("status"): vol.In(ANIMAL_STATUSES),
            vol.Required("effective_at"): _required_text,
            vol.Optional("notes"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_save_status_change(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        runtime = _runtime_data(hass)
        try:
            effective_at = _event_datetime_utc(hass, msg["effective_at"])
            result = await hass.async_add_executor_job(
                _save_status_change_sync,
                runtime,
                str(msg["animal_id"]),
                str(msg["status"]),
                effective_at,
                msg.get("notes"),
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0912_status_change_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _RESOLVE_STATUS_CHANGE_COMMAND,
            vol.Required("change_id"): _required_text,
            vol.Required("action"): vol.In(("confirm", "reschedule", "cancel")),
            vol.Optional("effective_at"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_resolve_status_change(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        runtime = _runtime_data(hass)
        try:
            effective_at = (
                _event_datetime_utc(hass, msg.get("effective_at"))
                if msg.get("effective_at")
                else None
            )
            result = await hass.async_add_executor_job(
                _resolve_status_change_sync,
                runtime,
                str(msg["change_id"]),
                str(msg["action"]),
                effective_at,
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0912_status_resolution_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    websocket_api.async_register_command(hass, websocket_state)
    websocket_api.async_register_command(hass, websocket_save_off_label)
    websocket_api.async_register_command(hass, websocket_save_treatment)
    websocket_api.async_register_command(hass, websocket_execute_treatment)
    websocket_api.async_register_command(hass, websocket_save_status_change)
    websocket_api.async_register_command(hass, websocket_resolve_status_change)
