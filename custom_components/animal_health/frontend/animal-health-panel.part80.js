Object.assign(T,{
 targetGroup026:["Gruppe","Group"],
 targetAnimals026:["Tiere","Animals"],
 targetAnimal026:["Tier","Animal"],
 targetGeneral026:["Allgemein","General"],
 targetSelectAnimals026:["Tiere auswählen","Select animals"],
 targetSelectedAnimals026:["Tiere ausgewählt","animals selected"],
 targetSelectGroup026:["Tiergruppe auswählen","Select animal group"],
 targetEmptyGroup026:["Die ausgewählte Tiergruppe enthält keine Tiere.","The selected animal group contains no animals."],
 targetRequired026:["Bitte mindestens ein Tier oder eine Tiergruppe auswählen.","Select at least one animal or an animal group."],
 groupAction026:["Gruppenaktion","Group action"],
 attachments026:["Anhänge","Attachments"],
 moveStepUp026:["Behandlungsschritt nach oben","Move treatment step up"],
 moveStepDown026:["Behandlungsschritt nach unten","Move treatment step down"]
});
const AH026=AnimalHealthPanel.prototype;
const AH026Base={
 open:AH026.open,
 taskForm:AH026.taskForm,
 syncTask:AH026.syncTask,
 taskCompact:AH026.taskCompact,
 taskManagementRow097:AH026.taskManagementRow097,
 symptomForm015:AH026.symptomForm015,
 medicationBatchForm0817:AH026.medicationBatchForm0817,
 treatmentPlanExecutionForm012:AH026.treatmentPlanExecutionForm012,
 openTreatmentPlanExecution012:AH026.openTreatmentPlanExecution012,
 planComponentRow012:AH026.planComponentRow012,
 treatmentBundle021:AH026.treatmentBundle021,
 eventCompact0817:AH026.eventCompact0817,
 fileFields:AH026.fileFields,
 handleInput:AH026.handleInput,
 handleChange:AH026.handleChange,
 handleClick:AH026.handleClick,
 handleSubmit:AH026.handleSubmit,
 render:AH026.render
};

AH026.targetAnimals026=function(){return(this.d?.animals||[]).filter(animal=>!animal.is_archived)};
AH026.targetGroups026=function(){const groups=this.orderedGroups017?.()||this.activeGroups?.()||this.features?.groups||[];return[...groups]};
AH026.targetAnimalsInGroup026=function(groupId){return this.targetAnimals026().filter(animal=>String(animal.group_id||"")===String(groupId||""))};
AH026.targetState026=function(key,initialAnimalId="",includeGeneral=false){this._targetStates026=this._targetStates026||{};let state=this._targetStates026[key];if(!state){const initial=String(initialAnimalId||"");state={scope:"animals",animalIds:initial?[initial]:[],groupId:"",open:false,includeGeneral:Boolean(includeGeneral)};this._targetStates026[key]=state}if(initialAnimalId&&!state.animalIds.length&&state.scope==="animals")state.animalIds=[String(initialAnimalId)];return state};
AH026.clearTargetState026=function(key=""){if(!this._targetStates026)return;if(key)delete this._targetStates026[key];else this._targetStates026={}};
AH026.targetCompatAnimal026=function(state){if(state?.scope==="group")return this.targetAnimalsInGroup026(state.groupId)[0]?.id||"";return state?.animalIds?.[0]||""};
AH026.targetSummary026=function(state){const animals=this.targetAnimals026(),ids=new Set((state?.animalIds||[]).map(String)),selected=animals.filter(animal=>ids.has(String(animal.id)));if(!selected.length)return this.t("targetSelectAnimals026");if(selected.length<=2)return selected.map(animal=>animal.name).join(" · ");return`${selected.length} ${this.t("targetSelectedAnimals026")}`};
AH026.targetSelector026=function(key,{initialAnimalId="",includeGeneral=false}={}){const state=this.targetState026(key,initialAnimalId,includeGeneral),groups=this.targetGroups026(),animals=this.targetAnimals026();if(!state.groupId&&groups.length)state.groupId=String(groups[0].id);const compat=this.targetCompatAnimal026(state),segments=includeGeneral?[["general","targetGeneral026"],["group","targetGroup026"],["animals","targetAnimal026"]]:[["group","targetGroup026"],["animals","targetAnimals026"]];return`<div class="wide targetSelector026" data-target-selector026="${esc(key)}"><div class="scopeSwitch026" role="group" aria-label="${esc(this.t("task_scope"))}">${segments.map(([scope,label])=>`<button type="button" data-action="target-scope-026" data-key="${esc(key)}" data-scope="${scope}" class="${state.scope===scope?"active026":""}" aria-pressed="${state.scope===scope?"true":"false"}">${this.t(label)}</button>`).join("")}</div>${includeGeneral?`<input type="hidden" name="task_scope" value="${state.scope==="general"?"general":"animal"}">`:""}<input type="hidden" name="animal_id" value="${esc(compat)}"><div class="targetPanel026" data-target-panel026="general" ${state.scope==="general"?"":"hidden"}></div><div class="targetPanel026" data-target-panel026="group" ${state.scope==="group"?"":"hidden"}><label><span>${this.t("targetGroup026")}</span><select data-target-group026 data-key="${esc(key)}">${groups.map(group=>`<option value="${esc(group.id)}" ${String(group.id)===String(state.groupId)?"selected":""}>${esc(group.name)}</option>`).join("")}</select></label></div><div class="targetPanel026" data-target-panel026="animals" ${state.scope==="animals"?"":"hidden"}><details class="animalMulti026"><summary><span data-target-summary026>${esc(this.targetSummary026(state))}</span><ha-icon icon="mdi:chevron-down"></ha-icon></summary><div class="animalMultiList026">${animals.map(animal=>`<label><input type="checkbox" data-target-animal026 data-key="${esc(key)}" value="${esc(animal.id)}" ${(state.animalIds||[]).map(String).includes(String(animal.id))?"checked":""}><span>${esc(animal.name)}</span></label>`).join("")}</div></details></div></div>`};
AH026.targetStateFromForm026=function(form,key){return this._targetStates026?.[key]||this.targetState026(key,form?.elements?.animal_id?.value||"")};
AH026.targetPayload026=function(key){const state=this._targetStates026?.[key];if(!state)throw Error(this.t("targetRequired026"));if(state.scope==="general")return{target_scope:"general"};if(state.scope==="group"){if(!state.groupId)throw Error(this.t("targetRequired026"));const members=this.targetAnimalsInGroup026(state.groupId);if(!members.length)throw Error(this.t("targetEmptyGroup026"));return{target_scope:"group",group_id:state.groupId}}if(!state.animalIds?.length)throw Error(this.t("selectOne"));return{target_scope:"animals",animal_ids:[...state.animalIds]}};
AH026.updateTargetCompatibility026=function(wrapper,state){if(!wrapper||!state)return;const compat=wrapper.querySelector('input[name="animal_id"]');if(compat)compat.value=this.targetCompatAnimal026(state);const scope=wrapper.querySelector('input[name="task_scope"]');if(scope)scope.value=state.scope==="general"?"general":"animal";const summary=wrapper.querySelector("[data-target-summary026]");if(summary)summary.textContent=this.targetSummary026(state)};
AH026.scopeMeta026=function(item){const direct=item?.data||{},planned=item?.planned||direct.planned||direct.task_execution?.planned||{};const source=direct.target_scope?direct:planned;return{scope:String(source?.target_scope||""),groupId:String(source?.target_group_id||""),groupName:String(source?.target_group_name||"")}};
AH026.scopeBadge026=function(item){const meta=this.scopeMeta026(item);if(meta.scope!=="group")return"";const group=meta.groupName||this.groupById?.(meta.groupId)?.name||this.t("targetGroup026");return`${this.t("groupAction026")} · ${group}`};

AH026.open=function(type,extra={}){if(type!==this.modal?.type)this.clearTargetState026();return AH026Base.open.call(this,type,extra)};
AH026.openTreatmentPlanExecution012=function(planId,animalId=""){this.clearTargetState026("treatment");return AH026Base.openTreatmentPlanExecution012.call(this,planId,animalId)};
AH026.taskForm=function(){let html=AH026Base.taskForm.call(this),selector=this.targetSelector026("task",{initialAnimalId:this.modal?.animalId||this.detail?.animal?.id||"",includeGeneral:true});html=html.replace(/<label><span>[^<]*<\/span><select name="task_scope"[^>]*>[\s\S]*?<\/select><\/label>/,selector);html=html.replace(/<fieldset class="wide" data-animals>[\s\S]*?<\/fieldset>/,"");return html};
AH026.symptomForm015=function(){let html=AH026Base.symptomForm015.call(this),selector=this.targetSelector026("symptom",{initialAnimalId:this.modal?.animalId||this.detail?.animal?.id||""});return html.replace(/<label class="wide"><span>[^<]*<\/span><select name="animal_id"[^>]*>[\s\S]*?<\/select><\/label>/,selector)};
AH026.medicationBatchForm0817=function(){let html=AH026Base.medicationBatchForm0817.call(this),state=this.medBatch0817||{},selector=this.targetSelector026("medication",{initialAnimalId:state.animalId||this.modal?.animalId||this.detail?.animal?.id||""});return html.replace(/<label><span>[^<]*<\/span><select name="animal_id"[^>]*>[\s\S]*?<\/select><\/label>/,selector)};
AH026.treatmentPlanExecutionForm012=function(){let html=AH026Base.treatmentPlanExecutionForm012.call(this),state=this.planExecution012||{},selector=this.targetSelector026("treatment",{initialAnimalId:state.animalId||this.modal?.animalId||this.detail?.animal?.id||""});return html.replace(/<label><span>[^<]*<\/span><select name="animal_id"[^>]*>[\s\S]*?<\/select><\/label>/,selector)};
AH026.syncTask=function(form){const wrapper=form?.querySelector?.('[data-target-selector026="task"]'),state=this._targetStates026?.task;if(wrapper&&state)this.updateTargetCompatibility026(wrapper,state);return AH026Base.syncTask.call(this,form)};

AH026.planComponentRow012=function(item,index,units,routes){let html=AH026Base.planComponentRow012.call(this,item,index,units,routes),count=this.ensurePlanDraft012()?.components?.length||0,controls=`<div class="planOrder026"><button type="button" data-action="plan-component-up-026" data-index="${index}" ${index<=0?"disabled":""} title="${esc(this.t("moveStepUp026"))}" aria-label="${esc(this.t("moveStepUp026"))}"><ha-icon icon="mdi:chevron-up"></ha-icon></button><button type="button" data-action="plan-component-down-026" data-index="${index}" ${index>=count-1?"disabled":""} title="${esc(this.t("moveStepDown026"))}" aria-label="${esc(this.t("moveStepDown026"))}"><ha-icon icon="mdi:chevron-down"></ha-icon></button></div>`;return html.replace("</article>",`${controls}</article>`)};

