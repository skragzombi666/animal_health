from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"
SOURCE = FRONTEND / "animal-health-panel.part99.js"
MANIFEST = ROOT / "custom_components" / "animal_health" / "manifest.json"
ANDROID = ROOT / "android" / "app" / "build.gradle.kts"


def source() -> str:
    return SOURCE.read_text(encoding="utf-8")


def test_039_task_forms_cover_all_specialised_kinds_and_visible_validation() -> None:
    frontend = source()
    for marker in (
        "taskKindFieldsets039",
        'fieldset("medication"',
        'fieldset("vaccination"',
        'fieldset("deworming"',
        'fieldset("supplement"',
        'fieldset("feed"',
        'fieldset("treatment"',
        'fieldset("health_check"',
        'fieldset("care"',
        'fieldset("veterinary_visit"',
        'name="planned_medication_name"',
        'name="planned_treatment_plan_id"',
        'name="treatment_plan_name"',
        "taskInvalid039",
        "reportValidity",
        'targetPayload026?.("task")',
    ):
        assert marker in frontend


def test_039_hidden_task_fields_are_disabled_and_do_not_block_submit() -> None:
    frontend = source()
    for marker in (
        "fieldset.hidden=!active",
        "field.disabled=!active||field.dataset.noPlans039!==undefined",
        "form.noValidate=true",
        'form?.dataset.form!=="task"',
        "await AH039Base.handleSubmit.call(this,event)",
    ):
        assert marker in frontend


def test_039_settings_have_exact_three_level_structure() -> None:
    frontend = source()
    for marker in (
        'id:"master"',
        'id:"medications"',
        'id:"developer"',
        'id:"group-order"',
        'id:"week-start"',
        'id:"entry-types"',
        'id:"symptoms"',
        'id:"local-suggestions"',
        'id:"product-databases"',
        'id:"favourites"',
        'id:"off-label"',
        'id:"medicines"',
        'id:"treatments"',
        'id:"ai"',
        'id:"administration"',
        'id:"danger"',
        'settingsNav039(this.settingsGroups039(),"settings-group-039")',
        'settingsNav039(group.items,"settings-item-039")',
        'data-action="settings-back-039"',
        "settingsContent039",
    ):
        assert marker in frontend
    assert 'id:"capture"' not in frontend
    assert 'id:"data"' not in frontend


def test_039_off_label_and_destructive_resets_are_separate_items() -> None:
    frontend = source()
    for marker in (
        "offLabelSettings039",
        ".offLabelPolicy012",
        "medicineSettings039",
        'template.content.querySelectorAll(".offLabelPolicy012").forEach(node=>node.remove())',
        "resetIntegrationHint039",
        "resetActivityHint039",
        "reset-activity-085",
        "dangerSettings039",
        "destructiveConfirm039",
    ):
        assert marker in frontend


def test_039_valid_task_submit_delegates_and_invalid_treatment_is_visible() -> None:
    frontend = source()
    harness = r'''
const T={};
const esc=value=>String(value??"");
class AnimalHealthPanel{}
AnimalHealthPanel.prototype.taskForm=function(){return""};
AnimalHealthPanel.prototype.syncTask=function(){};
AnimalHealthPanel.prototype.applyAITaskDraft=function(){};
AnimalHealthPanel.prototype.settingsPage081=function(){return""};
AnimalHealthPanel.prototype.handleClick=function(){};
AnimalHealthPanel.prototype.handleChange=function(){};
AnimalHealthPanel.prototype.handleSubmit=async function(){this.delegated=true;return"saved"};
AnimalHealthPanel.prototype.render=function(){};
'''
    checks = r'''
const field=(dataset={})=>({dataset,disabled:false,reportValidity(){this.reported=true},focus(){this.focused=true}});
const makeFieldset=(kind,fields)=>({dataset:{taskKind039:kind},hidden:false,setAttribute(){},querySelectorAll(){return fields}});
const makeForm=(kind,planValue="PLAN-1")=>{
 const activeField=field(),inactiveField=field(),plan=field();
 plan.value=planValue;plan.disabled=false;plan.selectedOptions=[{dataset:{name:"Plan A"},textContent:"Plan A"}];
 const name={value:""},fieldsets=[makeFieldset(kind,[activeField]),makeFieldset(kind==="treatment"?"medication":"treatment",[inactiveField])];
 return{
  tagName:"FORM",
  dataset:{form:"task"},
  elements:{task_kind:{value:kind},planned_treatment_plan_id:plan,treatment_plan_name:name},
  querySelectorAll(selector){return selector==="[data-task-kind039]"?fieldsets:[]},
  querySelector(selector){if(selector==="[data-treatment-plan039]")return kind==="treatment"?plan:null;if(selector===":invalid:not([disabled])")return null;return null},
  checkValidity(){return true},
  _activeField:activeField,
  _inactiveField:inactiveField,
  _plan:plan,
  _name:name,
 };
};
(async()=>{
 const validPanel=new AnimalHealthPanel();validPanel.targetPayload026=()=>({target_scope:"animals"});validPanel.notify=()=>{};
 const validForm=makeForm("medication");
 const result=await validPanel.handleSubmit({composedPath:()=>[validForm],preventDefault(){throw new Error("valid submit was prevented")}});
 if(result!=="saved"||!validPanel.delegated)throw new Error("valid task submit did not reach the shared save path");
 if(validForm._activeField.disabled)throw new Error("active task fields were disabled");
 if(!validForm._inactiveField.disabled)throw new Error("hidden task fields remained enabled");
 const invalidPanel=new AnimalHealthPanel();invalidPanel.targetPayload026=()=>({});invalidPanel.notify=message=>{invalidPanel.message=message};
 const invalidForm=makeForm("treatment","");let prevented=false;
 await invalidPanel.handleSubmit({composedPath:()=>[invalidForm],preventDefault(){prevented=true}});
 if(!prevented||invalidPanel.delegated)throw new Error("invalid treatment task reached the save path");
 if(!invalidPanel.message||!invalidForm._plan.reported||!invalidForm._plan.focused)throw new Error("invalid treatment was not reported visibly");
 const settingsPanel=new AnimalHealthPanel();settingsPanel.t=key=>key;
 const overview=settingsPanel.settingsPage081();
 if(!overview.includes('data-action="settings-group-039"'))throw new Error("settings overview is not navigable");
 settingsPanel.settingsGroupId039="medications";
 const group=settingsPanel.settingsPage081();
 if(!group.includes('data-action="settings-item-039"')||group.includes("offLabelPolicy012"))throw new Error("settings group is not a pure item overview");
 process.stdout.write("ok");
})().catch(error=>{console.error(error);process.exit(1)});
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


def test_039_existing_navigation_and_thumbnail_repairs_remain_present() -> None:
    part97 = (FRONTEND / "animal-health-panel.part97.js").read_text(encoding="utf-8")
    part98 = (FRONTEND / "animal-health-panel.part98.js").read_text(encoding="utf-8")
    final = source()
    assert "removeInternalHistory037" in part97
    assert "ensureAttachmentUrls037" in part97
    assert "openPrimaryCapture038" in part98
    assert "history.pushState" not in final
    assert "history.replaceState" not in final
    assert "history.back()" not in final


def test_039_release_version_and_shared_bundle_count_are_consistent() -> None:
    version = str(json.loads(MANIFEST.read_text(encoding="utf-8"))["version"])
    frontend = (FRONTEND / "animal-health-panel.part01.js").read_text(encoding="utf-8")
    assert f'const V="{version}"' in frontend
    parts = sorted(FRONTEND.glob("animal-health-panel.part*.js"))
    assert parts[-1] == SOURCE
    android = ANDROID.read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in android
    assert "versionCode = 900007" in android
    assert f"ordered.size == {len(parts)}" in android
    assert f"Expected {len(parts)} Animal Health frontend parts" in android


def test_039_final_frontend_patch_has_valid_javascript() -> None:
    result = subprocess.run(
        ["node", "--check", SOURCE],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
