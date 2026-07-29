from __future__ import annotations

import json
from pathlib import Path

from homeassistant.components.frontend import (
    async_register_built_in_panel,
    async_remove_panel,
)
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PANEL_URL_PATH = "animal-health"
PANEL_ELEMENT_NAME = "animal-health-panel"
PANEL_STATIC_URL = f"/api/{DOMAIN}/frontend"
_PANEL_STATE_KEY = f"{DOMAIN}_panel"


def _integration_version() -> str:
    manifest_path = Path(__file__).with_name("manifest.json")
    with manifest_path.open(encoding="utf-8") as file:
        return str(json.load(file)["version"])


INTEGRATION_VERSION = _integration_version()


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register the Animal Health frontend panel and its static assets."""
    state = hass.data.setdefault(_PANEL_STATE_KEY, {})
    if not state.get("static_path_registered"):
        frontend_path = Path(__file__).parent / "frontend"
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    PANEL_STATIC_URL,
                    str(frontend_path),
                    cache_headers=False,
                )
            ]
        )
        state["static_path_registered"] = True

    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title="Animal Health",
        sidebar_icon="mdi:paw",
        frontend_url_path=PANEL_URL_PATH,
        config={
            "_panel_custom": {
                "name": PANEL_ELEMENT_NAME,
                "module_url": (
                    f"{PANEL_STATIC_URL}/animal-health-panel.js"
                    f"?v={INTEGRATION_VERSION}"
                ),
                "embed_iframe": False,
                "trust_external": False,
                "config": {
                    "version": INTEGRATION_VERSION,
                },
            }
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
