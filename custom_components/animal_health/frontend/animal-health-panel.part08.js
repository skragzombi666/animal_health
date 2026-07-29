Object.assign(T,{
 groups:["Tiergruppen","Animal groups"],group:["Tiergruppe","Animal group"],allAnimals:["Gesamtbestand","All animals"],ungrouped:["Ohne Tiergruppe","Ungrouped"],createGroup:["Tiergruppe anlegen","Create group"],editGroup:["Tiergruppe bearbeiten","Edit group"],groupName:["Name der Tiergruppe","Group name"],groupDescription:["Beschreibung","Description"],documents:["Dokumente","Documents"],attachDocument:["Dokument anhängen","Attach document"],chooseFiles:["Datei auswählen","Choose file"],takePhoto:["Dokument fotografieren","Photograph document"],documentTitle:["Dokumenttitel","Document title"],healthPdf:["Gesundheitschronik als PDF","Health timeline as PDF"],jsonExport:["Daten als JSON exportieren","Export data as JSON"],backupExport:["Vollständiges Backup exportieren","Export full backup"],exports:["Export und Datensicherung","Export and backup"],localStorage:["Anhänge werden lokal auf Home Assistant gespeichert.","Attachments are stored locally on Home Assistant."],emptyNow:["Leer lassen für jetzt","Leave empty for now"],previous:["Zurück","Previous"],next:["Weiter","Next"],delete:["Löschen","Delete"],fileTooLarge:["Die Datei überschreitet die maximale Grösse von 15 MB.","The file exceeds the 15 MB size limit."],attachmentMissingEvent:["Der Eintrag wurde gespeichert, aber die Dokumentzuordnung konnte nicht ermittelt werden.","The record was saved, but its document target could not be determined."]
});
const AH071=AnimalHealthPanel.prototype;
const AH071Base={
 load:AH071.load,loadDetail:AH071.loadDetail,handleClick:AH071.handleClick,handleChange:AH071.handleChange,handleSubmit:AH071.handleSubmit,body:AH071.body,render:AH071.render,overview:AH071.overview,animals:AH071.animals,animalCard:AH071.animalCard,animalDetail:AH071.animalDetail,eventRow:AH071.eventRow,form:AH071.form,saveAnimal:AH071.saveAnimal,saveWeight:AH071.saveWeight,saveEvent:AH071.saveEvent,saveSymptom:AH071.saveSymptom,saveExecution:AH071.saveExecution,execForm:AH071.execForm
};
AH071.decorateFeatures=function(){
 const groups=new Map((this.features?.groups||[]).map(x=>[x.id,x]));
 const memberships=this.features?.memberships||{};
 for(const animal of this.d?.animals||[]){animal.group_id=memberships[animal.id]||null;animal.group_name=groups.get(animal.group_id)?.name||null}
 if(this.detail?.animal){const animal=this.detail.animal;animal.group_id=memberships[animal.id]||null;animal.group_name=groups.get(animal.group_id)?.name||null}
};
AH071.load=async function(){
 if(!this.h||this.busy)return;this.busy=true;this.render();
 try{
  [this.d,this.c,this.features]=await Promise.all([this.ws(`${D}/dashboard`),this.c||this.ws(`${D}/catalog`),this.ws(`${D}/features`)]);
  this.decorateFeatures();
  if(this.detail)await this.loadDetail(this.detail.animal.id,false);
  this.err=null;
 }catch(e){this.err=e?.message||String(e)}
 this.busy=false;this.render();
};
AH071.loadDetail=async function(id,r=true){
 try{
  const [detail,attachmentData]=await Promise.all([this.ws(`${D}/animal_detail`,{animal_id:id,event_limit:500}),this.ws(`${D}/attachments/list`,{animal_id:id})]);
  this.detail=detail;this.detail.attachments=attachmentData.attachments||[];this.decorateFeatures();
  const animals=this.detailAnimals(this.detail.animal.group_id);const index=Math.max(0,animals.findIndex(x=>x.id===id));this.animalPage=Math.floor(index/10);
  this.detailGroup=this.detail.animal.group_id||"ungrouped";this.view="animal-detail";if(r)this.render();
 }catch(e){this.notify(`${this.t("failed")}: ${e?.message||e}`,true)}
};
AH071.detailAnimals=function(groupId){return(this.d?.animals||[]).filter(x=>!x.is_archived&&(groupId?x.group_id===groupId:!x.group_id)).sort((a,b)=>a.name.localeCompare(b.name))};
AH071.groupById=function(id){return(this.features?.groups||[]).find(x=>x.id===id)};
AH071.body=function(){
 let html=AH071Base.body.call(this);
 if(this.d)html=html.replace("<header><b",'<header><button class="menuButton" data-action="menu" aria-label="Menu"><ha-icon icon="mdi:menu"></ha-icon></button><b');
 return html;
};
AH071.render=function(){AH071Base.render.call(this);this.shadowRoot.innerHTML+=`<style>${AH071_CSS}</style>`;if(this.d&&!this.features&&!this.busy&&this.h&&!this.featureLoadQueued){this.featureLoadQueued=true;queueMicrotask(()=>{this.featureLoadQueued=false;if(!this.features&&!this.busy)this.load()})}};
AH071.download=async function(kind,resourceId=""){
 const result=await this.ws(`${D}/download`,{kind,...(resourceId?{resource_id:resourceId}:{})});
 const link=document.createElement("a");link.href=result.url;link.rel="noopener";document.body.append(link);link.click();link.remove();
};
AH071.handleClick=async function(e){
 const b=e.composedPath().find(x=>x?.dataset&&(x.dataset.action||x.dataset.view));if(!b)return;
 const{action,id}=b.dataset;
 if(action==="menu"){this.dispatchEvent(new CustomEvent("hass-toggle-menu",{bubbles:true,composed:true}));return}
 if(action==="group-filter"){this.groupFilter=id||"all";if(b.dataset.view)this.view=b.dataset.view;this.render();return}
 if(action==="create-group"){this.open("create-group");return}
 if(action==="edit-group"){this.open("edit-group",{groupId:id});return}
 if(action==="attach-document"){this.open("attach-document",{animalId:id});return}
 if(action==="weight-step"){
  const input=this.shadowRoot.querySelector('form[data-form="weight"] input[name="weight"]');if(!input)return;
  const unit=this.shadowRoot.querySelector('form[data-form="weight"] select[name="weight_unit"]')?.value||"kg";
  const step=unit==="kg"?.01:1;const value=Number(input.value||0)+Number(b.dataset.delta||0)*step;input.value=String(Math.max(step,Math.round(value/step)*step));input.focus();return
 }
 if(action==="animal-page"){this.animalPage=Math.max(0,Number(this.animalPage||0)+Number(b.dataset.delta||0));this.render();return}
 if(action==="detail-group"){
  const groupId=id==="ungrouped"?null:id;const first=this.detailAnimals(groupId)[0];if(first)await this.loadDetail(first.id);return
 }
 if(action==="download-attachment"){await this.download("attachment",id);return}
 if(action==="export-pdf"){await this.download("animal_pdf",id);return}
 if(action==="export-json"){await this.download("json");return}
 if(action==="export-backup"){await this.download("backup");return}
 if(action==="delete-attachment"){
  await this.ws(`${D}/attachments/delete`,{attachment_id:id});await this.loadDetail(this.detail.animal.id);this.notify(this.t("done"));return
 }
 return AH071Base.handleClick.call(this,e);
};
AH071.handleChange=function(e){
 AH071Base.handleChange.call(this,e);const x=e.composedPath()[0],f=x?.form;
 if(f?.dataset.form==="weight"&&x.name==="animal_id")this.prefillWeight(f,x.value);
};
AH071.prefillWeight=function(form,animalId){
 const animal=this.animal(animalId),weight=animal?.latest_weight;const input=form.elements.weight,unit=form.elements.weight_unit;
 if(weight){input.value=weight.original_value;unit.value=weight.original_unit}else{input.value="";unit.value="kg"}
};
AH071.recordId=function(result){
 const candidates=[result,result?.response,result?.result,result?.response?.response,result?.event,result?.response?.event];
 for(const item of candidates)if(item&&typeof item==="object"&&(item.id||item.event_id))return item.id||item.event_id;
 return null;
};
AH071.filesFrom=function(form){return[...form.querySelectorAll('input[type="file"]')].flatMap(input=>[...input.files||[]])};
AH071.uploadFiles=async function(form,animalId,eventId=null){
 const files=this.filesFrom(form);if(!files.length)return[];const max=this.features?.max_attachment_size_bytes||15728640;const title=form.elements.document_title?.value||null;const uploaded=[];
 for(const file of files){
  if(file.size>max)throw Error(this.t("fileTooLarge"));
  const target=await this.ws(`${D}/attachments/upload`,{animal_id:animalId,...(eventId?{event_id:eventId}:{})});
  const payload=new FormData();payload.append("file",file,file.name||"document.jpg");if(title)payload.append("title",title);
  const response=await fetch(target.url,{method:"POST",body:payload,credentials:"same-origin"});if(!response.ok)throw Error((await response.text())||`HTTP ${response.status}`);uploaded.push(await response.json())
 }
 return uploaded;
};
AH071.saveAnimal=async function(o){
 let animalId=o.animal_id||null,result;
 if(animalId){const a=this.animal(animalId),p={device_id:a.device_id,name:o.name,species:o.species,breed:o.breed||null,color:o.color||null,birth_date:o.birth_date||null,arrival_date:o.arrival_date||null};if(o.sex)p.sex=o.sex;result=await this.svc("update_animal",p,true)}
 else{const p={name:o.name,species:o.species};for(const k of["breed","color","sex","birth_date","arrival_date"])if(o[k])p[k]=o[k];result=await this.svc("create_animal",p,true);animalId=this.recordId(result)}
 if(!animalId)throw Error("Animal ID missing from service response");
 await this.ws(`${D}/animal_group/set`,{animal_id:animalId,...(o.group_id?{group_id:o.group_id}:{})});return result
};
AH071.saveWeight=function(o){const p={device_id:this.animal(o.animal_id).device_id,weight:Number(o.weight),weight_unit:o.weight_unit};for(const k of["occurred_at","notes"])if(o[k])p[k]=o[k];return this.svc("record_weight",p,true)};
AH071.saveEvent=function(o){const p={device_id:this.animal(o.animal_id).device_id,event_type:o.event_type,title:o.title};for(const k of["occurred_at","notes"])if(o[k])p[k]=o[k];return this.svc("create_event",p,true)};
AH071.saveSymptom=function(o){const p={device_id:this.animal(o.animal_id).device_id,symptom:o.symptom,severity:o.severity};for(const k of["occurred_at","notes"])if(o[k])p[k]=o[k];if(o.symptom==="other")p.custom_symptom=o.custom_symptom;return this.svc("record_symptom",p,true)};
AH071.handleSubmit=async function(e){
 const f=e.composedPath().find(x=>x?.tagName==="FORM");if(!f)return;const kind=f.dataset.form;
 if(!["animal","group","weight","event","symptom","attachment","execute"].includes(kind))return AH071Base.handleSubmit.call(this,e);
 e.preventDefault();const o=data(f);this.busy=true;this.render();
 try{
  if(kind==="animal")await this.saveAnimal(o);
  if(kind==="group"){
   const payload={name:o.name,...(o.species?{species:o.species}:{}),...(o.description?{description:o.description}:{})};
   if(o.group_id)await this.ws(`${D}/groups/update`,{group_id:o.group_id,...payload});else await this.ws(`${D}/groups/create`,payload)
  }
  if(["weight","event","symptom"].includes(kind)){
   const result=kind==="weight"?await this.saveWeight(o):kind==="event"?await this.saveEvent(o):await this.saveSymptom(o);const files=this.filesFrom(f);
   if(files.length){const eventId=this.recordId(result);if(!eventId)throw Error(this.t("attachmentMissingEvent"));await this.uploadFiles(f,o.animal_id,eventId)}
  }
  if(kind==="execute"){
   const occurrence=this.occ(o.occurrence_id),result=await AH071Base.saveExecution.call(this,f,o),files=this.filesFrom(f);
   if(files.length&&occurrence?.animal_id)await this.uploadFiles(f,occurrence.animal_id,this.recordId(result))
  }
  if(kind==="attachment"){const files=this.filesFrom(f);if(!files.length)throw Error(this.t("chooseFiles"));await this.uploadFiles(f,o.animal_id,null)}
  this.busy=false;await this.after();
 }catch(x){this.busy=false;this.notify(`${this.t("failed")}: ${x?.message||x}`,true);this.render()}
};
AH071.fileFields=function(){return`<fieldset class="wide attachmentFields"><legend>${this.t("documents")}</legend>${this.field("documentTitle","document_title")}<div class="fileChoices wide"><label class="fileChoice"><ha-icon icon="mdi:file-upload-outline"></ha-icon><span>${this.t("chooseFiles")}</span><input type="file" name="attachment_files" multiple accept="image/*,application/pdf,text/plain,.doc,.docx,.odt,.rtf"></label><label class="fileChoice"><ha-icon icon="mdi:camera-outline"></ha-icon><span>${this.t("takePhoto")}</span><input type="file" name="camera_file" accept="image/*" capture="environment"></label></div><small class="wide hint">${this.t("localStorage")}</small></fieldset>`};
AH071.groupSelect=function(value=""){const options=[`<option value="">${this.t("ungrouped")}</option>`,...(this.features?.groups||[]).map(x=>`<option value="${esc(x.id)}" ${x.id===value?"selected":""}>${esc(x.name)}</option>`)];return`<label><span>${this.t("group")}</span><select name="group_id">${options.join("")}</select></label>`};
AH071.execForm=function(x){
 let html=AH071Base.execForm.call(this,x);if(!x?.animal_id)return html;
 const timeField=this.field("performed_at","performed_at","datetime-local");html=html.replace(timeField,`${timeField}<small class="hint">${this.t("emptyNow")}</small>`);
 return html.replace('<div class="buttons wide">',`${this.fileFields()}<div class="buttons wide">`)
};
AH071.form=function(){
 const m=this.modal;
 if(m?.type==="create-group"||m?.type==="edit-group"){
  const g=m.type==="edit-group"?this.groupById(m.groupId)||{}:{};return`<h2><ha-icon icon="mdi:account-group-outline"></ha-icon>${this.t(m.type==="edit-group"?"editGroup":"createGroup")}</h2><form data-form="group">${g.id?`<input type="hidden" name="group_id" value="${esc(g.id)}">`:""}${this.field("groupName","name","text",g.name,"required autofocus")}${this.field("species","species","text",g.species)}${this.area("groupDescription","description",g.description)}${this.buttons()}</form>`
 }
 if(m?.type==="attach-document")return`<h2><ha-icon icon="mdi:paperclip"></ha-icon>${this.t("attachDocument")}</h2><form data-form="attachment"><input type="hidden" name="animal_id" value="${esc(m.animalId)}">${this.fileFields()}${this.buttons()}</form>`;
 if(m?.type==="record-weight"){
  const a=this.animal(m.animalId)||(this.d.animals||[])[0],w=a?.latest_weight;return`<h2>${this.t("recordWeight")}</h2><form data-form="weight">${this.animalSel(m.animalId)}<label><span>${this.t("weight")}</span><div class="weightStepper"><button type="button" data-action="weight-step" data-delta="-1"><ha-icon icon="mdi:minus"></ha-icon></button><input name="weight" type="number" value="${esc(w?.original_value||"")}" required min="0.000001" step="any"><button type="button" data-action="weight-step" data-delta="1"><ha-icon icon="mdi:plus"></ha-icon></button></div></label>${this.sel("dose_unit","weight_unit",this.c.weight_units,w?.original_unit||"kg","required")}${this.field("occurred_at","occurred_at","datetime-local")}<small class="hint">${this.t("emptyNow")}</small>${this.area("notes","notes")}${this.fileFields()}${this.buttons()}</form>`
 }
 let html=AH071Base.form.call(this);
 if(m?.type==="create-animal"||m?.type==="edit-animal"){
  const groupId=m.type==="edit-animal"?this.animal(m.animalId)?.group_id||"":"";html=html.replace('<div class="buttons wide">',`${this.groupSelect(groupId)}<div class="buttons wide">`)
 }
 if(m?.type==="record-event"||m?.type==="record-symptom"){
  const timeField=this.field("occurred_at","occurred_at","datetime-local");html=html.replace(timeField,`${timeField}<small class="hint">${this.t("emptyNow")}</small>`);html=html.replace('<div class="buttons wide">',`${this.fileFields()}<div class="buttons wide">`)
 }
 return html
};
AH071.overview=function(){
 const base=AH071Base.overview.call(this);const groups=this.features?.groups||[];
 const groupCards=groups.map(g=>`<button class="groupCard" data-view="animals" data-action="group-filter" data-id="${esc(g.id)}"><ha-icon icon="mdi:account-group-outline"></ha-icon><span><b>${esc(g.name)}</b><small>${g.animal_count} ${this.t("animals")}</small></span></button>`).join("");
 return`${base}<section class="card"><div class="sectionHeading"><h2>${this.t("groups")}</h2><button data-action="create-group"><ha-icon icon="mdi:plus-circle-outline"></ha-icon>${this.t("createGroup")}</button></div><div class="groupCards">${groupCards||this.empty("noAnimals")}</div></section><section class="card"><h2>${this.t("exports")}</h2><p>${this.t("localStorage")}</p><div class="actions"><button data-action="export-json"><ha-icon icon="mdi:code-json"></ha-icon>${this.t("jsonExport")}</button><button data-action="export-backup"><ha-icon icon="mdi:backup-restore"></ha-icon>${this.t("backupExport")}</button></div></section>`
};
AH071.animals=function(){
 const q=this.filter.toLowerCase(),groups=this.features?.groups||[];let animals=this.d.animals.filter(x=>!q||[x.name,x.species,x.breed,x.status,x.id,x.group_name].some(y=>String(y||"").toLowerCase().includes(q)));const selected=this.groupFilter||"all";
 if(selected==="ungrouped")animals=animals.filter(x=>!x.group_id);else if(selected!=="all")animals=animals.filter(x=>x.group_id===selected);
 const tabs=[`<button class="${selected==="all"?"on":""}" data-action="group-filter" data-id="all">${this.t("allAnimals")}</button>`,...groups.map(g=>`<button class="${selected===g.id?"on":""}" data-action="group-filter" data-id="${esc(g.id)}">${esc(g.name)} <small>${g.animal_count}</small></button>`),`<button class="${selected==="ungrouped"?"on":""}" data-action="group-filter" data-id="ungrouped">${this.t("ungrouped")}</button>`].join("");
 return`${this.heading("animals",`<button data-action="create-group"><ha-icon icon="mdi:account-group-outline"></ha-icon>${this.t("createGroup")}</button><button class="primary" data-action="create-animal"><ha-icon icon="mdi:plus-circle-outline"></ha-icon>${this.t("createAnimal")}</button>`)}<div class="groupTabs">${tabs}</div><section class="grid">${animals.map(x=>this.animalCard(x)).join("")||this.empty("noAnimals")}</section>`
};
AH071.animalCard=function(a){let html=AH071Base.animalCard.call(this,a);if(a.group_name)html=html.replace(esc(a.species),`${esc(a.group_name)} · ${esc(a.species)}`);return html};
AH071.attachmentList=function(items){return items.length?`<div class="attachmentList">${items.map(x=>`<div class="attachment"><ha-icon icon="${String(x.media_type).startsWith("image/")?"mdi:file-image-outline":"mdi:file-document-outline"}"></ha-icon><button class="attachmentName" data-action="download-attachment" data-id="${esc(x.id)}"><b>${esc(x.title||x.filename)}</b><small>${esc(x.filename)} · ${this.num(x.size_bytes/1024,0)} KB</small></button><button data-action="delete-attachment" data-id="${esc(x.id)}" title="${this.t("delete")}"><ha-icon icon="mdi:delete-outline"></ha-icon></button></div>`).join("")}</div>`:this.empty("noEvents")};
AH071.eventRow=function(e){let html=AH071Base.eventRow.call(this,e);const attachments=(this.detail?.attachments||[]).filter(x=>x.event_id===e.id);if(attachments.length){const content=`<div class="eventAttachments">${attachments.map(x=>`<button data-action="download-attachment" data-id="${esc(x.id)}"><ha-icon icon="mdi:paperclip"></ha-icon>${esc(x.title||x.filename)}</button>`).join("")}</div>`;const at=html.lastIndexOf("</div>");if(at>=0)html=html.slice(0,at)+content+html.slice(at)}return html};
AH071.animalDetail=function(){
 if(!this.detail)return this.empty("loading");const a=this.detail.animal,w=a.latest_weight,p=this.detail.occurrences.filter(x=>x.status==="pending"),groups=this.features?.groups||[],groupId=a.group_id||null,animals=this.detailAnimals(groupId),pages=Math.max(1,Math.ceil(animals.length/10)),page=Math.min(Number(this.animalPage||0),pages-1),shown=animals.slice(page*10,page*10+10),generalAttachments=(this.detail.attachments||[]).filter(x=>!x.event_id);
 const groupButtons=[...groups.map(g=>`<button class="${groupId===g.id?"on":""}" data-action="detail-group" data-id="${esc(g.id)}">${esc(g.name)}</button>`),`<button class="${!groupId?"on":""}" data-action="detail-group" data-id="ungrouped">${this.t("ungrouped")}</button>`].join("");
 const switcher=`<section class="animalSwitcher"><div class="groupTabs compact">${groupButtons}</div><div class="switchRow"><button data-action="animal-page" data-delta="-1" ${page<=0?"disabled":""}><ha-icon icon="mdi:chevron-left"></ha-icon></button><div class="animalTiles">${shown.map(x=>`<button class="animalTile ${x.id===a.id?"on":""}" data-action="animal-detail" data-id="${esc(x.id)}"><ha-icon icon="mdi:paw"></ha-icon><span>${esc(x.name)}</span></button>`).join("")}</div><button data-action="animal-page" data-delta="1" ${page>=pages-1?"disabled":""}><ha-icon icon="mdi:chevron-right"></ha-icon></button></div></section>`;
 return`${this.heading("animals",`<button data-view="animals"><ha-icon icon="mdi:arrow-left"></ha-icon></button>`)}${switcher}<section class="hero"><ha-icon icon="mdi:paw"></ha-icon><div><h1>${esc(a.name)}</h1><p>${a.group_name?`${esc(a.group_name)} · `:""}${esc(a.species)}${a.breed?` · ${esc(a.breed)}`:""} · ${this.l(a.status)}</p></div><div class="actions"><button data-action="export-pdf" data-id="${a.id}"><ha-icon icon="mdi:file-pdf-box"></ha-icon>${this.t("healthPdf")}</button><button data-action="edit-animal" data-id="${a.id}">${this.t("edit")}</button><button data-action="animal-status" data-id="${a.id}">${this.t("changeStatus")}</button><button data-action="${a.is_archived?"restore":"archive"}" data-id="${a.id}">${this.t(a.is_archived?"restore":"archive")}</button></div></section>${this.quick(a.id)}<div class="quick"><button data-action="attach-document" data-id="${a.id}"><ha-icon icon="mdi:paperclip"></ha-icon>${this.t("attachDocument")}</button></div><section class="stats">${this.stat("mdi:scale",w?`${this.num(w.original_value)} ${w.original_unit}`:"–","currentWeight")}${this.stat("mdi:clipboard",p.length,"openTasks")}${this.stat("mdi:calendar",a.birth_date?this.fmt(a.birth_date):"–","birth_date")}${this.stat("mdi:identifier",a.id,"technicalId")}</section><section class="cols"><article class="card"><h2>${this.t("masterData")}</h2>${this.obj({group:a.group_name,species:a.species,breed:a.breed,color:a.color,sex:a.sex,birth_date:a.birth_date,arrival_date:a.arrival_date,status:a.status})}</article><article class="card"><h2>${this.t("upcoming")}</h2>${this.rows(p.slice(0,20))}</article></section><section class="card"><h2>${this.t("documents")}</h2>${this.attachmentList(generalAttachments)}</section><section class="card"><h2>${this.t("plannedActual")}</h2>${this.detail.events.map(x=>this.eventRow(x)).join("")||this.empty("noEvents")}</section>`
};
const AH071_CSS=`
.menuButton{display:none;border:0;background:transparent;padding:8px}.groupTabs{display:flex;gap:8px;overflow:auto;padding:2px 0 14px;margin-bottom:8px}.groupTabs button{white-space:nowrap}.groupTabs button.on,.animalTile.on{border-color:var(--primary-color);color:var(--primary-color);background:color-mix(in srgb,var(--primary-color) 10%,var(--card-background-color))}.groupTabs.compact{margin:0;padding:0 0 10px}.groupCards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px}.groupCard{justify-content:flex-start;text-align:left;padding:14px}.groupCard>span{display:flex;flex-direction:column;align-items:flex-start}.groupCard small{color:var(--secondary-text-color)}.sectionHeading{display:flex;justify-content:space-between;align-items:center;gap:10px}.sectionHeading h2{margin:0}.animalSwitcher{margin-bottom:14px;padding:12px;border:1px solid var(--divider-color);border-radius:14px;background:var(--card-background-color)}.switchRow{display:grid;grid-template-columns:auto 1fr auto;gap:8px;align-items:stretch}.animalTiles{display:grid;grid-template-columns:repeat(5,minmax(90px,1fr));gap:8px}.animalTile{min-width:0;flex-direction:column}.animalTile span{max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.weightStepper{display:grid;grid-template-columns:auto 1fr auto;gap:6px}.weightStepper button{padding:8px}.hint{display:block;color:var(--secondary-text-color);align-self:end;padding:0 0 9px}.attachmentFields{border:1px solid var(--divider-color);border-radius:10px;padding:12px}.fileChoices{display:grid;grid-template-columns:1fr 1fr;gap:8px}.fileChoice{display:flex!important;flex-direction:row!important;align-items:center;justify-content:center;padding:12px;border:1px dashed var(--divider-color);border-radius:10px;cursor:pointer}.fileChoice input{position:absolute!important;width:1px!important;height:1px!important;opacity:0}.attachmentList{display:flex;flex-direction:column}.attachment{display:grid;grid-template-columns:auto 1fr auto;gap:9px;align-items:center;padding:9px 0;border-top:1px solid var(--divider-color)}.attachment:first-child{border-top:0}.attachmentName{display:flex;flex-direction:column;align-items:flex-start;border:0;background:transparent;padding:0;text-align:left}.attachmentName small{color:var(--secondary-text-color)}.eventAttachments{display:flex;gap:6px;flex-wrap:wrap;margin-top:7px}.eventAttachments button{padding:5px 8px}.quick+.quick{margin-top:-10px}.modal fieldset.attachmentFields{display:grid}
@media(max-width:850px){.menuButton{display:inline-flex}.animalTiles{grid-template-columns:repeat(3,minmax(78px,1fr))}}
@media(max-width:520px){.animalTiles{grid-template-columns:repeat(2,minmax(75px,1fr))}.fileChoices{grid-template-columns:1fr}.sectionHeading{align-items:flex-start;flex-direction:column}}
`;
