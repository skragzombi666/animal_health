from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def _read(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    assert content.strip(), f"{path} is empty"
    return content


def _panel_source() -> str:
    parts = sorted(FRONTEND.glob("animal-health-panel.part*.js"))
    assert parts
    assert [path.name for path in parts] == [
        f"animal-health-panel.part{index:02d}.js"
        for index in range(1, len(parts) + 1)
    ]
    return "".join(_read(path) for path in parts)


def _runtime_smoke(panel_source: str) -> None:
    harness = r'''
class MockShadowRoot {
  constructor() { this.listeners = new Map(); this.innerHTML = ""; }
  addEventListener(type, listener) { this.listeners.set(type, listener); }
  querySelector() { return null; }
}
globalThis.HTMLElement = class {
  constructor() { this.isConnected = true; this.shadowRoot = null; }
  attachShadow() { this.shadowRoot = new MockShadowRoot(); return this.shadowRoot; }
  toggleAttribute() {}
  dispatchEvent() {}
};
globalThis.CustomEvent = class {};
globalThis.customElements = {
  elements: new Map(),
  get(name) { return this.elements.get(name); },
  define(name, constructor) { this.elements.set(name, constructor); },
};
'''
    assertions = r'''
const Panel = customElements.get("animal-health-panel");
if (!Panel) throw new Error("Panel element was not registered");
const panel = new Panel();
panel.d = {
  version: "0.7.1",
  today: "2026-07-29",
  summary: {active_animals: 0, overdue_tasks: 0, today_tasks: 0, pending_tasks: 0},
  animals: [], tasks: [], occurrences: [], events: [],
};
panel.c = {
  animal_sexes: [], animal_statuses: ["active"], species: [], breeds: [],
  task_kinds: ["reminder"], weight_units: ["kg"], dose_units: ["mg"],
  administration_routes: [], symptoms: ["other"],
  symptom_severities: ["moderate"], vaccination_targets: [],
  health_check_results: ["normal"], medicine_names: [], vaccine_names: [],
};
panel.features = {groups: [], memberships: {}, max_attachment_size_bytes: 15728640};
panel.connectedCallback();
for (const eventType of ["click", "input", "change", "submit"]) {
  if (!panel.shadowRoot.listeners.has(eventType)) throw new Error(`Missing ${eventType} listener`);
}
panel.shadowRoot.listeners.get("click")({composedPath: () => [{dataset: {action: "create-animal"}}]});
if (panel.modal?.type !== "create-animal") throw new Error("Create-animal dialog failed");
panel.shadowRoot.listeners.get("input")({composedPath: () => [{dataset: {filter: ""}, value: "hen"}]});
if (panel.filter !== "hen") throw new Error("Search filter failed");
console.log("Animal Health 0.7.1 dashboard runtime validation passed");
'''
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(harness)
        file.write(panel_source)
        file.write(assertions)
        file.flush()
        subprocess.run(["node", file.name], check=True)


def main() -> None:
    panel = _panel_source()
    manifest = json.loads(_read(INTEGRATION / "manifest.json"))
    python_files = (
        INTEGRATION / "__init__.py",
        INTEGRATION / "panel.py",
        INTEGRATION / "dashboard_api.py",
        INTEGRATION / "feature_store.py",
        INTEGRATION / "feature_api.py",
        INTEGRATION / "exports.py",
        INTEGRATION / "runtime.py",
    )
    for path in python_files:
        ast.parse(_read(path))

    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(panel)
        file.flush()
        subprocess.run(["node", "--check", file.name], check=True)

    _runtime_smoke(panel)

    assert manifest["version"] == "0.7.1"
    assert 'const V="0.7.1",D="animal_health"' in panel
    assert "mdi:plus-circle-outline" in panel
    assert "mdi:paw-plus" not in panel
    assert "content_base64" not in panel
    assert "fetch(target.url" in panel
    assert "hass-toggle-menu" in panel
    assert "animalSwitcher" in panel
    assert "weightStepper" in panel
    assert "emptyNow" in panel
    assert "attachments/upload" in panel
    assert "groups/create" in panel
    assert "export-pdf" in panel
    assert 'shadowRoot.addEventListener("click"' in panel
    assert "shadowRoot.onclick" not in panel
    for command in (
        "${D}/dashboard",
        "${D}/animal_detail",
        "${D}/catalog",
        "${D}/features",
        "${D}/download",
    ):
        assert command in panel
    for service in (
        "create_animal",
        "update_animal",
        "record_weight",
        "record_symptom",
        "create_event",
        "create_record_task",
        "record_task_veterinary_visit",
    ):
        assert service in panel
    for marker in ("http://", "https://", "unpkg", "jsdelivr", "cdnjs"):
        assert marker not in panel.lower()

    print("Animal Health 0.7.1 dashboard frontend validation passed")


if __name__ == "__main__":
    main()
