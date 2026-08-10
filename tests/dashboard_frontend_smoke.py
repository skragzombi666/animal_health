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
panel.h={language:"de",user:{is_admin:true}};
panel.d={version:"0.8.2",today:"2026-08-10",summary:{active_animals:1,overdue_tasks:0,today_tasks:0,upcoming_tasks:0,pending_tasks:0},animals:[{id:"AH-1",device_id:"device-1",name:"Tina",species:"Hund",breed:"Entlebucher Sennenhund",status:"active",is_archived:false,latest_weight:{original_value:20.5,original_unit:"kg"}}],tasks:[],occurrences:[],events:[]};
panel.c={animal_sexes:["male","female","other"],species:[{id:"dog",name_de:"Hund",name_en:"Dog",aliases:[]}],breeds:[],task_kinds:["reminder","weight","medication","vaccination","health_check","care","veterinary_visit"],weight_units:["kg","g"],dose_units:["mg","g","tablet","dose"],administration_routes:["oral"],symptoms:["other"],symptom_severities:["mild"],vaccination_targets:[],health_check_results:["normal"],medicine_names:[],vaccine_names:[]};
panel.features={groups:[{id:"GR-1",name:"Tschiggies",species:"dog",animal_count:1}],memberships:{},max_attachment_size_bytes:15728640};
panel.groupLifecycle={archived:{}};
panel.v080={primary_group_required:false,tags:[],tag_memberships:{},profiles:{}};
panel.v081={settings:{},group_events:[],group_tasks:[]};
panel.aiStatus={available:true,entities:["ai_task.test"],stt_available:true,stt_entities:["stt.test"]};
panel.profileUrls={};
panel.decorateFeatures();panel.decorateV080();panel.decorateV081();

const groupSelect=panel.primaryGroupSelect("");
if(groupSelect.includes("required"))throw new Error("Animal group is still required");
if(!groupSelect.includes("Ohne Tiergruppe"))throw new Error("Ungrouped option missing");

const profile=panel.profileField(panel.d.animals[0]);
if(!profile.includes("data-profile-selection")||!profile.includes('name="profile_image"'))throw new Error("Profile image selection feedback missing");

panel.modal={type:"record-weight",animalId:"AH-1"};
const weightForm=panel.form();
if(!weightForm.includes("Gewicht mit KI erfassen"))throw new Error("Contextual weight AI button missing");

const aiForm=panel.aiUploadForm();
if(!aiForm.includes("Foto oder Datei (optional)")||!aiForm.includes("Zusätzliche Angaben")||!aiForm.includes("Diktieren"))throw new Error("General multimodal AI capture missing");

panel.modal=null;
const settings=panel.settingsPage081();
if(!settings.includes("Animal Health zurücksetzen")||!settings.includes("Gefahrenbereich"))throw new Error("Reset UI missing");

console.log("Animal Health 0.8.2 dashboard runtime validation passed");
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
    assert manifest["version"] == "0.8.2"
    assert 'const V="0.8.2",D="animal_health"' in source

    for path in sorted(INTEGRATION.glob("*.py")):
        ast.parse(read(path))

    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(source)
        file.flush()
        subprocess.run(["node", "--check", file.name], check=True)

    backend = read(INTEGRATION / "v082_features.py")
    for marker in (
        "v082/attachment/preview",
        "v082/ai/analyze",
        "v082/reset",
        "primary_group_required",
        "Ohne Tiergruppe",
        "data-profile-selection",
        "compressProfileImage",
        "Original herunterladen",
        "KI-Erfassung",
        "Gewicht mit KI erfassen",
        "recurrence_type",
        "planned_dose_unit",
        "toggle-search",
        "animal-menu",
        "Animal Health zurücksetzen",
    ):
        assert marker in source or marker in backend

    runtime_smoke(source)
    print("Animal Health 0.8.2 dashboard frontend validation passed")


if __name__ == "__main__":
    main()
