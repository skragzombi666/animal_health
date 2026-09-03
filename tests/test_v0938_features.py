from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"
SOURCE = FRONTEND / "animal-health-panel.part98.js"
MANIFEST = ROOT / "custom_components" / "animal_health" / "manifest.json"
ANDROID = ROOT / "android" / "app" / "build.gradle.kts"


def test_038_shared_target_state_initializer_and_legacy_options_are_restored() -> None:
    frontend = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "ensureTargetState026=function",
        "initialAnimalId",
        "includeGeneral",
        "allowGeneral",
        'String(key)==="task"',
        "AH038Base.targetSelector026.call",
    ):
        assert marker in frontend


def test_038_primary_capture_actions_have_direct_routes() -> None:
    frontend = SOURCE.read_text(encoding="utf-8")
    for marker in (
        'action==="record-product"',
        'action==="record-symptom"',
        'action==="create-task"',
        'this.openMedicationBatch0817({animalId:target})',
        'this.open("record-symptom",{animalId:target})',
        'this.open("create-task",{animalId:target})',
    ):
        assert marker in frontend


def test_038_primary_capture_forms_render_on_first_click() -> None:
    frontend = SOURCE.read_text(encoding="utf-8")
    harness = r'''
class AnimalHealthPanel{}
AnimalHealthPanel.prototype.targetSelector026=function(key,options={}){
 const state=this.ensureTargetState026(key,options.defaultScope||"animals");
 this.selectorLog=this.selectorLog||[];
 this.selectorLog.push({key,options:{...options},state:{...state,animalIds:[...state.animalIds]}});
 return `${key}:${state.scope}:${state.animalIds.join(",")}:${options.allowGeneral}`
};
AnimalHealthPanel.prototype.handleClick=function(event){
 this.baseAction=event.composedPath().find(node=>node?.dataset?.action)?.dataset?.action||"";
 return "base"
};
AnimalHealthPanel.prototype.clearTargetState026=function(key){
 this._targetStates026=this._targetStates026||{};
 if(key)delete this._targetStates026[key];else this._targetStates026={}
};
AnimalHealthPanel.prototype.render=function(){
 this.renderCount=(this.renderCount||0)+1;
 if(this.modal?.type==="create-task")this.targetSelector026("task",{initialAnimalId:this.modal.animalId||"",includeGeneral:true});
 if(this.modal?.type==="record-symptom")this.targetSelector026("symptom",{initialAnimalId:this.modal.animalId||""});
 if(this.modal?.type==="medication-batch-0817")this.targetSelector026("medication",{initialAnimalId:this.medBatch0817?.animalId||""})
};
AnimalHealthPanel.prototype.open=function(type,extra={}){
 this.modal={type,...extra};
 this.render()
};
AnimalHealthPanel.prototype.openMedicationBatch0817=function({animalId=""}={}){
 this.medBatch0817={animalId};
 this.modal={type:"medication-batch-0817"};
 this.render()
};
'''
    checks = r'''
const panel=new AnimalHealthPanel();
panel.detail={animal:{id:"AH-1"}};
panel._targetStates026={task:{scope:"group",groupId:"GR-1",animalIds:null}};
const normalized=panel.ensureTargetState026("task");
if(normalized.scope!=="group"||normalized.groupId!=="GR-1"||normalized.animalIds.length!==0)throw new Error("state normalization failed");
panel._targetStates026={};
const symptomMarkup=panel.targetSelector026("symptom",{initialAnimalId:"AH-1"});
if(symptomMarkup!=="symptom:animals:AH-1:false")throw new Error(`symptom selector mismatch: ${symptomMarkup}`);
panel._targetStates026={};
const taskMarkup=panel.targetSelector026("task",{initialAnimalId:"AH-1",includeGeneral:true});
if(taskMarkup!=="task:animals:AH-1:true")throw new Error(`task selector mismatch: ${taskMarkup}`);
const click=action=>panel.handleClick({composedPath:()=>[{dataset:{action}}]});
panel._targetStates026={task:{scope:"group",groupId:"OLD",animalIds:[]}};
click("create-task");
if(panel.modal?.type!=="create-task")throw new Error("task modal not opened");
if(panel._targetStates026.task?.animalIds?.[0]!=="AH-1")throw new Error("task animal not selected");
panel._targetStates026={symptom:{scope:"group",groupId:"OLD",animalIds:[]}};
click("record-symptom");
if(panel.modal?.type!=="record-symptom")throw new Error("symptom modal not opened");
if(panel._targetStates026.symptom?.animalIds?.[0]!=="AH-1")throw new Error("symptom animal not selected");
panel._targetStates026={medication:{scope:"group",groupId:"OLD",animalIds:[]}};
click("record-product");
if(panel.modal?.type!=="medication-batch-0817")throw new Error("medication modal not opened");
if(panel._targetStates026.medication?.animalIds?.[0]!=="AH-1")throw new Error("medication animal not selected");
const result=click("record-event");
if(result!=="base"||panel.baseAction!=="record-event")throw new Error("unrelated action not delegated");
process.stdout.write("ok");
'''
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as script:
        script.write(harness)
        script.write("\n")
        script.write(frontend)
        script.write("\n")
        script.write(checks)
        script.flush()
        result = subprocess.run(
            ["node", script.name],
            check=False,
            capture_output=True,
            text=True,
        )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "ok"


def test_038_release_version_and_shared_bundle_count_are_updated() -> None:
    assert '"version": "0.9.38"' in MANIFEST.read_text(encoding="utf-8")
    frontend = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    assert 'const V="0.9.38"' in frontend
    android = ANDROID.read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in android
    assert "versionCode = 900007" in android
    assert "ordered.size == 98" in android
    assert "Expected 98 Animal Health frontend parts" in android
