Object.assign(T,{
 aiAssist:["KI-Erfassung","AI capture"],
 aiAssistant:["KI-Erfassung","AI capture"],
 aiAssistantWeight:["Gewicht mit KI erfassen","Capture weight with AI"],
 aiInputFiles:["Foto oder Datei (optional)","Photo or file (optional)"],
 aiInputHint:["Foto/Datei, Text oder Diktat können einzeln oder gemeinsam verwendet werden.","Photo/file, text or dictation can be used separately or together."],
 aiTakePhoto:["Foto aufnehmen","Take photo"],
 aiInputRequired:["Foto/Datei, Text oder Diktat eingeben.","Add a photo/file, text or dictation."],
 aiUseWeight:["In Gewichtserfassung übernehmen","Apply to weight entry"],
 aiWeight:["Erkanntes Gewicht","Recognized weight"],
 aiRecurrence:["Erkannte Wiederholung","Recognized recurrence"],
 aiDraftWarning:["KI-Hinweis","AI note"],
 profileSelected:["Bild ausgewählt","Image selected"],
 noProfileSelected:["Noch kein neues Bild ausgewählt","No new image selected"],
 more:["Mehr","More"],
 originalView:["Original laden","Load original"],
 originalDownload:["Original herunterladen","Download original"],
 resetArea:["Test / Gefahrenbereich","Test / danger zone"],
 resetAnimalHealth:["Animal Health zurücksetzen","Reset Animal Health"],
 resetWarning:["Alle Tiere, Tiergruppen, Tags, Aufgaben, Chronikeinträge, Gewichte, Anhänge und Einstellungen von Animal Health werden gelöscht. Die Integration bleibt installiert und startet danach leer.","All Animal Health animals, groups, tags, tasks, timeline records, weights, attachments and settings will be deleted. The integration stays installed and restarts empty."],
 resetConfirm:["Animal Health wirklich vollständig zurücksetzen?","Really reset Animal Health completely?"],
 resetNow:["Alle Animal-Health-Daten löschen","Delete all Animal Health data"],
 resetRunning:["Animal Health wird zurückgesetzt …","Animal Health is being reset …"],
 withoutGroup:["Ohne Tiergruppe","Without animal group"]
});
const AH082=AnimalHealthPanel.prototype;
const AH082Base={
 heading:AH082.heading,
 loadV080:AH082.loadV080,
 loadDetail:AH082.loadDetail,
 attachmentList:AH082.attachmentList,
 openImagePreview:AH082.openImagePreview,
 primaryGroupSelect:AH082.primaryGroupSelect,
 profileField:AH082.profileField,
 uploadAnimalPhoto:AH082.uploadAnimalPhoto,
 handleClick:AH082.handleClick,
 handleChange:AH082.handleChange,
 handleSubmit:AH082.handleSubmit,
 animals:AH082.animals,
 animalDetail:AH082.animalDetail,
 aiUploadForm:AH082.aiUploadForm,
 aiResultRows:AH082.aiResultRows,
 aiResultForm:AH082.aiResultForm,
 prepareAITask:AH082.prepareAITask,
 applyAITaskDraft:AH082.applyAITaskDraft,
 weightForm:AH082.weightForm,
 settingsPage081:AH082.settingsPage081,
 form:AH082.form,
 render:AH082.render
};
AH082.heading=function(key,action=""){
 const search=this.searchOpen?`<label class="search searchExpanded082"><ha-icon icon="mdi:magnify"></ha-icon><input data-filter value="${esc(this.filter)}" placeholder="${this.t("search")}"></label><button class="searchToggle082" data-action="close-search" title="${this.t("close")}"><ha-icon icon="mdi:close"></ha-icon></button>`:`<button class="searchToggle082 ${this.filter?"on":""}" data-action="toggle-search" title="${this.t("search")}"><ha-icon icon="mdi:magnify"></ha-icon></button>`;
 return`<div class="heading"><h1>${this.t(key)}</h1><div class="actions">${search}${action}</div></div>`
};
AH082.loadV080=async function(){
 this.v080=await this.ws(`${D}/v080/state`);this.profileUrls={};
 const profiles=this.v080?.profiles||{},entries=Object.entries(profiles).filter(([,id])=>id);
 await Promise.all(entries.map(async([animalId,attachmentId])=>{try{const result=await this.ws(`${D}/v082/attachment/preview`,{attachment_id:attachmentId,size:"profile"});this.profileUrls[animalId]=result.url}catch(_error){this.profileUrls[animalId]=null}}));
 this.decorateV080()
};
AH082.loadDetail=async function(id,rerender=true){
 await AH082Base.loadDetail.call(this,id,false);
 if(this.detail?.attachments){
  await Promise.all(this.detail.attachments.filter(item=>String(item.media_type||"").startsWith("image/")).map(async item=>{try{const result=await this.ws(`${D}/v082/attachment/preview`,{attachment_id:item.id,size:"thumb"});item.v082_preview_url=result.url}catch(_error){item.v082_preview_url=null}}))
 }
 if(rerender)this.render()
};
AH082.attachmentList=function(items){
 if(!items.length)return this.empty("noEvents");
 return`<div class="attachmentList">${items.map(item=>{const image=String(item.media_type||"").startsWith("image/"),preview=item.v082_preview_url||"";return`<div class="attachment">${image&&preview?`<button class="attachmentPreview" data-action="preview-attachment" data-id="${esc(item.id)}"><img src="${esc(preview)}" loading="lazy" alt="${esc(item.title||item.filename)}"></button>`:`<ha-icon icon="${image?"mdi:file-image-outline":"mdi:file-document-outline"}"></ha-icon>`}<button class="attachmentName" data-action="${image?"preview-attachment":"download-attachment"}" data-id="${esc(item.id)}"><b>${esc(item.title||item.filename)}</b><small>${esc(item.filename)} · ${this.num(item.size_bytes/1024,0)} KB</small></button>${image?`<button data-action="download-attachment" data-id="${esc(item.id)}" title="${this.t("originalDownload")}"><ha-icon icon="mdi:download-outline"></ha-icon></button>`:""}<button data-action="delete-attachment" data-id="${esc(item.id)}" title="${this.t("delete")}"><ha-icon icon="mdi:delete-outline"></ha-icon></button></div>`}).join("")}</div>`
};
AH082.openImagePreview=async function(id){
 try{
  const result=await this.ws(`${D}/v082/attachment/preview`,{attachment_id:id,size:"preview"}),overlay=document.createElement("div");
  overlay.className="imagePreviewOverlay imagePreview082";
  overlay.innerHTML=`<div class="imagePreviewToolbar082"><button type="button" data-action="image-preview-close"><ha-icon icon="mdi:close"></ha-icon></button><button type="button" data-action="image-original" data-id="${esc(id)}"><ha-icon icon="mdi:magnify-plus-outline"></ha-icon>${this.t("originalView")}</button><button type="button" data-action="download-attachment" data-id="${esc(id)}"><ha-icon icon="mdi:download-outline"></ha-icon>${this.t("originalDownload")}</button></div><img src="${esc(result.url)}" alt="">`;
  this.shadowRoot.append(overlay)
 }catch(error){this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}
};
AH082.primaryGroupSelect=function(value=""){
 const groups=this.activeGroups(),options=groups.map(group=>`<option value="${esc(group.id)}" ${group.id===value?"selected":""}>${esc(group.name)}</option>`).join("");
 return`<label><span>${this.t("primaryGroup")}</span><select name="group_id"><option value="" ${value?"":"selected"}>${this.t("withoutGroup")}</option>${options}<option value="__new__">＋ ${this.t("createGroupInline")}</option></select></label>`
};
AH082.profileField=function(animal){
 const url=animal?.profile_url||this.profileUrlFor(animal?.id),label=url?this.t("replaceAnimalPhoto"):this.t("chooseAnimalPhoto");
 return`<fieldset class="wide profileField profileField082"><legend>${this.t("animalPhoto")}</legend><div class="profilePreviewWrap082" data-profile-preview-wrap>${url?`<img class="profilePreview" src="${esc(url)}" alt="${esc(animal?.name||"")}">`:this.speciesVisual(animal?.species)}</div><label class="fileChoice"><ha-icon icon="mdi:image-plus-outline"></ha-icon><span>${label}</span><input type="file" name="profile_image" accept="image/*"></label><div class="fileSelection wide" data-profile-selection>${this.t("noProfileSelected")}</div>${url&&animal?.id?`<button type="button" data-action="remove-animal-photo" data-id="${esc(animal.id)}"><ha-icon icon="mdi:image-remove-outline"></ha-icon>${this.t("removeAnimalPhoto")}</button>`:""}</fieldset>`
};
AH082.compressProfileImage=async function(file){
 if(!file||!String(file.type||"").startsWith("image/")||typeof createImageBitmap!=="function")return file;
 try{
  const bitmap=await createImageBitmap(file),max=768,scale=Math.min(1,max/Math.max(bitmap.width,bitmap.height));
  if(scale>=1&&file.size<350000)return file;
  const canvas=document.createElement("canvas");canvas.width=Math.max(1,Math.round(bitmap.width*scale));canvas.height=Math.max(1,Math.round(bitmap.height*scale));
  const context=canvas.getContext("2d");context.drawImage(bitmap,0,0,canvas.width,canvas.height);bitmap.close?.();
  const blob=await new Promise(resolve=>canvas.toBlob(resolve,"image/jpeg",.82));if(!blob)return file;
  const stem=String(file.name||"animal-photo").replace(/\.[^.]+$/ ,"");
  return new File([blob],`${stem}-profile.jpg`,{type:"image/jpeg",lastModified:Date.now()})
 }catch(_error){return file}
};
AH082.uploadAnimalPhoto=async function(form,animalId){
 const source=form.elements.profile_image?.files?.[0];if(!source)return;
 const file=await this.compressProfileImage(source),max=this.features?.max_attachment_size_bytes||15728640;if(file.size>max)throw Error(this.t("fileTooLarge"));
 const target=await this.ws(`${D}/attachments/upload`,{animal_id:animalId}),payload=new FormData();payload.append("file",file,file.name||"animal-photo.jpg");payload.append("title",this.t("animalPhoto"));
 const response=await fetch(target.url,{method:"POST",body:payload,credentials:"same-origin"});if(!response.ok)throw Error((await response.text())||`HTTP ${response.status}`);
 const attachment=await response.json();await this.ws(`${D}/animal_photo/set`,{animal_id:animalId,attachment_id:attachment.id})
};
AH082.animals=function(){
 const q=this.filter.toLowerCase(),groups=this.activeGroups(),tagFilter=this.tagFilter||"all";let selected=this.groupFilter||"all";if(selected!=="all"&&selected!=="ungrouped"&&!groups.some(group=>group.id===selected))selected="all";
 let animals=this.d.animals.filter(animal=>!q||[animal.name,animal.species,animal.breed,animal.status,animal.id,animal.group_name,...(animal.tags||[]).map(tag=>tag.name)].some(value=>String(value||"").toLowerCase().includes(q)));
 if(selected==="ungrouped")animals=animals.filter(animal=>!animal.group_id);else if(selected!=="all")animals=animals.filter(animal=>animal.group_id===selected);
 if(tagFilter!=="all")animals=animals.filter(animal=>(animal.tag_ids||[]).includes(tagFilter));if(this.animalStatusFilter==="active")animals=animals.filter(animal=>animal.status==="active"&&!animal.is_archived);
 const tabs=[`<button class="${selected==="all"?"on":""}" data-action="group-filter" data-id="all">${this.t("allAnimals")}</button>`,...groups.map(group=>`<button class="${selected===group.id?"on":""}" data-action="group-filter" data-id="${esc(group.id)}">${esc(group.name)} <small>${group.animal_count}</small></button>`),`<button class="${selected==="ungrouped"?"on":""}" data-action="group-filter" data-id="ungrouped">${this.t("ungrouped")}</button>`].join("");
 const tagTabs=[`<span class="tagFilterItem"><button class="${tagFilter==="all"?"on":""}" data-action="tag-filter" data-id="all">${this.t("allTags")}</button></span>`,...(this.v080?.tags||[]).map(tag=>`<span class="tagFilterItem"><button class="${tagFilter===tag.id?"on":""}" data-action="tag-filter" data-id="${esc(tag.id)}">#${esc(tag.name)} <small>${tag.animal_count}</small></button><button class="tagEdit" data-action="edit-tag" data-id="${esc(tag.id)}" title="${this.t("editTag")}"><ha-icon icon="mdi:pencil-outline"></ha-icon></button></span>`)].join("");
 const manage=selected!=="all"&&selected!=="ungrouped"?`<button data-action="edit-group" data-id="${esc(selected)}"><ha-icon icon="mdi:pencil-outline"></ha-icon>${this.t("editGroup")}</button><button data-action="group-archive" data-id="${esc(selected)}"><ha-icon icon="mdi:archive-arrow-down-outline"></ha-icon>${this.t("archiveGroup")}</button><button data-action="group-delete" data-id="${esc(selected)}"><ha-icon icon="mdi:delete-outline"></ha-icon>${this.t("deleteGroup")}</button>`:"";
 const activeChip=this.animalStatusFilter?`<button class="filterChip" data-action="clear-animal-filter">${this.t("activeOnly")} ×</button>`:"";
 return`${this.heading("animals",`${manage}<button data-action="create-tag"><ha-icon icon="mdi:tag-plus-outline"></ha-icon>${this.t("createTag")}</button><button class="primary" data-action="create-group"><ha-icon icon="mdi:account-group-outline"></ha-icon>${this.t("createGroup")}</button><button class="primary" data-action="create-animal"><ha-icon icon="mdi:plus-circle-outline"></ha-icon>${this.t("createAnimal")}</button>`)}${activeChip}<div class="groupTabs">${tabs}</div><div class="tagTabs">${tagTabs}</div><section class="grid">${animals.map(animal=>this.animalCard(animal)).join("")||this.empty("noAnimals")}</section>`
};
AH082.animalDetail=function(){
 if(!this.detail)return this.empty("loading");
 const animal=this.detail.animal,weight=animal.latest_weight,pending=this.detail.occurrences.filter(item=>item.status==="pending"),groups=this.activeGroups(),groupId=animal.group_id,animals=this.detailAnimals(groupId),profileId=animal.profile_image_id,generalAttachments=(this.detail.attachments||[]).filter(item=>!item.event_id&&item.id!==profileId);
 const groupButtons=[...groups.map(group=>`<button class="${groupId===group.id?"on":""}" data-action="detail-group" data-id="${esc(group.id)}">${esc(group.name)}</button>`),`<button class="${!groupId?"on":""}" data-action="detail-group" data-id="ungrouped">${this.t("ungrouped")}</button>`].join("");
 const switcher=`<section class="animalSwitcher animalSwitcher082"><div class="groupTabs compact">${groupButtons}</div><div class="animalTiles animalTiles082">${animals.map(item=>`<button class="animalTile ${item.id===animal.id?"on":""}" data-action="animal-detail" data-id="${esc(item.id)}">${this.animalVisual(item,"tileAvatar")}<span>${esc(item.name)}</span></button>`).join("")}</div></section>`;
 const menu=this.animalMenuOpen?`<div class="animalOverflow082"><button data-action="export-pdf" data-id="${esc(animal.id)}"><ha-icon icon="mdi:file-pdf-box"></ha-icon>${this.t("healthPdf")}</button><button data-action="edit-animal" data-id="${esc(animal.id)}"><ha-icon icon="mdi:pencil-outline"></ha-icon>${this.t("edit")}</button><button data-action="animal-status" data-id="${esc(animal.id)}"><ha-icon icon="mdi:swap-horizontal"></ha-icon>${this.t("changeStatus")}</button><button data-action="${animal.is_archived?"restore":"archive"}" data-id="${esc(animal.id)}"><ha-icon icon="mdi:archive-outline"></ha-icon>${this.t(animal.is_archived?"restore":"archive")}</button></div>`:"";
 const more=this.moreAnimalActions?`<div class="quick quickMore082"><button data-action="ai-assist"><ha-icon icon="mdi:creation-outline"></ha-icon>${this.t("aiAssist")}</button><button data-action="record-event" data-id="${esc(animal.id)}"><ha-icon icon="mdi:note-plus-outline"></ha-icon>${this.t("recordGeneral")}</button><button data-action="attach-document" data-id="${esc(animal.id)}"><ha-icon icon="mdi:paperclip"></ha-icon>${this.t("attachDocument")}</button></div>`:"";
 return`${this.heading("animals",`<button data-view="animals"><ha-icon icon="mdi:arrow-left"></ha-icon></button>`)}${switcher}<section class="hero hero082">${this.animalVisual(animal,"heroAvatar")}<div><h1>${esc(animal.name)}</h1><p>${animal.group_name?`${esc(animal.group_name)} · `:""}${esc(animal.species)}${animal.breed?` · ${esc(animal.breed)}`:""} · ${this.l(animal.status)}</p>${this.tagChips(animal)}</div><button class="heroMenu082" data-action="animal-menu"><ha-icon icon="mdi:dots-vertical"></ha-icon></button></section>${menu}<div class="quick quick082"><button class="primary" data-action="record-weight" data-id="${esc(animal.id)}"><ha-icon icon="mdi:scale"></ha-icon>${this.t("recordWeight")}</button><button data-action="record-symptom" data-id="${esc(animal.id)}"><ha-icon icon="mdi:alert-plus"></ha-icon>${this.t("recordSymptom")}</button><button data-action="record-product" data-id="${esc(animal.id)}"><ha-icon icon="mdi:pill"></ha-icon>${this.t("recordProduct")}</button><button data-action="create-task" data-id="${esc(animal.id)}"><ha-icon icon="mdi:clipboard-plus"></ha-icon>${this.t("createTask")}</button><button data-action="animal-more"><ha-icon icon="mdi:dots-horizontal"></ha-icon>${this.t("more")}</button></div>${more}<section class="stats stats082">${this.stat("mdi:scale",weight?`${this.num(weight.original_value)} ${weight.original_unit}`:"–","currentWeight")}${this.stat("mdi:clipboard",pending.length,"openTasks")}</section><details class="card masterDetails082"><summary>${this.t("masterData")}</summary>${this.obj({group:animal.group_name,tags:(animal.tags||[]).map(tag=>tag.name),species:animal.species,breed:animal.breed,color:animal.color,sex:animal.sex,birth_date:animal.birth_date,arrival_date:animal.arrival_date,status:animal.status})}</details>${pending.length?`<section class="card"><h2>${this.t("upcoming")}</h2>${this.rows(pending.slice(0,10))}</section>`:""}<section class="card"><h2>${this.t("documents")}</h2>${this.attachmentList(generalAttachments)}</section><section class="card"><h2>${this.t("plannedActual")}</h2>${this.detail.events.map(item=>this.eventRow(item)).join("")||this.empty("noEvents")}</section>`
};
AH082.aiUploadForm=function(){
 let html=AH082Base.aiUploadForm.call(this);
 if(this.aiMode==="weight")html=html.replace(this.t("aiAssistant"),this.t("aiAssistantWeight"));
 html=html.replace(`<legend>${this.t("aiChooseFiles")}</legend>`,`<legend>${this.t("aiInputFiles")}</legend>`);
 html=html.replace(this.t("takePhoto"),this.t("aiTakePhoto"));
 html=html.replace("</fieldset>",`<small class="wide hint aiInputHint082">${this.t("aiInputHint")}</small></fieldset>`);
 return html
};
AH082.aiResultRows=function(s){
 let html=AH082Base.aiResultRows.call(this,s),extra=[];
 if(s.weight)extra.push(`<div><dt>${this.t("aiWeight")}</dt><dd>${esc([s.weight,s.weight_unit].filter(Boolean).join(" "))}</dd></div>`);
 if(s.recurrence_type)extra.push(`<div><dt>${this.t("aiRecurrence")}</dt><dd>${esc(`${this.l(s.recurrence_type)}${s.recurrence_interval?` × ${s.recurrence_interval}`:""}`)}</dd></div>`);
 if(!extra.length)return html;
 if(html.includes("</dl>"))return html.replace("</dl>",`${extra.join("")}</dl>`);
 return`${html}<dl class="aiResultList">${extra.join("")}</dl>`
};
AH082.aiResultForm=function(){
 if(this.aiMode!=="weight")return AH082Base.aiResultForm.call(this);
 const s=this.aiSuggestion||{};
 return`<h2><ha-icon icon="mdi:creation-outline"></ha-icon>${this.t("aiResult")}</h2><p class="aiNotice"><b>${this.t("aiSafety")}</b></p>${this.aiResultRows(s)}<div class="buttons aiResultButtons"><button type="button" data-action="ai-again"><ha-icon icon="mdi:file-refresh-outline"></ha-icon>${this.t("aiAgain")}</button><button type="button" class="primary" data-action="ai-use-weight"><ha-icon icon="mdi:scale"></ha-icon>${this.t("aiUseWeight")}</button></div>`
};
AH082.prepareAITask=function(){
 const s=this.aiSuggestion||{},allowed=new Set(this.c?.task_kinds||[]),suggested=s.suggested_record_type||"reminder",kind=allowed.has(suggested)?suggested:"reminder";
 const description=[s.notes,s.diagnosis?`${this.t("diagnosis")}: ${s.diagnosis}`:"",s.treatment?`${this.t("treatment_action")}: ${s.treatment}`:"",s.visit_reason?`${this.t("visit_reason")}: ${s.visit_reason}`:""].filter(Boolean).join("\n");
 this.aiTaskDraft={
  task_kind:kind,
  animal_id:s.matched_animal_id||"",
  title:s.suggested_title||s.medication_name||s.vaccine_name||s.treatment||s.visit_reason||this.t("aiAssistant"),
  description,
  recurrence_type:s.recurrence_type||"once",
  recurrence_interval:s.recurrence_interval||"1",
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
  planned_provider:s.provider||"",
  uncertainties:s.uncertainties||"",
  recognized_animal:s.animal_name||""
 };
 this.modal={type:"create-task"};this.render();this.notify(this.t("aiTaskPrepared"))
};
AH082.applyAITaskDraft=function(){
 const draft=this.aiTaskDraft,form=this.shadowRoot.querySelector('form[data-form="task"]');if(!draft||!form)return;
 const set=(name,value,allowEmpty=false)=>{const field=form.elements[name];if(!field)return;if(allowEmpty||value!==undefined&&value!==null&&value!=="")field.value=value??""};
 set("task_scope","animal",true);set("task_kind",draft.task_kind,true);this.syncTask(form);
 set("title",draft.title);set("description",draft.description,true);set("recurrence_type",draft.recurrence_type||"once",true);set("recurrence_interval",draft.recurrence_interval||"1",true);set("start_date",draft.start_date);set("due_time",draft.due_time,true);
 for(const check of form.querySelectorAll('[name="device_ids"]'))check.checked=false;
 const animal=this.animal(draft.animal_id);if(animal?.device_id){const check=[...form.querySelectorAll('[name="device_ids"]')].find(item=>item.value===animal.device_id);if(check)check.checked=true}
 const medicationFields=["planned_medication_name","planned_dose","planned_dose_unit","planned_route"];for(const name of medicationFields)set(name,draft[name],true);
 for(const name of["planned_vaccine_name","planned_vaccination_dose","planned_vaccination_dose_unit","planned_vaccination_route","planned_check_focus","planned_visit_reason","planned_provider"])set(name,draft[name],true);
 if(draft.planned_vaccination_target){const target=[...form.querySelectorAll('[name="planned_vaccination_targets"]')].find(item=>item.value===draft.planned_vaccination_target);if(target)target.checked=true}
 this.syncTask(form);
 if(draft.uncertainties||draft.recognized_animal&&!draft.animal_id){const notice=document.createElement("p");notice.className="wide aiDraftNotice082";notice.innerHTML=`<b>${this.t("aiDraftWarning")}:</b> ${esc(draft.uncertainties||`${this.t("aiAnimalName")}: ${draft.recognized_animal}`)}`;form.prepend(notice)}
 this.aiTaskDraft=null
};
AH082.weightForm=function(modal){
 let html=AH082Base.weightForm.call(this,modal);
 return html.replace("<form data-form=\"weight\">",`<form data-form="weight"><div class="wide aiFormAssist082"><button type="button" data-action="weight-ai-assist"><ha-icon icon="mdi:creation-outline"></ha-icon>${this.t("aiAssistantWeight")}</button></div>`)
};
AH082.applyWeightAIDraft=function(){
 const draft=this.weightAIDraft,form=this.shadowRoot.querySelector('form[data-form="weight"]');if(!draft||!form)return;
 const set=(name,value)=>{const field=form.elements[name];if(field&&value!==undefined&&value!==null&&value!=="")field.value=value};
 set("animal_id",draft.animal_id);set("weight",draft.weight);set("weight_unit",draft.weight_unit);set("occurred_at",draft.occurred_at);set("notes",draft.notes);
 if(draft.notice){const note=document.createElement("p");note.className="wide aiDraftNotice082";note.innerHTML=`<b>${this.t("aiDraftWarning")}:</b> ${esc(draft.notice)}`;form.prepend(note)}
 this.weightAIDraft=null
};
AH082.settingsPage081=function(){
 let html=AH082Base.settingsPage081.call(this);if(!this.h?.user?.is_admin)return html;
 return`${html}<section class="card dangerZone082"><h2>${this.t("resetArea")}</h2><p>${this.t("resetWarning")}</p><button class="danger" data-action="reset-v082"><ha-icon icon="mdi:delete-alert-outline"></ha-icon>${this.t("resetAnimalHealth")}</button></section>`
};
AH082.form=function(){
 if(this.modal?.type==="reset-v082")return`<h2><ha-icon icon="mdi:delete-alert-outline"></ha-icon>${this.t("resetAnimalHealth")}</h2><form data-form="reset-v082"><p class="wide resetWarning082">${this.t("resetConfirm")}</p><p class="wide">${this.t("resetWarning")}</p><input type="hidden" name="confirm" value="RESET"><div class="buttons wide"><button type="button" data-action="close">${this.t("close")}</button><button class="danger" type="submit">${this.t("resetNow")}</button></div></form>`;
 return AH082Base.form.call(this)
};
AH082.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset&&(node.dataset.action||node.dataset.view)),action=button?.dataset?.action,id=button?.dataset?.id;
 if(action==="toggle-search"){this.searchOpen=true;this.render();const input=this.shadowRoot.querySelector("[data-filter]");input?.focus();return}
 if(action==="close-search"){this.searchOpen=false;this.filter="";this.render();return}
 if(action==="animal-menu"){this.animalMenuOpen=!this.animalMenuOpen;this.render();return}
 if(action==="animal-more"){this.moreAnimalActions=!this.moreAnimalActions;this.render();return}
 if(action==="image-original"){try{const result=await this.ws(`${D}/download`,{kind:"attachment",resource_id:id}),image=this.shadowRoot.querySelector(".imagePreview082 img");if(image)image.src=result.url}catch(error){this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}return}
 if(action==="reset-v082"){this.open("reset-v082");return}
 if(action==="weight-ai-assist"){
  const form=button.closest("form"),values=form?data(form):{};this.weightAIReturn={animal_id:values.animal_id||this.modal?.animalId||"",values};this.aiMode="weight";this.aiFiles=[];this.aiContextDraft="";
  try{this.aiStatus=await this.ws(`${D}/ai/status`);if(!this.aiStatus?.available){this.notify(this.t("aiNoTask"),true);return}this.open("ai-upload")}catch(error){this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}return
 }
 if(action==="ai-assist"){
  this.aiMode="general";this.weightAIReturn=null;this.aiFiles=[];this.aiContextDraft="";
  try{this.aiStatus=await this.ws(`${D}/ai/status`);if(!this.aiStatus?.available){this.notify(this.t("aiNoTask"),true);return}this.open("ai-upload")}catch(error){this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}return
 }
 if(action==="ai-use-weight"){
  const s=this.aiSuggestion||{},original=this.weightAIReturn||{},recognized=Boolean(s.animal_name),animalId=s.matched_animal_id||(!recognized?original.animal_id:""),notice=s.uncertainties||(recognized&&!s.matched_animal_id?`${this.t("aiAnimalName")}: ${s.animal_name}`:"");
  this.weightAIDraft={animal_id:animalId||original.animal_id||"",weight:s.weight||"",weight_unit:s.weight_unit||"",occurred_at:s.occurred_at||"",notes:s.notes||"",notice};
  this.aiSuggestion=null;this.aiMode="general";this.modal={type:"record-weight",...(animalId||original.animal_id?{animalId:animalId||original.animal_id}:{})};this.render();return
 }
 if(action==="ai-again"){return AH082Base.handleClick.call(this,event)}
 return AH082Base.handleClick.call(this,event)
};
AH082.handleChange=function(event){
 AH082Base.handleChange.call(this,event);const input=event.composedPath()[0],form=input?.form;
 if(form?.dataset.form==="animal"&&input.name==="profile_image"){
  const file=input.files?.[0],target=form.querySelector("[data-profile-selection]"),wrap=form.querySelector("[data-profile-preview-wrap]");
  if(target){target.textContent=file?`${this.t("profileSelected")}: ${file.name||"Foto"}`:this.t("noProfileSelected");target.classList.toggle("hasFiles",Boolean(file))}
  if(file&&wrap){if(this.profileObjectUrl)URL.revokeObjectURL(this.profileObjectUrl);this.profileObjectUrl=URL.createObjectURL(file);wrap.innerHTML=`<img class="profilePreview" src="${esc(this.profileObjectUrl)}" alt="">`}
 }
};
AH082.handleSubmit=async function(event){
 const form=event.composedPath().find(node=>node?.tagName==="FORM");if(!form)return;
 if(form.dataset.form==="animal"){
  event.preventDefault();const values=data(form);values.tag_ids=[...form.querySelectorAll('[name="tag_ids"]:checked')].map(item=>item.value);if(values.group_id==="__new__"){this.notify(`${this.t("failed")}: ${this.t("primaryGroup")}`,true);return}
  this.animalDraft={...values};this.animalDraftModal=this.modal?.type;const submit=form.querySelector('button[type="submit"]');if(submit)submit.disabled=true;
  try{const result=await this.saveAnimal(values),animalId=values.animal_id||this.recordId(result);if(!animalId)throw Error("Animal ID missing from service response");await this.ws(`${D}/tags/set`,{animal_id:animalId,tag_ids:values.tag_ids});await this.uploadAnimalPhoto(form,animalId);this.animalDraft=null;this.animalDraftModal=null;await this.after()}catch(error){if(submit)submit.disabled=false;this.notify(`${this.t("failed")}: ${this.friendlyError?this.friendlyError(error):error?.message||error}`,true)}return
 }
 if(form.dataset.form==="ai-upload"){
  event.preventDefault();if(this.aiDictation){this.notify(this.t("aiStopBeforeAnalyze"),true);return}
  const files=this.aiFiles||[],context=String(form.elements.ai_context?.value||"").trim();if(!files.length&&!context){this.notify(this.t("aiInputRequired"),true);return}
  const submit=form.querySelector('button[type="submit"]'),entityId=form.elements.ai_entity_id?.value||"";this.aiContextDraft=context;if(submit)submit.disabled=true;this.notify(this.t("aiAnalyzing"));
  try{const uploaded=[];for(const file of files)uploaded.push(await this.aiUploadOne(file));this.aiSuggestion=await this.ws(`${D}/v082/ai/analyze`,{upload_ids:uploaded.map(item=>item.upload_id),context,mode:this.aiMode||"general",...(entityId?{entity_id:entityId}:{})});this.aiFiles=[];this.aiContextDraft="";this.modal={type:"ai-result"};this.render()}catch(error){if(submit)submit.disabled=false;this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}return
 }
 if(form.dataset.form==="reset-v082"){
  event.preventDefault();const submit=form.querySelector('button[type="submit"]');if(submit)submit.disabled=true;
  try{await this.ws(`${D}/v082/reset`,{confirm:"RESET"});this.modal=null;this.notify(this.t("resetRunning"));setTimeout(()=>window.location.reload(),1800)}catch(error){if(submit)submit.disabled=false;this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}return
 }
 return AH082Base.handleSubmit.call(this,event)
};
AH082.render=function(){
 const weightDraft=this.weightAIDraft;AH082Base.render.call(this);if(weightDraft&&this.modal?.type==="record-weight"){this.weightAIDraft=weightDraft;this.applyWeightAIDraft()}
 this.shadowRoot.innerHTML+=`<style>
.searchToggle082{min-width:42px}.searchExpanded082{min-width:min(360px,65vw)}.searchExpanded082 input{width:100%}
.profileField082 .profilePreviewWrap082{display:flex;align-items:center;justify-content:center;min-height:110px}.profileField082 .profilePreview{max-width:180px;max-height:140px;object-fit:cover;border-radius:12px}.profileField082 .fileSelection{padding:7px 9px;border-radius:8px;background:var(--secondary-background-color);color:var(--secondary-text-color)}.profileField082 .fileSelection.hasFiles{color:var(--primary-text-color);font-weight:500}
.animalSwitcher082 .animalTiles082{display:flex;gap:9px;overflow-x:auto;padding:2px 0 7px;scroll-snap-type:x proximity}.animalTiles082 .animalTile{flex:0 0 auto;scroll-snap-align:start}.hero082{position:relative}.hero082 .heroMenu082{margin-left:auto;align-self:flex-start}.animalOverflow082{display:flex;justify-content:flex-end;gap:8px;flex-wrap:wrap;margin:-8px 0 14px;padding:10px;border:1px solid var(--divider-color);border-radius:12px;background:var(--card-background-color)}.quick082{display:grid;grid-template-columns:repeat(5,minmax(0,1fr))}.quickMore082{margin-top:-8px}.stats082{grid-template-columns:repeat(2,1fr);max-width:720px}.masterDetails082 summary{cursor:pointer;font-weight:600}.masterDetails082 dl{margin-top:12px}
.imagePreview082{display:flex!important;flex-direction:column;gap:10px;background:#000d;padding:12px}.imagePreview082>img{max-width:100%;max-height:calc(100vh - 80px);object-fit:contain;margin:auto}.imagePreviewToolbar082{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap}.imagePreviewToolbar082 button{background:var(--card-background-color)}
.aiDraftNotice082,.resetWarning082{padding:11px 13px;border-radius:10px;background:var(--secondary-background-color);border-left:4px solid var(--warning-color,#f9a825)}.aiFormAssist082{display:flex;justify-content:flex-end}.aiInputHint082{color:var(--secondary-text-color)}.dangerZone082{border-color:var(--error-color)}button.danger{border-color:var(--error-color);color:var(--error-color)}
@media(max-width:850px){.heading{flex-direction:row;align-items:center}.heading>.actions{width:auto;margin-left:auto}.heading>.actions>:not(.searchToggle082):not(.searchExpanded082){max-width:100%}.animalSwitcher082 .groupTabs{overflow-x:auto;flex-wrap:nowrap}.hero082{padding:13px}.hero082 h1{font-size:1.5rem}.quick082{grid-template-columns:repeat(2,1fr)}.quick082 button:last-child{grid-column:1/-1}.animalOverflow082{justify-content:stretch}.animalOverflow082 button{flex:1 1 45%}.stats082{grid-template-columns:1fr 1fr}.searchExpanded082{position:absolute;left:14px;right:14px;top:64px;z-index:20;background:var(--card-background-color);box-shadow:var(--ha-card-box-shadow,0 3px 12px #0004)}}
@media(max-width:520px){.animalSwitcher082{padding:10px}.animalTiles082 .animalTile{min-width:92px}.quickMore082 button{flex:1 1 100%}.imagePreviewToolbar082 button{flex:1 1 auto}.stats082 .stat{min-width:0}.profileField082 .profilePreview{max-width:150px}}
</style>`
};