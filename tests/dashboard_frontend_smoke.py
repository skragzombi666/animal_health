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
  version: "0.7.2",
  today: "2026-08-06",
  summary: {active_animals: 1, overdue_tasks: 0, today_tasks: 0, pending_tasks: 0},
  animals: [{
    id: "AH-HEN", device_id: "device-hen", name: "BBQ", species: "Huhn",
    breed: "", status: "active", is_archived: false,
    latest_weight: {original_value: 2.5, original_unit: "kg"},
  }],
  tasks: [{
    id: "TASK-ONCE", title: "Erledigte Einmalserie", task_kind: "reminder",
    recurrence_type: "once", is_active: true, animal_name: "BBQ",
  }],
  occurrences: [{
    id: "OCC-DONE", task_id: "TASK-ONCE", task_title: "Erledigte Einmalserie",
    task_kind: "reminder", animal_id: "AH-HEN", animal_name: "BBQ",
    status: "completed", scheduled_local: "2026-08-06T11:00:00+02:00",
    is_overdue: false, is_today: false, is_upcoming: false,
  }],
  events: [],
};
panel.h = {language: "de"};
panel.c = {
  animal_sexes: [], animal_statuses: ["active"],
  species: [{id: "chicken", name_de: "Huhn", name_en: "Chicken", aliases: ["Haushuhn"]}],
  breeds: [], task_kinds: ["reminder"], weight_units: ["kg"], dose_units: ["mg"],
  administration_routes: [], symptoms: ["reduced_appetite", "other"],
  symptom_severities: ["moderate"], vaccination_targets: [],
  health_check_results: ["normal"], medicine_names: [], vaccine_names: [],
};
panel.features = {
  groups: [{id: "GR-CHICKIES", name: "Chickies", species: "chicken", animal_count: 1}],
  memberships: {"AH-HEN": "GR-CHICKIES"}, max_attachment_size_bytes: 15728640,
};
panel.decorateFeatures();
panel.connectedCallback();
for (const eventType of ["click", "input", "change", "submit"]) {
  if (!panel.shadowRoot.listeners.has(eventType)) throw new Error(`Missing ${eventType} listener`);
}
panel.shadowRoot.listeners.get("click")({composedPath: () => [{dataset: {action: "create-animal"}}]});
if (panel.modal?.type !== "create-animal") throw new Error("Create-animal dialog failed");
panel.shadowRoot.listeners.get("input")({composedPath: () => [{dataset: {filter: ""}, value: "hen"}]});
if (panel.filter !== "hen") throw new Error("Search filter failed");
if (panel.l("reduced_appetite") !== "Verminderter Appetit") throw new Error("German symptom localization failed");
panel.modal = {type: "create-group"};
const groupForm = panel.form();
if (!groupForm.includes('<select name="species" required>')) throw new Error("Group species is not a required select");
if (groupForm.includes('name="species" type="text"')) throw new Error("Group species is still free text");
panel.modal = {type: "create-task", animalId: "AH-HEN"};
if (!panel.form().includes('value="device-hen" checked')) throw new Error("Current animal is not preselected for tasks");
panel.view = "animals";
panel.groupFilter = "GR-CHICKIES";
panel.modal = null;
panel.handleClick({composedPath: () => [{dataset: {action: "create-animal"}}]});
if (panel.modal?.groupId !== "GR-CHICKIES") throw new Error("Current group is not carried into animal creation");
const groupedAnimalForm = panel.form();
if (!groupedAnimalForm.includes('value="GR-CHICKIES" selected')) throw new Error("Current group is not selected");
if (!groupedAnimalForm.includes('name="species" type="text" value="Huhn"')) throw new Error("Group species is not prefilled");
const weightInput = {value: "2.5", focus() {}};
panel.shadowRoot.querySelector = selector => selector.includes('input[name="weight"]') ? weightInput : selector.includes('select[name="weight_unit"]') ? {value: "kg"} : null;
panel.handleClick({composedPath: () => [{dataset: {action: "weight-step", delta: "1"}}]});
if (weightInput.value !== "2.51") throw new Error(`Weight rounding failed: ${weightInput.value}`);
const taskHtml = panel.tasks();
if ((taskHtml.match(/data-action="toggle"/g) || []).length !== 0) throw new Error("Completed one-off task still has an activation toggle");
if (panel.speciesIcon("chicken") !== "mdi:bird") throw new Error("Species icon mapping failed");
if (!panel.overview().includes('data-action="edit-group"')) throw new Error("Group edit action is missing");
console.log("Animal Health 0.7.2 dashboard runtime validation passed");
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

    assert manifest["version"] == "0.7.2"
    assert 'const V="0.7.2",D="animal_health"' in panel
    assert "Verminderter Appetit" in panel
    assert "response.blob()" in panel
    assert "link.download=filename" in panel
    assert "URL.createObjectURL(blob)" in panel
    assert "toFixed(decimals)" in panel
    assert 'class="brand"' in panel
    assert ".brand span{display:none}" in panel
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

    print("Animal Health 0.7.2 dashboard frontend validation passed")


if __name__ == "__main__":
    main()
