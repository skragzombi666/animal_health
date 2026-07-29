from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from urllib.parse import quote

import voluptuous as vol
from aiohttp import web

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers.http import KEY_HASS

from .const import DOMAIN
from .exports import animal_health_pdf_bytes, backup_zip_bytes, json_export_bytes
from .runtime import AnimalHealthRuntimeData

_FEATURES_COMMAND = f"{DOMAIN}/features"
_CREATE_GROUP_COMMAND = f"{DOMAIN}/groups/create"
_UPDATE_GROUP_COMMAND = f"{DOMAIN}/groups/update"
_DELETE_GROUP_COMMAND = f"{DOMAIN}/groups/delete"
_SET_ANIMAL_GROUP_COMMAND = f"{DOMAIN}/animal_group/set"
_LIST_ATTACHMENTS_COMMAND = f"{DOMAIN}/attachments/list"
_UPLOAD_ATTACHMENT_COMMAND = f"{DOMAIN}/attachments/upload"
_DELETE_ATTACHMENT_COMMAND = f"{DOMAIN}/attachments/delete"
_DOWNLOAD_COMMAND = f"{DOMAIN}/download"
_STATE_KEY = f"{DOMAIN}_feature_api"
_MAX_ATTACHMENT_SIZE = 15 * 1024 * 1024


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_text(value: Any) -> str:
    text = str(value).strip()
    if not text:
        raise vol.Invalid("value must not be empty")
    return text


def _consume_transfer_token(
    request: web.Request,
    expected_kind: str,
    resource_id: str | None = None,
) -> dict[str, Any]:
    hass: HomeAssistant = request.app[KEY_HASS]
    token = request.query.get("token", "")
    state = hass.data.setdefault(_STATE_KEY, {})
    tokens = state.setdefault("download_tokens", {})
    record = tokens.pop(token, None)
    if record is None:
        raise web.HTTPUnauthorized()
    if datetime.now(UTC) > record["expires_at"]:
        raise web.HTTPUnauthorized()
    if record["kind"] != expected_kind:
        raise web.HTTPForbidden()
    if resource_id is not None and record.get("resource_id") != resource_id:
        raise web.HTTPForbidden()
    return record


def _download_headers(filename: str) -> dict[str, str]:
    fallback = "".join(
        character
        if character.isascii()
        and 32 <= ord(character) < 127
        and character not in '\\/:*?"<>|'
        else "_"
        for character in filename
    )
    return {
        "Content-Disposition": (
            f'attachment; filename="{fallback}"; filename*=UTF-8\'\'{quote(filename)}'
        ),
        "Cache-Control": "no-store",
    }




class AnimalHealthAttachmentUploadView(HomeAssistantView):
    url = f"/api/{DOMAIN}/attachments"
    name = f"api:{DOMAIN}:attachment_upload"
    requires_auth = False

    async def post(self, request: web.Request) -> web.Response:
        token_record = _consume_transfer_token(request, "upload")
        reader = await request.multipart()
        filename: str | None = None
        media_type: str | None = None
        title: str | None = None
        content = bytearray()
        while part := await reader.next():
            if part.name == "title":
                title = (await part.text()).strip() or None
                continue
            if part.name != "file":
                continue
            filename = part.filename or "document"
            media_type = part.headers.get("Content-Type")
            while chunk := await part.read_chunk(size=64 * 1024):
                content.extend(chunk)
                if len(content) > _MAX_ATTACHMENT_SIZE:
                    raise web.HTTPRequestEntityTooLarge(
                        max_size=_MAX_ATTACHMENT_SIZE,
                        actual_size=len(content),
                    )
        if filename is None or not content:
            raise web.HTTPBadRequest(text="A non-empty file is required")
        try:
            item = await _runtime_data(request.app[KEY_HASS]).feature_store.create_attachment(
                animal_id=str(token_record["animal_id"]),
                event_id=token_record.get("event_id"),
                filename=filename,
                media_type=media_type,
                content=bytes(content),
                title=title,
            )
        except (KeyError, ValueError) as err:
            raise web.HTTPBadRequest(text=str(err)) from err
        return web.json_response(item, headers={"Cache-Control": "no-store"})


class AnimalHealthAttachmentView(HomeAssistantView):
    url = f"/api/{DOMAIN}/attachments/{{attachment_id}}"
    name = f"api:{DOMAIN}:attachment"
    requires_auth = False

    async def get(self, request: web.Request, attachment_id: str) -> web.Response:
        _consume_transfer_token(request, "attachment", attachment_id)
        hass: HomeAssistant = request.app[KEY_HASS]
        try:
            item, path = await _runtime_data(hass).feature_store.attachment_file(
                attachment_id
            )
            content = await hass.async_add_executor_job(path.read_bytes)
        except (KeyError, FileNotFoundError):
            raise web.HTTPNotFound() from None
        return web.Response(
            body=content,
            content_type=str(item["media_type"]),
            headers=_download_headers(str(item["filename"])),
        )


class AnimalHealthJsonExportView(HomeAssistantView):
    url = f"/api/{DOMAIN}/export/data.json"
    name = f"api:{DOMAIN}:export_json"
    requires_auth = False

    async def get(self, request: web.Request) -> web.Response:
        _consume_transfer_token(request, "json")
        hass: HomeAssistant = request.app[KEY_HASS]
        runtime = _runtime_data(hass)
        body = await hass.async_add_executor_job(
            json_export_bytes,
            runtime.feature_store.database_path,
        )
        return web.Response(
            body=body,
            content_type="application/json",
            charset="utf-8",
            headers=_download_headers("animal_health.json"),
        )


class AnimalHealthBackupExportView(HomeAssistantView):
    url = f"/api/{DOMAIN}/export/backup.zip"
    name = f"api:{DOMAIN}:export_backup"
    requires_auth = False

    async def get(self, request: web.Request) -> web.Response:
        _consume_transfer_token(request, "backup")
        hass: HomeAssistant = request.app[KEY_HASS]
        runtime = _runtime_data(hass)
        body = await hass.async_add_executor_job(
            backup_zip_bytes,
            runtime.feature_store.database_path,
            runtime.feature_store.attachment_root,
        )
        return web.Response(
            body=body,
            content_type="application/zip",
            headers=_download_headers("animal_health_backup.zip"),
        )


class AnimalHealthPdfExportView(HomeAssistantView):
    url = f"/api/{DOMAIN}/export/animals/{{animal_id}}/health.pdf"
    name = f"api:{DOMAIN}:export_animal_pdf"
    requires_auth = False

    async def get(self, request: web.Request, animal_id: str) -> web.Response:
        _consume_transfer_token(request, "animal_pdf", animal_id)
        hass: HomeAssistant = request.app[KEY_HASS]
        runtime = _runtime_data(hass)
        try:
            filename, body = await hass.async_add_executor_job(
                animal_health_pdf_bytes,
                runtime.feature_store.database_path,
                animal_id,
            )
        except KeyError:
            raise web.HTTPNotFound() from None
        return web.Response(
            body=body,
            content_type="application/pdf",
            headers=_download_headers(filename),
        )


def async_setup_feature_api(hass: HomeAssistant) -> None:
    """Register Animal Health 0.7.1 group, attachment and export APIs."""
    state = hass.data.setdefault(_STATE_KEY, {})
    if not state.get("views_registered"):
        hass.http.register_view(AnimalHealthAttachmentUploadView())
        hass.http.register_view(AnimalHealthAttachmentView())
        hass.http.register_view(AnimalHealthJsonExportView())
        hass.http.register_view(AnimalHealthBackupExportView())
        hass.http.register_view(AnimalHealthPdfExportView())
        state["views_registered"] = True

    @websocket_api.websocket_command({vol.Required("type"): _FEATURES_COMMAND})
    @websocket_api.async_response
    async def websocket_features(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            store = _runtime_data(hass).feature_store
            groups, memberships = await store.list_groups(), await store.memberships()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "features_failed", str(err))
            return
        connection.send_result(
            msg["id"],
            {
                "storage": "local",
                "max_attachment_size_bytes": 15 * 1024 * 1024,
                "groups": groups,
                "memberships": memberships,
                "exports": {
                    "json": f"/api/{DOMAIN}/export/data.json",
                    "backup": f"/api/{DOMAIN}/export/backup.zip",
                    "animal_pdf": f"/api/{DOMAIN}/export/animals/{{animal_id}}/health.pdf",
                },
            },
        )

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _CREATE_GROUP_COMMAND,
            vol.Required("name"): _required_text,
            vol.Optional("species"): _optional_text,
            vol.Optional("description"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_create_group(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            group = await _runtime_data(hass).feature_store.create_group(
                name=msg["name"],
                species=msg.get("species"),
                description=msg.get("description"),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "create_group_failed", str(err))
            return
        connection.send_result(msg["id"], group)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _UPDATE_GROUP_COMMAND,
            vol.Required("group_id"): _required_text,
            vol.Required("name"): _required_text,
            vol.Optional("species"): _optional_text,
            vol.Optional("description"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_update_group(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            group = await _runtime_data(hass).feature_store.update_group(
                msg["group_id"],
                name=msg["name"],
                species=msg.get("species"),
                description=msg.get("description"),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "update_group_failed", str(err))
            return
        connection.send_result(msg["id"], group)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _DELETE_GROUP_COMMAND,
            vol.Required("group_id"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_delete_group(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            await _runtime_data(hass).feature_store.delete_group(msg["group_id"])
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "delete_group_failed", str(err))
            return
        connection.send_result(msg["id"], {"deleted": msg["group_id"]})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SET_ANIMAL_GROUP_COMMAND,
            vol.Required("animal_id"): _required_text,
            vol.Optional("group_id"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_set_animal_group(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            await _runtime_data(hass).feature_store.set_animal_group(
                msg["animal_id"],
                msg.get("group_id"),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "set_animal_group_failed", str(err))
            return
        connection.send_result(
            msg["id"],
            {"animal_id": msg["animal_id"], "group_id": msg.get("group_id")},
        )

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _LIST_ATTACHMENTS_COMMAND,
            vol.Optional("animal_id"): _optional_text,
            vol.Optional("event_id"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_list_attachments(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            attachments = await _runtime_data(hass).feature_store.list_attachments(
                animal_id=msg.get("animal_id"),
                event_id=msg.get("event_id"),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "list_attachments_failed", str(err))
            return
        connection.send_result(msg["id"], {"attachments": attachments})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _UPLOAD_ATTACHMENT_COMMAND,
            vol.Required("animal_id"): _required_text,
            vol.Optional("event_id"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_upload_attachment(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        token = secrets.token_urlsafe(32)
        state = hass.data.setdefault(_STATE_KEY, {})
        tokens = state.setdefault("download_tokens", {})
        now = datetime.now(UTC)
        for old_token, record in list(tokens.items()):
            if record["expires_at"] < now:
                tokens.pop(old_token, None)
        tokens[token] = {
            "kind": "upload",
            "animal_id": msg["animal_id"],
            "event_id": msg.get("event_id"),
            "expires_at": now + timedelta(minutes=2),
        }
        connection.send_result(
            msg["id"],
            {
                "url": f"/api/{DOMAIN}/attachments?token={token}",
                "max_attachment_size_bytes": _MAX_ATTACHMENT_SIZE,
            },
        )

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _DELETE_ATTACHMENT_COMMAND,
            vol.Required("attachment_id"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_delete_attachment(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            await _runtime_data(hass).feature_store.delete_attachment(
                msg["attachment_id"]
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "delete_attachment_failed", str(err))
            return
        connection.send_result(msg["id"], {"deleted": msg["attachment_id"]})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _DOWNLOAD_COMMAND,
            vol.Required("kind"): vol.In(
                ("attachment", "json", "backup", "animal_pdf")
            ),
            vol.Optional("resource_id"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_download(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        kind = str(msg["kind"])
        resource_id = msg.get("resource_id")
        if kind in ("attachment", "animal_pdf") and not resource_id:
            connection.send_error(
                msg["id"], "resource_required", "A resource ID is required"
            )
            return
        token = secrets.token_urlsafe(32)
        state = hass.data.setdefault(_STATE_KEY, {})
        tokens = state.setdefault("download_tokens", {})
        now = datetime.now(UTC)
        for old_token, record in list(tokens.items()):
            if record["expires_at"] < now:
                tokens.pop(old_token, None)
        tokens[token] = {
            "kind": kind,
            "resource_id": resource_id,
            "expires_at": now + timedelta(minutes=2),
        }
        if kind == "attachment":
            path = f"/api/{DOMAIN}/attachments/{resource_id}"
        elif kind == "json":
            path = f"/api/{DOMAIN}/export/data.json"
        elif kind == "backup":
            path = f"/api/{DOMAIN}/export/backup.zip"
        else:
            path = f"/api/{DOMAIN}/export/animals/{resource_id}/health.pdf"
        connection.send_result(msg["id"], {"url": f"{path}?token={token}"})

    websocket_api.async_register_command(hass, websocket_features)
    websocket_api.async_register_command(hass, websocket_create_group)
    websocket_api.async_register_command(hass, websocket_update_group)
    websocket_api.async_register_command(hass, websocket_delete_group)
    websocket_api.async_register_command(hass, websocket_set_animal_group)
    websocket_api.async_register_command(hass, websocket_list_attachments)
    websocket_api.async_register_command(hass, websocket_upload_attachment)
    websocket_api.async_register_command(hass, websocket_delete_attachment)
    websocket_api.async_register_command(hass, websocket_download)
