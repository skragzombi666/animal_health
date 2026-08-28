from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import v0923_features
from .const import DOMAIN, SYMPTOM_SEVERITIES
from .runtime import AnimalHealthRuntimeData

_SYMPTOM_GROUP_UPDATE_COMMAND = f"{DOMAIN}/v0925/symptoms/group/update"
_PATCHED = False
_GROUP_ACTIONS = ("continue", "reassess", "resolve")


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
            episode["symptom_capture_batch_id"] = batches.get(
                str(episode.get("id") or ""), ""
            )
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
        if len({str(row["animal_id"]) for row in ordered}) != 1:
            raise ValueError("Grouped symptom updates must stay on one animal")
        if any(str(row["state"]) != "active" for row in ordered):
            raise ValueError("Only active symptom episodes can be updated")
        if any(occurred_date < str(row["started_date"]) for row in ordered):
            raise ValueError("An episode update cannot be before its start date")

        origin_batch_values = [
            str(
                _json_object(row["start_data_json"]).get("symptom_capture_batch_id")
                or ""
            ).strip()
            for row in ordered
        ]
        if len(ids) > 1 and (
            any(not batch for batch in origin_batch_values)
            or len(set(origin_batch_values)) != 1
        ):
            raise ValueError(
                "Symptoms can only be updated together when they were captured together"
            )

        action_batch_id = (
            v0923_features._record_id("SB") if len(ids) > 1 else None  # noqa: SLF001
        )
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
                    "UPDATE v0923_symptom_episodes "
                    "SET latest_severity=?,updated_at=? WHERE id=?",
                    (actual_severity, now, str(row["id"])),
                )
            results.append(event.as_dict())
    return results


def async_setup_v0925_features(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SYMPTOM_GROUP_UPDATE_COMMAND,
            vol.Required("episode_ids"): [_required_text],
            vol.Required("action"): vol.In(_GROUP_ACTIONS),
            vol.Optional("severity"): vol.In(SYMPTOM_SEVERITIES),
            vol.Optional("notes"): _optional_text,
            vol.Optional("occurred_date"): _optional_text,
            vol.Optional("occurred_time"): _optional_text,
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
            connection.send_error(
                msg["id"], "v0925_symptom_group_update_failed", str(err)
            )
            return
        connection.send_result(msg["id"], {"events": result})

    websocket_api.async_register_command(hass, websocket_symptom_group_update)
