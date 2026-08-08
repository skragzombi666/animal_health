Object.assign(T,{
 aiAssist:["KI-Dokument einlesen","Scan document with AI"],
 aiAssistant:["KI-Dokumentassistent","AI document assistant"],
 aiChooseFile:["Foto oder PDF auswählen","Choose photo or PDF"],
 aiAnalyze:["Mit KI analysieren","Analyze with AI"],
 aiAnalyzing:["Dokument wird analysiert …","Analyzing document …"],
 aiNoTask:["Keine Home-Assistant-AI-Task-Entität verfügbar. Richte zuerst einen AI-Task-Provider in Home Assistant ein.","No Home Assistant AI Task entity is available. Configure an AI Task provider in Home Assistant first."],
 aiProviderNotice:["Die Analyse verwendet die in Home Assistant konfigurierte AI-Task-Entität. Je nach Provider kann die Datei lokal oder extern verarbeitet werden.","Analysis uses the AI Task entity configured in Home Assistant. Depending on the provider, the file may be processed locally or externally."],
 aiSafety:["Die KI füllt nur einen Entwurf vor. Sie trifft keine medizinischen Entscheidungen und speichert nichts automatisch.","AI only prefills a draft. It makes no medical decisions and saves nothing automatically."],
 aiResult:["Erkannte Angaben","Extracted information"],
 aiUseTask:["Aufgabe mit diesen Angaben vorbereiten","Prepare task with these values"],
 aiAgain:["Anderes Dokument analysieren","Analyze another document"],
 aiSource:["Quelldatei","Source file"],
 aiDocumentType:["Dokumentart","Document type"],
 aiSuggestedType:["Vorgeschlagene Eintragsart","Suggested record type"],
 aiSuggestedTitle:["Vorgeschlagener Titel","Suggested title"],
 aiAnimalName:["Erkanntes Tier","Recognized animal"],
 aiDocumentDate:["Dokumentdatum","Document date"],
 aiScheduledDate:["Expliziter Termin","Explicit scheduled date"],
 aiConfidence:["Extraktionssicherheit","Extraction confidence"],
 aiUncertainties:["Unsicher / nicht eindeutig","Uncertain / ambiguous"],
 aiMedication:["Erkanntes Medikament","Recognized medication"],
 aiVaccine:["Erkannter Impfstoff","Recognized vaccine"],
 aiDose:["Erkannte Dosis","Recognized dose"],
 aiProvider:["Praxis / Behandler","Practice / provider"],
 aiTreatment:["Erkannte Behandlung","Recognized treatment"],
 aiVisitReason:["Erkannter Besuchsgrund","Recognized visit reason"],
 aiDiagnosis:["Erkannte Diagnoseangabe","Recognized diagnosis text"],
 aiTaskPrepared:["KI-Entwurf übernommen. Bitte alle Angaben kontrollieren und erst danach speichern.","AI draft applied. Check every field before saving."],
 aiFileRequired:["Bitte zuerst ein Foto oder PDF auswählen.","Choose a photo or PDF first."],
 aiUnsupported:["Für die KI-Analyse werden JPEG, PNG, WebP oder PDF unterstützt.","AI analysis supports JPEG, PNG, WebP or PDF."],
 aiTaskEntity:["AI-Task-Entität","AI Task entity"]
});
const AH080AI=AnimalHealthPanel.prototype;
const AH080AIBase={
 quick:AH080AI.quick,
 form:AH080AI.form,
 handleClick:AH080AI.handleClick,
 handleChange:AH080AI.handleChange,
 handleSubmit:AH080AI.handleSubmit,
 render:AH080AI.render
};
AH080AI.aiUploadForm=function(){
 const entities=this.aiStatus?.entities||[],entitySelect=entities.length>1?`<label class="wide"><span>${this.t("aiTaskEntity")}</span><select name="ai_entity_id"><option value="">Home Assistant</option>${entities.map(id=>`<option value="${esc(id)}">${esc(id)}</option>`).join("")}</select></label>`:"";
 return`<h2><ha-icon icon="mdi:creation-outline"></ha-icon>${this.t("aiAssistant")}</h2><form data-form="ai-upload"><p class="wide aiNotice"><b>${this.t("aiSafety")}</b><br>${this.t("aiProviderNotice")}</p>${entitySelect}<fieldset class="wide attachmentFields"><legend>${this.t("aiChooseFile")}</legend><div class="fileChoices wide"><label class="fileChoice"><ha-icon icon="mdi:file-document-plus-outline"></ha-icon><span>${this.t("aiChooseFile")}</span><input type="file" name="ai_file" accept="image/jpeg,image/png,image/webp,application/pdf"></label><button type="button" class="fileChoice" data-action="take-photo"><ha-icon icon="mdi:camera-outline"></ha-icon><span>${this.t("takePhoto")}</span></button><input class="cameraFallback" type="file" name="camera_file" accept="image/*" capture="environment" data-camera-fallback></div><div class="wide fileSelection" data-ai-file-selection>${this.t("noFileSelected")}</div></fieldset><div class="buttons wide"><button type="button" data-action="close">${this.t("close")}</button><button class="primary" type="submit"><ha-icon icon="mdi:creation-outline"></ha-icon>${this.t("aiAnalyze")}</button></div></form>`
};
AH080AI.aiResultRows=function(s){
 const rows=[
  ["aiSource",s.source_filename],
  ["aiDocumentType",s.document_type],
  ["aiSuggestedType",s.suggested_record_type?this.l(s.suggested_record_type):""],
  ["aiSuggestedTitle",s.suggested_title],
  ["aiAnimalName",s.animal_name],
  ["aiDocumentDate",s.document_date],
  ["aiScheduledDate",[s.scheduled_date,s.due_time].filter(Boolean).join(" ")],
  ["aiMedication",s.medication_name],
  ["aiVaccine",s.vaccine_name],
  ["aiDose",[s.dose,s.dose_unit].filter(Boolean).join(" ")],
  ["route",s.route],
  ["aiProvider",s.provider],
  ["aiVisitReason",s.visit_reason],
  ["aiTreatment",s.treatment],
  ["aiDiagnosis",s.diagnosis],
  ["notes",s.notes],
  ["aiConfidence",s.confidence],
  ["aiUncertainties",s.uncertainties]
 ].filter(([,value])=>String(value||"").trim());
 return rows.length?`<dl class="aiResultList">${rows.map(([key,value])=>`<div><dt>${this.t(key)}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl>`:`<div class="empty">${this.t("noEvents")}</div>`
};
AH080AI.aiResultForm=function(){const s=this.aiSuggestion||{};return`<h2><ha-icon icon="mdi:creation-outline"></ha-icon>${this.t("aiResult")}</h2><p class="aiNotice"><b>${this.t("aiSafety")}</b></p>${this.aiResultRows(s)}<div class="buttons aiResultButtons"><button type="button" data-action="ai-again"><ha-icon icon="mdi:file-refresh-outline"></ha-icon>${this.t("aiAgain")}</button><button type="button" class="primary" data-action="ai-use-task"><ha-icon icon="mdi:clipboard-edit-outline"></ha-icon>${this.t("aiUseTask")}</button></div>`};
AH080AI.form=function(){if(this.modal?.type==="ai-upload")return this.aiUploadForm();if(this.modal?.type==="ai-result")return this.aiResultForm();return AH080AIBase.form.call(this)};
AH080AI.quick=function(id=""){const html=AH080AIBase.quick.call(this,id);return html.replace('<div class="quick">','<div class="quick"><button data-action="ai-assist"><ha-icon icon="mdi:creation-outline"></ha-icon>'+this.t("aiAssist")+'</button>')};
AH080AI.updateAIFileSelection=function(form){const target=form?.querySelector("[data-ai-file-selection]");if(!target)return;const file=form.elements.ai_file?.files?.[0]||form.elements.camera_file?.files?.[0];target.textContent=file?`${this.t("selectedFiles")}: ${file.name||"Foto"}`:this.t("noFileSelected");target.classList.toggle("hasFiles",Boolean(file))};
AH080AI.prepareAITask=function(){
 const s=this.aiSuggestion||{},allowed=new Set(this.c?.task_kinds||[]);let kind=allowed.has(s.suggested_record_type)?s.suggested_record_type:"reminder";
 const description=[s.notes,s.diagnosis?`${this.t("diagnosis")}: ${s.diagnosis}`:"",s.treatment?`${this.t("treatment_action")}: ${s.treatment}`:""].filter(Boolean).join("\n");
 this.aiTaskDraft={
  task_kind:kind,
  animal_id:s.matched_animal_id||"",
  title:s.suggested_title||s.medication_name||s.vaccine_name||s.treatment||s.visit_reason||this.t("aiAssistant"),
  description,
  start_date:s.scheduled_date||this.d?.today||"",
  due_time:s.due_time||"",
  planned_medication_name:s.medication_name||"",
  planned_dose:s.dose||"",
  planned_dose_unit:s.dose_unit||"",
  planned_route:s.route||"",
  planned_vaccine_name:s.vaccine_name||"",
  planned_vaccination_dose:s.dose||"",
  planned_vaccination_dose_unit:s.dose_unit||"",
  planned_vaccination_route:s.route||"",
  planned_vaccination_target:s.vaccination_target||"",
  planned_check_focus:s.diagnosis||s.notes||"",
  planned_visit_reason:s.visit_reason||s.treatment||"",
  planned_provider:s.provider||""
 };
 this.modal={type:"create-task"};this.render();this.notify(this.t("aiTaskPrepared"))
};
AH080AI.applyAITaskDraft=function(){
 const draft=this.aiTaskDraft,form=this.shadowRoot.querySelector('form[data-form="task"]');if(!draft||!form)return;
 const set=(name,value)=>{const field=form.elements[name];if(field&&value!==undefined&&value!==null&&value!=="")field.value=value};
 set("task_scope","animal");set("task_kind",draft.task_kind);set("title",draft.title);set("description",draft.description);set("recurrence_type","once");set("recurrence_interval","1");set("start_date",draft.start_date);set("due_time",draft.due_time);this.syncTask(form);
 const animal=this.animal(draft.animal_id);if(animal?.device_id){const check=[...form.querySelectorAll('[name="device_ids"]')].find(item=>item.value===animal.device_id);if(check)check.checked=true}
 for(const name of["planned_medication_name","planned_dose","planned_dose_unit","planned_route","planned_vaccine_name","planned_vaccination_dose","planned_vaccination_dose_unit","planned_vaccination_route","planned_check_focus","planned_visit_reason","planned_provider"])set(name,draft[name]);
 if(draft.planned_vaccination_target){const target=[...form.querySelectorAll('[name="planned_vaccination_targets"]')].find(item=>item.value===draft.planned_vaccination_target);if(target)target.checked=true}
 this.syncTask(form);this.aiTaskDraft=null
};
AH080AI.render=function(){AH080AIBase.render.call(this);if(this.modal?.type==="create-task"&&this.aiTaskDraft)this.applyAITaskDraft();this.shadowRoot.innerHTML+=`<style>.aiNotice{padding:12px;border-radius:10px;background:var(--secondary-background-color);line-height:1.45}.aiResultList{margin:0 0 18px}.aiResultList div{display:grid;grid-template-columns:minmax(130px,200px) 1fr;gap:12px;padding:9px 0;border-top:1px solid var(--divider-color)}.aiResultList div:first-child{border-top:0}.aiResultList dt{color:var(--secondary-text-color)}.aiResultList dd{margin:0;overflow-wrap:anywhere}.aiResultButtons{margin-top:18px;flex-wrap:wrap}@media(max-width:520px){.aiResultList div{grid-template-columns:1fr;gap:3px}.aiResultButtons button{width:100%}}</style>`};
AH080AI.handleClick=async function(event){const button=event.composedPath().find(node=>node?.dataset?.action);const action=button?.dataset?.action;if(action==="ai-assist"){try{this.aiStatus=await this.ws(`${D}/ai/status`);if(!this.aiStatus?.available){this.notify(this.t("aiNoTask"),true);return}this.open("ai-upload")}catch(error){this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}return}if(action==="ai-use-task"){this.prepareAITask();return}if(action==="ai-again"){this.aiSuggestion=null;this.open("ai-upload");return}return AH080AIBase.handleClick.call(this,event)};
AH080AI.handleChange=function(event){AH080AIBase.handleChange.call(this,event);const input=event.composedPath()[0],form=input?.form;if(form?.dataset.form==="ai-upload"&&input.type==="file")this.updateAIFileSelection(form)};
AH080AI.handleSubmit=async function(event){
 const form=event.composedPath().find(node=>node?.tagName==="FORM");if(form?.dataset.form!=="ai-upload")return AH080AIBase.handleSubmit.call(this,event);event.preventDefault();const file=form.elements.ai_file?.files?.[0]||form.elements.camera_file?.files?.[0];if(!file){this.notify(this.t("aiFileRequired"),true);return}const submit=form.querySelector('button[type="submit"]');if(submit)submit.disabled=true;this.notify(this.t("aiAnalyzing"));
 try{const target=await this.ws(`${D}/ai/upload`);if(file.size>target.max_size_bytes)throw Error(this.t("fileTooLarge"));const payload=new FormData();payload.append("file",file,file.name||"animal-health-ai.jpg");const response=await fetch(target.url,{method:"POST",body:payload,credentials:"same-origin"});if(!response.ok){if(response.status===415)throw Error(this.t("aiUnsupported"));throw Error((await response.text())||`HTTP ${response.status}`)}const uploaded=await response.json(),entityId=form.elements.ai_entity_id?.value||"";this.aiSuggestion=await this.ws(`${D}/ai/analyze`,{upload_id:uploaded.upload_id,...(entityId?{entity_id:entityId}:{})});this.modal={type:"ai-result"};this.render()}catch(error){if(submit)submit.disabled=false;this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}
};
