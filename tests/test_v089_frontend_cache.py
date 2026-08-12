from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"
PANEL_BACKEND = ROOT / "custom_components" / "animal_health" / "panel.py"


def test_registered_panel_class_is_refreshed_in_place() -> None:
    source = (FRONTEND / "animal-health-panel.part07.js").read_text(encoding="utf-8")
    start = source.index('const AH_REGISTERED_PANEL=customElements.get("animal-health-panel")')
    registration = source[start:]
    harness = r'''
class HTMLElement {}
class OldPanel extends HTMLElement {}
OldPanel.prototype.marker=function(){return "old"};
globalThis.customElements={
  elements:new Map([["animal-health-panel",OldPanel]]),
  get(name){return this.elements.get(name)},
  define(name,value){this.elements.set(name,value)}
};
class AnimalHealthPanel extends HTMLElement {}
AnimalHealthPanel.prototype.marker=function(){return "new"};
'''
    checks = r'''
if(customElements.get("animal-health-panel")!==OldPanel)throw new Error("registered class was replaced");
if(AnimalHealthPanel!==OldPanel)throw new Error("module did not rebind to registered class");
if(new OldPanel().marker()!=="new")throw new Error("registered prototype did not receive new base methods");
'''
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(harness)
        file.write(registration)
        file.write(checks)
        file.flush()
        subprocess.run(["node", file.name], check=True)


def test_frontend_assets_are_not_cached() -> None:
    source = PANEL_BACKEND.read_text(encoding="utf-8")
    assert '"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"' in source
    assert '"Pragma": "no-cache"' in source
    assert '"Expires": "0"' in source
    assert "FRONTEND_REVISION" in source
    assert "?v={INTEGRATION_VERSION}-{FRONTEND_REVISION}" in source


def test_mismatch_has_one_shot_cache_busting_reload() -> None:
    source = (FRONTEND / "animal-health-panel.part30.js").read_text(encoding="utf-8")
    assert "sessionStorage.getItem(key)===target" in source
    assert "sessionStorage.setItem(key,target)" in source
    assert 'url.searchParams.set("_animal_health_frontend",target)' in source
    assert "window.location.replace(url.toString())" in source
    assert "backendVersion&&backendVersion!==V" in source
