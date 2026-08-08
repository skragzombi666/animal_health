from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.helpers.http import KEY_HASS

from . import feature_api

_TOKEN_RETRY_WINDOW = timedelta(minutes=15)


def _consume_transfer_token(
    request: web.Request,
    expected_kind: str,
    resource_id: str | None = None,
) -> dict[str, Any]:
    """Validate a transfer token without consuming it on the first HTTP request.

    Android WebView/DownloadManager may retry a download or perform more than one
    HTTP request for the same URL. Keeping the unguessable token valid for a short
    window makes JSON, backup, PDF and attachment downloads retry-safe while still
    retaining a bounded lifetime.
    """
    hass: HomeAssistant = request.app[KEY_HASS]
    token = request.query.get("token", "")
    state = hass.data.setdefault(feature_api._STATE_KEY, {})
    tokens = state.setdefault("download_tokens", {})
    record = tokens.get(token)
    if record is None:
        raise web.HTTPUnauthorized()
    now = datetime.now(UTC)
    if now > record["expires_at"]:
        tokens.pop(token, None)
        raise web.HTTPUnauthorized()
    if record["kind"] != expected_kind:
        raise web.HTTPForbidden()
    if resource_id is not None and record.get("resource_id") != resource_id:
        raise web.HTTPForbidden()
    record["expires_at"] = now + _TOKEN_RETRY_WINDOW
    return record


def apply_download_stabilization() -> None:
    """Make signed transfer URLs retry-safe for Android downloads."""
    feature_api._consume_transfer_token = _consume_transfer_token
