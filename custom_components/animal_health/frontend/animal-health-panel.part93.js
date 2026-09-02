Object.assign(T,{
 taskCompleted034:["Abgeschlossen","Completed"],
 taskCompletedHint034:["Erledigte Einmal-Aufgaben bleiben als Verlauf erhalten.","Completed one-off tasks remain available as history."],
 taskDuplicate034:["Duplizieren","Duplicate"],
 taskContinue034:["Fortsetzen / erneut planen","Continue / schedule again"],
 selectMoreAnimals034:["Weitere Tiere auswählen","Select more animals"],
 selectMoreItems034:["Weitere auswählen","Select more"],
 createAnimalFromSelection034:["Tier direkt anlegen","Create animal directly"],
 addCustomChoice034:["Neuen Eintrag ergänzen","Add new entry"],
 customChoiceName034:["Bezeichnung des neuen Eintrags","Name of the new entry"],
 databaseLoadUnavailable034:["Die Produktdatenbanken konnten nicht geladen werden. Integration und Frontend müssen auf demselben Versionsstand sein.","Product databases could not be loaded. The integration and frontend must use the same version."]
});
const AH034=AnimalHealthPanel.prototype;
const AH034Base={
 ws:AH034.ws,
 checks:AH034.checks,
 taskForm:AH034.taskForm,
 taskPlanEditor029:AH034.taskPlanEditor029,
 targetSelector026:AH034.targetSelector026,
 taskDefinitionItems097:AH034.taskDefinitionItems097,
 taskManagementRow097:AH034.taskManagementRow097,
 tasks:AH034.tasks,
 treatmentBundle021:AH034.treatmentBundle021,
 rawCompact021:AH034.rawCompact021,
 loadV0928:AH034.loadV0928,
 handleChange:AH034.handleChange
};
AH034.isTaskSource034=function(event){
 const data=event?.data||{},source=String(data.source||data.gabe_source||"");
 return Boolean(event?.task_id||event?.task_occurrence_id||data.task_id||data.source_task_id||data.source_task_occurrence_id||data.task_execution||source==="task"||source==="task_occurrence")
};
AH034.taskSourceIcon034=function(extraClass=""){
 return`<ha-icon class="taskSource034 ${esc(extraClass)}" icon="mdi:clipboard-check-outline" title="${esc(this.t("fromTask027"))}" aria-label="${esc(this.t("fromTask027"))}"></ha-icon>`
};
AH034.eventCompact0817=function(event){
 const gabeType=this.gabeTypeForEvent027?.(event);
 if(!gabeType)return AH033Base.eventCompact0817.call(this,event);
 const data=event?.data||{},snapshot=data.medication_snapshot||data.gabe_snapshot||{},product=data.product_name||data.medication_name||snapshot.name||event.title||this.gabeKindLabel027?.(gabeType)||"",dose=event.value!=null?`${this.num(event.value)} ${this.l(event.unit||"")}`:"",route=data.route||snapshot.route||"",extraTitle=this.taskTitleExtra027?.(event,product)||"",parts=[...(this.activeSummary027?.(event)||[])];
 if(route&&!parts.includes(this.l(route)))parts.push(this.l(route));
 if(extraTitle&&!parts.includes(extraTitle))parts.push(extraTitle);
 const global=this.view!=="animal-detail",animalName=global?(event.animal_name||this.animal?.(event.animal_id)?.name||""):"",typeBadge=gabeType!=="medication"?`<span class="gabeTypeBadge027">${esc(this.gabeKindLabel027(gabeType))}</span>`:"",scopeBadge=this.scopeBadge026?.(event)||"",taskIcon=this.isTaskSource034(event)?this.taskSourceIcon034():"",meta=parts.length?`<span class="gabeMetaInline034"> · <i>${parts.map(esc).join(" · ")}</i></span>`:"";
 return`<div class="row event eventOpen eventCompact0817 gabeCompact034 gabe-${gabeType}" role="button" tabindex="0" data-action="event-detail" data-id="${esc(event.id)}"><ha-icon icon="${this.gabeKindIcon027?.(gabeType)||"mdi:pill"}"></ha-icon><div class="gabeContent034"><div class="gabeFlow034">${animalName?`<span class="gabeAnimal034">${esc(animalName)}</span><span class="gabeSeparator034"> · </span>`:""}${dose?`<span class="gabeDose034">${esc(dose)}</span><span class="gabeSeparator034"> </span>`:""}<b class="gabeTitle034">${esc(product)}</b>${typeBadge}${scopeBadge}${taskIcon}${meta}</div>${event.notes?`<small>${esc(event.notes)}</small>`:""}</div></div>`
};
AH034.rawCompact021=function(event){
 if(this.gabeTypeForEvent027?.(event))return this.eventCompact0817(event);
 return AH034Base.rawCompact021?AH034Base.rawCompact021.call(this,event):AH033Base.eventCompact0817.call(this,event)
};
AH034.treatmentComponents034=function(event){
 const data=event?.data||{},execution=data.task_execution||{},planned=execution.planned||{},components=data.components||data.treatment_plan_components||planned.treatment_plan_components||planned.components||execution.treatment_plan_components||[];
 return Array.isArray(components)?components.filter(item=>item&&typeof item==="object"):[]
};
AH034.treatmentComponentText034=function(item){
 const name=String(item?.name||item?.product_name||"").trim(),dose=item?.dose!=null&&item?.dose!==""?`${this.num(item.dose)} ${this.l(item.unit||item.dose_unit||"")}`:"",route=item?.route?this.l(item.route):"",instructions=String(item?.instructions||"").trim();
 return[dose,name,route,instructions].filter(Boolean).join(" · ")
};
AH034.treatmentBundle021=function(event){
 let html=AH034Base.treatmentBundle021?AH034Base.treatmentBundle021.call(this,event):"";
 if(!html)return html;
 if(this.isTaskSource034(event)&&!html.includes("treatmentTaskSource034")){
  html=html.replace(/(<b[^>]*>[\s\S]*?)(<\/b>)/,`$1<span class="treatmentTaskSource034">${this.taskSourceIcon034("treatmentTaskIcon034")}</span>$2`)
 }
 const components=this.treatmentComponents034(event),plain=html.replace(/<[^>]*>/g," ").replace(/\s+/g," ").toLocaleLowerCase(),missing=components.filter(item=>{const name=String(item?.name||item?.product_name||"").trim().toLocaleLowerCase();return name&&!plain.includes(name)});
 if(!missing.length)return html;
 const rows=missing.map(item=>`<small>${esc(this.treatmentComponentText034(item))}</small>`).join("");
 if(html.includes('class="bundlePreview021"'))return html.replace(/(<span class="bundlePreview021">)([\s\S]*?)(<\/span>)/,`$1$2${rows}$3`);
 return html.replace(/(<\/div><button type="button" class="bundleChevron021")/,`<span class="bundlePreview021 treatmentPlanComponents034">${rows}</span>$1`)
};
AH034.choiceItems034=function(options,selected=[]){
 const map=new Map();
 for(const raw of options||[]){const value=String(raw?.id??raw?.value??raw),label=String(raw?.name??raw?.label??this.l(value));if(value)map.set(value,{value,label})}
 for(const raw of selected||[]){const value=String(raw);if(value&&!map.has(value))map.set(value,{value,label:this.l(value)})}
 return[...map.values()]
};
AH034.multiChoiceMarkup034=function(name,options,selected=[]){
 const chosen=new Set((selected||[]).map(String)),items=this.choiceItems034(options,selected),chips=items.filter(item=>chosen.has(item.value)),available=items.filter(item=>!chosen.has(item.value));
 return`<div class="checks wide multiChoice034" data-multi-choice034="${esc(name)}"><div class="multiChips034" data-multi-chips034>${chips.map(item=>`<button type="button" class="multiChip034" data-action="multi-remove-034" data-name="${esc(name)}" data-value="${esc(item.value)}"><span>${esc(item.label)}</span><ha-icon icon="mdi:close"></ha-icon></button>`).join("")}</div><div class="multiPicker034"><select data-multi-add034="${esc(name)}"><option value="">${esc(this.t("selectMoreItems034"))}</option>${available.map(item=>`<option value="${esc(item.value)}">${esc(item.label)}</option>`).join("")}</select><button type="button" data-action="multi-custom-034" data-name="${esc(name)}" title="${esc(this.t("addCustomChoice034"))}" aria-label="${esc(this.t("addCustomChoice034"))}"><ha-icon icon="mdi:plus"></ha-icon></button></div><div class="multiHidden034">${items.map(item=>`<input type="checkbox" data-multi-option034 data-label="${esc(item.label)}" name="${esc(name)}" value="${esc(item.value)}" ${chosen.has(item.value)?"checked":""}>`).join("")}</div></div>`
};
AH034.checks=function(name,options,selected=[]){
 const draft=this.aiTaskDraft||{},draftValues=name==="planned_vaccination_targets"?(draft.planned_vaccination_targets||draft.planned_vaccination_target):null,values=Array.isArray(draftValues)?draftValues:draftValues?[draftValues]:selected;
 return this.multiChoiceMarkup034(name,options,values)
};
AH034.taskPlanEditor029=function(task){
 let html=AH034Base.taskPlanEditor029?AH034Base.taskPlanEditor029.call(this,task):"";
 if(String(task?.task_kind||"")!=="vaccination")return html;
 const plan=task?.planned||task?.task_recording_template||{},selected=Array.isArray(plan.vaccination_targets)?plan.vaccination_targets:[],options=this.c?.vaccination_targets||[],replacement=`<fieldset class="wide taskVaccinationTargets029"><legend>${this.t("productTargets027")}</legend>${this.multiChoiceMarkup034("planned_vaccination_targets",options,selected)}</fieldset>`;
 return html.replace(/<fieldset class="wide taskVaccinationTargets029">[\s\S]*?<\/fieldset>/,replacement)
};
AH034.refreshMultiChoice034=function(root){
 if(!root)return;
 const inputs=[...root.querySelectorAll("[data-multi-option034]")],chips=root.querySelector("[data-multi-chips034]"),select=root.querySelector("[data-multi-add034]"),name=root.dataset.multiChoice034||"";
 if(chips)chips.innerHTML=inputs.filter(input=>input.checked).map(input=>`<button type="button" class="multiChip034" data-action="multi-remove-034" data-name="${esc(name)}" data-value="${esc(input.value)}"><span>${esc(input.dataset.label||this.l(input.value))}</span><ha-icon icon="mdi:close"></ha-icon></button>`).join("");
 if(select)select.innerHTML=`<option value="">${esc(this.t("selectMoreItems034"))}</option>${inputs.filter(input=>!input.checked).map(input=>`<option value="${esc(input.value)}">${esc(input.dataset.label||this.l(input.value))}</option>`).join("")}`;
 const form=root.closest("form");if(form?.dataset.form==="task")this.syncTask?.(form);else if(form?.dataset.form==="execute")this.syncExec?.(form)
};
AH034.addCustomChoice034=function(root){
 const name=root?.dataset?.multiChoice034||"",inputs=[...root.querySelectorAll("[data-multi-option034]")],other=inputs.find(input=>input.value==="other"),form=root.closest("form"),custom=form?.elements?.planned_custom_vaccination_target||form?.elements?.custom_vaccination_target;
 if(other){other.checked=true;this.refreshMultiChoice034(root);if(custom){custom.hidden=false;custom.disabled=false;custom.focus()}return}
 const value=String(globalThis.prompt?.(this.t("customChoiceName034"))||"").trim();if(!value)return;
 const input=document.createElement("input");input.type="checkbox";input.name=name;input.value=value;input.checked=true;input.dataset.multiOption034="";input.dataset.label=value;root.querySelector(".multiHidden034")?.append(input);this.refreshMultiChoice034(root)
};
AH034.animalPickerMarkup034=function(key,state){
 const animals=(this.d?.animals||[]).filter(animal=>!animal.is_archived),byId=new Map(animals.map(animal=>[String(animal.id),animal])),selected=[...new Set((state.animalIds||[]).map(String))],chosen=selected.map(id=>byId.get(id)).filter(Boolean),selectedSet=new Set(selected),available=animals.filter(animal=>!selectedSet.has(String(animal.id)));
 return`<div class="animalPicker034" data-animal-picker034="${esc(key)}"><div class="multiChips034">${chosen.map(animal=>`<button type="button" class="multiChip034" data-action="target-animal-remove-034" data-key="${esc(key)}" data-id="${esc(animal.id)}"><span>${esc(animal.name)}</span><ha-icon icon="mdi:close"></ha-icon></button>`).join("")}</div><div class="multiPicker034"><select data-target-animal-add034="${esc(key)}"><option value="">${esc(this.t("selectMoreAnimals034"))}</option>${available.map(animal=>`<option value="${esc(animal.id)}">${esc(animal.name)}</option>`).join("")}</select><button type="button" data-action="target-animal-create-034" data-key="${esc(key)}" title="${esc(this.t("createAnimalFromSelection034"))}" aria-label="${esc(this.t("createAnimalFromSelection034"))}"><ha-icon icon="mdi:plus"></ha-icon></button></div>${chosen.map(animal=>`<input type="checkbox" name="device_ids" value="${esc(animal.device_id||"")}" checked hidden>`).join("")}<input type="hidden" name="animal_id" value="${esc(chosen[0]?.id||"")}"></div>`
};
AH034.targetSelector026=function(key,options={}){
 const state=this.ensureTargetState026(key,options.defaultScope||"animals"),allowGeneral=options.allowGeneral!==false,allowGroup=options.allowGroup!==false,groups=this.targetGroups026(),tabs=[allowGroup?["group",this.t("targetGroup026")]:null,["animals",this.t("targetAnimals026")],allowGeneral?["general",this.t("targetGeneral026")]:null].filter(Boolean),groupOptions=groups.map(group=>`<option value="${esc(group.id)}" ${String(state.groupId)===String(group.id)?"selected":""}>${esc(group.name)}</option>`).join("");
 if(!tabs.some(([scope])=>scope===state.scope))state.scope=tabs[0][0];
 return`<section class="wide targetSelector026 targetSelector034" data-target-key026="${esc(key)}"><div class="scopeSwitch026">${tabs.map(([scope,label])=>`<button type="button" data-action="target-tab-026" data-key="${esc(key)}" data-scope="${scope}" class="${state.scope===scope?"active026":""}">${label}</button>`).join("")}</div>${allowGeneral?`<div class="targetPanel026" data-target-panel026="general" ${state.scope==="general"?"":"hidden"}><small>${this.t("targetGeneralHint026")}</small></div>`:""}${allowGroup?`<div class="targetPanel026" data-target-panel026="group" ${state.scope==="group"?"":"hidden"}><label><span>${this.t("group")}</span><select data-target-group026="${esc(key)}"><option value="">${this.t("selectGroup026")}</option>${groupOptions}</select></label></div>`:""}<div class="targetPanel026" data-target-panel026="animals" ${state.scope==="animals"?"":"hidden"}>${this.animalPickerMarkup034(key,state)}</div></section>`
};
AH034.updateTargetCompatibility026=function(key){
 const state=this.ensureTargetState026(key),root=this.shadowRoot.querySelector(`[data-target-key026="${key}"]`);if(!root)return;
 root.querySelectorAll("[data-target-panel026]").forEach(panel=>panel.hidden=panel.dataset.targetPanel026!==state.scope);
 root.querySelectorAll("[data-action='target-tab-026']").forEach(button=>button.classList.toggle("active026",button.dataset.scope===state.scope));
 const panel=root.querySelector('[data-target-panel026="animals"]');if(panel)panel.innerHTML=this.animalPickerMarkup034(key,state)
};
AH034.captureFormState034=function(form){return form?[...form.elements].filter(element=>element?.name).map(element=>({name:element.name,type:element.type||"",value:element.value,checked:Boolean(element.checked)})):[]};
AH034.restoreFormState034=function(form,state){
 if(!form||!Array.isArray(state))return;
 for(const element of form.elements){if(!element?.name)continue;if(element.type==="checkbox"||element.type==="radio"){const match=state.find(item=>item.name===element.name&&String(item.value)===String(element.value));if(match)element.checked=Boolean(match.checked)}else{const match=state.find(item=>item.name===element.name);if(match)element.value=match.value}}
 this.syncTask?.(form);this.syncExec?.(form);this.refreshTaskOptions012?.(form)
};
AH034.beginAnimalCreation034=function(key){
 const form=this.shadowRoot.querySelector(".modal form"),state=this.ensureTargetState026(key),animalIds=(this.d?.animals||[]).map(animal=>String(animal.id));
 this._resumeAfterAnimal034={key,modal:this.cloneNavValue033?.(this.modal)||this.modal,formState:this.captureFormState034(form),targetState:this.cloneNavValue033?.(state)||JSON.parse(JSON.stringify(state)),animalIds};this.modal={type:"create-animal"};this.render()
};
AH034.finishAnimalCreation034=function(){
 const resume=this._resumeAfterAnimal034;if(!resume)return;
 const oldIds=new Set(resume.animalIds||[]),createdCandidates=(this.d?.animals||[]).filter(animal=>!oldIds.has(String(animal.id))).sort((a,b)=>String(a.created_at||a.id||"").localeCompare(String(b.created_at||b.id||""))),created=createdCandidates[createdCandidates.length-1],state={...resume.targetState,animalIds:[...(resume.targetState?.animalIds||[]).map(String)]};
 if(created&&!state.animalIds.includes(String(created.id)))state.animalIds.push(String(created.id));
 this._targetStates026=this._targetStates026||{};this._targetStates026[resume.key]=state;this.modal=resume.modal;this._resumeAfterAnimal034=null;this.render();this.restoreFormState034(this.shadowRoot.querySelector(".modal form"),resume.formState);this.updateTargetCompatibility026(resume.key)
};
AH034.taskOccurrenceStats034=function(task){
 const items=(this.d?.occurrences||[]).filter(item=>String(item.task_id)===String(task.id)),pending=items.filter(item=>item.status==="pending"),completed=items.filter(item=>item.status==="completed").sort((a,b)=>String(b.completed_at||b.updated_at||b.scheduled_for).localeCompare(String(a.completed_at||a.updated_at||a.scheduled_for))),pendingCount=Math.max(pending.length,Number(task?.pending_count||0)),completedCount=Math.max(completed.length,Number(task?.completed_count||0)),lastCompleted=completed[0]||(task?.last_completed_at?{completed_at:task.last_completed_at,scheduled_for:task.last_completed_at}:null);
 return{items,pending,completed,pendingCount,completedCount,lastCompleted}
};
AH034.taskCompleted034=function(task){const stats=this.taskOccurrenceStats034(task);return task?.recurrence_type==="once"&&stats.pendingCount===0&&stats.completedCount>0};
AH034.taskDefinitionItems097=function(){return[...(this.d?.tasks||[])]};
AH034.taskManagementRow097=function(task){
 const animal=task.animal_id?this.animal(task.animal_id):null,completed=this.taskCompleted034(task),stats=this.taskOccurrenceStats034(task),next=this.taskNextOccurrence097(task),schedule=next?this.taskScheduleText097(next):stats.lastCompleted?this.fmt(stats.lastCompleted.completed_at||stats.lastCompleted.scheduled_for,true):this.t("noUpcoming097"),badges=[animal?animal.name:this.t("generalTask"),completed?this.t("taskCompleted034"):task.is_active?this.t("taskActive097"):this.t("taskStopped097"),task.task_kind?this.l(task.task_kind):""].filter(Boolean),plan=this.taskPlanSummary097(task),description=task.description?`<p>${esc(task.description)}</p>`:"";
 return`<article class="taskDefinition097 ${task.is_active?"":"inactive097"} ${completed?"completed034":""}"><div class="taskDefinitionMain097"><h3>${esc(task.title)}</h3><div class="taskDefinitionBadges097">${badges.map(item=>`<span>${esc(item)}</span>`).join("")}</div>${description}<small>${esc(this.recurrence(task))} · ${completed?this.t("taskCompleted034"):this.t("next")}: ${esc(schedule)}</small>${plan?`<em>${esc(plan)}</em>`:""}</div><div class="taskDefinitionActions097">${completed?"":`<button type="button" data-action="edit-task-097" data-id="${esc(task.id)}" title="${esc(this.t("edit"))}"><ha-icon icon="mdi:pencil-outline"></ha-icon></button>`}<button type="button" data-action="task-duplicate-034" data-id="${esc(task.id)}" title="${esc(this.t("taskDuplicate034"))}" aria-label="${esc(this.t("taskDuplicate034"))}"><ha-icon icon="mdi:content-copy"></ha-icon></button>${completed?`<button type="button" data-action="task-continue-034" data-id="${esc(task.id)}" title="${esc(this.t("taskContinue034"))}" aria-label="${esc(this.t("taskContinue034"))}"><ha-icon icon="mdi:calendar-refresh-outline"></ha-icon></button>`:`<button type="button" data-action="toggle" data-id="${esc(task.id)}" title="${esc(this.t(task.is_active?"stopTask097":"resumeTask097"))}"><ha-icon icon="mdi:${task.is_active?"pause-circle-outline":"play-circle-outline"}"></ha-icon></button>`}</div></article>`
};
AH034.tasks=function(){
 const all=this.taskDefinitionItems097(),query=String(this.taskSearch097||"").trim().toLocaleLowerCase(),items=query?all.filter(task=>{const animal=task.animal_id?this.animal(task.animal_id):null;return[task.title,task.description,task.task_kind,animal?.name].some(value=>String(value||"").toLocaleLowerCase().includes(query))}):all,completed=items.filter(task=>this.taskCompleted034(task)),series=items.filter(task=>!this.taskCompleted034(task)&&task.is_active&&task.recurrence_type!=="once"),oneOff=items.filter(task=>!this.taskCompleted034(task)&&task.is_active&&task.recurrence_type==="once"),inactive=items.filter(task=>!this.taskCompleted034(task)&&!task.is_active),count=items.length;
 return`<section class="card taskManagement097"><div class="taskManagementHead097"><div><h2>${this.t("taskManagement097")}</h2><p>${this.t("taskManagementHint097")}</p></div><span>${count}</span></div><label class="taskSearch097"><ha-icon icon="mdi:magnify"></ha-icon><input type="search" data-task-search097 value="${esc(this.taskSearch097||"")}" placeholder="${esc(this.t("taskSearch097"))}"></label>${count?`${this.taskManagementSection097("activeSeries097",series)}${this.taskManagementSection097("openOneOff097",oneOff)}${this.taskManagementSection097("taskCompleted034",completed)}${this.taskManagementSection097("inactiveTasks097",inactive)}`:this.empty(query?"noTaskSearch097":"noTasks")}</section>`
};
AH034.taskDraft034=function(task,continued=false){
 const planned=task?.planned||task?.task_recording_template||{},targets=planned.vaccination_targets||planned.planned_vaccination_targets||[];
 return{task_kind:task.task_kind||"reminder",title:task.title||"",description:task.description||"",recurrence_type:continued&&task.recurrence_type==="once"?"daily":task.recurrence_type||"once",recurrence_interval:String(task.recurrence_interval||1),start_date:this.d?.today||"",end_date:"",due_time:task.due_time||"",animal_id:task.animal_id||"",planned_medication_name:planned.medication_name||planned.product_name||"",planned_dose:planned.dose??"",planned_dose_unit:planned.dose_unit||planned.unit||"",planned_route:planned.route||"",planned_vaccination_targets:Array.isArray(targets)?targets:[targets].filter(Boolean),planned_vaccine_name:planned.vaccine_name||"",planned_antigen:planned.antigen||"",planned_vaccination_dose:planned.dose??"",planned_vaccination_dose_unit:planned.dose_unit||"",planned_vaccination_route:planned.route||"",planned_check_focus:planned.check_focus||"",planned_care_action:planned.care_action||"",planned_visit_reason:planned.visit_reason||"",planned_provider:planned.provider||"",planned_treatment_plan_id:planned.treatment_plan_id||"",treatment_plan_name:planned.treatment_plan_name||""}
};
AH034.openTaskCopy034=function(task,continued=false){
 if(!task)return;
 const meta=this.scopeMeta026?.(task)||{},scope=meta.target_scope||meta.scope||(task.animal_id?"animals":"general"),animalIds=scope==="animals"?[task.animal_id].filter(Boolean):(meta.target_animal_ids||[]),groupId=meta.target_group_id||meta.group_id||"";
 this.aiTaskDraft=this.taskDraft034(task,continued);this._targetStates026=this._targetStates026||{};this._targetStates026.task={scope:["general","group","animals"].includes(scope)?scope:"animals",groupId:String(groupId||""),animalIds:[...new Set(animalIds.map(String))]};this.modal={type:"create-task",animalId:animalIds[0]||""};this.render()
};
AH034.taskForm=function(){
 let html=AH034Base.taskForm.call(this),draft=this.aiTaskDraft;if(!draft)return html;
 html=this.prefillInput087(html,"end_date",draft.end_date||"");html=this.prefillInput087(html,"planned_care_action",draft.planned_care_action||"");html=this.prefillInput087(html,"treatment_plan_name",draft.treatment_plan_name||"");html=this.prefillInput087(html,"planned_treatment_plan_id",draft.planned_treatment_plan_id||"");return html
};
AH034.androidV0928Store034=function(){try{const value=JSON.parse(localStorage.getItem("animal_health_v0934_product_databases")||"{}");return value&&typeof value==="object"?value:{}}catch(_error){return{}}};
AH034.saveAndroidV0928Store034=function(store){localStorage.setItem("animal_health_v0934_product_databases",JSON.stringify(store))};
AH034.defaultDatabases034=function(){return[
 {id:"swissmedic_ch",name:"Swissmedic Tierarzneimittel",description:"Offizielle Schweizer Tierarzneimittel.",product_types:["medication"],source_type:"official",source_name:"Swissmedic",enabled:true,priority:100,version:"bundled",is_system:true,supports_local_overrides:true},
 {id:"swissmedic_dewormers",name:"Swissmedic Entwurmungsmittel",description:"Entwurmungsmittel aus dem Schweizer Tierarzneimittelbestand.",product_types:["deworming"],source_type:"official",source_name:"Swissmedic",enabled:true,priority:95,version:"bundled",is_system:true,supports_local_overrides:true,view_of:"swissmedic_ch"},
 {id:"vaccines_ch",name:"Impfstoffe Schweiz",description:"Mitgelieferte Schweizer Impfstoffdaten.",product_types:["vaccination"],source_type:"bundled",source_name:"Animal Health",enabled:true,priority:80,version:"bundled",is_system:true,supports_local_overrides:true},
 {id:"animal_health_supplements",name:"Ergänzungen",description:"Mitgelieferte Ergänzungsprodukte.",product_types:["supplement"],source_type:"bundled",source_name:"Animal Health",enabled:true,priority:60,version:"bundled",is_system:true,supports_local_overrides:true},
 {id:"animal_health_feed_chicken",name:"Futtermittel Hühner",description:"Mitgelieferte Futtermittel für Hühner.",product_types:["feed"],source_type:"bundled",source_name:"Animal Health",enabled:true,priority:60,version:"bundled",is_system:true,supports_local_overrides:true},
 {id:"user_curated",name:"Eigene Produkte",description:"Lokal angelegte und importierte Produkte.",product_types:["medication","vaccination","deworming","supplement","feed"],source_type:"user",source_name:"Lokal",enabled:true,priority:120,version:"local",is_system:true,supports_local_overrides:false}
]};
AH034.productArray034=function(document,keys=[]){if(Array.isArray(document))return document;if(!document||typeof document!=="object")return[];for(const key of["products","items","entries",...keys])if(Array.isArray(document[key]))return document[key];return[]};
AH034.normaliseBundledProducts034=function(document,databaseId,kind,keys=[]){
 return this.productArray034(document,keys).map((raw,index)=>{const source=raw&&typeof raw==="object"?raw:{name:String(raw||"")},fields=source.fields&&typeof source.fields==="object"?source.fields:{},item={...source,...fields},name=String(item.name||item.product_name||item.name_de||item.label||"").trim();return{...item,id:String(item.id||item.item_id||`${databaseId}-${index+1}`),database_id:databaseId,kind:String(item.kind||item.product_type||kind),name,target_species:Array.isArray(item.target_species)?item.target_species:Array.isArray(item.species)?item.species:[],hidden:false,is_hidden:false,is_custom:false,is_modified:false,source_type:"bundled",fields:{...item}}}).filter(item=>item.name)
};
AH034.loadAndroidBundle034=async function(){
 if(this._androidBundle034)return this._androidBundle034;
 const read=async name=>{try{const response=await fetch(name,{cache:"no-store"});return response.ok?await response.json():null}catch(_error){return null}},[databaseDocument,medicines,vaccines]=await Promise.all([read("product_databases_0928.json"),read("medicines_ch.json"),read("vaccines_ch.json")]),defaults=this.defaultDatabases034(),catalogDatabases=Array.isArray(databaseDocument?.databases)?databaseDocument.databases:[],byId=new Map(defaults.map(item=>[String(item.id),{...item}]));
 for(const database of catalogDatabases){const id=String(database?.id||"");if(id)byId.set(id,{...(byId.get(id)||{}),...database,enabled:database.enabled!==false})}
 const databases=[...byId.values()],products=[];
 if(Array.isArray(databaseDocument?.products))products.push(...databaseDocument.products);
 for(const database of catalogDatabases){const id=String(database?.id||"");if(id)products.push(...this.normaliseBundledProducts034(database?.products||[],id,String(database?.product_types?.[0]||"supplement")))}
 products.push(...this.normaliseBundledProducts034(databaseDocument?.supplements||[],"animal_health_supplements","supplement",["supplements"]));products.push(...this.normaliseBundledProducts034(databaseDocument?.feeds||databaseDocument?.chicken_feed||[],"animal_health_feed_chicken","feed",["feeds","chicken_feed"]));products.push(...this.normaliseBundledProducts034(medicines,"swissmedic_ch","medication",["medicines","records"]));products.push(...this.normaliseBundledProducts034(vaccines,"vaccines_ch","vaccination",["vaccines","records"]));
 for(const product of products){const classifications=Array.isArray(product.classifications)?[...product.classifications]:[];if(product.database_id==="swissmedic_ch"&&/worm|wurm|anthelm|entwurm|fluben|fenbend|ivermect/i.test(`${product.name} ${JSON.stringify(product.fields||{})}`)&&!classifications.includes("deworming"))classifications.push("deworming");product.classifications=classifications}
 const unique=new Map();for(const product of products){const key=`${product.database_id}:${product.id}`;if(!unique.has(key))unique.set(key,product)}this._androidBundle034={databases,products:[...unique.values()]};return this._androidBundle034
};
AH034.productMergeKey034=function(item){const field=item?.fields||{},authorisation=String(item?.authorisation_number||field.authorisation_number||item?.registration_number||field.registration_number||"").trim().toLocaleLowerCase(),name=String(item?.name||"").trim().toLocaleLowerCase();return`${item?.kind||"product"}:${authorisation||name}`};
AH034.androidV0928State034=async function(){
 const bundle=await this.loadAndroidBundle034(),store=this.androidV0928Store034(),enabled=store.enabled||{},hidden=store.hidden||{},overrides=store.overrides||{},userDatabases=Array.isArray(store.databases)?store.databases:[],userProducts=Array.isArray(store.products)?store.products:[],databases=[...bundle.databases.map(item=>({...item,enabled:enabled[item.id]!==undefined?Boolean(enabled[item.id]):item.enabled!==false})),...userDatabases.map(item=>({...item,enabled:enabled[item.id]!==undefined?Boolean(enabled[item.id]):item.enabled!==false}))],products=[...bundle.products,...userProducts].map(item=>{const override=overrides[item.id]||{},isHidden=Boolean(hidden[item.id]??item.is_hidden??item.hidden);return{...item,...override,hidden:isHidden,is_hidden:isHidden,is_modified:Boolean(Object.keys(override).length)}}),priority=new Map(databases.map(database=>[String(database.id),Number(database.priority||0)]));
 for(const database of databases)database.item_count=String(database.id)==="swissmedic_dewormers"?products.filter(item=>item.database_id==="swissmedic_ch"&&(item.classifications||[]).includes("deworming")).length:products.filter(item=>String(item.database_id)===String(database.id)).length;
 const active=new Set(databases.filter(database=>database.enabled!==false).map(database=>String(database.id))),mergedMap=new Map();for(const item of products.filter(item=>!item.is_hidden&&active.has(String(item.database_id))).sort((a,b)=>(priority.get(String(b.database_id))||0)-(priority.get(String(a.database_id))||0))){const key=this.productMergeKey034(item);if(key&&!mergedMap.has(key))mergedMap.set(key,item)}
 return{databases,products,merged_products:[...mergedMap.values()],views:{deworming_database_id:"swissmedic_dewormers",swissmedic_database_id:"swissmedic_ch"}}
};
AH034.androidV0928Command034=async function(type,payload={}){
 const store=this.androidV0928Store034();store.databases=Array.isArray(store.databases)?store.databases:[];store.products=Array.isArray(store.products)?store.products:[];store.enabled=store.enabled||{};store.hidden=store.hidden||{};store.overrides=store.overrides||{};
 if(type.endsWith("/state"))return this.androidV0928State034();
 if(type.endsWith("/database/toggle"))store.enabled[payload.database_id]=Boolean(payload.enabled);
 else if(type.endsWith("/database/delete")){store.databases=store.databases.filter(item=>String(item.id)!==String(payload.database_id));store.products=store.products.filter(item=>String(item.database_id)!==String(payload.database_id))}
 else if(type.endsWith("/database/save")){const fields=payload.fields||{},id=String(payload.database_id||`user-${Date.now()}`),current=store.databases.find(item=>String(item.id)===id),item={...(current||{}),id,name:String(payload.name||current?.name||"Eigene Datenbank"),description:String(fields.description||current?.description||""),product_types:Array.isArray(payload.product_types)?payload.product_types:current?.product_types||[],source_type:"user",source_name:String(fields.source_name||current?.source_name||"Lokal"),priority:Number(fields.priority??current?.priority??100),enabled:true,version:String(fields.version||current?.version||"local"),is_system:false,supports_local_overrides:false};store.databases=store.databases.filter(entry=>String(entry.id)!==id);store.databases.push(item)}
 else if(type.endsWith("/database/import")){const document=payload.document||{},topProducts=Array.isArray(document.products)?document.products:[],sourceDatabases=Array.isArray(document.databases)?document.databases:document.database?[document.database]:[{name:document.name||"Importierte Datenbank",description:document.description||"",product_types:document.product_types||["medication","vaccination","deworming","supplement","feed"],products:topProducts}];for(const source of sourceDatabases){const sourceId=String(source.id||""),id=`import-${Date.now()}-${Math.random().toString(36).slice(2,7)}`,item={...source,id,source_type:"user",source_name:source.source_name||"Import",enabled:true,is_system:false,supports_local_overrides:false};delete item.products;store.databases.push(item);const nested=Array.isArray(source.products)?source.products:[],matches=topProducts.filter(entry=>!entry.database_id||!sourceId||String(entry.database_id)===sourceId);for(const product of[...nested,...matches])store.products.push({...product,...(product.fields||{}),id:`${id}-${Math.random().toString(36).slice(2,9)}`,database_id:id,is_custom:true,is_modified:false,is_hidden:false,hidden:false,source_type:"user",fields:{...(product.fields||{}),...product}})}}
 else if(type.endsWith("/product/save")){const id=String(payload.item_id||`product-${Date.now()}-${Math.random().toString(36).slice(2,7)}`),state=await this.androidV0928State034(),existing=state.products.find(item=>String(item.id)===id),item={...(existing||{}),...(payload.fields||{}),id,database_id:String(payload.database_id||existing?.database_id||"user_curated"),kind:String(payload.kind||existing?.kind||"medication"),name:String(payload.name||existing?.name||""),target_species:Array.isArray(payload.target_species)?payload.target_species:existing?.target_species||[],fields:{...(existing?.fields||{}),...(payload.fields||{})},is_custom:!existing||existing.source_type==="user",source_type:existing?.source_type||"user",hidden:false,is_hidden:false};if(existing&&existing.source_type!=="user")store.overrides[id]=item;else{store.products=store.products.filter(entry=>String(entry.id)!==id);store.products.push(item)}}
 else if(type.endsWith("/product/archive"))store.hidden[payload.item_id]=Boolean(payload.hidden);
 else if(type.endsWith("/product/reset")){delete store.hidden[payload.item_id];delete store.overrides[payload.item_id]}
 else if(type.endsWith("/product/delete")){const before=store.products.length;store.products=store.products.filter(item=>String(item.id)!==String(payload.item_id));if(before===store.products.length)store.hidden[payload.item_id]=true}
 else throw Error(this.t("databaseLoadUnavailable034"));
 this.saveAndroidV0928Store034(store);return this.androidV0928State034()
};
AH034.ws=function(type,payload={}){if(typeof globalThis.AndroidBridge!=="undefined"&&String(type).startsWith(`${D}/v0928/`))return this.androidV0928Command034(type,payload);return AH034Base.ws.call(this,type,payload)};
AH034.loadV0928=async function(){this.v0928Error030="";try{const state=await this.ws(`${D}/v0928/state`);this.v0928=state&&Array.isArray(state.databases)?state:{databases:[],products:[],merged_products:[],views:{}}}catch(_error){this.v0928={databases:[],products:[],merged_products:[],views:{}};this.v0928Error030=this.t("databaseLoadUnavailable034")}};
AH034.navMarker034=function(snapshot,depth){return{version:2,depth:Math.max(0,Number(depth||0)),snapshot}};
AH034.currentNavMarker034=function(){const state=globalThis.history?.state;return state&&typeof state==="object"?state.__animalHealthNav034:null};
AH034.writeNavEntry034=function(snapshot,{push=false,depth=this._ahNavDepth034||0}={}){try{const current=globalThis.history?.state,state=current&&typeof current==="object"?{...current}:{},marker=this.navMarker034(snapshot,depth);delete state.__animalHealthNav033;state.__animalHealthNav034=marker;if(push)globalThis.history.pushState(state,"",globalThis.location.href);else globalThis.history.replaceState(state,"",globalThis.location.href);this._ahNavDepth034=marker.depth}catch(_error){}};
AH034.requestBack034=function(){const marker=this.currentNavMarker034(),depth=Math.max(0,Number(marker?.depth??this._ahNavDepth034??0));if(depth<=0)return false;if(this._ahBackPending034)return true;this._ahBackPending034=true;globalThis.history.back();clearTimeout(this._ahBackTimer034);this._ahBackTimer034=setTimeout(()=>{this._ahBackPending034=false},1200);return true};
AH034.restoreNavSnapshot034=async function(marker){
 if(!marker?.snapshot)return;const resumeAnimal=Boolean(this._resumeAfterAnimal034)&&(this.modal?.type==="create-animal"||this._animalCreationCompleted034);this._ahNavRestoring034=true;this._ahNavDepth034=Math.max(0,Number(marker.depth||0));
 try{await this.restoreNavSnapshot033(marker);if(resumeAnimal&&this._resumeAfterAnimal034){const completed=this._animalCreationCompleted034;this._animalCreationCompleted034=false;if(completed)this.finishAnimalCreation034();else{const resume=this._resumeAfterAnimal034;this._targetStates026=this._targetStates026||{};this._targetStates026[resume.key]=resume.targetState;this.modal=resume.modal;this._resumeAfterAnimal034=null;this.render();this.restoreFormState034(this.shadowRoot.querySelector(".modal form"),resume.formState)}}}finally{this._ahNavRestoring034=false}
};
AH034.bindInternalHistory034=function(){
 if(this._ahNavPopHandler033){globalThis.removeEventListener("popstate",this._ahNavPopHandler033);this._ahNavPopHandler033=null}if(this._ahNavPopHandler034)return;
 this._ahNavPopHandler034=event=>{this._ahBackPending034=false;clearTimeout(this._ahBackTimer034);const marker=event.state?.__animalHealthNav034;if(marker)void this.restoreNavSnapshot034(marker)};globalThis.addEventListener("popstate",this._ahNavPopHandler034);const current=this.currentNavMarker034();if(current)this._ahNavDepth034=Math.max(0,Number(current.depth||0));else this.writeNavEntry034(this.navSnapshot033(),{depth:0});this._nativeBackHandler034=()=>this.requestBack034();globalThis.__animalHealthHandleBack034=this._nativeBackHandler034
};
AH034.connectedCallback=function(){AH033Base.connectedCallback.call(this);queueMicrotask(()=>this.bindInternalHistory034())};
AH034.disconnectedCallback=function(){if(this._ahNavPopHandler034){globalThis.removeEventListener("popstate",this._ahNavPopHandler034);this._ahNavPopHandler034=null}clearTimeout(this._ahBackTimer034);if(globalThis.__animalHealthHandleBack034===this._nativeBackHandler034)delete globalThis.__animalHealthHandleBack034;if(AH033Base.disconnectedCallback)AH033Base.disconnectedCallback.call(this)};
AH034.performCustomClick034=async function(button){
 const action=String(button?.dataset?.action||"");
 if(action==="target-animal-remove-034"){const state=this.ensureTargetState026(button.dataset.key);state.animalIds=(state.animalIds||[]).filter(id=>String(id)!==String(button.dataset.id));this.updateTargetCompatibility026(button.dataset.key);this.refreshTaskOptions012?.(this.shadowRoot.querySelector(".modal form"));return true}
 if(action==="target-animal-create-034"){this.beginAnimalCreation034(button.dataset.key);return true}
 if(action==="multi-remove-034"){const root=button.closest("[data-multi-choice034]"),input=[...root.querySelectorAll("[data-multi-option034]")].find(item=>String(item.value)===String(button.dataset.value));if(input)input.checked=false;this.refreshMultiChoice034(root);return true}
 if(action==="multi-custom-034"){this.addCustomChoice034(button.closest("[data-multi-choice034]"));return true}
 if(action==="task-duplicate-034"||action==="task-continue-034"){const task=this.task?.(button.dataset.id)||(this.d?.tasks||[]).find(item=>String(item.id)===String(button.dataset.id));this.openTaskCopy034(task,action==="task-continue-034");return true}
 return false
};
AH034.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset&&(node.dataset.action||node.dataset.view));if(!button)return AH033Base.handleClick.call(this,event);
 const before=this.navSnapshot033(),backward=this.backwardControl033(button),current=this.currentNavMarker034(),depth=Math.max(0,Number(current?.depth??this._ahNavDepth034??0));if(backward&&depth>0){this.requestBack034();return}
 const handled=await this.performCustomClick034(button),result=handled?undefined:await AH033Base.handleClick.call(this,event),after=this.navSnapshot033();if(this._ahNavRestoring034||this.navSignature033(before)===this.navSignature033(after))return result;if(backward){this.writeNavEntry034(after,{depth});return result}this.writeNavEntry034(before,{depth});this.writeNavEntry034(after,{push:true,depth:depth+1});return result
};
AH034.handleChange=function(event){
 const input=event.composedPath()[0];
 if(input?.dataset?.targetAnimalAdd034!==undefined){const key=input.dataset.targetAnimalAdd034,state=this.ensureTargetState026(key);if(input.value&&!state.animalIds.includes(input.value))state.animalIds.push(input.value);this.updateTargetCompatibility026(key);this.refreshTaskOptions012?.(this.shadowRoot.querySelector(".modal form"));return}
 if(input?.dataset?.multiAdd034!==undefined){const root=input.closest("[data-multi-choice034]"),option=[...root.querySelectorAll("[data-multi-option034]")].find(item=>String(item.value)===String(input.value));if(option)option.checked=true;this.refreshMultiChoice034(root);return}
 return AH034Base.handleChange.call(this,event)
};
AH034.handleSubmit=async function(event){
 const form=event.composedPath().find(node=>node?.tagName==="FORM"),animalResume=form?.dataset.form==="animal"&&Boolean(this._resumeAfterAnimal034),taskForm=form?.dataset.form==="task",result=await AH033Base.handleSubmit.call(this,event);
 if(animalResume&&this.modal?.type!=="create-animal"){if(this.requestBack034())this._animalCreationCompleted034=true;else this.finishAnimalCreation034()}
 if(taskForm&&this.modal?.type!=="create-task")this.aiTaskDraft=null;if(!this._ahNavRestoring034){const current=this.currentNavMarker034();if(current)this.writeNavEntry034(this.navSnapshot033(),{depth:current.depth})}return result
};
AH034.render=function(){
 AH033Base.render.call(this);this.shadowRoot.innerHTML+=`<style>
.gabeCompact034{align-items:flex-start!important}.gabeContent034{display:block;min-width:0;width:100%}.gabeFlow034{display:block;min-width:0;line-height:1.28;overflow-wrap:anywhere}.gabeAnimal034{font-weight:650}.gabeDose034{font-weight:650;color:var(--secondary-text-color);white-space:nowrap}.gabeTitle034{display:inline;font-weight:700}.gabeSeparator034{white-space:pre}.gabeMetaInline034{color:var(--secondary-text-color);font-size:.82rem;font-weight:400}.gabeMetaInline034 i{font-style:italic}.gabeFlow034>.gabeTypeBadge027,.gabeFlow034>.scopeBadge026{display:inline-flex!important;width:auto!important;max-width:100%;margin:0 0 0 5px!important;vertical-align:.08em}.taskSource034{position:static!important;display:inline-flex!important;width:18px!important;height:18px!important;min-width:18px!important;margin:0 0 0 5px!important;vertical-align:-.22em!important;transform:none!important;inset:auto!important}.treatmentTaskSource034{display:inline}.treatmentSummary021 .bundleText021>b{white-space:normal!important;overflow:visible!important;text-overflow:clip!important}.treatmentPlanComponents034{display:grid!important;gap:1px;margin-top:2px}.multiChoice034,.animalPicker034{display:grid;gap:7px;min-width:0}.multiChips034{display:flex;flex-wrap:wrap;gap:6px;min-height:0}.multiChip034{display:inline-flex!important;align-items:center;gap:5px;min-width:0;max-width:100%;padding:7px 9px!important;border:1px solid var(--divider-color)!important;border-radius:999px!important;background:var(--secondary-background-color)!important}.multiChip034 span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.multiChip034 ha-icon{width:18px;height:18px;flex:0 0 auto}.multiPicker034{display:grid;grid-template-columns:minmax(0,1fr) 54px;gap:0;min-width:0}.multiPicker034 select{min-width:0;border-radius:9px 0 0 9px!important}.multiPicker034>button{min-width:54px;border-radius:0 9px 9px 0!important;border-left:0!important;display:grid!important;place-items:center}.multiHidden034{display:none}.targetSelector034 .targetPanel026[data-target-panel026="animals"]{min-width:0}.taskDefinition097.completed034{opacity:1}.taskDefinition097.completed034 .taskDefinitionBadges097 span:nth-child(2){border-color:var(--success-color,#43a047);color:var(--success-color,#43a047)}.taskDefinitionActions097{flex-wrap:wrap}@media(max-width:600px){.gabeMetaInline034{font-size:.78rem}.taskSource034{width:17px!important;height:17px!important;min-width:17px!important}.multiPicker034{grid-template-columns:minmax(0,1fr) 50px}.multiPicker034>button{min-width:50px}}
</style>`
};
