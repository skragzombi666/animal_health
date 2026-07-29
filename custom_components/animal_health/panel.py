from __future__ import annotations

import hashlib
import json
from pathlib import Path

from aiohttp import web

from homeassistant.components.frontend import (
    async_register_built_in_panel,
    async_remove_panel,
)
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers.http import KEY_HASS

from .const import DOMAIN

PANEL_URL_PATH = "animal-health"
PANEL_ELEMENT_NAME = "animal-health-panel"
PANEL_MODULE_URL = f"/api/{DOMAIN}/frontend/animal-health-panel.js"
_PANEL_STATE_KEY = f"{DOMAIN}_panel"
_FRONTEND_DIR = Path(__file__).parent / "frontend"
_FRONTEND_PARTS = tuple(sorted(_FRONTEND_DIR.glob("animal-health-panel.part*.js")))


def _integration_version() -> str:
    manifest_path = Path(__file__).with_name("manifest.json")
    with manifest_path.open(encoding="utf-8") as file:
        return str(json.load(file)["version"])


def _frontend_source() -> str:
    if not _FRONTEND_PARTS:
        raise RuntimeError("Animal Health frontend source parts are missing")
    return "".join(path.read_text(encoding="utf-8") for path in _FRONTEND_PARTS)


def _frontend_revision() -> str:
    source = _frontend_source().encode("utf-8")
    return hashlib.sha256(source).hexdigest()[:12]


INTEGRATION_VERSION = _integration_version()
FRONTEND_REVISION = _frontend_revision()


class AnimalHealthPanelView(HomeAssistantView):
    """Serve the bundled Animal Health JavaScript module."""

    url = PANEL_MODULE_URL
    name = "api:animal_health:frontend"
    requires_auth = False

    async def get(self, request: web.Request) -> web.Response:
        """Return the assembled frontend module."""
        source = await request.app[KEY_HASS].async_add_executor_job(_frontend_source)
        return web.Response(
            text=source,
            content_type="application/javascript",
            headers={"Cache-Control": "no-cache"},
        )


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register the Animal Health frontend panel and module endpoint."""
    state = hass.data.setdefault(_PANEL_STATE_KEY, {})
    if not state.get("frontend_view_registered"):
        hass.http.register_view(AnimalHealthPanelView())
        state["frontend_view_registered"] = True

    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title="Animal Health",
        sidebar_icon="mdi:paw",
        frontend_url_path=PANEL_URL_PATH,
        config={
            "version": INTEGRATION_VERSION,
            "_panel_custom": {
                "name": PANEL_ELEMENT_NAME,
                "module_url": (
                    f"{PANEL_MODULE_URL}?v={INTEGRATION_VERSION}-{FRONTEND_REVISION}"
                ),
                "embed_iframe": False,
                "trust_external": False,
            },
        },
        require_admin=False,
        update=True,
    )
    state["panel_registered"] = True


def async_unregister_panel(hass: HomeAssistant) -> None:
    """Remove the Animal Health sidebar panel."""
    state = hass.data.setdefault(_PANEL_STATE_KEY, {})
    if state.get("panel_registered"):
        async_remove_panel(hass, PANEL_URL_PATH)
        state["panel_registered"] = False
