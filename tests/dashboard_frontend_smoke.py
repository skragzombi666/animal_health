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
panel.h = {language: "de"};
panel.d = {
  version: "0.7.4",
  today: "2026-08-08",
  summary: {active_animals: 1, overdue_tasks: 0, today_tasks: 0, upcoming_tasks: 1, pending_tasks: 1},
  animals: [{id: "AH-1", device_id: "device-1", name: "Curry", species: "Huhn", status: "active", is_archived: false}],
  tasks: [{id: "TK-OFF", title: "Wägen", task_kind: "weight", recurrence_type: "weekly", is_active: false, animal_name: "Curry"}],
  occurrences: [{id: "OC-1", task_id: "TK-OFF", task_title: "Wägen", task_kind: "weight", animal_id: "AH-1", animal_name: "Curry", status: "pending", scheduled_local: "2026-08-09T14:00:00+02:00", scheduled_date: "2026-08-09", is_overdue: false, is_today: false, is_upcoming: true}],
  events: [
    {id: "EV-1", animal_id: "AH-1", animal_name: "Curry", event_type: "symptom", title: "diarrhea", occurred_at: "2026-08-08T13:21:00+02:00", notes: "Test"},
    {id: "EV-2", animal_id: "AH-1", animal_name: "Curry", event_type: "status_change", title: "status_change", occurred_at: "2026-08-08T15:29:00+02:00"},
  ],
};
panel.c = {animal_sexes: ["male", "female", "other"], species: [{id: "chicken", name_de: "Huhn", name_en: "Chicken", aliases: []}], breeds: [], task_kinds: ["weight"], weight_units: ["kg"], dose_units: [], administration_routes: [], symptoms: ["diarrhea"], symptom_severities: [], vaccination_targets: [], health_check_results: [], medicine_names: [], vaccine_names: []};
panel.features = {groups: [], memberships: {}, max_attachment_size_bytes: 15728640};
panel.groupLifecycle = {archived: {}};

panel.applyTaskVisibility(panel.d, panel.d.tasks);
if (panel.d.occurrences.length !== 0) throw new Error("Inactive task occurrence remains visible");
if (panel.d.summary.pending_tasks !== 0 || panel.d.summary.upcoming_tasks !== 0) throw new Error("Inactive task still affects summary counters");

const reactivated = {
  occurrences: [{id: "OC-2", task_id: "TK-ON", status: "pending", is_overdue: false, is_today: true, is_upcoming: false}],
  summary: {pending_tasks: 1, overdue_tasks: 0, today_tasks: 1, upcoming_tasks: 0},
};
panel.applyTaskVisibility(reactivated, [{id: "TK-ON", is_active: true}]);
if (reactivated.occurrences.length !== 1) throw new Error("Reactivated task occurrence was hidden");

if (panel.eventTitle(panel.d.events[0]) !== "Durchfall") throw new Error("Symptom event title is not localized");
if (panel.eventTitle(panel.d.events[1]) !== "Statusänderung") throw new Error("Status-change event title is not localized");
const row = panel.eventRow(panel.d.events[0]);
if (!row.includes('data-action="event-detail"') || !row.includes('data-id="EV-1"')) throw new Error("Timeline event is not clickable");
panel.modal = {type: "event-detail", eventId: "EV-1"};
const detail = panel.form();
if (!detail.includes("Durchfall") || !detail.includes("Curry") || !detail.includes('data-action="animal-detail"')) throw new Error("Event detail modal is incomplete");

if (!panel.fileFields().includes('data-action="take-photo"')) throw new Error("Direct camera action is missing");
if (!panel.speciesVisual("chicken").includes("🐔")) throw new Error("Chicken visual regressed");
console.log("Animal Health 0.7.4 dashboard runtime validation passed");
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
    for path in (
        INTEGRATION / "__init__.py",
        INTEGRATION / "panel.py",
        INTEGRATION / "dashboard_api.py",
        INTEGRATION / "feature_store.py",
        INTEGRATION / "feature_api.py",
        INTEGRATION / "download_stabilization.py",
        INTEGRATION / "group_lifecycle.py",
        INTEGRATION / "catalog.py",
        INTEGRATION / "exports.py",
        INTEGRATION / "runtime.py",
    ):
        ast.parse(_read(path))

    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(panel)
        file.flush()
        subprocess.run(["node", "--check", file.name], check=True)

    _runtime_smoke(panel)

    assert manifest["version"] == "0.7.4"
    assert 'const V="0.7.4",D="animal_health"' in panel
    for marker in (
        "animal-health-brand.svg",
        "navigator.mediaDevices.getUserMedia",
        "attachmentPreview",
        "groups/archive",
        "groups/restore",
        "preparingDownload",
        "applyTaskVisibility",
        'data-action=\\"event-detail\\"',
        "eventDetails",
    ):
        assert marker in panel
    for external in ("http://", "https://", "unpkg", "jsdelivr", "cdnjs"):
        assert external not in panel.lower()

    print("Animal Health 0.7.4 dashboard frontend validation passed")


if __name__ == "__main__":
    main()
