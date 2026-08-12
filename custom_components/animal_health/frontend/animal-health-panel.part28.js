const AH087=AnimalHealthPanel.prototype;
const AH087Base={
 taskForm:AH087.taskForm,
 aiDraftFromSuggestion083:AH087.aiDraftFromSuggestion083
};
AH087.aiDraftFromSuggestion083=function(s){
 const known=new Set(["reminder","weight","medication","vaccination","health_check","care","veterinary_visit","treatment"]);
 let kind=known.has(s?.suggested_record_type)?s.suggested_record_type:"reminder";
 if(kind==="reminder"&&s?.medication_name)kind="medication";
 else if(kind==="reminder"&&s?.vaccine_name)kind="vaccination";
 const recognized=String(s?.animal_name||"").trim(),needle=this.norm083?.(recognized)||recognized.toLocaleLowerCase();
 const animalId=s?.matched_animal_id||(this.d?.animals||[]).find(animal=>{const name=this.norm083?.(animal.name)||String(animal.name||"").toLocaleLowerCase();return needle&&name===needle})?.id||"";
 const description=[s?.notes,s?.diagnosis?`${this.t("diagnosis")}: ${s.diagnosis}`:"",s?.treatment?`${this.t("treatment_action")}: ${s.treatment}`:"",s?.visit_reason?`${this.t("visit_reason")}: ${s.visit_reason}`:""].filter(Boolean).join("\n");
 return{
  task_kind:kind,
  animal_id:animalId,
  title:s?.suggested_title||s?.medication_name||s?.vaccine_name||s?.treatment||s?.visit_reason||this.t("aiAssistant"),
  description,
  recurrence_type:["once","daily","weekly","monthly"].includes(s?.recurrence_type)?s.recurrence_type:"once",
  recurrence_interval:s?.recurrence_interval||"1",
  start_date:s?.scheduled_date||s?.document_date||this.d?.today||"",
  due_time:s?.due_time||"",
  planned_medication_name:s?.medication_name||"",
  planned_dose:s?.dose||"",
  planned_dose_unit:s?.dose_unit||"",
  planned_route:s?.route||"",
  planned_vaccine_name:s?.vaccine_name||"",
  planned_vaccination_dose:s?.dose||"",
  planned_vaccination_dose_unit:s?.dose_unit||"",
  planned_vaccination_route:s?.route||"",
  planned_vaccination_target:s?.vaccination_target||"",
  planned_check_focus:s?.diagnosis||s?.notes||"",
  planned_visit_reason:s?.visit_reason||s?.treatment||"",
  planned_provider:s?.provider||"",
  planned_treatment_action:s?.treatment||"",
  uncertainties:s?.uncertainties||"",
  recognized_animal:recognized
 }
};
AH087.regexEscape087=function(value){return String(value??"").replace(/[.*+?^${}()|[\]\\]/g,"\\$&")};
AH087.prefillInput087=function(html,name,value){
 if(value===undefined||value===null)return html;const n=this.regexEscape087(name),safe=esc(value);
 const textarea=new RegExp(`(<textarea\\b[^>]*\\bname="${n}"[^>]*>)[\\s\\S]*?(<\\/textarea>)`);
 if(textarea.test(html))return html.replace(textarea,`$1${safe}$2`);
 const input=new RegExp(`<input\\b[^>]*\\bname="${n}"[^>]*>`);
 return html.replace(input,tag=>{const cleaned=tag.replace(/\svalue="[^"]*"/g,"");return cleaned.replace(/>$/,` value="${safe}">`)})
};
AH087.prefillSelect087=function(html,name,value){
 if(value===undefined||value===null||value==="")return html;const n=this.regexEscape087(name),v=this.regexEscape087(esc(value)),select=new RegExp(`(<select\\b[^>]*\\bname="${n}"[^>]*>)([\\s\\S]*?)(<\\/select>)`);
 return html.replace(select,(_all,open,options,close)=>{const cleared=options.replace(/\sselected(?=[\s>])/g,"");const option=new RegExp(`(<option\\b[^>]*\\bvalue="${v}"[^>]*)(>)`);return open+cleared.replace(option,"$1 selected$2")+close})
};
AH087.prefillAnimal087=function(html,animalId){
 const animal=this.animal(animalId);if(!animal?.device_id)return html;const value=this.regexEscape087(esc(animal.device_id)),input=new RegExp(`<input\\b[^>]*\\bname="device_ids"[^>]*\\bvalue="${value}"[^>]*>`);
 return html.replace(input,tag=>/\schecked(?=[\s>])/.test(tag)?tag:tag.replace(/>$/," checked>"))
};
AH087.taskForm=function(){
 let html=AH087Base.taskForm.call(this),draft=this.aiTaskDraft;if(!draft)return html;
 html=this.prefillSelect087(html,"task_scope","animal");
 html=this.prefillSelect087(html,"task_kind",draft.task_kind||"reminder");
 html=this.prefillInput087(html,"title",draft.title||"");
 html=this.prefillInput087(html,"description",draft.description||"");
 html=this.prefillSelect087(html,"recurrence_type",draft.recurrence_type||"once");
 html=this.prefillInput087(html,"recurrence_interval",draft.recurrence_interval||"1");
 html=this.prefillInput087(html,"start_date",draft.start_date||this.d?.today||"");
 html=this.prefillInput087(html,"due_time",draft.due_time||"");
 html=this.prefillInput087(html,"planned_medication_name",draft.planned_medication_name||"");
 html=this.prefillInput087(html,"planned_dose",draft.planned_dose||"");
 html=this.prefillSelect087(html,"planned_dose_unit",draft.planned_dose_unit||"");
 html=this.prefillSelect087(html,"planned_route",draft.planned_route||"");
 html=this.prefillInput087(html,"planned_vaccine_name",draft.planned_vaccine_name||"");
 html=this.prefillInput087(html,"planned_vaccination_dose",draft.planned_vaccination_dose||"");
 html=this.prefillSelect087(html,"planned_vaccination_dose_unit",draft.planned_vaccination_dose_unit||"");
 html=this.prefillSelect087(html,"planned_vaccination_route",draft.planned_vaccination_route||"");
 html=this.prefillInput087(html,"planned_check_focus",draft.planned_check_focus||"");
 html=this.prefillInput087(html,"planned_visit_reason",draft.planned_visit_reason||"");
 html=this.prefillInput087(html,"planned_provider",draft.planned_provider||"");
 html=this.prefillInput087(html,"planned_treatment_action",draft.planned_treatment_action||"");
 html=this.prefillAnimal087(html,draft.animal_id);
 if(draft.planned_vaccination_target){const value=this.regexEscape087(esc(draft.planned_vaccination_target)),target=new RegExp(`<input\\b[^>]*\\bname="planned_vaccination_targets"[^>]*\\bvalue="${value}"[^>]*>`);html=html.replace(target,tag=>/\schecked(?=[\s>])/.test(tag)?tag:tag.replace(/>$/," checked>"))}
 return html
};
