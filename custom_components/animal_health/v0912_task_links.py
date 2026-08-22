from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .runtime import AnimalHealthRuntimeData

_COMMAND = f"{DOMAIN}/v0912/task_plan/link"


def _runtime(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _link_sync(path: Path, task_id: str, plan_id: int) -> None:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        plan = connection.execute(
            "SELECT id,name,components_json FROM v0911_treatment_plans WHERE id=?",
            (plan_id,),
        ).fetchone()
        if plan is None:
            raise KeyError(plan_id)
        try:
            components = json.loads(str(plan["components_json"] or "[]"))
        except json.JSONDecodeError:
            components = []
        if not isinstance(components, list):
            components = []
        row = connection.execute(
            "SELECT task_kind,template_json FROM task_record_configs WHERE task_id=?",
            (task_id,),
        ).fetchone()
        if row is None:
            raise KeyError(task_id)
        if str(row["task_kind"]) != "treatment":
            raise ValueError("Only treatment tasks can be linked to a treatment plan")
        try:
            template = json.loads(str(row["template_json"] or "{}"))
        except json.JSONDecodeError:
            template = {}
        if not isinstance(template, dict):
            template = {}
        template["treatment_plan_id"] = plan_id
        template["treatment_plan_name"] = str(plan["name"])
        template["treatment_plan_components"] = components
        now = datetime.now(UTC).replace(microsecond=0).isoformat()
        encoded = json.dumps(template, ensure_ascii=False, sort_keys=True)
        connection.execute(
            "UPDATE task_record_configs SET template_json=?,updated_at=? WHERE task_id=?",
            (encoded, now, task_id),
        )
        connection.execute(
            """
            UPDATE task_occurrence_plans
            SET planned_json=?,updated_at=?
            WHERE occurrence_id IN (
                SELECT id FROM task_occurrences
                WHERE task_id=? AND status='pending'
            )
            """,
            (encoded, now, task_id),
        )
        connection.commit()
    finally:
        connection.close()


def async_setup_v0912_task_links(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command(
        {
            vol.Required("type"): _COMMAND,
            vol.Required("task_id"): str,
            vol.Required("plan_id"): vol.Coerce(int),
        }
    )
    @websocket_api.async_response
    async def websocket_link(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        runtime = _runtime(hass)
        try:
            await hass.async_add_executor_job(
                _link_sync,
                runtime.feature_store.database_path,
                str(msg["task_id"]),
                int(msg["plan_id"]),
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0912_task_plan_link_failed", str(err))
            return
        connection.send_result(msg["id"], {"linked": True})

    websocket_api.async_register_command(hass, websocket_link)
