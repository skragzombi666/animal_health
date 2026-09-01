from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any, cast

import voluptuous as vol
from aiohttp import web

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import task_records, v082_features, v0924_features
from .const import DATABASE_NAME, DOMAIN
from .runtime import AnimalHealthRuntimeData

_TASK_PLAN_UPDATE_COMMAND = f"{DOMAIN}/v0929/task/plan/update"
_PATCHED = False


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _database_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(DATABASE_NAME))


def _required_text(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise vol.Invalid("value must not be empty")
    return text


def _update_pending_plans_sync(path: Path, task_id: str, template: dict[str, Any]) -> None:
    encoded = json.dumps(template, ensure_ascii=False, sort_keys=True)
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute(
            """
            UPDATE task_occurrence_plans
            SET planned_json = ?, updated_at = ?
            WHERE occurrence_id IN (
                SELECT occurrence.id
                FROM task_occurrences AS occurrence
                WHERE occurrence.task_id = ?
                  AND occurrence.status = 'pending'
            )
              AND resolved_at IS NULL
            """,
            (encoded, now, task_id),
        )


def _no_store(response: web.StreamResponse) -> web.StreamResponse:
    response.headers["Cache-Control"] = "private, no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def apply_v0929_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    original_v082_validate = v082_features._validate_preview_token  # noqa: SLF001

    def validate_v082_preview_token(hass: HomeAssistant, token: str, attachment_id: str):
        try:
            return original_v082_validate(hass, token, attachment_id)
        except (web.HTTPUnauthorized, web.HTTPForbidden) as err:
            raise web.HTTPGone(text="Preview token expired; request a fresh preview URL") from err

    v082_features._validate_preview_token = validate_v082_preview_token  # type: ignore[assignment]  # noqa: SLF001

    original_v082_get = v082_features.AnimalHealthPreviewView.get

    async def v082_get_no_store(self, request: web.Request, attachment_id: str):
        response = await original_v082_get(self, request, attachment_id)
        return _no_store(response)

    v082_features.AnimalHealthPreviewView.get = v082_get_no_store  # type: ignore[method-assign]

    original_v0924_verify = v0924_features._verify_attachment_token  # noqa: SLF001

    def verify_v0924_attachment_token(request: web.Request, attachment_id: str) -> None:
        try:
            original_v0924_verify(request, attachment_id)
        except (web.HTTPUnauthorized, web.HTTPForbidden) as err:
            raise web.HTTPGone(text="Attachment token expired; request a fresh URL") from err

    v0924_features._verify_attachment_token = verify_v0924_attachment_token  # type: ignore[assignment]  # noqa: SLF001

    original_v0924_get = v0924_features.AnimalHealthV0924AttachmentView.get

    async def v0924_get_no_store(self, request: web.Request, attachment_id: str, variant: str):
        response = await original_v0924_get(self, request, attachment_id, variant)
        return _no_store(response)

    v0924_features.AnimalHealthV0924AttachmentView.get = v0924_get_no_store  # type: ignore[method-assign]


def async_setup_v0929_features(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command(
        {
            vol.Required("type"): _TASK_PLAN_UPDATE_COMMAND,
            vol.Required("task_id"): _required_text,
            vol.Required("title"): _required_text,
            vol.Required("plan_values"): dict,
        }
    )
    @websocket_api.async_response
    async def websocket_task_plan_update(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        task_id = str(msg["task_id"])
        store = task_records.TaskRecordStore(hass)
        try:
            current = await store.get_task_config(task_id)
            template = await hass.async_add_executor_job(
                partial(
                    task_records.build_task_template,
                    current.task_kind,
                    dict(msg["plan_values"]),
                    title=str(msg["title"]),
                    current=current.template,
                )
            )
            await store.configure_task(task_id, current.task_kind, template)
            await hass.async_add_executor_job(
                _update_pending_plans_sync,
                _database_path(hass),
                task_id,
                template,
            )
            await _runtime_data(hass).coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0929_task_plan_update_failed", str(err))
            return
        connection.send_result(
            msg["id"],
            {
                "task_id": task_id,
                "task_kind": current.task_kind,
                "planned": template,
                "future_only": True,
            },
        )

    websocket_api.async_register_command(hass, websocket_task_plan_update)
