from __future__ import annotations

import secrets
import shutil
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from urllib.parse import quote

import voluptuous as vol
from aiohttp import web
from PIL import Image, ImageOps

from homeassistant.components import ai_task, websocket_api
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.http import KEY_HASS

from . import v080_features
from .ai_assist import get_ai_upload
from .const import DOMAIN
from .runtime import AnimalHealthRuntimeData

_STATE_KEY = f"{DOMAIN}_v082"
_PREVIEW_COMMAND = f"{DOMAIN}/v082/attachment/preview"
_RESET_COMMAND = f"{DOMAIN}/v082/reset"
_AI_ANALYZE_COMMAND = f"{DOMAIN}/v082/ai/analyze"
_PREVIEW_TTL = timedelta(minutes=30)
_MAX_CONTEXT_LENGTH = 4000
_PREVIEW_SIZES = {
    "thumb": (360, 76),
    "profile": (768, 82),
    "preview": (1600, 84),
}
_AI_FIELDS = (
    "document_type",
    "suggested_record_type",
    "suggested_title",
    "animal_name",
    "document_date",
    "scheduled_date",
    "due_time",
    "medication_name",
    "vaccine_name",
    "dose",
    "dose_unit",
    "route",
    "vaccination_target",
    "provider",
    "diagnosis",
    "treatment",
    "visit_reason",
    "notes",
    "confidence",
    "uncertainties",
    "weight",
    "weight_unit",
    "occurred_at",
    "recurrence_type",
    "recurrence_interval",
)
_AI_STRUCTURE = vol.Schema(
    {
        vol.Optional(field, description="Return an empty string when absent or uncertain"): str
        for field in _AI_FIELDS
    },
    extra=vol.PREVENT_EXTRA,
)


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _required_text(value: Any) -> str:
    text = str(value).strip()
    if not text:
        raise vol.Invalid("value must not be empty")
    return text


def _optional_context(value: Any) -> str:
    text = str(value or "").strip()
    if len(text) > _MAX_CONTEXT_LENGTH:
        raise vol.Invalid(f"context must not exceed {_MAX_CONTEXT_LENGTH} characters")
    return text


def _state(hass: HomeAssistant) -> dict[str, Any]:
    return hass.data.setdefault(_STATE_KEY, {})


def _initialize_v080_without_forced_group(store) -> None:
    with store._connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS animal_tags (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_animal_tags_name
                ON animal_tags(name COLLATE NOCASE);

            CREATE TABLE IF NOT EXISTS animal_tag_memberships (
                animal_id TEXT NOT NULL
                    REFERENCES animals(id) ON DELETE CASCADE,
                tag_id TEXT NOT NULL
                    REFERENCES animal_tags(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                PRIMARY KEY (animal_id, tag_id)
            );
            CREATE INDEX IF NOT EXISTS idx_animal_tag_memberships_tag
                ON animal_tag_memberships(tag_id, animal_id);

            CREATE TABLE IF NOT EXISTS animal_profiles (
                animal_id TEXT PRIMARY KEY
                    REFERENCES animals(id) ON DELETE CASCADE,
                image_attachment_id TEXT
                    REFERENCES attachments(id) ON DELETE SET NULL,
                updated_at TEXT NOT NULL
            );
            """
        )


_ORIGINAL_V080_STATE_SYNC = v080_features._state_sync


def _v082_state_sync(store) -> dict[str, Any]:
    result = _ORIGINAL_V080_STATE_SYNC(store)
    result["primary_group_required"] = False
    return result


def apply_v082_patches() -> None:
    if getattr(v080_features, "_animal_health_v082_patched", False):
        return
    v080_features._initialize_sync = _initialize_v080_without_forced_group
    v080_features._state_sync = _v082_state_sync
    v080_features._animal_health_v082_patched = True


def _preview_path(root: Path, attachment_id: str, size: str) -> Path:
    return root / f"{attachment_id}-{size}.jpg"


def _render_preview(source: Path, target: Path, size: str) -> None:
    max_edge, quality = _PREVIEW_SIZES[size]
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
        if image.mode != "RGB":
            if "A" in image.getbands():
                background = Image.new("RGB", image.size, "white")
                background.paste(image, mask=image.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")
        image.save(temporary, format="JPEG", quality=quality, optimize=True)
    temporary.replace(target)


def _preview_token(hass: HomeAssistant, attachment_id: str, size: str) -> str:
    token = secrets.token_urlsafe(32)
    _state(hass).setdefault("preview_tokens", {})[token] = {
        "attachment_id": attachment_id,
        "size": size,
        "expires_at": datetime.now(UTC) + _PREVIEW_TTL,
    }
    return token


def _validate_preview_token(
    hass: HomeAssistant,
    token: str,
    attachment_id: str,
) -> dict[str, Any]:
    tokens = _state(hass).setdefault("preview_tokens", {})
    now = datetime.now(UTC)
    for key, item in list(tokens.items()):
        if item["expires_at"] < now:
            tokens.pop(key, None)
    record = tokens.get(token)
    if record is None or record["expires_at"] < now:
        raise web.HTTPUnauthorized()
    if record["attachment_id"] != attachment_id:
        raise web.HTTPForbidden()
    return record


class AnimalHealthPreviewView(HomeAssistantView):
    url = f"/api/{DOMAIN}/v082/attachments/{{attachment_id}}/preview"
    name = f"api:{DOMAIN}:v082_attachment_preview"
    requires_auth = False

    async def get(self, request: web.Request, attachment_id: str) -> web.Response:
        hass: HomeAssistant = request.app[KEY_HASS]
        record = _validate_preview_token(
            hass,
            request.query.get("token", ""),
            attachment_id,
        )
        runtime = _runtime_data(hass)
        try:
            item, source = await runtime.feature_store.attachment_file(attachment_id)
        except (KeyError, FileNotFoundError):
            raise web.HTTPNotFound() from None
        if not str(item.get("media_type") or "").startswith("image/"):
            raise web.HTTPUnsupportedMediaType(text="Preview is only available for images")
        preview_root = runtime.feature_store.attachment_root.parent / "previews"
        target = _preview_path(preview_root, attachment_id, str(record["size"]))
        if not target.is_file():
            try:
                await hass.async_add_executor_job(
                    _render_preview,
                    source,
                    target,
                    str(record["size"]),
                )
            except Exception as err:
                raise web.HTTPInternalServerError(text=str(err)) from err
        body = await hass.async_add_executor_job(target.read_bytes)
        return web.Response(
            body=body,
            content_type="image/jpeg",
            headers={
                "Cache-Control": "private, max-age=1800",
                "Content-Disposition": (
                    f"inline; filename*=UTF-8''{quote(str(item.get('filename') or 'preview.jpg'))}"
                ),
            },
        )


def _animal_context(hass: HomeAssistant) -> tuple[list[str], dict[str, str]]:
    names: list[str] = []
    by_name: dict[str, str] = {}
    for animal in _runtime_data(hass).coordinator.data.values():
        name = str(animal.name).strip()
        if not name:
            continue
        names.append(name)
        by_name[name.casefold()] = str(animal.id)
    return sorted(names, key=str.casefold), by_name


def _ai_instructions(hass: HomeAssistant, mode: str, context: str) -> str:
    names, _ = _animal_context(hass)
    common = (
        "This is data-entry assistance only. Extract only facts explicitly visible in the supplied "
        "images/documents or explicitly stated in the user's supplemental text. Never diagnose, "
        "prescribe, recommend, calculate or infer medical facts. If information is absent, ambiguous "
        "or contradictory, return an empty string and explain the problem in uncertainties. "
        f"Known animal names are: {', '.join(names) if names else '(none)'}. Set animal_name only "
        "when exactly one known animal is clearly identified. Use canonical dose_unit values only "
        "when explicitly supplied: mcg, mg, g, ul, ml, drop, tablet, dose. Use canonical weight_unit "
        "values only when explicitly supplied: mg, g, kg. Preserve count-based doses: for example "
        "'1 tablet' means dose='1' and dose_unit='tablet', never mg. recurrence_type may be once, "
        "daily, weekly or monthly. Set recurrence_type and recurrence_interval only when a cadence "
        "is explicitly stated; for example 'once daily' means daily and 1. scheduled_date and due_time "
        "are only for an explicitly stated future schedule. occurred_at is only an explicitly stated "
        "measurement or event time. confidence must be high, medium or low."
    )
    if mode == "weight":
        instructions = (
            common
            + " The current form is a weight entry. Focus only on animal_name, weight, weight_unit, "
            "occurred_at and notes. Read a scale display when visible. suggested_record_type must be "
            "'weight'. Do not turn unrelated text into another medical record."
        )
    else:
        instructions = (
            common
            + " Classify supplied material using suggested_record_type: medication, vaccination, "
            "veterinary_visit, treatment, health_check, weight, reminder or other. suggested_title "
            "must be a short neutral title grounded in supplied information."
        )
    if context:
        instructions += (
            "\n\nUser-provided supplemental text follows. It is factual input for extraction, not "
            "permission to invent missing information:\n---\n"
            + context
            + "\n---"
        )
    return instructions


def _normalize_ai_result(hass: HomeAssistant, data: Any, mode: str) -> dict[str, Any]:
    raw = data if isinstance(data, dict) else {}
    result = {field: str(raw.get(field) or "").strip() for field in _AI_FIELDS}
    allowed_types = {
        "medication",
        "vaccination",
        "veterinary_visit",
        "treatment",
        "health_check",
        "weight",
        "reminder",
        "other",
    }
    if mode == "weight":
        result["suggested_record_type"] = "weight"
    elif result["suggested_record_type"] not in allowed_types:
        result["suggested_record_type"] = "other"
    if result["confidence"] not in {"high", "medium", "low"}:
        result["confidence"] = "low" if result["confidence"] else ""
    if result["recurrence_type"] not in {"once", "daily", "weekly", "monthly"}:
        result["recurrence_type"] = ""
        result["recurrence_interval"] = ""
    if result["weight_unit"] not in {"mg", "g", "kg"}:
        result["weight_unit"] = ""
    if result["dose_unit"] not in {
        "mcg",
        "mg",
        "g",
        "ul",
        "ml",
        "drop",
        "tablet",
        "dose",
    }:
        result["dose_unit"] = ""
    _, by_name = _animal_context(hass)
    result["matched_animal_id"] = by_name.get(result["animal_name"].casefold(), "")
    return result


def _reset_database_sync(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        tables = [
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
        for table in tables:
            safe = table.replace('"', '""')
            connection.execute(f'DELETE FROM "{safe}"')
        try:
            connection.execute("DELETE FROM sqlite_sequence")
        except sqlite3.OperationalError:
            pass
        connection.commit()


async def _perform_reset(
    hass: HomeAssistant,
    entry_id: str,
    database_path: Path,
    storage_root: Path,
) -> None:
    await hass.config_entries.async_unload(entry_id)

    entity_registry = er.async_get(hass)
    for entity in list(entity_registry.entities.values()):
        if entity.config_entry_id == entry_id:
            entity_registry.async_remove(entity.entity_id)

    device_registry = dr.async_get(hass)
    for device in list(device_registry.devices.values()):
        if entry_id in device.config_entries:
            device_registry.async_remove_device(device.id)

    await hass.async_add_executor_job(_reset_database_sync, database_path)
    await hass.async_add_executor_job(shutil.rmtree, storage_root, True)
    await hass.config_entries.async_setup(entry_id)


def async_setup_v082_features(hass: HomeAssistant) -> None:
    state = _state(hass)
    if not state.get("preview_view_registered"):
        hass.http.register_view(AnimalHealthPreviewView())
        state["preview_view_registered"] = True

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _PREVIEW_COMMAND,
            vol.Required("attachment_id"): _required_text,
            vol.Optional("size", default="thumb"): vol.In(tuple(_PREVIEW_SIZES)),
        }
    )
    @websocket_api.async_response
    async def websocket_preview(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            item, _ = await _runtime_data(hass).feature_store.attachment_file(
                msg["attachment_id"]
            )
            if not str(item.get("media_type") or "").startswith("image/"):
                raise ValueError("Attachment is not an image")
            size = str(msg.get("size") or "thumb")
            token = _preview_token(hass, msg["attachment_id"], size)
        except Exception as err:
            connection.send_error(msg["id"], "v082_preview_failed", str(err))
            return
        connection.send_result(
            msg["id"],
            {
                "url": (
                    f"/api/{DOMAIN}/v082/attachments/{msg['attachment_id']}/preview"
                    f"?token={token}"
                ),
                "size": size,
            },
        )

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _AI_ANALYZE_COMMAND,
            vol.Optional("upload_ids", default=[]): vol.All(
                [_required_text], vol.Length(max=10)
            ),
            vol.Optional("entity_id"): _required_text,
            vol.Optional("context", default=""): _optional_context,
            vol.Optional("mode", default="general"): vol.In(("general", "weight")),
        }
    )
    @websocket_api.async_response
    async def websocket_ai_analyze(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        upload_ids = list(msg.get("upload_ids") or [])
        context = str(msg.get("context") or "").strip()
        if not upload_ids and not context:
            connection.send_error(
                msg["id"],
                "v082_ai_input_missing",
                "Add a photo/document, text or dictation before analysis",
            )
            return
        records: list[tuple[str, dict[str, Any]]] = []
        for upload_id in upload_ids:
            record = get_ai_upload(hass, upload_id)
            if record is None:
                connection.send_error(
                    msg["id"],
                    "v082_ai_upload_missing",
                    "AI upload expired or missing",
                )
                return
            media_type = str(record.get("media_type") or "")
            if media_type != "application/pdf" and not media_type.startswith("image/"):
                connection.send_error(
                    msg["id"],
                    "v082_ai_unsupported",
                    "Only image and PDF uploads can be analyzed",
                )
                return
            records.append((upload_id, record))
        entities = sorted(hass.states.async_entity_ids("ai_task"))
        entity_id = msg.get("entity_id")
        if entity_id is None and len(entities) == 1:
            entity_id = entities[0]
        try:
            result = await ai_task.async_generate_data(
                hass,
                task_name=f"animal_health_{msg.get('mode', 'general')}_extraction",
                entity_id=entity_id,
                instructions=_ai_instructions(
                    hass,
                    str(msg.get("mode") or "general"),
                    context,
                ),
                structure=_AI_STRUCTURE,
                attachments=[
                    {
                        "media_content_id": f"media-source://{DOMAIN}/{upload_id}",
                        "media_content_type": str(record["media_type"]),
                    }
                    for upload_id, record in records
                ],
            )
            normalized = _normalize_ai_result(
                hass,
                result.data,
                str(msg.get("mode") or "general"),
            )
            normalized["source_filenames"] = [
                str(record["filename"]) for _, record in records
            ]
            normalized["source_filename"] = (
                normalized["source_filenames"][0]
                if normalized["source_filenames"]
                else ""
            )
        except Exception as err:
            connection.send_error(msg["id"], "v082_ai_analysis_failed", str(err))
            return
        connection.send_result(msg["id"], normalized)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _RESET_COMMAND,
            vol.Required("confirm"): vol.In(("RESET",)),
        }
    )
    @websocket_api.async_response
    async def websocket_reset(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        connection.require_admin()
        runtime = _runtime_data(hass)
        entry = next(
            entry
            for entry in hass.config_entries.async_entries(DOMAIN)
            if entry.state is ConfigEntryState.LOADED
        )
        database_path = runtime.feature_store.database_path
        storage_root = runtime.feature_store.attachment_root.parent
        connection.send_result(msg["id"], {"resetting": True})
        hass.async_create_task(
            _perform_reset(
                hass,
                entry.entry_id,
                database_path,
                storage_root,
            ),
            "Animal Health 0.8.2 reset",
        )

    websocket_api.async_register_command(hass, websocket_preview)
    websocket_api.async_register_command(hass, websocket_ai_analyze)
    websocket_api.async_register_command(hass, websocket_reset)
