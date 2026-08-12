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
  version:"0.8.9",
  today:"2026-08-11",
  summary:{active_animals:2,overdue_tasks:0,today_tasks:0,upcoming_tasks:0,pending_tasks:0},
  animals:[
    {id:"AH-1",device_id:"device-1",name:"Tina",species:"Huhn",breed:"Legehybride",color:"Hellbraun",sex:"female",birth_date:"2024-01-01",status:"active",is_archived:false,latest_weight:{original_value:2.05,original_unit:"kg"}},
    {id:"AH-2",device_id:"device-2",name:"Berta",species:"Huhn",breed:"Marans",color:"Schwarz",sex:"female",birth_date:"2025-01-01",status:"active",is_archived:false,latest_weight:{original_value:2.2,original_unit:"kg"}}
  ],
  tasks:[],occurrences:[],events:[]
};
panel.c={
  animal_sexes:["male","female","other"],
  species:[{id:"chicken",name_de:"Huhn",name_en:"Chicken",aliases:["Hühner"]},{id:"dog",name_de:"Hund",name_en:"Dog",aliases:[]}],
  breeds:[{id:"chicken.hybrid",species_id:"chicken",name:"Legehybride",aliases:[]},{id:"chicken.marans",species_id:"chicken",name:"Marans",aliases:[]}],
  task_kinds:["reminder","weight","medication","vaccination","health_check","care","veterinary_visit","treatment"],
  weight_units:["kg","g"],
  dose_units:["mcg","mg","g","ml","drop","tablet","dose"],
  administration_routes:["oral"],
  symptoms:["other"],
  symptom_severities:["mild","moderate","severe","critical"],
  vaccination_targets:[],
  health_check_results:["normal"],
  medicine_names:[],
  vaccine_names:[]
};
panel.features={
  groups:[{id:"GR-1",name:"Hühner",species:"chicken",animal_count:2}],
  memberships:{"AH-1":"GR-1","AH-2":"GR-1"},
  max_attachment_size_bytes:15728640
};
panel.groupLifecycle={archived:{}};
panel.v080={primary_group_required:false,tags:[],tag_memberships:{},profiles:{}};
panel.v081={settings:{},group_events:[],group_tasks:[]};
panel.v083={
  animal_metadata:{"AH-1":{distinctive_features:"Leichter weisser Kragen"}},
  group_metadata:{"GR-1":{breed:"Legehybride"}},
  custom_values:[
    {id:1,kind:"breed",species_id:"chicken",breed_context:"",value:"Eigene Rasse",catalog_source:"custom"},
    {id:2,kind:"color",species_id:"chicken",breed_context:"legehybride",value:"Eigene Farbe",catalog_source:"custom"},
    {id:3,kind:"medication",species_id:"chicken",breed_context:"",value:"Eigenes Medikament",catalog_source:"custom",authorisation_status:"unknown"}
  ],
  medicines:[
    {id:"chicken.med",name:"HuhnMed 10 mg/ml",target_species:["chicken"],aliases:[],catalog_source:"standard"},
    {id:"dog.med",name:"HundMed 40 mg",target_species:["dog"],aliases:[],catalog_source:"standard"}
  ]
};
panel.v084={suggestions:{
  medication_name:[{value:"HuhnMed Verlauf",species_id:"chicken",count:2,last_used:"2026-08-11T10:00:00+00:00"}],
  provider:[{value:"Tierarztpraxis Verlauf",species_id:"chicken",count:1,last_used:"2026-08-10T10:00:00+00:00"}]
}};
panel.aiStatus={available:true,entities:["ai_task.test"],stt_available:true,stt_entities:["stt.test"]};
panel.profileUrls={};
panel.decorateFeatures();
panel.decorateV080();
panel.decorateV081();
panel.decorateV083();

const groupSelect=panel.primaryGroupSelect("");
if(groupSelect.includes("required"))throw new Error("Animal group is still required");
if(!groupSelect.includes("Ohne Tiergruppe"))throw new Error("Ungrouped animal option missing");

panel.modal={type:"edit-animal",animalId:"AH-1"};
const animalForm=panel.form();
if(!animalForm.includes('name="distinctive_features"'))throw new Error("Distinctive features field missing");
if(!animalForm.includes('data-combo083="breed"')||!animalForm.includes('data-combo083="color"'))throw new Error("Stable breed/color combobox missing");

panel.modal={type:"edit-group",groupId:"GR-1"};
const groupForm=panel.form();
if(!groupForm.includes('name="breed"'))throw new Error("Group breed field missing");

const lifecycle=panel.groupLifecycleForm({groupId:"GR-1",mode:"delete"});
if(!lifecycle.includes('value="ungroup"')||!lifecycle.includes("Tiere keiner Tiergruppe zuordnen"))throw new Error("Ungroup-on-delete option missing");

const medicationForm={
  elements:{},
  querySelector(selector){if(selector==='[name="show_off_label"]:checked')return this.showOff?{}:null;return null;},
  querySelectorAll(){return []},
  showOff:false
};
medicationForm.elements.animal_id={value:"AH-1"};
let meds=panel.comboCandidates083("medication",medicationForm);
if(!meds.some(item=>item.value==="HuhnMed Verlauf"))throw new Error("Local-history medication missing");
if(!meds.some(item=>item.value==="HuhnMed 10 mg/ml"))throw new Error("On-label medication missing");
if(meds.some(item=>item.value==="HundMed 40 mg"))throw new Error("Off-label medication shown by default");
medicationForm.showOff=true;
meds=panel.comboCandidates083("medication",medicationForm);
const off=meds.find(item=>item.value==="HundMed 40 mg");
if(!off||!off.offlabel)throw new Error("Off-label medication not marked");

const field=()=>({value:"",dispatchEvent(){}});
const animalCheck={value:"device-1",checked:false};
const fields={
  task_scope:field(),task_kind:field(),title:field(),description:field(),
  recurrence_type:field(),recurrence_interval:field(),start_date:field(),due_time:field(),
  planned_medication_name:field(),planned_dose:field(),planned_dose_unit:field(),planned_route:field(),
  planned_vaccine_name:field(),planned_vaccination_dose:field(),planned_vaccination_dose_unit:field(),
  planned_vaccination_route:field(),planned_check_focus:field(),planned_visit_reason:field(),planned_provider:field()
};
const taskForm={
  elements:fields,
  querySelectorAll(selector){if(selector==='[name="device_ids"]')return [animalCheck];if(selector==='[name="planned_vaccination_targets"]')return [];return [];},
  querySelector(){return null;},
  prepend(){}
};
panel.syncTask=()=>{};
panel.shadowRoot.querySelector=selector=>selector==='form[data-form="task"]'?taskForm:null;
panel.aiTaskDraft={
  task_kind:"medication",animal_id:"AH-1",title:"Doxycyclin",
  description:"",recurrence_type:"daily",recurrence_interval:"1",start_date:"2026-08-11",due_time:"",
  planned_medication_name:"Doxycyclin 100 mg/Tablette",planned_dose:"1",planned_dose_unit:"tablet",planned_route:"oral",
  planned_vaccine_name:"",planned_vaccination_dose:"",planned_vaccination_dose_unit:"",planned_vaccination_route:"",
  planned_check_focus:"",planned_visit_reason:"",planned_provider:"",uncertainties:"",recognized_animal:"Tina"
};
if(!panel.applyAITaskDraft083(9))throw new Error("AI task draft was not applied");
if(!animalCheck.checked)throw new Error("AI-recognized animal was not selected");
if(fields.task_kind.value!=="medication")throw new Error("AI task kind was not applied");
if(fields.planned_medication_name.value!=="Doxycyclin 100 mg/Tablette")throw new Error("AI medication was not applied");
if(fields.planned_dose.value!=="1"||fields.planned_dose_unit.value!=="tablet")throw new Error("AI dose/unit was not applied");
if(fields.recurrence_type.value!=="daily"||fields.recurrence_interval.value!=="1")throw new Error("AI recurrence was not applied");

panel.aiBatch083=[
  {suggested_record_type:"weight",animal_name:"Tina",matched_animal_id:"AH-1",animal_id:"AH-1",weight:"2.05",weight_unit:"kg",document_date:"2026-08-11",due_time:"20:00",notes:"",confidence:"high",uncertainties:"",reviewed:false,status:"pending"},
  {suggested_record_type:"weight",animal_name:"Berta",matched_animal_id:"AH-2",animal_id:"AH-2",weight:"2.20",weight_unit:"kg",document_date:"2026-08-11",due_time:"20:00",notes:"",confidence:"low",uncertainties:"Handschrift unsicher",reviewed:false,status:"pending"}
];
panel.aiBatchExpanded086=new Set([0]);
let batch=panel.aiBatchForm083();
if(!batch.includes("aiBatchSummary086")||!batch.includes("Für alle Einträge"))throw new Error("Compact AI batch summary/global controls missing");
if(!batch.includes("Gewogen am")||!batch.includes("Uhrzeit"))throw new Error("Weight batch uses task-planning timing labels");
if(!batch.includes("status certain")||!batch.includes("status uncertain"))throw new Error("AI confidence status icons missing");
if(!batch.includes("mdi:delete-outline")||!batch.includes("mdi:content-save-outline"))throw new Error("Compact trash/save controls missing");
if(panel.aiBatchReady083(panel.aiBatch083[0]))throw new Error("Unreviewed AI batch entry is save-ready");
panel.aiBatch083[0].reviewed=true;
if(!panel.aiBatchReady083(panel.aiBatch083[0]))throw new Error("Reviewed complete AI batch entry is not save-ready");
batch=panel.aiBatchForm083();
if(!batch.includes("status manual")||!batch.includes('aria-pressed="true"'))throw new Error("Manual review has no visible green status");
panel.updateBatchField083({dataset:{batchField083:"weight",batchIndex086:"0"},value:"2.10"});
if(panel.aiBatch083[0].reviewed)throw new Error("Editing an AI batch entry did not invalidate manual review");

panel.modal={type:"record-product-081",animalId:"AH-1"};
const productForm=panel.form();
if(!productForm.includes('data-action="ai-product-086"'))throw new Error("Medication form AI shortcut missing");
panel.modal={type:"record-symptom",animalId:"AH-1"};
const symptomForm=panel.form();
if(!symptomForm.includes('data-action="ai-symptom-086"'))throw new Error("Symptom form AI shortcut missing");

console.log("Animal Health 0.8.9 dashboard runtime validation passed");
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
    assert manifest["version"] == "0.8.9"
    assert 'const V="0.8.9",D="animal_health"' in source

    for path in sorted(INTEGRATION.glob("*.py")):
        ast.parse(read(path))

    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(source)
        file.flush()
        subprocess.run(["node", "--check", file.name], check=True)

    backend = read(INTEGRATION / "v083_features.py")
    backend084 = read(INTEGRATION / "v084_features.py")
    backend086 = read(INTEGRATION / "v086_features.py")
    backend088 = read(INTEGRATION / "v088_features.py")
    panel_backend = read(INTEGRATION / "panel.py")
    for marker in (
        "v083/state",
        "v083/animal_metadata/set",
        "v083/group_metadata/set",
        "v083/custom_value/remember",
        "v083/ai/analyze",
        "v086/ai/analyze",
        "v088/ai/analyze",
        "WEIGHT-LIST COMPLETENESS RULES",
        "animal_v083_metadata",
        "animal_group_v083_metadata",
        "animal_custom_values",
        "entries_json",
        "Tiere keiner Tiergruppe zuordnen",
        "distinctive_features",
        "data-combo083",
        "show_off_label",
        "mdi:pencil-outline",
        "applyAITaskDraft083",
        "cropOverlay083",
        "Details zur KI-Erkennung",
        "v084/history_suggestions",
        "v084/diagnostics",
        "v084/reset_activity",
        "Datenbankdiagnose",
        "open-updates-084",
        "Verlaufs- und Aufgabendaten zurücksetzen",
        "animal-health-brand.png",
        "aiBatchSummary086",
        "aiBatchCommon086",
        "ai-product-086",
        "ai-symptom-086",
        "detailLoading086",
        'size:"thumb"',
        "aria-pressed",
        "aiBatchWeightDate088",
    ):
        assert (
            marker in source
            or marker in backend
            or marker in backend084
            or marker in backend086
            or marker in backend088
            or marker in panel_backend
        ), marker

    runtime_smoke(source)
    print("Animal Health 0.8.9 dashboard frontend validation passed")


if __name__ == "__main__":
    main()