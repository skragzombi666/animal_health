from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"
SOURCE = FRONTEND / "animal-health-panel.part96.js"


def source() -> str:
    return SOURCE.read_text(encoding="utf-8")


def test_036_documents_card_uses_all_animal_attachments_and_hides_when_empty() -> None:
    frontend = source()
    for marker in (
        "animalDocuments036",
        "this.detail?.attachments||[]",
        "section.remove()",
        "this.attachmentList(documents)",
        'section.classList.add("animalDocuments036")',
    ):
        assert marker in frontend
    assert "!item.event_id" not in frontend
    assert "!x.event_id" not in frontend


def test_036_animal_task_dialog_contains_all_states_and_global_overview() -> None:
    frontend = source()
    for marker in (
        "taskState036",
        "taskCompleted036",
        'group(this.t("activeTasks031"),active)',
        'group(this.t("taskCompleted034"),completed)',
        'group(this.t("inactiveTasks097"),inactive)',
        'data-action="task-overview-036"',
        'this.view="tasks"',
    ):
        assert marker in frontend


def test_036_duplicate_and_replan_are_separate_persistent_operations() -> None:
    frontend = source()
    for marker in (
        'taskContinue034:["Erneut planen"',
        'copy_mode:mode',
        'source_task_id:',
        'source_root_task_id:',
        'name="copy_mode"',
        'name="source_task_id"',
        'action==="task-duplicate-034"||action==="task-continue-034"',
        'mode==="replan"',
    ):
        assert marker in frontend
    assert 'continued&&task.recurrence_type==="once"?"daily"' not in frontend


def test_036_frontend_behaviour_is_deterministic() -> None:
    frontend = source()
    harness = r'''
const T={};
const I={reminder:"mdi:bell-outline",medication:"mdi:pill"};
const esc=value=>String(value??"");
class AnimalHealthPanel{}
for(const name of [
 "open","animalDetail","animalTasks031","activeAnimalTasks031","animalTaskRow031",
 "animalTasksModal031","taskManagementRow097","taskDraft034","openTaskCopy034",
 "applyAITaskDraft","taskForm","performCustomClick034","render"
]) AnimalHealthPanel.prototype[name]=function(){};
AnimalHealthPanel.prototype.after=async function(){};
'''
    checks = r'''
(async()=>{
 const panel=new AnimalHealthPanel();
 panel.t=key=>key;
 panel.l=value=>String(value||"");
 panel.fmt=value=>String(value||"");
 panel.num=value=>String(value||"");
 panel.notify=()=>{};
 panel.render=()=>{};
 panel.taskTargetsAnimal031=()=>true;
 panel.taskCompleted034=task=>String(task.recurrence_type||"once")==="once"&&Number(task.pending_count||0)===0&&Number(task.completed_count||0)>0;
 panel.d={today:"2026-09-02",tasks:[],animals:[]};
 panel.detail={animal:{id:"AH-1",name:"Chlümpli"},attachments:[
  {id:"AT-1",animal_id:"AH-1",filename:"general.pdf"},
  {id:"AT-2",animal_id:"AH-1",event_id:"EV-1",filename:"chronicle.jpg"},
  {id:"AT-X",animal_id:"AH-2",filename:"other.pdf"}
 ],tasks:[]};
 const documents=panel.animalDocuments036();
 if(documents.length!==2||!documents.some(item=>item.event_id==="EV-1"))throw new Error("event-linked attachments are not aggregated");
 const task={id:"TK-1",animal_id:"AH-1",title:"Metacam",task_kind:"medication",recurrence_type:"once",recurrence_interval:1,start_date:"2026-08-01",end_date:"2026-08-05",due_time:"08:30",planned:{medication_name:"Metacam",dose:0.1,dose_unit:"ml",route:"oral",task_origin:{mode:"replan",source_task_id:"TK-0",source_task_title:"Earlier",root_task_id:"TK-ROOT"}}};
 const duplicate=panel.taskDraft034(task,"duplicate");
 const replan=panel.taskDraft034(task,"replan");
 if(duplicate.recurrence_type!=="once"||replan.recurrence_type!=="once")throw new Error("once task was silently converted into a series");
 if(duplicate.copy_mode!=="duplicate"||replan.copy_mode!=="replan")throw new Error("copy modes are not distinct");
 if(replan.source_root_task_id!=="TK-ROOT")throw new Error("replan root lineage was lost");
 if(replan.end_date!=="2026-09-06")throw new Error("schedule duration was not preserved");
 if(replan.planned_medication_name!=="Metacam"||replan.planned_dose!==0.1)throw new Error("planned treatment data was not copied");
 const groupTarget=panel.taskTargetMeta036({animal_id:"AH-1",planned:{target_scope:"group",target_group_id:"GR-1",target_animal_ids:["AH-1","AH-2"]}});
 if(groupTarget.scope!=="group"||groupTarget.groupId!=="GR-1")throw new Error("group target was not preserved");
 panel.d.tasks=[
  {id:"ACTIVE",title:"Active",animal_id:"AH-1",recurrence_type:"daily",is_active:true,pending_count:1,completed_count:2},
  {id:"DONE",title:"Done",animal_id:"AH-1",recurrence_type:"once",is_active:true,pending_count:0,completed_count:1},
  {id:"OFF",title:"Inactive",animal_id:"AH-1",recurrence_type:"once",is_active:false,pending_count:0,completed_count:0}
 ];
 const animalTasks=panel.animalTasks031(panel.detail.animal);
 if(animalTasks.map(item=>item.id).join(",")!=="ACTIVE,DONE,OFF")throw new Error("animal task states are incomplete or incorrectly ordered");
 if(panel.activeAnimalTasks031(panel.detail.animal).map(item=>item.id).join(",")!=="ACTIVE")throw new Error("completed task is counted as active");
 await panel.performCustomClick034({dataset:{action:"task-duplicate-034",id:"DONE"}});
 if(panel.modal?.type!=="create-task"||panel.aiTaskDraft?.copy_mode!=="duplicate")throw new Error("duplicate action did not open a copy draft");
 await panel.performCustomClick034({dataset:{action:"task-continue-034",id:"DONE"}});
 if(panel.modal?.type!=="create-task"||panel.aiTaskDraft?.copy_mode!=="replan")throw new Error("replan action did not open a linked draft");
})().catch(error=>{console.error(error);process.exit(1)});
'''
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(harness)
        file.write(frontend)
        file.write(checks)
        file.flush()
        subprocess.run(["node", file.name], check=True)
