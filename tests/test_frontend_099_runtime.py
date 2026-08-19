from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"


def _source() -> str:
    parts = sorted(FRONTEND.glob("animal-health-panel.part*.js"))
    assert [path.name for path in parts] == [
        f"animal-health-panel.part{index:02d}.js" for index in range(1, len(parts) + 1)
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in parts)


def test_099_runtime_calendar_and_pull_behaviour() -> None:
    harness = r'''
class MockShadowRoot {
  constructor(){this.innerHTML="";this.listeners=[];}
  addEventListener(type,handler,options){this.listeners.push({type,handler,options});}
  querySelector(){return null;}
  querySelectorAll(){return [];}
}
globalThis.HTMLElement=class{
  constructor(){this.isConnected=true;this.shadowRoot=null;this.hostListeners=[];}
  attachShadow(){this.shadowRoot=new MockShadowRoot();return this.shadowRoot;}
  addEventListener(type,handler,options){this.hostListeners.push({type,handler,options});}
  toggleAttribute(){}
  dispatchEvent(){}
};
globalThis.CustomEvent=class{};
globalThis.customElements={elements:new Map(),get(name){return this.elements.get(name)},define(name,value){this.elements.set(name,value)}};
globalThis.localStorage={getItem(){return null},setItem(){}};
'''
    checks = r'''
(async()=>{
 const Panel=customElements.get("animal-health-panel");
 if(!Panel)throw new Error("Panel is not registered");
 const panel=new Panel();
 panel.h={language:"de"};
 panel.d={today:"2026-08-19",tasks:[],occurrences:[],animals:[],events:[]};
 panel.bindPullRefresh099();
 const types=panel.hostListeners.map(item=>item.type);
 for(const required of ["touchstart","touchmove","touchend","touchcancel"]){if(!types.includes(required))throw new Error(`Missing host listener: ${required}`)}
 const move=panel.hostListeners.find(item=>item.type==="touchmove");
 if(move.options?.passive!==false||move.options?.capture!==true)throw new Error("Touch move must be non-passive capture");
 const task={id:"TK-1",title:"Doxycyclin",task_kind:"medication",animal_id:"AH-1",animal_name:"Tina",planned:{medication_name:"Doxycyclin"}};
 panel.d.tasks=[task];
 const state=panel.calendarState097(task,"2026-08-18","2026-08-19");
 if(state.key!=="unconfirmed"||state.occurrence!==null||state.date!=="2026-08-18")throw new Error("Virtual past calendar state is invalid");
 const icon=panel.calendarIcon097(task,state);
 if(!icon.includes('data-action="calendar-execute-099"')||!icon.includes('data-task-id="TK-1"')||!icon.includes('data-date="2026-08-18"'))throw new Error("Virtual past calendar item is not executable");
 panel.svc=async(service,payload,response)=>{
  if(service!=="list_task_occurrences"||payload.task_id!=="TK-1"||payload.from_date!=="2026-08-18"||payload.to_date!=="2026-08-18"||response!==true)throw new Error("Occurrence lookup payload is invalid");
  return{response:{occurrences:[{id:"OC-1",task_id:"TK-1",task_title:"Doxycyclin",animal_id:"AH-1",animal_name:"Tina",scheduled_date:"2026-08-18",scheduled_for:"2026-08-18T18:00:00+00:00",status:"pending"}]}}
 };
 const occurrence=await panel.resolveCalendarOccurrence099("TK-1","2026-08-18");
 if(occurrence.id!=="OC-1"||occurrence.task_kind!=="medication"||occurrence.is_overdue!==true||occurrence.planned.medication_name!=="Doxycyclin")throw new Error("Resolved occurrence was not decorated correctly");
 console.log("Animal Health 0.9.9 runtime validation passed");
})().catch(error=>{console.error(error);process.exit(1)});
'''
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(harness)
        file.write(_source())
        file.write(checks)
        file.flush()
        subprocess.run(["node", file.name], check=True)
