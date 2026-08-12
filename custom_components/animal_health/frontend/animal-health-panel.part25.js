Object.assign(T,{
 aiReviewRequired086:["Noch nicht geprüft","Not yet reviewed"],
 aiReviewUndo086:["Prüfung zurücknehmen","Undo review"]
});
const AH086=AnimalHealthPanel.prototype;
const AH086Base={
 handleSubmit:AH086.handleSubmit,
 handleClick:AH086.handleClick,
 render:AH086.render
};
AH086.aiBatchDataComplete086=function(entry){
 if(!entry||entry.status==="discarded"||entry.status==="saved")return false;
 const animalId=entry.animal_id||entry.matched_animal_id;
 if(!animalId)return false;
 const type=entry.suggested_record_type;
 if(type==="weight")return Number(entry.weight)>0&&Boolean(entry.weight_unit);
 if(type==="medication")return Boolean(entry.medication_name)&&Boolean(entry.dose)&&Boolean(entry.dose_unit);
 return Boolean(entry.suggested_title||entry.medication_name||entry.treatment||entry.visit_reason)
};
AH086.aiBatchReady083=function(entry){return Boolean(entry?.reviewed)&&this.aiBatchDataComplete086(entry)};
AH086.aiBatchStatus083=function(entry){
 if(entry?.status==="saved")return this.t("aiSaved");
 if(entry?.status==="discarded")return this.t("aiDiscard");
 if(entry?.reviewed&&this.aiBatchDataComplete086(entry))return this.t("aiReviewed");
 return this.t("aiReviewRequired086")
};
AH086.updateBatchField083=function(input){
 if(!input?.dataset?.batchField083||!this.aiBatch083?.length)return;
 const entry=this.aiBatch083[this.aiBatchIndex083||0];
 entry[input.dataset.batchField083]=input.value;
 entry.reviewed=false;
 if(input.dataset.batchField083==="animal_id"){
  const animal=this.animal(input.value);
  entry.matched_animal_id=input.value;
  entry.animal_name=animal?.name||entry.animal_name
 }
};
AH086.aiBatchForm083=function(){
 const entries=this.aiBatch083||[],index=Math.min(Math.max(Number(this.aiBatchIndex083||0),0),Math.max(0,entries.length-1)),entry=entries[index]||{},animalId=entry.animal_id||entry.matched_animal_id||"",type=entry.suggested_record_type||"other",animals=(this.d?.animals||[]).filter(animal=>!animal.is_archived),overview=entries.map((item,i)=>`<button type="button" data-action="ai-batch-goto-083" data-index="${i}" class="${i===index?"on":""} ${item.status||""} ${item.reviewed?"reviewed086":""}"><span>${i+1}. ${esc(item.animal_name||item.suggested_title||item.medication_name||this.t("aiEntry"))}</span><small>${esc(this.aiBatchStatus083(item))}</small></button>`).join(""),animalSelect=`<label><span>${this.t("animal")}</span><select data-batch-field083="animal_id"><option value="">–</option>${animals.map(animal=>`<option value="${esc(animal.id)}" ${animal.id===animalId?"selected":""}>${esc(animal.name)}</option>`).join("")}</select></label>`,typeSelect=`<label><span>${this.t("event_type")}</span><select data-batch-field083="suggested_record_type">${["weight","medication","vaccination","treatment","health_check","veterinary_visit","reminder","other"].map(value=>`<option value="${value}" ${value===type?"selected":""}>${esc(this.l(value))}</option>`).join("")}</select></label>`;
 let fields="";
 if(type==="weight")fields=`${this.fieldBatch083("weight","weight",entry.weight,"number")}${this.selectBatch083("dose_unit","weight_unit",this.c?.weight_units||["g","kg"],entry.weight_unit||"kg")}${this.fieldBatch083("occurred_at","occurred_at",entry.occurred_at||entry.document_date,"datetime-local")}`;
 else if(type==="medication")fields=`${this.fieldBatch083("medication_name","medication_name",entry.medication_name)}${this.fieldBatch083("dose","dose",entry.dose,"number")}${this.selectBatch083("dose_unit","dose_unit",this.c?.dose_units||[],entry.dose_unit)}${this.selectBatch083("recurrence_type","recurrence_type",["once","daily","weekly","monthly"],entry.recurrence_type||"once")}${this.fieldBatch083("recurrence_interval","recurrence_interval",entry.recurrence_interval||"1","number")}${this.fieldBatch083("start_date","scheduled_date",entry.scheduled_date||entry.document_date||this.d?.today,"date")}`;
 else fields=`${this.fieldBatch083("title","suggested_title",entry.suggested_title||entry.treatment||entry.visit_reason)}${this.fieldBatch083("start_date","scheduled_date",entry.scheduled_date||entry.document_date||this.d?.today,"date")}`;
 const notes=`<label class="wide"><span>${this.t("notes")}</span><textarea rows="3" data-batch-field083="notes">${esc(entry.notes||"")}</textarea></label>`,details=this.aiRecognitionDetails083(entry),discarded=entry.status==="discarded",saved=entry.status==="saved",reviewed=Boolean(entry.reviewed),reviewLabel=reviewed?this.t("aiReviewUndo086"):this.t("aiReview"),reviewIcon=reviewed?"mdi:check-decagram":"mdi:check-circle-outline";
 return`<h2><ha-icon icon="mdi:creation-outline"></ha-icon>${this.t("aiBatch")}</h2><p>${entries.length} ${this.t("aiBatchCount")}</p><div class="aiBatchLayout083"><nav class="aiBatchOverview083">${overview}</nav><section class="aiBatchEditor083"><h3>${this.t("aiEntry")} ${index+1} / ${entries.length}</h3><div class="formgrid083">${animalSelect}${typeSelect}${fields}${notes}</div>${details}<div class="buttons wide aiBatchControls083"><button type="button" data-action="ai-batch-prev-083" ${index<=0?"disabled":""}><ha-icon icon="mdi:chevron-left"></ha-icon>${this.t("previous")}</button><button type="button" data-action="ai-batch-next-083" ${index>=entries.length-1?"disabled":""}>${this.t("next")}<ha-icon icon="mdi:chevron-right"></ha-icon></button><button type="button" data-action="ai-batch-review-083" aria-pressed="${reviewed?"true":"false"}" class="${reviewed?"primary reviewed086":""}" ${saved||discarded?"disabled":""}><ha-icon icon="${reviewIcon}"></ha-icon>${reviewLabel}</button><button type="button" data-action="ai-batch-discard-083" ${saved?"disabled":""}>${discarded?this.t("aiRestore"):this.t("aiDiscard")}</button><button type="button" class="primary" data-action="ai-batch-save-one-083" ${!this.aiBatchReady083(entry)?"disabled":""}>${this.t("aiSaveOne")}</button></div></section></div><div class="buttons wide"><button type="button" data-action="close">${this.t("close")}</button><button type="button" class="primary" data-action="ai-batch-save-all-083">${this.t("aiSaveReady")}</button></div>`
};
AH086.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset?.action),action=button?.dataset?.action;
 if(action==="ai-batch-review-083"){
  const entry=this.aiBatch083?.[this.aiBatchIndex083||0];
  if(entry){entry.reviewed=!entry.reviewed;this.render()}
  return
 }
 return AH086Base.handleClick.call(this,event)
};
AH086.handleSubmit=async function(event){
 await AH086Base.handleSubmit.call(this,event);
 if(this.modal?.type==="ai-batch-083"&&this.aiBatch083?.length&&!this.aiBatchReviewInitialized086){
  for(const entry of this.aiBatch083)entry.reviewed=false;
  this.aiBatchReviewInitialized086=true;
  this.render()
 }
};
AH086.render=function(){
 AH086Base.render.call(this);
 this.shadowRoot.innerHTML+=`<style>.aiBatchOverview083 .reviewed086 small{font-weight:700}.aiBatchControls083 .reviewed086{font-weight:700;box-shadow:inset 0 0 0 2px var(--primary-color)}</style>`
};
