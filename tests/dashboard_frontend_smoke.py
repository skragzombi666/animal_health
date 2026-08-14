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
  version:"0.9.0-alpha.1",
  today:"2026-08-14",
  summary:{active_animals:2,overdue_tasks:0,today_tasks:0,upcoming_tasks:1,pending_tasks:1},
  animals:[
    {id:"AH-1",device_id:"device-1",name:"Tina",species:"chicken",status:"active",is_archived:false},
    {id:"AH-2",device_id:"device-2",name:"Berta",species:"chicken",status:"active",is_archived:false}
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
panel.c={
  task_kinds:["reminder","weight","medication","vaccination","health_check","care","veterinary_visit"],
  dose_units:["mcg","mg","g","ul","ml","drop","tablet","dose"],
  administration_routes:["oral"],
  species:[{id:"chicken",name_de:"Huhn",name_en:"Chicken",aliases:[]}]
};
panel.v083={medicines:[{id:"doxy",name:"Doxycare Tabletten",target_species:["chicken"],aliases:[]}],custom_values:[],animal_metadata:{},group_metadata:{}};
panel.v084={suggestions:{medication_name:[]}};
panel.v0817={off_label_enabled:false,medications:[{id:1,name:"Eigene Tropfen",species_id:"chicken",default_unit:"drop",default_route:"oral"}]};
const calendar=panel.calendar();
if(!calendar.includes('data-action="calendar-prev-0816"')||!calendar.includes('data-action="calendar-next-0816"'))throw new Error("Calendar month navigation missing");
if(!calendar.includes('data-action="calendar-today-0816"'))throw new Error("Calendar today navigation missing");
if(!calendar.includes('data-calendar-kind')||!calendar.includes('data-calendar-animal'))throw new Error("Calendar filters missing");
if(!calendar.includes("Doxycyclin"))throw new Error("Virtual recurring medication is missing from calendar");
panel.calendarOffset0816=1;
if(panel.calendar()===calendar)throw new Error("Calendar month navigation does not change the rendered month");
panel.overviewScope0816="today";
const todayView=panel.overview();
if(!todayView.includes("Heute relevant"))throw new Error("Today relevance heading missing");
if(todayView.includes("innerhalb 24 h"))throw new Error("Legacy 24-hour relevance wording is still rendered");
if(!todayView.includes("Heute ist nichts relevant"))throw new Error("Completed recurring dose is not suppressed for today");
panel.overviewScope0816="week";
const weekView=panel.overview();
if(!weekView.includes("Morgen relevant")||!weekView.includes("Doxycyclin"))throw new Error("Weekly virtual recurrence missing");
if(panel.l("tablet")!=="Tablette"||panel.l("drop")!=="Tropfen"||panel.l("ul")!=="µl")throw new Error("Dose-unit localization missing");
if(panel.medicationUnit0817("Doxycare Tabletten")!=="tablet")throw new Error("Tablet default unit inference missing");
if(panel.medicationUnit0817("Eigene Tropfen")!=="drop")throw new Error("Custom medication default unit missing");
panel.medBatch0817={animalId:"AH-1",date:"2026-08-14",time:"17:30",notes:"",mode:"new",items:[
  {product_type:"medication",product_name:"Doxycare Tabletten",dose:"1",dose_unit:"tablet",route:"oral",notes:"",correction_event_id:""},
  {product_type:"medication",product_name:"Eigene Tropfen",dose:"2",dose_unit:"drop",route:"oral",notes:"",correction_event_id:""}
]};
const batch=panel.medicationBatchForm0817();
if(!batch.includes('name="product_name_0"')||!batch.includes('name="product_name_1"'))throw new Error("Multi-medication rows missing");
if(!batch.includes('data-action="med-add-0817"'))throw new Error("Add-medication control missing");
if(!batch.includes("Tablette")||!batch.includes("Tropfen"))throw new Error("Localized dose units missing from medication form");
const events=[
 {id:"EV-1",animal_id:"AH-1",animal_name:"Tina",event_type:"medication",occurred_at:"2026-08-14T15:30:00+00:00",title:"Doxycare Tabletten",notes:null,value:1,unit:"tablet",correction_of_event_id:null,data:{medication_name:"Doxycare Tabletten",route:"oral"}},
 {id:"EV-2",animal_id:"AH-1",animal_name:"Tina",event_type:"medication",occurred_at:"2026-08-14T15:31:00+00:00",title:"Eigene Tropfen",notes:null,value:2,unit:"drop",correction_of_event_id:null,data:{medication_name:"Eigene Tropfen",route:"oral"}}
];
panel.detail={animal:panel.d.animals[0],events,occurrences:[],attachments:[]};
panel.view="animal-detail";
const firstRow=panel.eventRow(events[0]);
if(!firstRow.includes("dayHeader0817")||!firstRow.includes("1 Tablette Doxycare Tabletten"))throw new Error("Compact day-grouped medication history missing");
const secondRow=panel.eventRow(events[1]);
if(secondRow.includes("dayHeader0817"))throw new Error("Day header repeated for same day");
const detail=panel.eventDetail("EV-1");
if(!detail.includes('data-action="med-edit-0817"')||!detail.includes('data-action="med-copy-0817"')||!detail.includes('data-action="med-repeat-0817"'))throw new Error("Medication detail actions missing");
if(detail.includes('data-action="animal-detail"'))throw new Error("Redundant open-animal action still shown inside animal view");
panel.modal={type:"day-detail-0817",day:"2026-08-14",animalId:"AH-1"};
const day=panel.dayDetail0817();
if(!day.includes('data-action="day-repeat-0817"')||!day.includes("Doxycare Tabletten")||!day.includes("Eigene Tropfen"))throw new Error("Daily summary/repeat workflow missing");
console.log("Animal Health 0.9.0-alpha.1 dashboard runtime validation passed");
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
    assert manifest["version"] == "0.9.0-alpha.1"
    assert 'const V="0.9.0-alpha.1",D="animal_health"' in source
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
    backend0817 = read(INTEGRATION / "v0817_features.py")
    patches0817 = read(INTEGRATION / "v0817_patches.py")
    panel_backend = read(INTEGRATION / "panel.py")
    combined = "\n".join((source, backend083, backend084, backend086, backend088, backend0817, patches0817, panel_backend))
    for marker in (
        "v083/ai/analyze",
        "v086/ai/analyze",
        "v088/ai/analyze",
        "WEIGHT-LIST COMPLETENESS RULES",
        "animal_custom_values",
        "Tiere keiner Tiergruppe zuordnen",
        "distinctive_features",
        "data-combo083",
        "applyAITaskDraft083",
        "v084/diagnostics",
        "Datenbankdiagnose",
        "calendar-prev-0816",
        "data-calendar-kind",
        "virtualRelevantItems0816",
        "Heute relevant",
        "v0817_medications",
        "v0817/medications/record",
        "off_label_enabled",
        "medication-batch-0817",
        "med-repeat-0817",
        "med-copy-0817",
        "med-edit-0817",
        "day-repeat-0817",
        "offLabelSetting0817",
        'tablet:["Tablette"',
        'drop:["Tropfen"',
        '"tablet": "Tablette"',
    ):
        assert marker in combined, marker

    runtime_smoke(source)
    print("Animal Health 0.9.0-alpha.1 dashboard frontend validation passed")


if __name__ == "__main__":
    main()
