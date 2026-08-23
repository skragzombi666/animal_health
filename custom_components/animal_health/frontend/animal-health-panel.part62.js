Object.assign(T,{
 choosePlanMedication014:["Medikament auswählen oder suchen","Choose or search medication"]
});
Object.assign(L,{
 coffee_spoon:["Kaffeelöffel","Coffee spoon"],
 oral:["Oral","Oral"],
 topical:["Topisch","Topical"],
 subcutaneous:["Subkutan","Subcutaneous"],
 intramuscular:["Intramuskulär","Intramuscular"],
 intravenous:["Intravenös","Intravenous"],
 eye:["Auge","Eye"],
 ear:["Ohr","Ear"],
 spray:["Spray","Spray"]
});
const AH014=AnimalHealthPanel.prototype;
const AH014Base={
 planComponentRow012:AH014.planComponentRow012,
 handleInput:AH014.handleInput,
 handleChange:AH014.handleChange,
 handleClick:AH014.handleClick,
 seriesRelevantItems095:AH014.seriesRelevantItems095,
 render:AH014.render
};
AH014.planComponentRow012=function(item,index,units,routes){
 const action=item.type==="action",medication=item.type==="medication";
 const nameField=medication?`<label class="planComponentName012 planMedicationField014"><span>${this.t("componentName012")}</span><div class="planMedicationControl014"><input data-plan-component012="name" data-plan-med-search014 data-index="${index}" value="${esc(item.name||"")}" placeholder="${esc(this.t("choosePlanMedication014"))}" autocomplete="off" required><button type="button" data-action="plan-med-open-014" data-index="${index}" title="${esc(this.t("search"))}" aria-label="${esc(this.t("search"))}"><ha-icon icon="mdi:chevron-down"></ha-icon></button></div><div class="planMedSuggest014" data-plan-med-suggest014="${index}" hidden></div></label>`:`<label class="planComponentName012"><span>${this.t("componentName012")}</span><input data-plan-component012="name" data-index="${index}" value="${esc(item.name||"")}" required></label>`;
 return`<article class="planComponent012"><div class="planComponentHead012"><label><span>${this.t("componentType012")}</span><select data-plan-component012="type" data-index="${index}">${[["medication","componentMedication012"],["supplement","componentSupplement012"],["feed","componentFeed012"],["action","componentAction012"]].map(([value,label])=>`<option value="${value}" ${item.type===value?"selected":""}>${this.t(label)}</option>`).join("")}</select></label>${nameField}<button type="button" data-action="plan-component-remove-012" data-index="${index}" title="${this.t("delete")}"><ha-icon icon="mdi:delete-outline"></ha-icon></button></div>${action?"":`<div class="planDose012"><label><span>${this.t("componentAmount012")}</span><input type="number" min="0.000001" step="any" data-plan-component012="dose" data-index="${index}" value="${esc(item.dose||"")}" required></label><label><span>${this.t("dose_unit")}</span><select data-plan-component012="unit" data-index="${index}">${units.map(unit=>`<option value="${esc(unit)}" ${item.unit===unit?"selected":""}>${esc(this.l(unit))}</option>`).join("")}</select></label><label><span>${this.t("route")}</span><select data-plan-component012="route" data-index="${index}"><option value="">–</option>${routes.map(route=>`<option value="${esc(route)}" ${item.route===route?"selected":""}>${esc(this.l(route))}</option>`).join("")}</select></label></div>`}<label class="planInstruction012"><span>${this.t("componentInstructions012")}</span><input data-plan-component012="instructions" data-index="${index}" value="${esc(item.instructions||"")}"></label></article>`
};
AH014.planMedicationOptions014=function(input){
 const draft=this.ensurePlanDraft012(),species=draft.species_id?[String(draft.species_id)]:[],current=String(input?.value||""),q=this.norm083?this.norm083(current):current.toLocaleLowerCase();
 return this.medicationOptionsForSpecies012(species,current,false).map(option=>this.enrichMedicationOption013?this.enrichMedicationOption013(option):option).filter(option=>{if(!q)return true;const search=this.medicationSearchText013?this.medicationSearchText013(option):[option.value,option.active_ingredient,option.concentration,option.dosage_form].filter(Boolean).join(" ");return(this.norm083?this.norm083(search):search.toLocaleLowerCase()).includes(q)}).slice(0,60)
};
AH014.renderPlanMedicationSuggestions014=function(input,open=true){
 const index=Number(input?.dataset?.index),form=input?.form,menu=form?.querySelector(`[data-plan-med-suggest014="${index}"]`);if(!menu)return;
 const options=this.planMedicationOptions014(input);
 menu.innerHTML=options.length?options.map(option=>`<button type="button" class="planMedOption014" data-action="plan-med-option-014" data-index="${index}" data-value="${esc(option.value)}">${this.medicationOptionMarkup013?this.medicationOptionMarkup013(option):`<span><b>${esc(option.value)}</b></span>`}</button>`).join(""):`<div class="comboEmpty083">${this.t("noEvents")}</div>`;
 menu.hidden=!open
};
AH014.applyPlanMedication014=function(input,value){
 const index=Number(input?.dataset?.index),draft=this.ensurePlanDraft012(),item=draft.components[index];if(!item)return;
 item.name=value;input.value=value;
 const menu=input.form?.querySelector(`[data-plan-med-suggest014="${index}"]`);if(menu)menu.hidden=true;
 input.focus()
};
AH014.handleInput=function(event){
 const input=event.composedPath()[0];
 if(input?.dataset&&"planMedSearch014" in input.dataset){this.updatePlanDraft012(input);this.renderPlanMedicationSuggestions014(input,true);return}
 return AH014Base.handleInput.call(this,event)
};
AH014.handleChange=function(event){
 const input=event.composedPath()[0];
 if(input?.dataset&&"planMedSearch014" in input.dataset){this.updatePlanDraft012(input);const menu=input.form?.querySelector(`[data-plan-med-suggest014="${input.dataset.index}"]`);if(menu)menu.hidden=true;return}
 return AH014Base.handleChange.call(this,event)
};
AH014.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset?.action),action=button?.dataset?.action;
 if(action==="plan-med-open-014"){const input=button.closest("label")?.querySelector("[data-plan-med-search014]");if(input){this.renderPlanMedicationSuggestions014(input,true);input.focus()}return}
 if(action==="plan-med-option-014"){const form=button.closest("form"),input=form?.querySelector(`[data-plan-med-search014][data-index="${button.dataset.index}"]`);if(input)this.applyPlanMedication014(input,button.dataset.value||"");return}
 return AH014Base.handleClick.call(this,event)
};
AH014.seriesRelevantItems095=function(today,horizonEnd){
 const result=[],todayKey=this.dateKey0815(today),endKey=this.dateKey0815(horizonEnd);
 for(const task of this.d?.tasks||[]){
  if(!this.isSeriesTask095(task))continue;
  const startKey=String(task.start_date||"").slice(0,10),taskEndKey=String(task.end_date||"").slice(0,10);if(startKey&&startKey>endKey)continue;if(taskEndKey&&taskEndKey<todayKey)continue;
  const taskOccurrences=(this.d?.occurrences||[]).filter(item=>String(item.task_id)===String(task.id)),pending=taskOccurrences.filter(item=>item.status==="pending").sort((a,b)=>this.occurrenceDate0816(a).localeCompare(this.occurrenceDate0816(b)));
  const overdue=pending.filter(item=>item.is_overdue),latestOverdue=overdue.length?overdue[overdue.length-1]:null;
  if(latestOverdue)result.push({task,key:this.occurrenceDate0816(latestOverdue),occurrence:latestOverdue,isOverdue:true});
  let occurrence=pending.find(item=>{const key=this.occurrenceDate0816(item);return key>=todayKey&&key<=endKey})||null,key=occurrence?this.occurrenceDate0816(occurrence):"";
  if(!key){
   const start=this.utcDate0815(task.start_date)||new Date(today),scanStart=start>today?start:new Date(today),interval=Math.max(1,Number(task.recurrence_interval||1)),type=String(task.recurrence_type||"daily"),span=type==="monthly"?interval*32+35:type==="weekly"?interval*7+8:interval+2,calculatedEnd=this.addDays0815(scanStart,span),taskEnd=taskEndKey?this.utcDate0815(taskEndKey):null,scanEnd=taskEnd&&taskEnd<calculatedEnd?taskEnd:calculatedEnd;
   for(let day=new Date(scanStart);day<=scanEnd;day=this.addDays0815(day,1)){
    const candidate=this.dateKey0815(day);if(!this.taskOccurs0815(task,candidate))continue;
    const existing=taskOccurrences.find(item=>this.occurrenceDate0816(item)===candidate);if(existing&&existing.status!=="pending")continue;
    key=candidate;occurrence=existing?.status==="pending"?existing:null;break
   }
  }
  if(key&&(!latestOverdue||key!==this.occurrenceDate0816(latestOverdue)))result.push({task,key,occurrence,isOverdue:false})
 }
 return result.sort((a,b)=>(a.isOverdue===b.isOverdue?a.key.localeCompare(b.key):a.isOverdue?-1:1))
};
AH014.render=function(){
 AH014Base.render.call(this);
 this.shadowRoot.innerHTML+=`<style>
header{width:100%!important;padding-right:0!important}header nav{flex:1 1 auto!important;min-width:44px!important;margin-left:auto!important;justify-content:flex-end!important;overflow:visible!important}header nav>button:last-child{margin-left:auto!important}.planMedicationField014{position:relative}.planMedicationControl014{display:grid;grid-template-columns:minmax(0,1fr) auto}.planMedicationControl014 input{border-radius:8px 0 0 8px!important}.planMedicationControl014 button{border-radius:0 8px 8px 0;padding:0 10px}.planMedSuggest014{position:absolute;z-index:600;top:100%;left:0;right:0;max-height:320px;overflow:auto;padding:5px;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:9px;box-shadow:0 8px 24px #0005}.planMedOption014{width:100%;display:flex!important;align-items:center;justify-content:space-between!important;gap:10px;text-align:left!important;border:0!important;background:transparent!important;padding:9px!important;border-radius:7px!important}.planMedOption014:hover,.planMedOption014:focus-visible{background:var(--secondary-background-color)!important}
</style>`
};
