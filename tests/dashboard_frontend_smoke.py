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


def runtime_smoke(source: str, version: str) -> None:
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
  addEventListener(){}
};
globalThis.CustomEvent=class{};
globalThis.customElements={elements:new Map(),get(n){return this.elements.get(n)},define(n,c){this.elements.set(n,c)}};
const localValues=new Map();
globalThis.localStorage={getItem:key=>localValues.has(key)?localValues.get(key):null,setItem:(key,value)=>localValues.set(key,String(value))};
'''
    checks = r'''
const Panel=customElements.get("animal-health-panel");
if(!Panel)throw new Error("Panel not registered");
const panel=new Panel();
panel.h={language:"de",user:{is_admin:true}};
panel.d={
 version:"__VERSION__",today:"2026-08-19",
 summary:{active_animals:1,overdue_tasks:1,today_tasks:1,upcoming_tasks:2,pending_tasks:3},
 animals:[{id:"AH-1",device_id:"device-1",name:"Tina",species:"chicken",status:"active",is_archived:false,group_id:"GR-1",group_name:"Hühner",tag_ids:[],tags:[]}],
 tasks:[
  {id:"TK-REQ",animal_id:"AH-1",animal_name:"Tina",title:"Pflichtgewicht",task_kind:"weight",is_active:true,recurrence_type:"daily",recurrence_interval:1,start_date:"2026-08-17",end_date:null,due_time:null,confirmation_mode:"required",overdue_count:1,next_pending_local:"2026-08-17T00:00:00+02:00",planned:{measurement:"weight"}},
  {id:"TK-ROUT",animal_id:"AH-1",animal_name:"Tina",title:"Routinepflege",task_kind:"care",is_active:true,recurrence_type:"daily",recurrence_interval:1,start_date:"2026-08-17",end_date:null,due_time:null,confirmation_mode:"routine",overdue_count:0,not_documented_count:1,next_pending_local:"2026-08-19T00:00:00+02:00",planned:{care_action:"Pflege"}},
  {id:"TK-WEEK",animal_id:"AH-1",animal_name:"Tina",title:"Wochenkontrolle",task_kind:"health_check",is_active:true,recurrence_type:"weekly",recurrence_interval:1,start_date:"2026-08-19",end_date:null,due_time:null,confirmation_mode:"required",overdue_count:0,next_pending_local:"2026-08-19T00:00:00+02:00",planned:{check_focus:"Allgemeinzustand"}}
 ],
 occurrences:[
  {id:"OC-REQ",task_id:"TK-REQ",animal_id:"AH-1",animal_name:"Tina",task_title:"Pflichtgewicht",task_kind:"weight",scheduled_date:"2026-08-17",scheduled_local:"2026-08-17T00:00:00+02:00",scheduled_for:"2026-08-16T22:00:00+00:00",status:"pending",confirmation_mode:"required",is_overdue:true,is_today:false,is_upcoming:false},
  {id:"OC-ROUT",task_id:"TK-ROUT",animal_id:"AH-1",animal_name:"Tina",task_title:"Routinepflege",task_kind:"care",scheduled_date:"2026-08-17",scheduled_local:"2026-08-17T00:00:00+02:00",scheduled_for:"2026-08-16T22:00:00+00:00",status:"not_documented",confirmation_mode:"routine",is_not_documented:true,is_overdue:false,is_today:false,is_upcoming:false},
  {id:"OC-ROUT-NOW",task_id:"TK-ROUT",animal_id:"AH-1",animal_name:"Tina",task_title:"Routinepflege",task_kind:"care",scheduled_date:"2026-08-19",scheduled_local:"2026-08-19T00:00:00+02:00",scheduled_for:"2026-08-18T22:00:00+00:00",status:"pending",confirmation_mode:"routine",is_overdue:false,is_today:true,is_upcoming:false},
  {id:"OC-WEEK",task_id:"TK-WEEK",animal_id:"AH-1",animal_name:"Tina",task_title:"Wochenkontrolle",task_kind:"health_check",scheduled_date:"2026-08-19",scheduled_local:"2026-08-19T00:00:00+02:00",scheduled_for:"2026-08-18T22:00:00+00:00",status:"pending",confirmation_mode:"required",is_overdue:false,is_today:true,is_upcoming:false}
 ],events:[]
};
panel.features={groups:[{id:"GR-1",name:"Hühner",species:"chicken",animal_count:1,is_archived:false}],memberships:{"AH-1":"GR-1"}};
panel.v080={tags:[],tag_memberships:{},profiles:{}};
panel.v081={settings:{week_start:"monday"},group_events:[],group_tasks:[]};
panel.profileUrls={};panel.aiStatus={entities:[],stt_entities:[]};
panel.c={task_kinds:["reminder","weight","medication","vaccination","health_check","care","veterinary_visit"],dose_units:["mg","dose"],administration_routes:["oral"],species:[{id:"chicken",name_de:"Huhn",name_en:"Chicken",aliases:[]}]};
panel.v083={medicines:[],custom_values:[],animal_metadata:{},group_metadata:{}};panel.v084={suggestions:{}};panel.v0817={off_label_enabled:false,medications:[]};
const calendar=panel.calendar();
if(!calendar.includes("Nicht einzeln dokumentiert")||!calendar.includes("Überfällig"))throw new Error("Confirmation legend missing");
if(!calendar.includes('calendarState-overdue')||!calendar.includes('data-id="OC-REQ"'))throw new Error("Required overdue item missing");
if(!calendar.includes('calendarState-undocumented')||!calendar.includes('data-id="OC-ROUT"'))throw new Error("Undocumented routine item missing");
if(!calendar.includes('calendarState-due')||!calendar.includes('data-id="OC-WEEK"'))throw new Error("Current weekly item missing");
const overview=panel.overview();
if(!overview.includes("Anstehend")||!overview.includes("Pflichtgewicht")||!overview.includes("Wochenkontrolle"))throw new Error("Dynamic relevance missing");
if(!overview.includes("Überfällig")||!overview.includes("Diese Woche"))throw new Error("Period buckets missing");
const tasks=panel.tasks();
if(!tasks.includes("Aufgaben & Serien")||!tasks.includes("Bestätigung erforderlich")||!tasks.includes("Routine"))throw new Error("Confirmation modes missing from task management");
const field=panel.confirmationField010("routine");
if(!field.includes('name="confirmation_mode"')||!field.includes("Routine ohne Einzelbestätigung")||!field.includes('value="routine" selected'))throw new Error("Confirmation selector missing");
const weekly=panel.periodBounds010(panel.task("TK-WEEK"),"2026-08-19");
if(weekly.start!=="2026-08-17"||weekly.end!=="2026-08-23")throw new Error("Weekly period is not calendar-week based");
console.log("Animal Health dashboard runtime validation passed");
'''.replace("__VERSION__", version)
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(harness)
        file.write(source)
        file.write(checks)
        file.flush()
        subprocess.run(["node", file.name], check=True)


def main() -> None:
    source = panel_source()
    manifest = json.loads(read(INTEGRATION / "manifest.json"))
    version = manifest["version"]
    assert 'const V="0.9.41",D="animal_health"' in source
    for path in sorted(INTEGRATION.glob("*.py")):
        ast.parse(read(path))
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(source)
        file.flush()
        subprocess.run(["node", "--check", file.name], check=True)
    for marker in (
        "confirmationMode010",
        "not_documented",
        "calendarState-undocumented",
        "calendarState-overdue",
        "homeAnimalsCard091",
        "quickCaptureCompact091",
        "animalCaptureIcons090A7",
        "upcomingLinks096",
    ):
        assert marker in source, marker
    runtime_smoke(source, version)
    print(f"Animal Health {version} dashboard frontend validation passed")


if __name__ == "__main__":
    main()
