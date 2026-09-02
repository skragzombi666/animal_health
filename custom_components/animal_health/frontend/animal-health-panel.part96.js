Object.assign(T,{
 taskContinue034:["Erneut planen","Schedule again"],
 taskOverview036:["Zur Aufgabenübersicht","Open task overview"],
 noAnimalTasks036:["Für dieses Tier sind keine Aufgaben vorhanden.","No tasks are available for this animal."],
 taskDuplicateNotice036:["Neue unabhängige Aufgabe auf Basis von","New independent task based on"],
 taskReplanNotice036:["Neue Planung derselben Aufgabe auf Basis von","New schedule of the same task based on"],
 taskCopyOrigin036:["Kopie von","Copy of"],
 taskReplanOrigin036:["Erneut geplant aus","Scheduled again from"]
});
const AH036=AnimalHealthPanel.prototype;
const AH036Base={
 open:AH036.open,
 after:AH036.after,
 animalDetail:AH036.animalDetail,
 animalTasks031:AH036.animalTasks031,
 activeAnimalTasks031:AH036.activeAnimalTasks031,
 animalTaskRow031:AH036.animalTaskRow031,
 animalTasksModal031:AH036.animalTasksModal031,
 taskManagementRow097:AH036.taskManagementRow097,
 taskDraft034:AH036.taskDraft034,
 openTaskCopy034:AH036.openTaskCopy034,
 applyAITaskDraft:AH036.applyAITaskDraft,
 taskForm:AH036.taskForm,
 performCustomClick034:AH036.performCustomClick034,
 render:AH036.render
};
AH036.animalDocuments036=function(){
 const animalId=String(this.detail?.animal?.id||""),items=this.detail?.attachments||[],seen=new Set,result=[];
 for(const item of items){
  if(!item)continue;
  if(animalId&&item.animal_id&&String(item.animal_id)!==animalId)continue;
  const key=String(item.id||`${item.event_id||""}|${item.filename||""}|${item.created_at||""}`);if(seen.has(key))continue;seen.add(key);result.push(item)
 }
 return result
};
AH036.decorateAnimalDocuments036=function(html){
 const documents=this.animalDocuments036(),template=document.createElement("template");template.innerHTML=html;
 const section=[...template.content.querySelectorAll("section.card")].find(node=>[...node.children].some(child=>child.tagName==="H2"&&child.textContent.trim()===this.t("documents")));
 if(!section)return html;
 if(!documents.length){section.remove();return template.innerHTML}
 const heading=[...section.children].find(child=>child.tagName==="H2"),content=document.createElement("template");content.innerHTML=this.attachmentList(documents);section.replaceChildren();if(heading)section.append(heading);section.append(content.content.cloneNode(true));section.classList.add("animalDocuments036");return template.innerHTML
};
AH036.animalDetail=function(){return this.decorateAnimalDocuments036(AH036Base.animalDetail.call(this))};
AH036.taskById036=function(id){const needle=String(id||"");return[...(this.d?.tasks||[]),...(this.detail?.tasks||[])].find(task=>String(task?.id||"")===needle)||null};
AH036.taskPlan036=function(task){return task?.planned||task?.task_recording_template||{}};
AH036.taskCompleted036=function(task){
 if(typeof this.taskCompleted034==="function")return Boolean(this.taskCompleted034(task));
 const pending=Number(task?.pending_count||0),completed=Number(task?.completed_count||0);return String(task?.recurrence_type||"once")==="once"&&pending===0&&completed>0
};
AH036.taskState036=function(task){return this.taskCompleted036(task)?"completed":task?.is_active===false?"inactive":"active"};
AH036.animalTasks031=function(animal=this.detail?.animal){
 if(!animal)return[];const byId=new Map;
 for(const task of[...(this.d?.tasks||[]),...(this.detail?.tasks||[])]){const id=String(task?.id||"");if(!id||!this.taskTargetsAnimal031(task,animal))continue;byId.set(id,{...(byId.get(id)||{}),...task})}
 const order={active:0,completed:1,inactive:2};return[...byId.values()].sort((a,b)=>order[this.taskState036(a)]-order[this.taskState036(b)]||String(a.title||"").localeCompare(String(b.title||""),undefined,{sensitivity:"base"}))
};
AH036.activeAnimalTasks031=function(animal=this.detail?.animal){return this.animalTasks031(animal).filter(task=>this.taskState036(task)==="active")};
AH036.taskOrigin036=function(task){
 let origin=this.taskPlan036(task)?.task_origin;if(typeof origin==="string"){try{origin=JSON.parse(origin)}catch(_error){origin=null}}
 if(!origin||typeof origin!=="object")return null;const mode=String(origin.mode||""),sourceTaskId=String(origin.source_task_id||"");if(!["duplicate","replan"].includes(mode)||!sourceTaskId)return null;return{mode,sourceTaskId,sourceTaskTitle:String(origin.source_task_title||this.taskById036(sourceTaskId)?.title||sourceTaskId),rootTaskId:String(origin.root_task_id||sourceTaskId)}
};
AH036.taskOriginText036=function(task){const origin=this.taskOrigin036(task);return origin?`${this.t(origin.mode==="replan"?"taskReplanOrigin036":"taskCopyOrigin036")}: ${origin.sourceTaskTitle}`:""};
AH036.taskManagementRow097=function(task){
 const html=AH036Base.taskManagementRow097.call(this,task),origin=this.taskOriginText036(task);if(!origin)return html;
 const template=document.createElement("template");template.innerHTML=html;const main=template.content.querySelector(".taskDefinitionMain097");if(!main)return html;const marker=document.createElement("small");marker.className="taskOrigin036";marker.textContent=origin;main.append(marker);return template.innerHTML
};
AH036.animalTaskRow031=function(task){
 const state=this.taskState036(task),completed=state==="completed",inactive=state==="inactive",plan=this.taskPlanSummary031(task),scope=this.taskScope031(task),recurrence=this.recurrenceLabel095?.(task)||this.l(task.recurrence_type||"once"),stats=this.taskOccurrenceStats034?.(task),completedAt=stats?.lastCompleted?.completed_at||stats?.lastCompleted?.updated_at||stats?.lastCompleted?.scheduled_for||task.last_completed_at||"",nextValue=task.next_pending_local||task.next_pending_at||"",status=completed?(completedAt?`${this.t("lastCompleted097")}: ${this.fmt(completedAt,true)}`:this.t("taskCompleted034")):(nextValue?`${this.t("nextExecution031")}: ${this.fmt(nextValue,true)}`:""),origin=this.taskOriginText036(task),editTitle=esc(this.t("editTask097")),duplicateTitle=esc(this.t("taskDuplicate034")),replanTitle=esc(this.t("taskContinue034")),toggleTitle=esc(this.t(inactive?"activate":"deactivate")),duplicate=`<button type="button" data-action="task-duplicate-034" data-id="${esc(task.id)}" title="${duplicateTitle}" aria-label="${duplicateTitle}"><ha-icon icon="mdi:content-copy"></ha-icon></button>`,actions=completed?`${duplicate}<button type="button" data-action="task-continue-034" data-id="${esc(task.id)}" title="${replanTitle}" aria-label="${replanTitle}"><ha-icon icon="mdi:calendar-refresh-outline"></ha-icon></button>`:`<button type="button" data-action="edit-task-097" data-id="${esc(task.id)}" title="${editTitle}" aria-label="${editTitle}"><ha-icon icon="mdi:pencil-outline"></ha-icon></button>${duplicate}<button type="button" data-action="animal-task-toggle-031" data-id="${esc(task.id)}" title="${toggleTitle}" aria-label="${toggleTitle}"><ha-icon icon="mdi:${inactive?"play-circle-outline":"pause-circle-outline"}"></ha-icon></button>`;
 return`<article class="animalTaskRow031 ${inactive?"inactive031":""} ${completed?"completed036":""}"><ha-icon icon="${I[task.task_kind]||I.reminder}"></ha-icon><div><b>${esc(task.title)}</b><span>${[scope,this.l(task.task_kind||"reminder"),recurrence].filter(Boolean).map(esc).join(" · ")}</span>${plan?`<small>${esc(plan)}</small>`:""}${status?`<small>${esc(status)}</small>`:""}${origin?`<small class="taskOrigin036">${esc(origin)}</small>`:""}</div><div>${actions}</div></article>`
};
AH036.animalTasksModal031=function(){
 const animal=this.animal(this.modal?.animalId)||this.detail?.animal,tasks=this.animalTasks031(animal),active=tasks.filter(task=>this.taskState036(task)==="active"),completed=tasks.filter(task=>this.taskState036(task)==="completed"),inactive=tasks.filter(task=>this.taskState036(task)==="inactive"),group=(label,items)=>items.length?`<section class="animalTaskGroup031"><h3>${esc(label)} <small>${items.length}</small></h3>${items.map(task=>this.animalTaskRow031(task)).join("")}</section>`:"";
 return`<div class="animalTasksModal031"><div class="animalTasksModalHead031"><div><h2><ha-icon icon="mdi:clipboard-text-outline"></ha-icon>${this.t("animalTasks031")}</h2><p>${this.t("animalTasksFor031")} <b>${esc(animal?.name||"")}</b></p></div><div class="animalTasksModalActions036"><button type="button" data-action="task-overview-036"><ha-icon icon="mdi:format-list-bulleted"></ha-icon>${this.t("taskOverview036")}</button><button type="button" class="primary" data-action="create-task" data-id="${esc(animal?.id||"")}"><ha-icon icon="mdi:clipboard-plus-outline"></ha-icon>${this.t("createAnimalTask031")}</button></div></div>${group(this.t("activeTasks031"),active)}${group(this.t("taskCompleted034"),completed)}${group(this.t("inactiveTasks097"),inactive)}${!tasks.length?this.empty("noAnimalTasks036"):""}</div>`
};
AH036.taskTargetMeta036=function(task){
 const plan=this.taskPlan036(task),rawScope=String(plan.target_scope||task?.target_scope||task?.scope||""),directId=String(task?.animal_id||""),fromPlan=Array.isArray(plan.target_animal_ids)?plan.target_animal_ids:Array.isArray(task?.target_animal_ids)?task.target_animal_ids:[],animalIds=[...new Set([...fromPlan.map(String),...(directId?[directId]:[])])],groupId=String(plan.target_group_id||task?.target_group_id||task?.group_id||"");let scope=rawScope==="animal"?"animals":rawScope==="all"?"general":rawScope;
 if(scope==="group"&&groupId)return{scope,groupId,animalIds};if(scope==="general"&&!directId&&!animalIds.length)return{scope,groupId:"",animalIds:[]};if(animalIds.length)return{scope:"animals",groupId:"",animalIds};return{scope:"general",groupId:"",animalIds:[]}
};
AH036.shiftedEndDate036=function(task,startDate){
 const originalStart=String(task?.start_date||"").slice(0,10),originalEnd=String(task?.end_date||"").slice(0,10),nextStart=String(startDate||"").slice(0,10);if(!originalStart||!originalEnd||!nextStart)return"";const startMs=Date.parse(`${originalStart}T00:00:00Z`),endMs=Date.parse(`${originalEnd}T00:00:00Z`),nextMs=Date.parse(`${nextStart}T00:00:00Z`);if(!Number.isFinite(startMs)||!Number.isFinite(endMs)||!Number.isFinite(nextMs)||endMs<startMs)return"";return new Date(nextMs+(endMs-startMs)).toISOString().slice(0,10)
};
AH036.taskDraft034=function(task,continued=false){
 const mode=continued===true||continued==="replan"?"replan":"duplicate",plan=this.taskPlan036(task),origin=this.taskOrigin036(task),targets=plan.vaccination_targets||plan.planned_vaccination_targets||[],startDate=this.d?.today||new Date().toISOString().slice(0,10),productName=plan.product_name||plan.medication_name||"";
 return{task_kind:task?.task_kind||"reminder",title:task?.title||"",description:task?.description||"",recurrence_type:task?.recurrence_type||"once",recurrence_interval:String(task?.recurrence_interval||1),start_date:startDate,end_date:this.shiftedEndDate036(task,startDate),due_time:task?.due_time||"",animal_id:task?.animal_id||"",planned_medication_name:plan.medication_name||productName,planned_product_name:productName,planned_dose:plan.dose??"",planned_dose_unit:plan.dose_unit||plan.unit||"",planned_route:plan.route||"",dose_basis:plan.dose_basis||"",feed_status:plan.feed_status||"",planned_vaccination_targets:Array.isArray(targets)?targets:[targets].filter(Boolean),planned_custom_vaccination_target:plan.custom_vaccination_target||"",planned_vaccine_name:plan.vaccine_name||"",planned_antigen:plan.antigen||"",planned_vaccination_dose:plan.dose??"",planned_vaccination_dose_unit:plan.dose_unit||"",planned_vaccination_route:plan.route||"",planned_check_focus:plan.check_focus||"",planned_care_action:plan.care_action||"",planned_visit_reason:plan.visit_reason||"",planned_provider:plan.provider||"",planned_treatment_action:plan.treatment_action||"",planned_treatment_plan_id:plan.treatment_plan_id||"",treatment_plan_name:plan.treatment_plan_name||"",copy_mode:mode,source_task_id:String(task?.id||""),source_task_title:String(task?.title||""),source_root_task_id:mode==="replan"?String(origin?.rootTaskId||task?.id||""):""}
};
AH036.openTaskCopy034=function(task,continued=false){
 if(!task){this.notify(`${this.t("failed")}: ${this.t("noTasks")}`,true);return}
 const draft=this.taskDraft034(task,continued),target=this.taskTargetMeta036(task);this.taskCopyMeta036={mode:draft.copy_mode,sourceTaskId:draft.source_task_id,sourceTaskTitle:draft.source_task_title,rootTaskId:draft.source_root_task_id};this.aiTaskDraft=draft;this._targetStates026=this._targetStates026||{};this._targetStates026.task={scope:target.scope,groupId:target.groupId,animalIds:target.animalIds,open:false,includeGeneral:true};this.modal={type:"create-task",animalId:target.animalIds[0]||""};this.render()
};
AH036.applyAITaskDraft=function(){
 const draft=this.aiTaskDraft,form=this.shadowRoot.querySelector('form[data-form="task"]');if(!draft||!form)return;
 const set=(name,value)=>{const field=form.elements[name];if(!field||value===undefined||value===null)return;if(typeof field.length==="number"&&!field.tagName){for(const item of field)if(item.type!=="checkbox"&&item.type!=="radio")item.value=value}else if(field.type!=="checkbox"&&field.type!=="radio")field.value=value};
 if(draft.animal_id&&!this._targetStates026?.task){this._targetStates026=this._targetStates026||{};this._targetStates026.task={scope:"animals",groupId:"",animalIds:[String(draft.animal_id)],open:false,includeGeneral:true};this.updateTargetCompatibility026?.("task")}
 for(const name of["task_kind","title","description","recurrence_type","recurrence_interval","start_date","end_date","due_time"])set(name,draft[name]);this.syncTask?.(form);
 for(const name of["planned_medication_name","planned_product_name","planned_dose","planned_dose_unit","planned_route","dose_basis","feed_status","planned_custom_vaccination_target","planned_vaccine_name","planned_antigen","planned_vaccination_dose","planned_vaccination_dose_unit","planned_vaccination_route","planned_check_focus","planned_care_action","planned_visit_reason","planned_provider","planned_treatment_action","planned_treatment_plan_id","treatment_plan_name"])set(name,draft[name]);
 const selected=new Set((Array.isArray(draft.planned_vaccination_targets)?draft.planned_vaccination_targets:[draft.planned_vaccination_targets]).filter(Boolean).map(String));for(const input of form.querySelectorAll('[name="planned_vaccination_targets"]'))input.checked=selected.has(String(input.value));const multi=form.querySelector('[data-multi-choice034="planned_vaccination_targets"]');if(multi)this.refreshMultiChoice034?.(multi);this.syncTask?.(form);this.refreshTaskOptions012?.(form);this.aiTaskDraft=null
};
AH036.taskForm=function(){
 let html=AH036Base.taskForm.call(this),draft=this.aiTaskDraft,meta=this.taskCopyMeta036;if(!meta&&!draft?.copy_mode)return html;const mode=meta?.mode||draft.copy_mode,sourceTaskId=meta?.sourceTaskId||draft.source_task_id||"",sourceTaskTitle=meta?.sourceTaskTitle||draft.source_task_title||sourceTaskId,rootTaskId=meta?.rootTaskId||draft.source_root_task_id||"",notice=`${this.t(mode==="replan"?"taskReplanNotice036":"taskDuplicateNotice036")} «${sourceTaskTitle}».`,hidden=`<input type="hidden" name="copy_mode" value="${esc(mode)}"><input type="hidden" name="source_task_id" value="${esc(sourceTaskId)}"><input type="hidden" name="source_task_title" value="${esc(sourceTaskTitle)}">${rootTaskId?`<input type="hidden" name="source_root_task_id" value="${esc(rootTaskId)}">`:""}`;
 html=html.replace(/(<form\b[^>]*data-form="task"[^>]*>)/,`$1<p class="wide taskCopyNotice036"><ha-icon icon="${mode==="replan"?"mdi:calendar-refresh-outline":"mdi:content-copy"}"></ha-icon><span>${esc(notice)}</span></p>`);return html.replace("</form>",`${hidden}</form>`)
};
AH036.open=function(type,extra={}){if(type!=="create-task"||!this.taskCopyMeta036){this.taskCopyMeta036=null;if(type==="create-task")this.aiTaskDraft=null}return AH036Base.open.call(this,type,extra)};
AH036.after=async function(){this.taskCopyMeta036=null;return AH036Base.after.call(this)};
AH036.performCustomClick034=async function(button){
 const action=String(button?.dataset?.action||"");
 if(action==="task-duplicate-034"||action==="task-continue-034"){this.openTaskCopy034(this.taskById036(button.dataset.id),action==="task-continue-034"?"replan":"duplicate");return true}
 if(action==="task-overview-036"){this.taskCopyMeta036=null;this.aiTaskDraft=null;this.modal=null;this.detail=null;this.view="tasks";this.filter="";this.taskSearch097="";this.render();return true}
 if(action==="create-task"||action==="edit-task-097"){this.taskCopyMeta036=null;this.aiTaskDraft=null}
 return AH036Base.performCustomClick034.call(this,button)
};
AH036.render=function(){AH036Base.render.call(this);this.shadowRoot.innerHTML+=`<style>
.animalDocuments036 .attachmentList{margin-top:4px}.animalTasksModalActions036{display:flex;align-items:center;justify-content:flex-end;gap:7px;flex-wrap:wrap}.animalTasksModalActions036 button{display:flex;align-items:center;gap:6px;white-space:nowrap}.animalTaskRow031.completed036>ha-icon{opacity:.75}.taskOrigin036{display:block!important;color:var(--secondary-text-color)!important;font-size:.76rem!important;font-style:normal!important}.taskCopyNotice036{display:flex;align-items:flex-start;gap:9px;margin:0;padding:10px 12px;border:1px solid var(--divider-color);border-radius:10px;background:var(--secondary-background-color);color:var(--secondary-text-color)}.taskCopyNotice036 ha-icon{flex:0 0 auto}@media(max-width:620px){.animalTasksModalActions036{align-self:stretch;justify-content:stretch}.animalTasksModalActions036 button{flex:1;justify-content:center}.taskCopyNotice036{align-items:center}}
</style>`};
