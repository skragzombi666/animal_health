from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PART = ROOT / "custom_components" / "animal_health" / "frontend" / "animal-health-panel.part28.js"


def test_ai_task_prefill_is_rendered_deterministically() -> None:
    source = PART.read_text(encoding="utf-8")
    harness = r'''
const esc=x=>String(x??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
class AnimalHealthPanel{}
AnimalHealthPanel.prototype.t=function(k){return k};
AnimalHealthPanel.prototype.norm083=function(v){return String(v||"").trim().toLowerCase()};
AnimalHealthPanel.prototype.animal=function(id){return this.d.animals.find(a=>a.id===id)};
AnimalHealthPanel.prototype.aiDraftFromSuggestion083=function(){return {}};
AnimalHealthPanel.prototype.taskForm=function(){return `<form data-form="task">
<select name="task_scope"><option value="animal" selected>animal</option><option value="general">general</option></select>
<select name="task_kind"><option value="reminder" selected>reminder</option><option value="medication">medication</option></select>
<input type="checkbox" name="device_ids" value="device-1">
<input name="title" value="">
<textarea name="description"></textarea>
<select name="recurrence_type"><option value="once" selected>once</option><option value="daily">daily</option></select>
<input name="recurrence_interval" value="1">
<input name="start_date" value="2026-08-12">
<input name="due_time" value="">
<input name="planned_medication_name" value="">
<input name="planned_dose" value="">
<select name="planned_dose_unit"><option value="mg" selected>mg</option><option value="tablet">tablet</option></select>
<select name="planned_route"><option value=""></option><option value="oral">oral</option></select>
<input name="planned_vaccine_name" value="">
<input name="planned_vaccination_dose" value="">
<select name="planned_vaccination_dose_unit"><option value=""></option><option value="tablet">tablet</option></select>
<select name="planned_vaccination_route"><option value=""></option><option value="oral">oral</option></select>
<input name="planned_check_focus" value="">
<input name="planned_visit_reason" value="">
<input name="planned_provider" value="">
<input name="planned_treatment_action" value="">
</form>`};
'''
    checks = r'''
const panel=new AnimalHealthPanel();
panel.d={today:"2026-08-12",animals:[{id:"AH-1",device_id:"device-1",name:"Chlümpli"}]};
const suggestion={suggested_record_type:"medication",suggested_title:"Doxyclin treatment",animal_name:"Chlümpli",document_date:"2026-07-20",medication_name:"Doxyclin",dose:"1",dose_unit:"tablet",route:"oral",notes:"1x täglich bis auf weiteres.",recurrence_type:"daily",recurrence_interval:"1"};
panel.aiTaskDraft=panel.aiDraftFromSuggestion083(suggestion);
if(panel.aiTaskDraft.task_kind!=="medication")throw new Error("medication task kind mapping failed");
if(panel.aiTaskDraft.animal_id!=="AH-1")throw new Error("animal name fallback mapping failed");
const html=panel.taskForm();
if(!/<option value="medication" selected>/.test(html))throw new Error("task kind not preselected");
if(!/name="device_ids" value="device-1" checked>/.test(html))throw new Error("animal not preselected");
if(!/name="title" value="Doxyclin treatment">/.test(html))throw new Error("title not prefilled");
if(!/<textarea name="description">1x täglich bis auf weiteres\.<\/textarea>/.test(html))throw new Error("description not prefilled");
if(!/<option value="daily" selected>/.test(html))throw new Error("recurrence not preselected");
if(!/name="start_date" value="2026-07-20">/.test(html))throw new Error("start date not prefilled");
if(!/name="planned_medication_name" value="Doxyclin">/.test(html))throw new Error("medication not prefilled");
if(!/name="planned_dose" value="1">/.test(html))throw new Error("dose not prefilled");
if(!/<option value="tablet" selected>/.test(html))throw new Error("dose unit not preselected");
if(!/<option value="oral" selected>/.test(html))throw new Error("route not preselected");
'''
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(harness)
        file.write(source)
        file.write(checks)
        file.flush()
        subprocess.run(["node", file.name], check=True)
