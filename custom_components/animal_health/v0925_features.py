from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, datetime
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import v0912_features, v0923_features
from .const import ADMINISTRATION_ROUTES, DOMAIN, DOSE_UNITS, SYMPTOM_SEVERITIES
from .runtime import AnimalHealthRuntimeData

_SYMPTOM_GROUP_UPDATE_COMMAND = f"{DOMAIN}/v0925/symptoms/group/update"
_TREATMENT_UPDATE_COMMAND = f"{DOMAIN}/v0925/treatment/update"
_MEDICATION_UPDATE_COMMAND = f"{DOMAIN}/v0925/medication/update"
_PATCHED = False
_GROUP_ACTIONS = ("continue", "reassess", "resolve")
_LIST_TARGETS = ("medication", "task", "both")


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


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


def _json_object(value: Any) -> dict[str, Any]:
    try:
        decoded = json.loads(str(value or "{}"))
    except (TypeError, json.JSONDecodeError):
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _start_batch_ids(path) -> dict[str, str]:
    with v0923_features._connect(path) as connection:  # noqa: SLF001
        rows = connection.execute(
            """
            SELECT ep.id,ev.data_json
            FROM v0923_symptom_episodes AS ep
            LEFT JOIN events AS ev ON ev.id=ep.start_event_id
            """
        ).fetchall()
    result: dict[str, str] = {}
    for row in rows:
        data = _json_object(row["data_json"])
        batch_id = str(data.get("symptom_capture_batch_id") or "").strip()
        if batch_id:
            result[str(row["id"])] = batch_id
    return result


def apply_v0925_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True
    base_episode_state = v0923_features._episode_state_sync  # noqa: SLF001

    def episode_state_with_capture_groups(path):
        result = base_episode_state(path)
        batches = _start_batch_ids(path)
        for episode in result.get("episodes", []):
            episode["symptom_capture_batch_id"] = batches.get(str(episode.get("id") or ""), "")
        return result

    v0923_features._episode_state_sync = episode_state_with_capture_groups  # noqa: SLF001


def _group_update_sync(
    database,
    episode_ids: list[str],
    action: str,
    severity: str | None,
    occurred_at,
    occurred_date: str,
    precision: str,
    notes: str | None,
) -> list[dict[str, Any]]:
    ids: list[str] = []
    seen: set[str] = set()
    for raw in episode_ids:
        episode_id = str(raw or "").strip()
        if not episode_id or episode_id in seen:
            continue
        seen.add(episode_id)
        ids.append(episode_id)
    if not ids:
        raise ValueError("At least one symptom episode is required")
    if len(ids) > 30:
        raise ValueError("At most 30 symptom episodes can be updated together")
    if action == "reassess" and severity not in SYMPTOM_SEVERITIES:
        raise ValueError("A valid severity is required for reassessment")

    placeholders = ",".join("?" for _ in ids)
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    results: list[dict[str, Any]] = []
    with database._connect() as connection:  # noqa: SLF001
        rows = connection.execute(
            f"""
            SELECT ep.*,ev.data_json AS start_data_json
            FROM v0923_symptom_episodes AS ep
            LEFT JOIN events AS ev ON ev.id=ep.start_event_id
            WHERE ep.id IN ({placeholders})
            """,
            ids,
        ).fetchall()
        by_id = {str(row["id"]): row for row in rows}
        if len(by_id) != len(ids):
            missing = next(item for item in ids if item not in by_id)
            raise KeyError(missing)
        ordered = [by_id[item] for item in ids]
        animals = {str(row["animal_id"]) for row in ordered}
        if len(animals) != 1:
            raise ValueError("Grouped symptom updates must stay on one animal")
        if any(str(row["state"]) != "active" for row in ordered):
            raise ValueError("Only active symptom episodes can be updated")
        if any(occurred_date < str(row["started_date"]) for row in ordered):
            raise ValueError("An episode update cannot be before its start date")

        origin_batches = {
            str(_json_object(row["start_data_json"]).get("symptom_capture_batch_id") or "").strip()
            for row in ordered
        }
        origin_batches.discard("")
        if len(ids) > 1 and len(origin_batches) != 1:
            raise ValueError("Symptoms can only be updated together when they were captured together")
        action_batch_id = v0923_features._record_id("SB") if len(ids) > 1 else None  # noqa: SLF001
        resolve = action == "resolve"

        for row in ordered:
            actual_severity = str(severity or row["latest_severity"])
            event_action = "resolved" if resolve else "reassessment"
            state = "resolved" if resolve else "active"
            event = v0923_features._episode_event(  # noqa: SLF001
                database,
                connection,
                episode_id=str(row["id"]),
                animal_id=str(row["animal_id"]),
                symptom=str(row["symptom"]),
                severity=actual_severity,
                occurred_at=occurred_at,
                occurred_date=occurred_date,
                precision=precision,
                action=event_action,
                state=state,
                notes=notes,
                capture_batch_id=action_batch_id,
            )
            v0923_features._insert_assessment(  # noqa: SLF001
                connection,
                episode_id=str(row["id"]),
                event_id=event.id,
                action=event_action,
                occurred_at=occurred_at,
                occurred_date=occurred_date,
                precision=precision,
                severity=actual_severity,
                notes=notes,
                created_at=now,
            )
            if resolve:
                connection.execute(
                    """
                    UPDATE v0923_symptom_episodes
                    SET state='resolved',ended_at=?,ended_date=?,latest_severity=?,updated_at=?
                    WHERE id=?
                    """,
                    (
                        occurred_at.isoformat(),
                        occurred_date,
                        actual_severity,
                        now,
                        str(row["id"]),
                    ),
                )
            else:
                connection.execute(
                    "UPDATE v0923_symptom_episodes SET latest_severity=?,updated_at=? WHERE id=?",
                    (actual_severity, now, str(row["id"])),
                )
            results.append(event.as_dict())
    return results


def _update_treatment_sync(
    path,
    treatment_id: int,
    name: str,
    species_id: str | None,
    list_as: str,
    description: str | None,
    components: list[Any],
) -> dict[str, Any]:
    clean_name = _required_text(name)
    species = str(species_id or "").strip().casefold()
    validated = [v0912_features._validate_component(item) for item in components]  # noqa: SLF001
    if not validated:
        raise ValueError("A treatment plan needs at least one component or action")
    default = next((item for item in validated if item["type"] != "action"), None)
    default_unit = str(default["unit"] if default else "dose")
    default_route = str(default["route"] or "") if default else ""
    encoded = json.dumps(validated, ensure_ascii=False, sort_keys=True)
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with v0912_features._connect(path) as connection:  # noqa: SLF001
        cursor = connection.execute(
            """
            UPDATE v0911_treatment_plans
            SET name=?,normalized_name=?,species_id=?,list_as=?,description=?,
                default_unit=?,default_route=?,components_json=?,updated_at=?
            WHERE id=?
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
                treatment_id,
            ),
        )
        if cursor.rowcount < 1:
            raise KeyError(treatment_id)
        row = connection.execute(
            """
            SELECT id,name,species_id,list_as,description,default_unit,
                   default_route,components_json
            FROM v0911_treatment_plans WHERE id=?
            """,
            (treatment_id,),
        ).fetchone()
    if row is None:
        raise KeyError(treatment_id)
    return v0912_features._plan_dict(row)  # noqa: SLF001


def _update_medication_sync(
    path,
    medication_id: int,
    name: str,
    species_id: str | None,
    default_unit: str,
    default_route: str | None,
) -> dict[str, Any]:
    clean_name = _required_text(name)
    species = str(species_id or "").strip().casefold()
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with v0912_features._connect(path) as connection:  # noqa: SLF001
        cursor = connection.execute(
            """
            UPDATE v0817_medications
            SET name=?,normalized_name=?,species_id=?,default_unit=?,default_route=?,updated_at=?
            WHERE id=?
            """,
            (
                clean_name,
                _normalise(clean_name),
                species,
                default_unit,
                default_route or None,
                now,
                medication_id,
            ),
        )
        if cursor.rowcount < 1:
            raise KeyError(medication_id)
        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='animal_custom_values'"
        ).fetchone():
            connection.execute(
                """
                INSERT INTO animal_custom_values(
                    kind,species_id,breed_context,value,normalized_value,created_at,updated_at
                ) VALUES('medication',?,'',?,?,?,?,?)
                ON CONFLICT(kind,species_id,breed_context,normalized_value) DO UPDATE SET
                    value=excluded.value,updated_at=excluded.updated_at
                """,
                (species, clean_name, _normalise(clean_name), now, now),
            )
        row = connection.execute(
            """
            SELECT id,name,species_id,default_unit,default_route
            FROM v0817_medications WHERE id=?
            """,
            (medication_id,),
        ).fetchone()
    if row is None:
        raise KeyError(medication_id)
    return {
        "id": int(row["id"]),
        "name": str(row["name"]),
        "species_id": str(row["species_id"] or ""),
        "default_unit": str(row["default_unit"]),
        "default_route": str(row["default_route"] or ""),
    }


def async_setup_v0925_features(hass: HomeAssistant) -> None:
    temporal = {
        vol.Optional("occurred_date"): _optional_text,
        vol.Optional("occurred_time"): _optional_text,
    }

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SYMPTOM_GROUP_UPDATE_COMMAND,
            vol.Required("episode_ids"): [_required_text],
            vol.Required("action"): vol.In(_GROUP_ACTIONS),
            vol.Optional("severity"): vol.In(SYMPTOM_SEVERITIES),
            vol.Optional("notes"): _optional_text,
            **temporal,
        }
    )
    @websocket_api.async_response
    async def websocket_symptom_group_update(hass, connection, msg) -> None:
        runtime = _runtime_data(hass)
        try:
            occurred_at, precision, day = v0923_features._event_when(  # noqa: SLF001
                hass,
                msg.get("occurred_date"),
                msg.get("occurred_time"),
            )
            result = await hass.async_add_executor_job(
                _group_update_sync,
                runtime.database,
                msg["episode_ids"],
                msg["action"],
                msg.get("severity"),
                occurred_at,
                day,
                precision,
                msg.get("notes"),
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0925_symptom_group_update_failed", str(err))
            return
        connection.send_result(msg["id"], {"events": result})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _TREATMENT_UPDATE_COMMAND,
            vol.Required("treatment_id"): vol.Coerce(int),
            vol.Required("name"): _required_text,
            vol.Optional("species_id"): _optional_text,
            vol.Required("list_as"): vol.In(_LIST_TARGETS),
            vol.Optional("description"): _optional_text,
            vol.Required("components"): list,
        }
    )
    @websocket_api.async_response
    async def websocket_treatment_update(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(
                _update_treatment_sync,
                v0912_features._database_path(hass),  # noqa: SLF001
                int(msg["treatment_id"]),
                msg["name"],
                msg.get("species_id"),
                msg["list_as"],
                msg.get("description"),
                msg["components"],
            )
        except sqlite3.IntegrityError as err:
            connection.send_error(msg["id"], "v0925_treatment_conflict", str(err))
            return
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0925_treatment_update_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _MEDICATION_UPDATE_COMMAND,
            vol.Required("medication_id"): vol.Coerce(int),
            vol.Required("name"): _required_text,
            vol.Optional("species_id"): _optional_text,
            vol.Required("default_unit"): vol.In(DOSE_UNITS),
            vol.Optional("default_route"): vol.Any(None, "", vol.In(ADMINISTRATION_ROUTES)),
        }
    )
    @websocket_api.async_response
    async def websocket_medication_update(hass, connection, msg) -> None:
        try:
            result = await hass.async_add_executor_job(
                _update_medication_sync,
                v0912_features._database_path(hass),  # noqa: SLF001
                int(msg["medication_id"]),
                msg["name"],
                msg.get("species_id"),
                msg["default_unit"],
                msg.get("default_route") or None,
            )
        except sqlite3.IntegrityError as err:
            connection.send_error(msg["id"], "v0925_medication_conflict", str(err))
            return
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0925_medication_update_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    websocket_api.async_register_command(hass, websocket_symptom_group_update)
    websocket_api.async_register_command(hass, websocket_treatment_update)
    websocket_api.async_register_command(hass, websocket_medication_update)
