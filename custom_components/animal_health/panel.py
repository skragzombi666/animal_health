from __future__ import annotations

import hashlib
import json
import re
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
PANEL_BRAND_URL = f"/api/{DOMAIN}/frontend/animal-health-brand.png"
PANEL_LEGACY_BRAND_URL = f"/api/{DOMAIN}/frontend/animal-health-brand.svg"
_PANEL_STATE_KEY = f"{DOMAIN}_panel"
_FRONTEND_DIR = Path(__file__).parent / "frontend"
_FRONTEND_BUNDLE_PATH = _FRONTEND_DIR / "dist" / "animal-health-panel.js"
_BRAND_MASTER_PATH = Path(__file__).parent / "brand" / "icon.png"
_BRAND_UI_PATH = _FRONTEND_DIR / "animal-health-brand.svg"
_NO_STORE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}
_BRAND_CACHE_HEADERS = {
    "Cache-Control": "public, max-age=31536000, immutable",
}


def _integration_version() -> str:
    manifest_path = Path(__file__).with_name("manifest.json")
    with manifest_path.open(encoding="utf-8") as file:
        return str(json.load(file)["version"])


def _frontend_source() -> str:
    if not _FRONTEND_BUNDLE_PATH.is_file():
        raise RuntimeError("Animal Health frontend bundle is missing")
    source = _FRONTEND_BUNDLE_PATH.read_text(encoding="utf-8")
    version = _integration_version()
    return re.sub(
        r'const V="[^"]+",D="animal_health";',
        f'const V="{version}",D="animal_health";',
        source,
        count=1,
    )


def _frontend_revision() -> str:
    source = _frontend_source().encode("utf-8")
    return hashlib.sha256(source).hexdigest()[:12]


def _brand_revision() -> str:
    return hashlib.sha256(_BRAND_UI_PATH.read_bytes()).hexdigest()[:12]


INTEGRATION_VERSION = _integration_version()
FRONTEND_REVISION = _frontend_revision()
BRAND_REVISION = _brand_revision()


class AnimalHealthPanelView(HomeAssistantView):
    """Serve the bundled Animal Health JavaScript module."""

    url = PANEL_MODULE_URL
    name = "api:animal_health:frontend"
    requires_auth = False

    async def get(self, request: web.Request) -> web.Response:
        """Return the checked-in frontend bundle."""
        source = await request.app[KEY_HASS].async_add_executor_job(_frontend_source)
        return web.Response(
            text=source,
            content_type="application/javascript",
            headers=_NO_STORE_HEADERS,
        )


class AnimalHealthBrandView(HomeAssistantView):
    """Serve the lightweight derivative of the canonical Animal Health logo."""

    url = PANEL_BRAND_URL
    name = "api:animal_health:brand"
    requires_auth = False

    async def get(self, request: web.Request) -> web.Response:
        source = await request.app[KEY_HASS].async_add_executor_job(
            _BRAND_UI_PATH.read_text,
            "utf-8",
        )
        return web.Response(
            text=source,
            content_type="image/svg+xml",
            headers=_BRAND_CACHE_HEADERS,
        )


class AnimalHealthLegacyBrandView(HomeAssistantView):
    """Keep the previous SVG endpoint available for cached older frontends."""

    url = PANEL_LEGACY_BRAND_URL
    name = f"api:{DOMAIN}:brand_legacy"
    requires_auth = False

    async def get(self, request: web.Request) -> web.Response:
        source = await request.app[KEY_HASS].async_add_executor_job(
            _BRAND_UI_PATH.read_text,
            "utf-8",
        )
        return web.Response(
            text=source,
            content_type="image/svg+xml",
            headers=_BRAND_CACHE_HEADERS,
        )


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register the Animal Health frontend panel and module endpoint."""
    from .v0937_features import apply_v0937_patches

    apply_v0937_patches()
    state = hass.data.setdefault(_PANEL_STATE_KEY, {})
    if not state.get("frontend_view_registered"):
        hass.http.register_view(AnimalHealthPanelView())
        hass.http.register_view(AnimalHealthBrandView())
        hass.http.register_view(AnimalHealthLegacyBrandView())
        state["frontend_view_registered"] = True

    brand_url = f"{PANEL_BRAND_URL}?v={INTEGRATION_VERSION}-{BRAND_REVISION}"
    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title="Animal Health",
        sidebar_icon="mdi:paw",
        frontend_url_path=PANEL_URL_PATH,
        config={
            "version": INTEGRATION_VERSION,
            "brand_url": brand_url,
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
