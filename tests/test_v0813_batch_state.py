from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"
INTEGRATION = ROOT / "custom_components" / "animal_health"


def _source() -> str:
    return "".join(
        path.read_text(encoding="utf-8")
        for path in sorted(FRONTEND.glob("animal-health-panel.part*.js"))
    )


def test_weight_ai_stays_on_original_v083_single_pass() -> None:
    route = (FRONTEND / "animal-health-panel.part29.js").read_text(encoding="utf-8")
    backend = (INTEGRATION / "v083_features.py").read_text(encoding="utf-8")

    assert 'p?.mode==="weight"?`${D}/v083/ai/analyze`:type' in route
    assert 'p?.mode==="weight"?`${D}/v088/ai/analyze`:type' not in route
    assert "A handwritten list with nine animal " in backend
    assert "Do not silently discard uncertain " in backend


def test_batch_name_matching_and_manual_review_runtime() -> None:
    source = _source()
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
(async()=>{
const Panel=customElements.get("animal-health-panel");
if(!Panel)throw new Error("Panel not registered");
const panel=new Panel();
panel.render=()=>{};
panel.h={language:"de",user:{is_admin:true}};
panel.d={animals:[
  {id:"AH-H",device_id:"dev-h",name:"Hanibelle",is_archived:false},
  {id:"AH-N",device_id:"dev-n",name:"Nugget",is_archived:false},
  {id:"AH-T",device_id:"dev-t",name:"Tina",is_archived:false}
]};
panel.c={weight_units:["g","kg"]};

const close=panel.fuzzyAnimalMatch0813("Hanibel");
if(!close||close.animal.id!=="AH-H"||!close.approximate)throw new Error("Conservative fuzzy name match failed");
if(panel.fuzzyAnimalMatch0813("Emma"))throw new Error("Unknown animal was matched too aggressively");

panel.aiBatch083=[{
  suggested_record_type:"weight",animal_name:"Nugget",matched_animal_id:"",animal_id:"",
  weight:"2.2",weight_unit:"kg",document_date:"2026-05-06",due_time:"20:00",
  notes:"",confidence:"medium",uncertainties:"",reviewed:false,status:"pending",capture_mode:"weight"
}];
if(!panel.prepareBatchNameMatches0813())throw new Error("Exact recognized animal was not post-matched");
if(panel.aiBatch083[0].animal_id!=="AH-N")throw new Error("Exact Nugget association missing");

panel.aiBatch083=[{
  suggested_record_type:"weight",animal_name:"Unknown",matched_animal_id:"",animal_id:"",
  weight:"2.2",weight_unit:"kg",document_date:"2026-05-06",due_time:"20:00",
  notes:"",confidence:"medium",uncertainties:"",reviewed:false,status:"pending",capture_mode:"weight"
}];
panel.updateBatchField083({dataset:{batchField083:"animal_id",batchIndex086:"0"},value:"AH-N"});
if(panel.aiBatch083[0].animal_id!=="AH-N")throw new Error("Manual animal selection was not stored in batch state");
if(!panel.aiBatchDataComplete086(panel.aiBatch083[0]))throw new Error("Manually corrected weight entry remains incomplete");
await panel.handleClick({composedPath(){return[{dataset:{action:"ai-batch-review-086",index:"0"}}]}});
if(!panel.aiBatch083[0].reviewed)throw new Error("Corrected gray entry cannot be marked manually reviewed");
console.log("Animal Health 0.8.13 batch state runtime validation passed");
})().catch(error=>{console.error(error);process.exit(1)});
'''
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(harness)
        file.write(source)
        file.write(checks)
        file.flush()
        subprocess.run(["node", file.name], check=True)
