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
panel.d={version:"0.8.1",today:"2026-08-09",summary:{active_animals:2,overdue_tasks:1,today_tasks:1,upcoming_tasks:1,pending_tasks:2},animals:[
{id:"AH-1",device_id:"device-1",name:"Curry",species:"Huhn",breed:"Legehybride",status:"active",is_archived:false,latest_weight:{original_value:1.25,original_unit:"kg"}},
{id:"AH-2",device_id:"device-2",name:"BBQ",species:"Huhn",status:"active",is_archived:false,latest_weight:{original_value:2.52,original_unit:"kg"}}
],tasks:[
{id:"TK-OFF",title:"Wägen",task_kind:"weight",recurrence_type:"weekly",is_active:false,animal_name:"Curry"},
{id:"TK-TREAT",title:"Fuss behandeln",task_kind:"treatment",recurrence_type:"once",is_active:true,animal_name:"BBQ"}
],occurrences:[
{id:"OC-OFF",task_id:"TK-OFF",task_title:"Wägen",task_kind:"weight",animal_id:"AH-1",animal_name:"Curry",status:"pending",scheduled_local:"2026-08-09T14:00:00+02:00",scheduled_date:"2026-08-09",is_overdue:false,is_today:true,is_upcoming:false},
{id:"OC-TREAT",task_id:"TK-TREAT",task_title:"Fuss behandeln",task_kind:"treatment",animal_id:"AH-2",animal_name:"BBQ",status:"pending",scheduled_local:"2026-08-09T15:00:00+02:00",scheduled_date:"2026-08-09",is_overdue:false,is_today:true,is_upcoming:false,planned:{treatment_action:"Fuss behandeln"}}
],events:[
{id:"EV-W0",animal_id:"AH-2",animal_name:"BBQ",event_type:"weight",title:"weight_measurement",occurred_at:"2026-08-01T10:00:00+02:00",value:2.5,unit:"kg"},
{id:"EV-W1",animal_id:"AH-2",animal_name:"BBQ",event_type:"weight",title:"weight_measurement",occurred_at:"2026-08-08T18:09:00+02:00",value:2.52,unit:"kg"},
{id:"EV-S",animal_id:"AH-1",animal_name:"Curry",event_type:"status_change",title:"status_change",occurred_at:"2026-08-08T15:29:00+02:00",data:{previous_status:"rehomed",new_status:"active"}},
{id:"EV-H",animal_id:"AH-1",animal_name:"Curry",event_type:"symptom",title:"diarrhea",occurred_at:"2026-08-08T13:21:00+02:00"}
]};
panel.c={animal_sexes:["male","female","other"],species:[{id:"chicken",name_de:"Huhn",name_en:"Chicken",aliases:[]}],breeds:[{id:"chicken.hybrid",species_id:"chicken",name:"Legehybride"}],task_kinds:["reminder","weight","treatment"],weight_units:["kg","g"],dose_units:[],administration_routes:[],symptoms:["diarrhea"],symptom_severities:[],vaccination_targets:[],health_check_results:[],medicine_names:[],vaccine_names:[]};
panel.features={groups:[{id:"GR-1",name:"Tschiggis",species:"chicken",animal_count:2}],memberships:{"AH-1":"GR-1","AH-2":"GR-1"},max_attachment_size_bytes:15728640};
panel.groupLifecycle={archived:{}};
panel.v080={primary_group_required:true,tags:[{id:"TG-1",name:"Bumblefoot",animal_count:1}],tag_memberships:{"AH-1":["TG-1"]},profiles:{"AH-1":"AT-1","AH-2":null}};
panel.v081={settings:{},group_events:[],group_tasks:[]};
panel.aiStatus={available:false,entities:[],stt_available:false,stt_entities:[]};
panel.profileUrls={"AH-1":"/photo-curry.jpg"};
panel.decorateFeatures();panel.decorateV080();panel.decorateV081();panel.applyTaskVisibility(panel.d,panel.d.tasks);
if(panel.d.occurrences.some(x=>x.id==="OC-OFF"))throw new Error("Inactive task occurrence remains visible");
const tasks=panel.tasks();if(!tasks.includes("Serie fortsetzen")||!tasks.includes("Serie pausiert"))throw new Error("Recurring task pause/resume UX missing");if(!tasks.includes("Behandlung"))throw new Error("Treatment task kind missing");
const groupSelect=panel.primaryGroupSelect("GR-1");if(!groupSelect.includes("required")||groupSelect.includes("Ohne Tiergruppe")||!groupSelect.includes("Neue Tiergruppe anlegen"))throw new Error("Primary group selector invalid");
const lifecycle=panel.groupLifecycleForm({groupId:"GR-1",mode:"archive"});if(lifecycle.includes("Aus der Gruppe entfernen"))throw new Error("0.8 still allows ungrouping primary group members");
panel.modal={type:"edit-animal",animalId:"AH-1"};const animalForm=panel.form();if(!animalForm.includes("Bumblefoot")||!animalForm.includes("Tierbild ersetzen")||!animalForm.includes('name="profile_image"'))throw new Error("Tags/photo missing from animal form");
panel.modal={type:"record-weight",animalId:"AH-2"};const weightForm=panel.form();for(const label of ["−0,10 kg","−0,01 kg","+0,01 kg","+0,10 kg"])if(!weightForm.includes(label))throw new Error(`Weight step missing: ${label}`);
panel.weightPrevious={"EV-W1":{value:2.5,unit:"kg"}};panel.modal={type:"event-detail",eventId:"EV-W1"};const weightDetail=panel.form();if(!weightDetail.includes("Letzte Messung")||!weightDetail.includes("2.5 kg")||!weightDetail.includes("Neue Messung")||!weightDetail.includes("2.52 kg")||!weightDetail.includes("Gewicht korrigieren"))throw new Error("Weight transition/correction detail missing");
panel.modal={type:"event-detail",eventId:"EV-S"};const statusDetail=panel.form();if(!statusDetail.includes("Weitervermittelt")||!statusDetail.includes("Aktiv"))throw new Error("Status transition regressed");
panel.timelineMode="health";const healthTimeline=panel.timeline();if(!healthTimeline.includes("Durchfall")||healthTimeline.includes("Statusänderung"))throw new Error("Health timeline separation failed");panel.timelineMode="activity";const activityTimeline=panel.timeline();if(!activityTimeline.includes("Statusänderung")||activityTimeline.includes("Durchfall"))throw new Error("Activity timeline separation failed");
const card=panel.animalCard(panel.animal("AH-1"));if(!card.includes("/photo-curry.jpg")||!card.includes("Bumblefoot"))throw new Error("Animal photo/tag not rendered on card");
panel._overviewStats=true;const stat=panel.stat("mdi:paw",2,"activeAnimals");panel._overviewStats=false;if(!stat.includes('data-action="summary-filter"'))throw new Error("Dashboard stat not clickable");
panel.modal={type:"execute",occurrenceId:"OC-TREAT"};const treatmentForm=panel.form();if(!treatmentForm.includes('name="treatment_action"'))throw new Error("Treatment execution fields missing");
const overview=panel.overview();if(!overview.includes("Jetzt relevant")||!overview.includes("Schnell erfassen")||!overview.includes("Medikament / Supplement"))throw new Error("0.8.1 operational start page missing");
console.log("Animal Health 0.8.1 dashboard runtime validation passed");
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
    assert manifest["version"] == "0.8.1"
    assert 'const V="0.8.1",D="animal_health"' in source
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
        INTEGRATION / "v080_features.py",
        INTEGRATION / "v080_task_policy.py",
        INTEGRATION / "v080_weight.py",
        INTEGRATION / "v081_features.py",
        INTEGRATION / "v081_fixes.py",
        INTEGRATION / "v081_stt.py",
    ):
        ast.parse(read(path))
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(source)
        file.flush()
        subprocess.run(["node", "--check", file.name], check=True)
    for marker in (
        "animal-health-brand.svg",
        "navigator.mediaDevices.getUserMedia",
        "applyTaskVisibility",
        "eventDetails",
        "statusTransition",
        "v080/state",
        "animal_photo/set",
        "tags/set",
        "seriesPause",
        "document_in_timeline",
        "previous_weight",
        "weight-step-080",
        "healthTimeline",
        "activityTimeline",
        "record_task_treatment",
        "quickCaptureGrid",
        "v081/group_event/create_safe",
    ):
        assert marker in source
    runtime_smoke(source)
    print("Animal Health 0.8.1 dashboard frontend validation passed")


if __name__ == "__main__":
    main()
