Object.assign(T,{
 activeTasks031:["Aktive Aufgaben","Active tasks"],
 animalTasks031:["Aufgaben","Tasks"],
 animalTasksFor031:["Aufgaben für","Tasks for"],
 manageAnimalTasks031:["Aufgaben dieses Tiers verwalten","Manage this animal's tasks"],
 noActiveAnimalTasks031:["Für dieses Tier sind keine aktiven Aufgaben vorhanden.","No active tasks are available for this animal."],
 noUpcomingAnimalTasks031:["Derzeit sind keine Ausführungen anstehend.","No executions are currently upcoming."],
 createAnimalTask031:["Aufgabe anlegen","Create task"],
 nextExecution031:["Nächste Ausführung","Next execution"]
});
const AH031=AnimalHealthPanel.prototype;
const AH031Base={
 animalDetail:AH031.animalDetail,
 animalSeriesStatus097:AH031.animalSeriesStatus097,
 animalUpcomingRow029:AH031.animalUpcomingRow029,
 form:AH031.form,
 handleClick:AH031.handleClick,
 render:AH031.render
};
AH031.taskPlan031=function(task){return task?.planned||task?.task_recording_template||{}};
AH031.taskTargetsAnimal031=function(task,animal){
 if(!task||!animal)return false;
 const plan=this.taskPlan031(task),animalId=String(animal.id||""),groupId=String(animal.group_id||""),targetIds=Array.isArray(plan.target_animal_ids)?plan.target_animal_ids.map(String):[];
 if(String(task.animal_id||"")===animalId||targetIds.includes(animalId))return true;
 const targetGroup=String(task.group_id||task.target_group_id||plan.target_group_id||"");
 return Boolean(groupId&&targetGroup===groupId)
};
AH031.animalTasks031=function(animal=this.detail?.animal){
 if(!animal)return[];
 const pendingIds=new Set([...(this.d?.occurrences||[]),...(this.detail?.occurrences||[])].filter(item=>item.status==="pending").map(item=>String(item.task_id||""))),byId=new Map;
 for(const task of[...(this.d?.tasks||[]),...(this.detail?.tasks||[])]){
  const id=String(task?.id||"");if(!id||!this.taskTargetsAnimal031(task,animal))continue;
  const recurring=String(task.recurrence_type||"once")!=="once",manageable=task.is_active===false||recurring||pendingIds.has(id)||Boolean(task.next_pending_local||task.next_pending_at);
  if(manageable)byId.set(id,{...(byId.get(id)||{}),...task})
 }
 return[...byId.values()].sort((a,b)=>Number(b.is_active!==false)-Number(a.is_active!==false)||String(a.title||"").localeCompare(String(b.title||""),undefined,{sensitivity:"base"}))
};
AH031.activeAnimalTasks031=function(animal=this.detail?.animal){return this.animalTasks031(animal).filter(task=>task.is_active!==false)};
AH031.taskScope031=function(task){const plan=this.taskPlan031(task),scope=String(plan.target_scope||task?.target_scope||"");if(scope==="group")return plan.target_group_name||task.group_name||"";return""};
AH031.taskPlanSummary031=function(task){
 const plan=this.taskPlan031(task),kind=String(task?.task_kind||"reminder"),name=kind==="vaccination"?plan.vaccine_name:plan.medication_name||plan.product_name,dose=plan.dose!=null&&plan.dose!==""?`${this.num(plan.dose)} ${this.l(plan.dose_unit||"")}`:"";
 return[name,dose].filter(Boolean).join(" · ")
};
AH031.animalUpcomingRow029=function(item){
 const task=item.task||this.task?.(item.task_id);if(!task)return"";
 const recurrence=this.recurrenceLabel095?.(task)||this.l(task.recurrence_type||"once"),date=item.key?this.fmt(item.key):"",status=item.isOverdue?`${this.t("overdueOnly010")} · ${date}`:date?`${this.t("nextDue095")}: ${date}`:recurrence,scope=this.taskScope031(task),canExecute=Boolean(item.occurrence&&item.occurrence.status==="pending"&&(item.isOverdue||String(item.key||"")<=String(this.d?.today||"")));
 return`<div class="nextTask animalUpcomingRow029"><div class="nextTaskIcon"><ha-icon icon="${I[task.task_kind]||I.reminder}"></ha-icon></div><div class="nextTaskMain static0816"><b>${esc(task.title)}</b><span>${[scope,recurrence,status].filter(Boolean).map(esc).join(" · ")}</span></div><div class="animalUpcomingActions029"><button type="button" data-action="edit-task-097" data-id="${esc(task.id)}" title="${esc(this.t("editTask097"))}" aria-label="${esc(this.t("editTask097"))}"><ha-icon icon="mdi:pencil-outline"></ha-icon></button>${canExecute?`<button class="primary compactExecute" data-action="execute" data-id="${esc(item.occurrence.id)}">${this.t("execute")}</button>`:""}</div></div>`
};
AH031.animalSeriesStatus097=function(){
 const animal=this.detail?.animal;if(!animal)return"";
 const groups=this.dynamicRelevantGroups095().map(group=>({...group,items:group.items.filter(item=>this.itemTargetsAnimal029(item,animal))})).filter(group=>group.items.length),tasks=this.activeAnimalTasks031(animal);
 if(!groups.length&&!tasks.length)return"";
 const title=esc(this.t("manageAnimalTasks031"));
 return`<section class="card animalUpcoming029"><div class="animalUpcomingHead031"><h2>${this.t("upcoming096")}</h2><button type="button" data-action="animal-tasks-031" data-id="${esc(animal.id)}" title="${title}" aria-label="${title}"><ha-icon icon="mdi:clipboard-text-outline"></ha-icon></button></div>${groups.length?groups.map(group=>`<div class="relevantGroup relevantGroup029"><div class="relevantGroupHead095 relevantGroupHead031"><h3>${esc(group.label)}</h3><span>${group.items.length}</span></div>${group.items.map(item=>this.animalUpcomingRow029(item)).join("")}</div>`).join(""):`<div class="empty">${this.t("noUpcomingAnimalTasks031")}</div>`}</section>`
};
AH031.decorateTaskStat031=function(html,animal){
 const template=document.createElement("template");template.innerHTML=html;
 const candidates=[...template.content.querySelectorAll(".stats .stat")],node=candidates.find(item=>item.querySelector("span")?.textContent?.trim()===this.t("openTasks")||item.querySelector('ha-icon[icon="mdi:clipboard"]'));
 if(!node)return html;
 const button=document.createElement("button"),count=this.activeAnimalTasks031(animal).length,label=this.t("activeTasks031"),title=this.t("manageAnimalTasks031");
 button.type="button";button.className=`${node.className} taskStat031`;button.dataset.action="animal-tasks-031";button.dataset.id=String(animal.id||"");button.title=title;button.setAttribute("aria-label",`${label}: ${count}. ${title}`);button.innerHTML=`<ha-icon icon="mdi:clipboard-check-outline"></ha-icon><div><strong>${esc(count)}</strong><span>${esc(label)}</span></div>`;node.replaceWith(button);
 return template.innerHTML
};
AH031.animalDetail=function(){const html=AH031Base.animalDetail.call(this),animal=this.detail?.animal;return animal?this.decorateTaskStat031(html,animal):html};
AH031.animalTaskRow031=function(task){
 const plan=this.taskPlanSummary031(task),scope=this.taskScope031(task),recurrence=this.recurrenceLabel095?.(task)||this.l(task.recurrence_type||"once"),nextValue=task.next_pending_local||task.next_pending_at||"",next=nextValue?`${this.t("nextExecution031")}: ${this.fmt(nextValue,true)}`:"",inactive=task.is_active===false,editTitle=esc(this.t("editTask097")),toggleTitle=esc(this.t(inactive?"activate":"deactivate"));
 return`<article class="animalTaskRow031 ${inactive?"inactive031":""}"><ha-icon icon="${I[task.task_kind]||I.reminder}"></ha-icon><div><b>${esc(task.title)}</b><span>${[scope,this.l(task.task_kind||"reminder"),recurrence].filter(Boolean).map(esc).join(" · ")}</span>${plan?`<small>${esc(plan)}</small>`:""}${next?`<small>${esc(next)}</small>`:""}</div><div><button type="button" data-action="edit-task-097" data-id="${esc(task.id)}" title="${editTitle}" aria-label="${editTitle}"><ha-icon icon="mdi:pencil-outline"></ha-icon></button><button type="button" data-action="animal-task-toggle-031" data-id="${esc(task.id)}" title="${toggleTitle}" aria-label="${toggleTitle}"><ha-icon icon="mdi:${inactive?"play-circle-outline":"pause-circle-outline"}"></ha-icon></button></div></article>`
};
AH031.animalTasksModal031=function(){
 const animal=this.animal(this.modal?.animalId)||this.detail?.animal,tasks=this.animalTasks031(animal),active=tasks.filter(task=>task.is_active!==false),inactive=tasks.filter(task=>task.is_active===false),group=(label,items)=>items.length?`<section class="animalTaskGroup031"><h3>${esc(label)} <small>${items.length}</small></h3>${items.map(task=>this.animalTaskRow031(task)).join("")}</section>`:"";
 return`<div class="animalTasksModal031"><div class="animalTasksModalHead031"><div><h2><ha-icon icon="mdi:clipboard-text-outline"></ha-icon>${this.t("animalTasks031")}</h2><p>${this.t("animalTasksFor031")} <b>${esc(animal?.name||"")}</b></p></div><button type="button" class="primary" data-action="create-task" data-id="${esc(animal?.id||"")}"><ha-icon icon="mdi:clipboard-plus-outline"></ha-icon>${this.t("createAnimalTask031")}</button></div>${group(this.t("activeTasks031"),active)}${group(this.t("inactiveTasks097"),inactive)}${!tasks.length?this.empty("noActiveAnimalTasks031"):""}</div>`
};
AH031.form=function(){if(this.modal?.type==="animal-tasks-031")return this.animalTasksModal031();return AH031Base.form.call(this)};
AH031.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset?.action),action=button?.dataset?.action;
 if(action==="animal-tasks-031"){this.open("animal-tasks-031",{animalId:button.dataset.id||this.detail?.animal?.id||""});return}
 if(action==="animal-task-toggle-031"){
  const task=this.task(button.dataset.id);if(!task)return;button.disabled=true;
  try{await this.svc("set_task_active",{task_id:task.id,is_active:task.is_active===false},true);await this.load();this.modal={type:"animal-tasks-031",animalId:this.detail?.animal?.id||this.modal?.animalId||""};this.render()}catch(error){button.disabled=false;this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}
  return
 }
 return AH031Base.handleClick.call(this,event)
};
AH031.render=function(){AH031Base.render.call(this);this.shadowRoot.innerHTML+=`<style>
button.taskStat031{appearance:none;border:0;text-align:left;color:inherit;font:inherit;cursor:pointer}.taskStat031:hover,.taskStat031:focus-visible{outline:2px solid var(--primary-color);outline-offset:2px}.animalUpcomingHead031{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px}.animalUpcomingHead031 h2{margin:0}.animalUpcomingHead031>button{width:44px;height:44px;min-width:44px;padding:0;display:grid;place-items:center;border-radius:12px}.animalUpcomingHead031>button ha-icon{width:25px;height:25px}.relevantGroupHead031{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:10px!important}.relevantGroupHead031 h3{margin:0!important;font-size:1rem!important}.relevantGroupHead031 span{display:inline-grid;place-items:center;min-width:24px;height:24px;padding:0 6px;border-radius:999px;background:var(--secondary-background-color);color:var(--secondary-text-color);font-size:.78rem}.animalTasksModal031{display:grid;gap:14px;min-width:min(680px,82vw)}.animalTasksModalHead031{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.animalTasksModalHead031 h2{display:flex;align-items:center;gap:8px;margin:0}.animalTasksModalHead031 p{margin:4px 0 0;color:var(--secondary-text-color)}.animalTasksModalHead031>button{display:flex;align-items:center;gap:7px;white-space:nowrap}.animalTaskGroup031{display:grid;gap:0}.animalTaskGroup031>h3{display:flex;align-items:baseline;gap:7px;margin:0 0 4px}.animalTaskGroup031>h3 small{color:var(--secondary-text-color)}.animalTaskRow031{display:grid;grid-template-columns:38px minmax(0,1fr) auto;align-items:center;gap:10px;padding:10px 0;border-top:1px solid var(--divider-color)}.animalTaskRow031:first-of-type{border-top:0}.animalTaskRow031>ha-icon{width:29px;height:29px}.animalTaskRow031>div:nth-child(2){display:flex;min-width:0;flex-direction:column;gap:2px}.animalTaskRow031 b,.animalTaskRow031 span,.animalTaskRow031 small{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.animalTaskRow031 span,.animalTaskRow031 small{color:var(--secondary-text-color);font-size:.82rem}.animalTaskRow031>div:last-child{display:flex;gap:5px}.animalTaskRow031>div:last-child button{width:40px;height:40px;min-width:40px;padding:0;display:grid;place-items:center}.animalTaskRow031.inactive031{opacity:.62}@media(max-width:620px){.animalTasksModal031{min-width:0}.animalTasksModalHead031{align-items:stretch;flex-direction:column}.animalTasksModalHead031>button{align-self:flex-end}.animalTaskRow031{grid-template-columns:32px minmax(0,1fr)}.animalTaskRow031>div:last-child{grid-column:2;justify-content:flex-end}.animalTaskRow031 b,.animalTaskRow031 span,.animalTaskRow031 small{white-space:normal}.relevantGroupHead031 h3{font-size:.96rem!important}}
</style>`};
