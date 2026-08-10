const AH081ST=AnimalHealthPanel.prototype;
const AH081STBase={
 aiUploadForm:AH081Base.aiUploadForm,
 decorateV081:AH081ST.decorateV081,
 overview:AH081ST.overview,
 eventRow:AH081Base.eventRow,
 syncGroupEvent081:AH081ST.syncGroupEvent081,
 groupEventPayload081:AH081ST.groupEventPayload081,
 render:AH081ST.render
};
AH081ST.decorateV081=function(){
 AH081STBase.decorateV081.call(this);
 const configs=new Map((this.v081?.group_tasks||[]).map(item=>[String(item.task_id),item]));
 for(const task of this.d?.tasks||[]){const config=configs.get(String(task.id));if(!config)continue;task.animal_name=config.group_name}
 for(const occurrence of this.d?.occurrences||[]){const config=configs.get(String(occurrence.task_id));if(!config)continue;occurrence.animal_name=config.group_name}
};
AH081ST.overview=function(){
 const pending=this.pendingSorted(),now=Date.now(),limit=now+24*60*60*1000,urgent=pending.filter(item=>item.is_overdue||new Date(item.scheduled_local||item.scheduled_for).getTime()<=limit),basis=urgent.length?urgent:pending,shown=basis.slice(0,3),remaining=Math.max(0,basis.length-shown.length),urgentClass=urgent.length?"hasUrgent":"";
 return`<div class="operationalHeading"><h1>${this.t("overview")}</h1></div><section class="actionNow ${urgentClass}"><div class="actionNowHead"><div><small>${urgent.length?this.t("within24h"):this.t("nextTasks")}</small><h2>${this.t("actionNow")}</h2></div>${urgent.length?`<strong>${urgent.length}</strong>`:""}</div>${shown.length?shown.map(item=>this.taskCompact(item)).join(""):`<div class="nothingDue"><ha-icon icon="mdi:check-circle-outline"></ha-icon><span>${this.t("nothingDue")}</span></div>`}${remaining?`<button class="moreTasks" data-view="tasks">+${remaining} ${this.t("moreTasks")}</button>`:""}</section><section class="quickCaptureCard"><h2>${this.t("quickCapture")}</h2><div class="quickCaptureGrid"><button data-action="record-weight"><ha-icon icon="mdi:scale"></ha-icon><span>${this.t("recordWeight")}</span></button><button data-action="record-symptom"><ha-icon icon="mdi:alert-circle-outline"></ha-icon><span>${this.t("recordSymptom")}</span></button><button data-action="record-product"><ha-icon icon="mdi:pill"></ha-icon><span>${this.t("recordProduct")}</span></button><button data-action="record-event"><ha-icon icon="mdi:note-plus-outline"></ha-icon><span>${this.t("recordGeneral")}</span></button><button data-action="create-task"><ha-icon icon="mdi:clipboard-plus-outline"></ha-icon><span>${this.t("createTask")}</span></button><button data-action="ai-assist"><ha-icon icon="mdi:creation-outline"></ha-icon><span>${this.t("aiAssist")}</span></button></div></section>`
};
AH081ST.eventRow=function(event){
 if(event?.group_id)return AH081STBase.eventRow.call(this,event);
 let html=AH081STBase.eventRow.call(this,event),badge="";
 const corrected=(this.d?.events||[]).find(item=>String(item.correction_of_event_id||"")===String(event.id));
 if(corrected)badge=`<small class="correctionBadge"><ha-icon icon="mdi:check-decagram-outline"></ha-icon>${this.t("correctedEntry")}</small>`;
 else if(event?.correction_of_event_id)badge=`<small class="correctionBadge"><ha-icon icon="mdi:pencil-outline"></ha-icon>${this.t("correctionEntry")}</small>`;
 if(!badge)return html;const index=html.lastIndexOf("</div>");return index>=0?html.slice(0,index)+badge+html.slice(index):html+badge
};
AH081ST.syncGroupEvent081=function(form){
 AH081STBase.syncGroupEvent081.call(this,form);const kind=form?.elements?.event_type?.value||"observation",defaultBlock=form?.querySelector?.("[data-group-event-default]"),hide=["medication","weight","vaccination","veterinary_visit","treatment","care"].includes(kind);
 if(defaultBlock){defaultBlock.hidden=hide;for(const field of defaultBlock.querySelectorAll("input,select,textarea"))field.disabled=hide}
};
AH081ST.groupEventPayload081=function(form,values){return AH081STBase.groupEventPayload081.call(this,form,values)};
AH081ST.aiUploadForm=function(){
 const original=this.aiStatus||{},settings=this.v081?.settings||{},aiChosen=settings.ai_task_entity_id||"",sttChosen=settings.stt_entity_id||"";
 this.aiStatus={...original,entities:aiChosen?[aiChosen]:(original.entities||[]).slice(0,1),stt_entities:sttChosen?[sttChosen]:(original.stt_entities||[]).slice(0,1)};
 let html;try{html=AH081STBase.aiUploadForm.call(this)}finally{this.aiStatus=original}
 const hidden=`<input type="hidden" name="ai_entity_id" value="${esc(aiChosen)}"><input type="hidden" name="ai_stt_entity_id" value="${esc(sttChosen)}">`;
 html=html.replace('<form data-form="ai-upload">',`<form data-form="ai-upload">${hidden}`);
 const language=this.aiLastSttLanguage?`${this.t("sttLanguage")}: ${esc(this.aiLastSttLanguage)}`:"";
 return html.replace('<div class="buttons wide">',`<small class="wide sttLanguage081" data-stt-language>${language}</small><div class="buttons wide">`)
};
AH081ST.handleSubmit=async function(event){
 const form=event.composedPath().find(node=>node?.tagName==="FORM");
 if(form?.dataset.form==="group-event-081"){
  event.preventDefault();const values=data(form);this.busy=true;this.render();
  try{await this.ws(`${D}/v081/group_event/create_safe`,this.groupEventPayload081(form,values));this.busy=false;this.modal=null;await this.load();this.notify(this.t("done"))}catch(error){this.busy=false;this.notify(`${this.t("failed")}: ${error?.message||error}`,true);this.render()}return
 }
 return AH081.handleSubmit.call(this,event)
};
AH081ST.render=function(){AH081STBase.render.call(this);this.shadowRoot.innerHTML+=`<style>.operationalHeading{display:flex;align-items:center;justify-content:space-between;margin:2px 0 12px}.operationalHeading h1{margin:0}.correctionBadge{display:inline-flex!important;align-items:center;gap:4px;color:var(--primary-color);font-size:.78rem}.correctionBadge ha-icon{width:15px;height:15px}</style>`};
