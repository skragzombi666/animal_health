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
class MockShadowRoot { constructor(){this.listeners=new Map();this.innerHTML="";} addEventListener(t,l){this.listeners.set(t,l);} querySelector(){return null;} }
globalThis.HTMLElement=class{constructor(){this.isConnected=true;this.shadowRoot=null;}attachShadow(){this.shadowRoot=new MockShadowRoot();return this.shadowRoot;}toggleAttribute(){}dispatchEvent(){}};
globalThis.CustomEvent=class{};
globalThis.customElements={elements:new Map(),get(n){return this.elements.get(n)},define(n,c){this.elements.set(n,c)}};
'''
    checks = r'''
const Panel=customElements.get("animal-health-panel");
if(!Panel)throw new Error("Panel not registered");
const panel=new Panel();
panel.h={language:"de"};
panel.d={version:"0.7.5",today:"2026-08-08",summary:{active_animals:1,overdue_tasks:0,today_tasks:0,upcoming_tasks:1,pending_tasks:1},animals:[{id:"AH-1",device_id:"device-1",name:"Curry",species:"Huhn",status:"active",is_archived:false}],tasks:[{id:"TK-OFF",title:"Wägen",task_kind:"weight",recurrence_type:"once",is_active:false,animal_name:"Curry"}],occurrences:[{id:"OC-1",task_id:"TK-OFF",task_title:"Wägen",task_kind:"weight",animal_id:"AH-1",animal_name:"Curry",status:"pending",scheduled_local:"2026-08-09T14:00:00+02:00",scheduled_date:"2026-08-09",is_overdue:false,is_today:false,is_upcoming:true}],events:[{id:"EV-1",animal_id:"AH-1",animal_name:"Curry",event_type:"symptom",title:"diarrhea",occurred_at:"2026-08-08T13:21:00+02:00",notes:"Test"},{id:"EV-2",animal_id:"AH-1",animal_name:"Curry",event_type:"status_change",title:"status_change",occurred_at:"2026-08-08T15:29:00+02:00",data:{previous_status:"active",new_status:"missing"}}]};
panel.c={animal_sexes:["male","female","other"],species:[{id:"chicken",name_de:"Huhn",name_en:"Chicken",aliases:[]}],breeds:[],task_kinds:["weight"],weight_units:["kg"],dose_units:[],administration_routes:[],symptoms:["diarrhea"],symptom_severities:[],vaccination_targets:[],health_check_results:[],medicine_names:[],vaccine_names:[]};
panel.features={groups:[],memberships:{},max_attachment_size_bytes:15728640};panel.groupLifecycle={archived:{}};
panel.applyTaskVisibility(panel.d,panel.d.tasks);
if(panel.d.occurrences.length!==0)throw new Error("Inactive task occurrence remains visible");
if(panel.d.summary.pending_tasks!==0||panel.d.summary.upcoming_tasks!==0)throw new Error("Inactive task still affects summary");
const taskHtml=panel.tasks();
if(!taskHtml.includes("Wägen")||!taskHtml.includes("Deaktiviert")||!taskHtml.includes(">Aktivieren</button>"))throw new Error("Inactive one-off task cannot be reactivated");
const reactivated={occurrences:[{id:"OC-2",task_id:"TK-ON",status:"pending",is_overdue:false,is_today:true,is_upcoming:false}],summary:{pending_tasks:1,overdue_tasks:0,today_tasks:1,upcoming_tasks:0}};
panel.applyTaskVisibility(reactivated,[{id:"TK-ON",is_active:true}]);if(reactivated.occurrences.length!==1)throw new Error("Reactivated task hidden");
if(panel.eventTitle(panel.d.events[0])!=="Durchfall")throw new Error("Diarrhea not localized");
if(panel.eventTitle(panel.d.events[1])!=="Statusänderung")throw new Error("Status change not localized");
const row=panel.eventRow(panel.d.events[0]);if(!row.includes('data-action="event-detail"'))throw new Error("Event row not clickable");
panel.modal={type:"event-detail",eventId:"EV-1"};const detail=panel.form();if(!detail.includes("Durchfall")||!detail.includes("Curry")||!detail.includes('data-action="animal-detail"'))throw new Error("Event details incomplete");
panel.modal={type:"event-detail",eventId:"EV-2"};const statusDetail=panel.form();if(!statusDetail.includes("Vorheriger Status")||!statusDetail.includes("Aktiv")||!statusDetail.includes("Neuer Status")||!statusDetail.includes("Vermisst"))throw new Error("Status transition details missing");
panel.loadDetail=id=>{panel._openedAnimal=id};
panel.handleClick({composedPath:()=>[{dataset:{action:"animal-detail",id:"AH-1"}}]});
if(panel.modal!==null||panel._openedAnimal!=="AH-1")throw new Error("Open animal does not close event modal");
if(!panel.fileFields().includes('data-action="take-photo"'))throw new Error("Camera action missing");
if(!panel.speciesVisual("chicken").includes("🐔"))throw new Error("Chicken visual regressed");
console.log("Animal Health 0.7.5 dashboard runtime validation passed");
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
    assert manifest["version"] == "0.7.5"
    assert 'const V="0.7.5",D="animal_health"' in source
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
        ast.parse(read(path))
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(source)
        file.flush()
        subprocess.run(["node", "--check", file.name], check=True)
    for marker in ("animal-health-brand.svg","navigator.mediaDevices.getUserMedia","attachmentPreview","groups/archive","groups/restore","preparingDownload","applyTaskVisibility","eventDetails","taskInactive","statusTransition"):
        assert marker in source
    runtime_smoke(source)
    print("Animal Health 0.7.5 dashboard frontend validation passed")


if __name__ == "__main__":
    main()
