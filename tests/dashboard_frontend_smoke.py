from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def read(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"{path} is empty"
    return text


def panel_source() -> str:
    parts = sorted(FRONTEND.glob("animal-health-panel.part*.js"))
    assert parts
    assert [path.name for path in parts] == [
        f"animal-health-panel.part{index:02d}.js"
        for index in range(1, len(parts) + 1)
    ]
    return "".join(read(path) for path in parts)


def runtime_smoke(source: str) -> None:
    harness = r'''
class MockShadowRoot {
  constructor(){this.listeners=new Map();this.innerHTML="";}
  addEventListener(t,l){this.listeners.set(t,l);}
  querySelector(){return null;}
  querySelectorAll(){return [];}
}
globalThis.HTMLElement=class{
  constructor(){this.isConnected=true;this.shadowRoot=null;}
  attachShadow(){this.shadowRoot=new MockShadowRoot();return this.shadowRoot;}
  toggleAttribute(){}
  dispatchEvent(){}
};
globalThis.CustomEvent=class{};
globalThis.customElements={elements:new Map(),get(n){return this.elements.get(n)},define(n,c){this.elements.set(n,c)}};
'''
    checks = r'''
const Panel=customElements.get("animal-health-panel");
if(!Panel)throw new Error("Panel not registered");
const panel=new Panel();
panel.h={language:"de",user:{is_admin:true}};
panel.d={
  version:"0.8.16",
  today:"2026-08-14",
  summary:{active_animals:2,overdue_tasks:0,today_tasks:0,upcoming_tasks:1,pending_tasks:1},
  animals:[
    {id:"AH-1",device_id:"device-1",name:"Tina",species:"Huhn",status:"active",is_archived:false},
    {id:"AH-2",device_id:"device-2",name:"Berta",species:"Huhn",status:"active",is_archived:false}
  ],
  tasks:[{
    id:"TK-1",animal_id:"AH-1",animal_name:"Tina",title:"Doxycyclin",
    task_kind:"medication",is_active:true,recurrence_type:"daily",recurrence_interval:1,
    start_date:"2026-08-13",end_date:null,due_time:"20:00",planned:{medication_name:"Doxycyclin"}
  }],
  occurrences:[{
    id:"OC-DONE",task_id:"TK-1",animal_id:"AH-1",animal_name:"Tina",task_title:"Doxycyclin",
    task_kind:"medication",scheduled_date:"2026-08-14",scheduled_local:"2026-08-14T20:00:00+02:00",
    scheduled_for:"2026-08-14T18:00:00+00:00",status:"completed",is_overdue:false,is_today:false,is_upcoming:false
  }],
  events:[]
};
panel.c={task_kinds:["reminder","weight","medication","vaccination","health_check","care","veterinary_visit"]};
const calendar=panel.calendar();
if(!calendar.includes('data-action="calendar-prev-0816"')||!calendar.includes('data-action="calendar-next-0816"'))throw new Error("Calendar month navigation missing");
if(!calendar.includes('data-action="calendar-today-0816"'))throw new Error("Calendar today navigation missing");
if(!calendar.includes('data-calendar-kind')||!calendar.includes('data-calendar-animal'))throw new Error("Calendar filters missing");
if(!calendar.includes("Doxycyclin"))throw new Error("Virtual recurring medication is missing from calendar");
panel.calendarOffset0816=1;
const nextMonth=panel.calendar();
if(nextMonth===calendar)throw new Error("Calendar month navigation does not change the rendered month");
panel.overviewScope0816="today";
const todayView=panel.overview();
if(!todayView.includes("Heute relevant"))throw new Error("Today relevance heading missing");
if(todayView.includes("innerhalb 24 h"))throw new Error("Legacy 24-hour relevance wording is still rendered");
if(!todayView.includes("Heute ist nichts relevant"))throw new Error("Completed recurring dose is not suppressed for today");
panel.overviewScope0816="week";
const weekView=panel.overview();
if(!weekView.includes("Morgen relevant"))throw new Error("Tomorrow relevance group missing");
if(!weekView.includes("Doxycyclin"))throw new Error("Tomorrow's virtual recurring medication is missing");
panel.overviewScope0816="month";
const monthView=panel.overview();
if(!monthView.includes("Nächste Woche")||!monthView.includes("Rest diesen Monat"))throw new Error("Monthly relevance grouping missing");
console.log("Animal Health 0.8.16 dashboard runtime validation passed");
'''
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(harness)
        file.write(source)
        file.write(checks)
        file.flush()
        subprocess.run(["node", file.name], check=True)


def main() -> None:
    source = panel_source()
    manifest = json.loads(read(INTEGRATION / "manifest.json"))
    assert manifest["version"] == "0.8.16"
    assert 'const V="0.8.16",D="animal_health"' in source
    assert 'p?.mode==="weight"?`${D}/v083/ai/analyze`:type' in source
    assert 'p?.mode==="weight"?`${D}/v088/ai/analyze`:type' not in source

    for path in sorted(INTEGRATION.glob("*.py")):
        ast.parse(read(path))

    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(source)
        file.flush()
        subprocess.run(["node", "--check", file.name], check=True)

    backend083 = read(INTEGRATION / "v083_features.py")
    backend084 = read(INTEGRATION / "v084_features.py")
    backend086 = read(INTEGRATION / "v086_features.py")
    backend088 = read(INTEGRATION / "v088_features.py")
    panel_backend = read(INTEGRATION / "panel.py")
    combined = "\n".join((source, backend083, backend084, backend086, backend088, panel_backend))
    for marker in (
        "v083/ai/analyze",
        "v086/ai/analyze",
        "v088/ai/analyze",
        "WEIGHT-LIST COMPLETENESS RULES",
        "animal_v083_metadata",
        "animal_group_v083_metadata",
        "animal_custom_values",
        "Tiere keiner Tiergruppe zuordnen",
        "distinctive_features",
        "data-combo083",
        "show_off_label",
        "applyAITaskDraft083",
        "cropOverlay083",
        "v084/history_suggestions",
        "v084/diagnostics",
        "v084/reset_activity",
        "Datenbankdiagnose",
        "Verlaufs- und Aufgabendaten zurücksetzen",
        "animal-health-brand.png",
        "aiBatchSummary086",
        "aiBatchCommon086",
        "ai-product-086",
        "ai-symptom-086",
        "prepareBatchAssociations0812",
        "fuzzyAnimalMatch0813",
        "manual_animal_selection0813",
        "calendar-prev-0816",
        "calendar-next-0816",
        "data-calendar-kind",
        "data-calendar-animal",
        "data-overview-scope",
        "virtualRelevantItems0816",
        "todayRelevantItems0816",
        "Heute relevant",
        "Morgen relevant",
        "Nächste Woche",
        "Rest diesen Monat",
    ):
        assert marker in combined, marker

    runtime_smoke(source)
    print("Animal Health 0.8.16 dashboard frontend validation passed")


if __name__ == "__main__":
    main()
