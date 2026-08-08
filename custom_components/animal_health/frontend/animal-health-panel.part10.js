Object.assign(T,{
 weight_measurement:["Gewichtserfassung","Weight measurement"],
 mixedGroup:["Gemischt / keine feste Tierart","Mixed / no fixed species"],
 archiveGroup:["Tiergruppe archivieren","Archive animal group"],
 restoreGroup:["Tiergruppe wiederherstellen","Restore animal group"],
 deleteGroup:["Tiergruppe löschen","Delete animal group"],
 archivedGroups:["Archivierte Tiergruppen","Archived animal groups"],
 groupMembersAction:["Der Tiergruppe sind noch Tiere zugeordnet. Was soll mit ihnen geschehen?","Animals are still assigned to this group. What should happen to them?"],
 removeFromGroup:["Aus der Gruppe entfernen","Remove from group"],
 moveToExistingGroup:["In bestehende Tiergruppe verschieben","Move to existing animal group"],
 moveToNewGroup:["In neu anzulegende Tiergruppe verschieben","Move to a new animal group"],
 targetGroup:["Zielgruppe","Target group"],
 newGroupName:["Name der neuen Tiergruppe","New animal group name"],
 confirmArchiveGroup:["Tiergruppe wirklich archivieren?","Archive this animal group?"],
 confirmDeleteGroup:["Tiergruppe wirklich löschen?","Delete this animal group?"],
 noFileSelected:["Noch keine Datei ausgewählt","No file selected yet"],
 selectedFiles:["Ausgewählt","Selected"],
 preparingDownload:["Download wird gestartet …","Starting download …"],
 downloadStarted:["Download wurde gestartet.","Download started."],
 cameraUnavailable:["Direkter Kamerazugriff ist nicht verfügbar. Die Systemauswahl wird geöffnet.","Direct camera access is unavailable. Opening the system picker."],
 takePhotoNow:["Foto aufnehmen","Take photo"],
 closeCamera:["Kamera schliessen","Close camera"]
});
const AH073=AnimalHealthPanel.prototype;
const AH073Base={
 load:AH073.load,
 loadDetail:AH073.loadDetail,
 render:AH073.render,
 body:AH073.body,
 handleClick:AH073.handleClick,
 handleChange:AH073.handleChange,
 handleSubmit:AH073.handleSubmit,
 form:AH073.form,
 overview:AH073.overview,
 animals:AH073.animals,
 animalCard:AH073.animalCard,
 animalDetail:AH073.animalDetail,
 eventRow:AH073.eventRow,
 attachmentList:AH073.attachmentList,
 download:AH073.download,
 speciesIcon:AH073.speciesIcon,
 speciesSelect:AH073.speciesSelect
};
AH073.isGroupArchived=function(groupId){return Boolean(this.groupLifecycle?.archived?.[groupId])};
AH073.activeGroups=function(){return(this.features?.groups||[]).filter(group=>!this.isGroupArchived(group.id))};
AH073.archivedGroups=function(){return(this.features?.groups||[]).filter(group=>this.isGroupArchived(group.id))};
AH073.speciesId=function(value){return String(this.speciesItem(value)?.id||value||"").trim().toLocaleLowerCase()};
AH073.speciesIcon=function(value){return this.speciesId(value)==="chicken"?"mdi:egg-outline":AH073Base.speciesIcon.call(this,value)};
AH073.speciesVisual=function(value){return this.speciesId(value)==="chicken"?`<span class="speciesEmoji" role="img" aria-label="${esc(this.speciesLabel(value))}">🐔</span>`:`<ha-icon icon="${this.speciesIcon(value)}"></ha-icon>`};
AH073.speciesSelect=function(value="",required=true){
 const items=this.c?.species||[],matched=this.speciesItem(value),selected=matched?.id||String(value||""),known=new Set(items.map(item=>String(item.id)));
 const legacy=selected&&!known.has(selected)?`<option value="${esc(selected)}" selected>${esc(value)}</option>`:"";
 const options=items.map(item=>`<option value="${esc(item.id)}" ${item.id===selected?"selected":""}>${esc((this.lang()?item.name_en:item.name_de)||item.name_de||item.name_en||item.id)}</option>`).join("");
 const emptyLabel=required?"–":this.t("mixedGroup");
 return`<label><span>${this.t("species")}</span><select name="species" ${required?"required":""}><option value="" ${selected?"":"selected"} ${required?"disabled":""}>${emptyLabel}</option>${legacy}${options}</select></label>`
};
AH073.load=async function(){
 await AH073Base.load.call(this);
 if(!this.h||!this.d)return;
 try{this.groupLifecycle=await this.ws(`${D}/groups/lifecycle`)}catch(error){this.groupLifecycle={archived:{}};this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}
 this.render()
};
AH073.loadDetail=async function(id,r=true){
 await AH073Base.loadDetail.call(this,id,false);
 if(this.detail?.attachments){
  await Promise.all(this.detail.attachments.filter(item=>String(item.media_type||"").startsWith("image/")).map(async item=>{
   try{const result=await this.ws(`${D}/download`,{kind:"attachment",resource_id:item.id});item.preview_url=result.url}catch(_error){item.preview_url=null}
  }))
 }
 if(r)this.render()
};
AH073.body=function(){
 return AH073Base.body.call(this).replace('<b class="brand"><ha-icon icon="mdi:paw"></ha-icon><span>Animal Health</span></b>','<b class="brand"><img class="brandIcon" src="/api/animal_health/frontend/animal-health-brand.svg" alt=""><span>Animal Health</span></b>')
};
AH073.render=function(){AH073Base.render.call(this);this.shadowRoot.innerHTML+=`<style>${AH073_CSS}</style>`};
AH073.downloadName=function(kind,resourceId=""){return({json:"animal_health.json",backup:"animal_health_backup.zip",animal_pdf:`animal_health_${resourceId}.pdf`,attachment:`attachment_${resourceId}`}[kind]||"animal_health_download")};
AH073.download=async function(kind,resourceId="",button=null){
 if(button){button.disabled=true;button.classList.add("working")}
 this.notify(this.t("preparingDownload"));
 try{
  const result=await this.ws(`${D}/download`,{kind,...(resourceId?{resource_id:resourceId}:{})});
  const link=document.createElement("a");link.href=result.url;link.download=this.downloadName(kind,resourceId);link.style.display="none";document.body.append(link);link.click();link.remove();
  this.notify(this.t("downloadStarted"))
 }finally{if(button)setTimeout(()=>{button.disabled=false;button.classList.remove("working")},1000)}
};
AH073.breedItem=function(value){
 const needle=String(value||"").trim().toLocaleLowerCase();if(!needle)return null;
 return(this.c?.breeds||[]).find(item=>[item.id,item.name,item.display,...(item.aliases||[])].some(candidate=>String(candidate||"").trim().toLocaleLowerCase()===needle))||null
};
AH073.breedsFor=function(species){const id=this.speciesId(species);return(this.c?.breeds||[]).filter(item=>!id||item.species_id===id)};
AH073.colorSuggestions=function(species,breed){
 const speciesId=this.speciesId(species),breedId=String(this.breedItem(breed)?.id||"");
 const speciesMap={
  chicken:["Braun","Rotbraun","Schwarz","Weiss","Grau","Gold","Silber","Gescheckt"],
  dog:["Schwarz","Braun","Weiss","Grau","Creme","Gold","Rot","Schwarz-Weiss","Braun-Weiss","Dreifarbig","Gescheckt"],
  cat:["Schwarz","Weiss","Grau","Blau","Braun","Rot","Creme","Getigert","Schildpatt","Gescheckt"],
  sheep:["Weiss","Schwarz","Braun","Grau","Gescheckt"],
  goat:["Weiss","Schwarz","Braun","Grau","Gescheckt"],
  rabbit:["Weiss","Schwarz","Braun","Grau","Blau","Rot","Wildfarben","Gescheckt"],
  cattle:["Schwarz","Braun","Rotbraun","Weiss","Schwarz-Weiss","Rot-Weiss"],
  horse:["Braun","Dunkelbraun","Schwarz","Fuchs","Schimmel","Falbe","Schecke"]
 };
 const breedMap={
  "chicken.hybrid":["Braun","Rotbraun","Weiss","Schwarz"],
  "chicken.marans":["Schwarz-Kupfer","Blau-Kupfer","Weiss","Schwarz"],
  "chicken.sussex":["Weiss-Schwarz","Rot-Weiss","Braun"],
  "chicken.wyandotte":["Silber-schwarzgesäumt","Gold-schwarzgesäumt","Weiss","Schwarz"],
  "dog.border_collie":["Schwarz-Weiss","Braun-Weiss","Dreifarbig","Blue Merle","Red Merle"],
  "dog.bernese_mountain_dog":["Schwarz-Braun-Weiss"],
  "dog.golden_retriever":["Creme","Gold"],
  "cat.russian_blue":["Blau-Grau"],
  "rabbit.blue_vienna":["Blau-Grau"]
 };
 return[...(breedMap[breedId]||[]),...(speciesMap[speciesId]||[])].filter((value,index,array)=>array.indexOf(value)===index)
};
AH073.sexChoices=function(value=""){return`<fieldset class="wide sexChoices"><legend>${this.t("sex")}</legend>${(this.c?.animal_sexes||[]).map(item=>`<label><input type="radio" name="sex" value="${esc(item)}" ${item===value?"checked":""}><span>${esc(this.l(item))}</span></label>`).join("")}</fieldset>`};
AH073.animalLists=function(species,breed){
 const speciesItems=(this.c?.species||[]).map(item=>item.name_de||item.name_en||item.name||item.id),breeds=this.breedsFor(species),colors=this.colorSuggestions(species,breed);
 return`<datalist id="species">${speciesItems.map(value=>`<option value="${esc(value)}">`).join("")}</datalist><datalist id="breeds">${breeds.map(item=>`<option value="${esc(item.name||item.name_de||item.name_en||item.id)}">`).join("")}</datalist><datalist id="colors">${colors.map(value=>`<option value="${esc(value)}">`).join("")}</datalist>`
};
AH073.refreshAnimalSuggestions=function(form){
 if(!form)return;const species=form.elements.species?.value||"",breed=form.elements.breed?.value||"",breedList=form.querySelector("#breeds"),colorList=form.querySelector("#colors");
 if(breedList)breedList.innerHTML=this.breedsFor(species).map(item=>`<option value="${esc(item.name||item.name_de||item.name_en||item.id)}">`).join("");
 if(colorList)colorList.innerHTML=this.colorSuggestions(species,breed).map(value=>`<option value="${esc(value)}">`).join("")
};
AH073.fileFields=function(){return`<fieldset class="wide attachmentFields"><legend>${this.t("documents")}</legend>${this.field("documentTitle","document_title")}<div class="fileChoices wide"><label class="fileChoice"><ha-icon icon="mdi:file-upload-outline"></ha-icon><span>${this.t("chooseFiles")}</span><input type="file" name="attachment_files" multiple accept="image/*,application/pdf,text/plain,.doc,.docx,.odt,.rtf"></label><button type="button" class="fileChoice" data-action="take-photo"><ha-icon icon="mdi:camera-outline"></ha-icon><span>${this.t("takePhoto")}</span></button><input class="cameraFallback" type="file" name="camera_file" accept="image/*" capture="environment" data-camera-fallback></div><div class="wide fileSelection" data-file-selection>${this.t("noFileSelected")}</div><small class="wide hint">${this.t("localStorage")}</small></fieldset>`};
AH073.updateFileSelection=function(form){const target=form?.querySelector("[data-file-selection]");if(!target)return;const files=this.filesFrom(form);target.textContent=files.length?`${this.t("selectedFiles")}: ${files.map(file=>file.name||"Foto").join(", ")}`:this.t("noFileSelected");target.classList.toggle("hasFiles",files.length>0)};
AH073.startCamera=async function(button){
 const form=button?.closest("form"),fallback=form?.querySelector("[data-camera-fallback]");if(!form||!fallback)return;
 if(!navigator.mediaDevices?.getUserMedia){this.notify(this.t("cameraUnavailable"));fallback.click();return}
 try{
  const stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:"environment"}},audio:false});this.cameraStream=stream;this.cameraForm=form;
  const overlay=document.createElement("div");overlay.className="cameraOverlay";overlay.innerHTML=`<div class="cameraBox"><video autoplay playsinline></video><div class="cameraButtons"><button type="button" data-action="camera-close">${this.t("closeCamera")}</button><button type="button" class="primary" data-action="camera-shot"><ha-icon icon="mdi:camera"></ha-icon>${this.t("takePhotoNow")}</button></div></div>`;this.shadowRoot.querySelector(".modal")?.append(overlay);const video=overlay.querySelector("video");video.srcObject=stream;await video.play()
 }catch(_error){this.notify(this.t("cameraUnavailable"));fallback.click()}
};
AH073.stopCamera=function(){for(const track of this.cameraStream?.getTracks?.()||[])track.stop();this.cameraStream=null;this.shadowRoot.querySelector(".cameraOverlay")?.remove()};
AH073.captureCamera=async function(){
 const video=this.shadowRoot.querySelector(".cameraOverlay video"),form=this.cameraForm;if(!video||!form)return;
 const canvas=document.createElement("canvas");canvas.width=video.videoWidth||1280;canvas.height=video.videoHeight||720;canvas.getContext("2d").drawImage(video,0,0,canvas.width,canvas.height);
 const blob=await new Promise(resolve=>canvas.toBlob(resolve,"image/jpeg",.9));if(blob){const file=new File([blob],`animal-health-${new Date().toISOString().replaceAll(":","-")}.jpg`,{type:"image/jpeg"}),transfer=new DataTransfer();transfer.items.add(file);const input=form.querySelector('[name="camera_file"]');input.files=transfer.files;this.updateFileSelection(form)}
 this.stopCamera()
};
AH073.openImagePreview=async function(id){
 try{const result=await this.ws(`${D}/download`,{kind:"attachment",resource_id:id}),overlay=document.createElement("div");overlay.className="imagePreviewOverlay";overlay.innerHTML=`<button type="button" class="imagePreviewClose" data-action="image-preview-close"><ha-icon icon="mdi:close"></ha-icon></button><img src="${esc(result.url)}" alt="">`;this.shadowRoot.append(overlay)}catch(error){this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}
};
AH073.attachmentList=function(items){return items.length?`<div class="attachmentList">${items.map(item=>{const image=String(item.media_type||"").startsWith("image/");return`<div class="attachment">${image&&item.preview_url?`<button class="attachmentPreview" data-action="preview-attachment" data-id="${esc(item.id)}"><img src="${esc(item.preview_url)}" alt="${esc(item.title||item.filename)}"></button>`:`<ha-icon icon="${image?"mdi:file-image-outline":"mdi:file-document-outline"}"></ha-icon>`}<button class="attachmentName" data-action="download-attachment" data-id="${esc(item.id)}"><b>${esc(item.title||item.filename)}</b><small>${esc(item.filename)} · ${this.num(item.size_bytes/1024,0)} KB</small></button><button data-action="delete-attachment" data-id="${esc(item.id)}" title="${this.t("delete")}"><ha-icon icon="mdi:delete-outline"></ha-icon></button></div>`}).join("")}</div>`:this.empty("noEvents")};
AH073.eventTitle=function(event){return event?.title&&T[event.title]?this.t(event.title):String(event?.title||"")};
AH073.eventRow=function(event){
 let html=AH071Base.eventRow.call(this,{...event,title:this.eventTitle(event)}),attachments=(this.detail?.attachments||[]).filter(item=>item.event_id===event.id);
 if(attachments.length){const content=`<div class="eventAttachments">${attachments.map(item=>String(item.media_type||"").startsWith("image/")&&item.preview_url?`<button class="eventImage" data-action="preview-attachment" data-id="${esc(item.id)}"><img src="${esc(item.preview_url)}" alt="${esc(item.title||item.filename)}"><span>${esc(item.title||item.filename)}</span></button>`:`<button data-action="download-attachment" data-id="${esc(item.id)}"><ha-icon icon="mdi:paperclip"></ha-icon>${esc(item.title||item.filename)}</button>`).join("")}</div>`;const at=html.lastIndexOf("</div>");if(at>=0)html=html.slice(0,at)+content+html.slice(at)}
 return html
};
AH073.animalCard=function(animal){return AH073Base.animalCard.call(this,animal).replace('<ha-icon icon="mdi:paw"></ha-icon>',this.speciesVisual(animal.species))};
AH073.groupCard=function(group,archived=false){
 const main=archived?`<div class="groupOpen static">${this.speciesVisual(group.species)}<span><b>${esc(group.name)}</b><small>${esc(this.speciesLabel(group.species))} · ${group.animal_count} ${this.t("animals")}</small></span></div>`:`<button class="groupOpen" data-view="animals" data-action="group-filter" data-id="${esc(group.id)}">${this.speciesVisual(group.species)}<span><b>${esc(group.name)}</b><small>${esc(this.speciesLabel(group.species))} · ${group.animal_count} ${this.t("animals")}</small></span></button>`;
 const tools=archived?`<div class="groupTools"><button data-action="group-restore" data-id="${esc(group.id)}" title="${this.t("restoreGroup")}"><ha-icon icon="mdi:archive-arrow-up-outline"></ha-icon></button><button data-action="group-delete" data-id="${esc(group.id)}" title="${this.t("deleteGroup")}"><ha-icon icon="mdi:delete-outline"></ha-icon></button></div>`:`<div class="groupTools"><button data-action="edit-group" data-id="${esc(group.id)}" title="${this.t("editGroup")}"><ha-icon icon="mdi:pencil-outline"></ha-icon></button><button data-action="group-archive" data-id="${esc(group.id)}" title="${this.t("archiveGroup")}"><ha-icon icon="mdi:archive-arrow-down-outline"></ha-icon></button><button data-action="group-delete" data-id="${esc(group.id)}" title="${this.t("deleteGroup")}"><ha-icon icon="mdi:delete-outline"></ha-icon></button></div>`;
 return`<article class="groupCard ${archived?"muted":""}">${main}${tools}</article>`
};
AH073.overview=function(){
 const base=AH071Base.overview.call(this),active=this.activeGroups(),archived=this.archivedGroups(),cards=active.map(group=>this.groupCard(group)).join(""),archivedCards=archived.map(group=>this.groupCard(group,true)).join("");
 return`${base}<section class="card"><div class="sectionHeading"><h2>${this.t("groups")}</h2><button data-action="create-group"><ha-icon icon="mdi:plus-circle-outline"></ha-icon>${this.t("createGroup")}</button></div><div class="groupCards">${cards||this.empty("noAnimals")}</div></section>${archived.length?`<section class="card"><h2>${this.t("archivedGroups")}</h2><div class="groupCards">${archivedCards}</div></section>`:""}<section class="card"><h2>${this.t("exports")}</h2><p>${this.t("localStorage")}</p><div class="actions"><button data-action="export-json"><ha-icon icon="mdi:code-json"></ha-icon>${this.t("jsonExport")}</button><button data-action="export-backup"><ha-icon icon="mdi:backup-restore"></ha-icon>${this.t("backupExport")}</button></div></section>`
};
AH073.animals=function(){
 const q=this.filter.toLowerCase(),groups=this.activeGroups();let animals=this.d.animals.filter(animal=>!q||[animal.name,animal.species,animal.breed,animal.status,animal.id,animal.group_name].some(value=>String(value||"").toLowerCase().includes(q)));let selected=this.groupFilter||"all";if(selected!=="all"&&selected!=="ungrouped"&&!groups.some(group=>group.id===selected))selected="all";
 if(selected==="ungrouped")animals=animals.filter(animal=>!animal.group_id);else if(selected!=="all")animals=animals.filter(animal=>animal.group_id===selected);
 const tabs=[`<button class="${selected==="all"?"on":""}" data-action="group-filter" data-id="all">${this.t("allAnimals")}</button>`,...groups.map(group=>`<button class="${selected===group.id?"on":""}" data-action="group-filter" data-id="${esc(group.id)}">${esc(group.name)} <small>${group.animal_count}</small></button>`),`<button class="${selected==="ungrouped"?"on":""}" data-action="group-filter" data-id="ungrouped">${this.t("ungrouped")}</button>`].join("");
 const manage=selected!=="all"&&selected!=="ungrouped"?`<button data-action="edit-group" data-id="${esc(selected)}"><ha-icon icon="mdi:pencil-outline"></ha-icon>${this.t("editGroup")}</button><button data-action="group-archive" data-id="${esc(selected)}"><ha-icon icon="mdi:archive-arrow-down-outline"></ha-icon>${this.t("archiveGroup")}</button><button data-action="group-delete" data-id="${esc(selected)}"><ha-icon icon="mdi:delete-outline"></ha-icon>${this.t("deleteGroup")}</button>`:"";
 return`${this.heading("animals",`${manage}<button data-action="create-group"><ha-icon icon="mdi:account-group-outline"></ha-icon>${this.t("createGroup")}</button><button class="primary" data-action="create-animal"><ha-icon icon="mdi:plus-circle-outline"></ha-icon>${this.t("createAnimal")}</button>`)}<div class="groupTabs">${tabs}</div><section class="grid">${animals.map(animal=>this.animalCard(animal)).join("")||this.empty("noAnimals")}</section>`
};
AH073.animalDetail=function(){
 if(!this.detail)return this.empty("loading");const animal=this.detail.animal,weight=animal.latest_weight,pending=this.detail.occurrences.filter(item=>item.status==="pending"),groups=this.activeGroups(),groupId=animal.group_id||null,animals=this.detailAnimals(groupId),pages=Math.max(1,Math.ceil(animals.length/10)),page=Math.min(Number(this.animalPage||0),pages-1),shown=animals.slice(page*10,page*10+10),generalAttachments=(this.detail.attachments||[]).filter(item=>!item.event_id);
 const groupButtons=[...groups.map(group=>`<button class="${groupId===group.id?"on":""}" data-action="detail-group" data-id="${esc(group.id)}">${esc(group.name)}</button>`),`<button class="${!groupId?"on":""}" data-action="detail-group" data-id="ungrouped">${this.t("ungrouped")}</button>`].join("");
 const switcher=`<section class="animalSwitcher"><div class="groupTabs compact">${groupButtons}</div><div class="switchRow"><button data-action="animal-page" data-delta="-1" ${page<=0?"disabled":""}><ha-icon icon="mdi:chevron-left"></ha-icon></button><div class="animalTiles">${shown.map(item=>`<button class="animalTile ${item.id===animal.id?"on":""}" data-action="animal-detail" data-id="${esc(item.id)}">${this.speciesVisual(item.species)}<span>${esc(item.name)}</span></button>`).join("")}</div><button data-action="animal-page" data-delta="1" ${page>=pages-1?"disabled":""}><ha-icon icon="mdi:chevron-right"></ha-icon></button></div></section>`;
 return`${this.heading("animals",`<button data-view="animals"><ha-icon icon="mdi:arrow-left"></ha-icon></button>`)}${switcher}<section class="hero">${this.speciesVisual(animal.species)}<div><h1>${esc(animal.name)}</h1><p>${animal.group_name?`${esc(animal.group_name)} · `:""}${esc(animal.species)}${animal.breed?` · ${esc(animal.breed)}`:""} · ${this.l(animal.status)}</p></div><div class="actions"><button data-action="export-pdf" data-id="${animal.id}"><ha-icon icon="mdi:file-pdf-box"></ha-icon>${this.t("healthPdf")}</button><button data-action="edit-animal" data-id="${animal.id}">${this.t("edit")}</button><button data-action="animal-status" data-id="${animal.id}">${this.t("changeStatus")}</button><button data-action="${animal.is_archived?"restore":"archive"}" data-id="${animal.id}">${this.t(animal.is_archived?"restore":"archive")}</button></div></section>${this.quick(animal.id)}<div class="quick"><button data-action="attach-document" data-id="${animal.id}"><ha-icon icon="mdi:paperclip"></ha-icon>${this.t("attachDocument")}</button></div><section class="stats">${this.stat("mdi:scale",weight?`${this.num(weight.original_value)} ${weight.original_unit}`:"–","currentWeight")}${this.stat("mdi:clipboard",pending.length,"openTasks")}${this.stat("mdi:calendar",animal.birth_date?this.fmt(animal.birth_date):"–","birth_date")}${this.stat("mdi:identifier",animal.id,"technicalId")}</section><section class="cols"><article class="card"><h2>${this.t("masterData")}</h2>${this.obj({group:animal.group_name,species:animal.species,breed:animal.breed,color:animal.color,sex:animal.sex,birth_date:animal.birth_date,arrival_date:animal.arrival_date,status:animal.status})}</article><article class="card"><h2>${this.t("upcoming")}</h2>${this.rows(pending.slice(0,20))}</article></section><section class="card"><h2>${this.t("documents")}</h2>${this.attachmentList(generalAttachments)}</section><section class="card"><h2>${this.t("plannedActual")}</h2>${this.detail.events.map(item=>this.eventRow(item)).join("")||this.empty("noEvents")}</section>`
};
AH073.groupLifecycleForm=function(modal){
 const group=this.groupById(modal.groupId)||{},members=Object.entries(this.features?.memberships||{}).filter(([,groupId])=>groupId===modal.groupId).map(([animalId])=>this.animal(animalId)).filter(Boolean),targets=this.activeGroups().filter(item=>item.id!==modal.groupId),mode=modal.mode||"archive",title=mode==="delete"?this.t("deleteGroup"):this.t("archiveGroup"),question=mode==="delete"?this.t("confirmDeleteGroup"):this.t("confirmArchiveGroup");
 const disposition=members.length?`<p class="wide">${this.t("groupMembersAction")}</p><fieldset class="wide disposition"><label><input type="radio" name="disposition" value="ungroup" checked><span>${this.t("removeFromGroup")}</span></label><label><input type="radio" name="disposition" value="existing"><span>${this.t("moveToExistingGroup")}</span></label><label><input type="radio" name="disposition" value="new"><span>${this.t("moveToNewGroup")}</span></label></fieldset><label class="wide" data-existing-target hidden><span>${this.t("targetGroup")}</span><select name="target_group_id">${targets.map(item=>`<option value="${esc(item.id)}">${esc(item.name)}</option>`).join("")}</select></label><div class="wide newGroupFields" data-new-target hidden>${this.field("newGroupName","new_group_name")}${this.speciesSelect("",false)}</div><div class="wide memberNames">${members.map(item=>`<span>${esc(item.name)}</span>`).join("")}</div>`:"";
 return`<h2>${title}: ${esc(group.name||"")}</h2><form data-form="group-lifecycle"><input type="hidden" name="group_id" value="${esc(modal.groupId)}"><input type="hidden" name="mode" value="${esc(mode)}"><p class="wide">${question}</p>${disposition}${this.buttons(mode==="delete"?"delete":"archive")}</form>`
};
AH073.form=function(){
 const modal=this.modal;
 if(modal?.type==="group-lifecycle")return this.groupLifecycleForm(modal);
 if(modal?.type==="create-group"||modal?.type==="edit-group"){
  const group=modal.type==="edit-group"?this.groupById(modal.groupId)||{}:{},archived=group.id&&this.isGroupArchived(group.id),tools=group.id?`<div class="wide groupLifecycleButtons">${archived?`<button type="button" data-action="group-restore" data-id="${esc(group.id)}"><ha-icon icon="mdi:archive-arrow-up-outline"></ha-icon>${this.t("restoreGroup")}</button>`:`<button type="button" data-action="group-archive" data-id="${esc(group.id)}"><ha-icon icon="mdi:archive-arrow-down-outline"></ha-icon>${this.t("archiveGroup")}</button>`}<button type="button" class="danger" data-action="group-delete" data-id="${esc(group.id)}"><ha-icon icon="mdi:delete-outline"></ha-icon>${this.t("deleteGroup")}</button></div>`:"";
  return`<h2>${this.speciesVisual(group.species)}${this.t(modal.type==="edit-group"?"editGroup":"createGroup")}</h2><form data-form="group">${group.id?`<input type="hidden" name="group_id" value="${esc(group.id)}">`:""}${this.field("groupName","name","text",group.name,"required autofocus")}${this.speciesSelect(group.species,false)}${this.area("groupDescription","description",group.description)}${tools}${this.buttons()}</form>`
 }
 if(modal?.type==="create-animal"||modal?.type==="edit-animal"){
  const current=modal.type==="edit-animal"?this.animal(modal.animalId)||{}:{},draft=this.animalDraft&&this.animalDraftModal===modal.type?this.animalDraft:null,animal=draft||current,groupId=draft?.group_id??(modal.type==="edit-animal"?current.group_id||"":modal.groupId||""),group=this.groupById(groupId);let species=animal.species||"";if(!species&&group?.species)species=this.speciesLabel(group.species);
  return`<h2><ha-icon icon="mdi:plus-circle-outline"></ha-icon>${this.t(modal.type==="edit-animal"?"edit":"createAnimal")}</h2><form data-form="animal">${current.id?`<input type="hidden" name="animal_id" value="${esc(current.id)}">`:""}${this.field("name","name","text",animal.name,"required autofocus")}${this.field("species","species","text",species,'required list="species"')}${this.field("breed","breed","text",animal.breed,'list="breeds"')}${this.field("color","color","text",animal.color,'list="colors"')}${this.sexChoices(animal.sex||"")}${this.field("birth_date","birth_date","date",animal.birth_date)}${this.field("arrival_date","arrival_date","date",animal.arrival_date)}${this.groupSelect(groupId)}${this.animalLists(species,animal.breed)}${this.buttons()}</form>`
 }
 return AH073Base.form.call(this)
};
AH073.friendlyError=function(error){
 const message=String(error?.message||error||""),match=message.match(/Breed\s+(.+?)\s+belongs to\s+([^,]+),\s*not\s+([^\s.]+)/i);if(!match)return message;
 const breed=match[1],expected=this.speciesLabel(match[2]),actual=this.speciesLabel(match[3]);return this.lang()?`Breed ${breed} belongs to ${expected} and cannot be used for ${actual}.`:`Die Rasse ${breed} gehört zur Tierart ${expected} und kann nicht für ${actual} verwendet werden.`
};
AH073.executeGroupLifecycle=async function(values){
 const groupId=values.group_id,mode=values.mode,members=Object.entries(this.features?.memberships||{}).filter(([,id])=>id===groupId).map(([animalId])=>animalId);let targetGroupId=null;
 if(members.length){
  if(values.disposition==="existing"){targetGroupId=values.target_group_id;if(!targetGroupId)throw Error(this.t("targetGroup"))}
  if(values.disposition==="new"){
   if(!String(values.new_group_name||"").trim())throw Error(this.t("newGroupName"));const created=await this.ws(`${D}/groups/create`,{name:values.new_group_name,...(values.species?{species:values.species}:{})});targetGroupId=created.id
  }
  await Promise.all(members.map(animalId=>this.ws(`${D}/animal_group/set`,{animal_id:animalId,...(targetGroupId?{group_id:targetGroupId}:{})})))
 }
 if(mode==="delete")await this.ws(`${D}/groups/delete`,{group_id:groupId});else await this.ws(`${D}/groups/archive`,{group_id:groupId});this.groupFilter="all"
};
AH073.syncDisposition=function(form){if(!form)return;const value=form.elements.disposition?.value||"ungroup",existing=form.querySelector("[data-existing-target]"),newTarget=form.querySelector("[data-new-target]");if(existing)existing.hidden=value!=="existing";if(newTarget)newTarget.hidden=value!=="new"};
AH073.handleChange=function(event){
 AH073Base.handleChange.call(this,event);const input=event.composedPath()[0],form=input?.form;if(!form)return;
 if(form.dataset.form==="animal"&&["species","breed","group_id"].includes(input.name))this.refreshAnimalSuggestions(form);
 if(input.type==="file")this.updateFileSelection(form);
 if(form.dataset.form==="group-lifecycle"&&input.name==="disposition")this.syncDisposition(form)
};
AH073.handleSubmit=async function(event){
 const form=event.composedPath().find(node=>node?.tagName==="FORM");if(!form)return;
 if(form.dataset.form==="animal"){
  event.preventDefault();const values=data(form);this.animalDraft={...values};this.animalDraftModal=this.modal?.type;const submit=form.querySelector('button[type="submit"]');if(submit)submit.disabled=true;
  try{await this.saveAnimal(values);this.animalDraft=null;this.animalDraftModal=null;await this.after()}catch(error){if(submit)submit.disabled=false;this.notify(`${this.t("failed")}: ${this.friendlyError(error)}`,true)}return
 }
 if(form.dataset.form==="group-lifecycle"){
  event.preventDefault();const values=data(form),submit=form.querySelector('button[type="submit"]');if(submit)submit.disabled=true;
  try{await this.executeGroupLifecycle(values);this.modal=null;await this.load();this.notify(this.t("done"))}catch(error){if(submit)submit.disabled=false;this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}return
 }
 return AH073Base.handleSubmit.call(this,event)
};
AH073.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset&&(node.dataset.action||node.dataset.view));if(!button)return;const{action,id}=button.dataset;
 if(action==="take-photo"){await this.startCamera(button);return}
 if(action==="camera-close"){this.stopCamera();return}
 if(action==="camera-shot"){await this.captureCamera();return}
 if(action==="image-preview-close"){button.closest(".imagePreviewOverlay")?.remove();return}
 if(action==="preview-attachment"){await this.openImagePreview(id);return}
 if(action==="download-attachment"){try{await this.download("attachment",id,button)}catch(error){this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}return}
 if(action==="export-pdf"){try{await this.download("animal_pdf",id,button)}catch(error){this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}return}
 if(action==="export-json"){try{await this.download("json","",button)}catch(error){this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}return}
 if(action==="export-backup"){try{await this.download("backup","",button)}catch(error){this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}return}
 if(action==="group-archive"||action==="group-delete"){this.open("group-lifecycle",{groupId:id,mode:action==="group-delete"?"delete":"archive"});return}
 if(action==="group-restore"){try{await this.ws(`${D}/groups/restore`,{group_id:id});this.modal=null;await this.load();this.notify(this.t("done"))}catch(error){this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}return}
 return AH073Base.handleClick.call(this,event)
};
const AH073_CSS=`
.brandIcon{display:block;width:32px;height:32px;border-radius:50%}.speciesEmoji{display:inline-grid;place-items:center;width:24px;height:24px;font-size:23px;line-height:1}.animalHead .speciesEmoji{width:28px;height:28px;font-size:27px}.hero>.speciesEmoji{width:48px;height:48px;font-size:45px}.animalTile .speciesEmoji{width:25px;height:25px;font-size:24px}.groupCard{grid-template-columns:1fr auto}.groupTools{display:flex;border-left:1px solid var(--divider-color)}.groupTools button{border:0;border-radius:0;border-left:1px solid var(--divider-color);padding:10px}.groupTools button:first-child{border-left:0}.groupOpen.static{display:flex;align-items:center;gap:7px;padding:14px}.groupOpen.static>span{display:flex;flex-direction:column;align-items:flex-start}.groupLifecycleButtons{display:flex;gap:8px;flex-wrap:wrap}.danger{color:var(--error-color)}.sexChoices{display:grid!important;grid-template-columns:repeat(3,1fr)!important;gap:8px!important}.sexChoices label,.disposition label{display:flex!important;flex-direction:row!important;align-items:center!important;gap:8px;padding:10px;border:1px solid var(--divider-color);border-radius:9px;background:var(--secondary-background-color)}.sexChoices input,.disposition input{width:auto!important}.newGroupFields{display:grid;grid-template-columns:1fr 1fr;gap:13px}.memberNames{display:flex;gap:6px;flex-wrap:wrap}.memberNames span{padding:5px 8px;border-radius:999px;background:var(--secondary-background-color)}.fileSelection{padding:8px 10px;border-radius:8px;background:var(--secondary-background-color);color:var(--secondary-text-color)}.fileSelection.hasFiles{color:var(--primary-text-color);font-weight:500}.cameraFallback{position:absolute!important;width:1px!important;height:1px!important;opacity:0!important;pointer-events:none}.cameraOverlay,.imagePreviewOverlay{position:fixed;z-index:300;inset:0;background:#000d;display:grid;place-items:center;padding:16px}.cameraBox{width:min(900px,100%);display:grid;gap:12px}.cameraBox video{width:100%;max-height:75vh;object-fit:contain;background:#000;border-radius:12px}.cameraButtons{display:flex;justify-content:flex-end;gap:8px}.attachmentPreview{padding:0;width:58px;height:58px;overflow:hidden;border-radius:9px}.attachmentPreview img{width:100%;height:100%;object-fit:cover}.attachment:has(.attachmentPreview){grid-template-columns:auto 1fr auto}.eventImage{display:grid!important;grid-template-columns:44px auto!important;align-items:center!important;text-align:left!important;padding:4px 7px!important}.eventImage img{width:40px;height:40px;object-fit:cover;border-radius:6px}.imagePreviewOverlay img{max-width:min(1200px,95vw);max-height:90vh;object-fit:contain;border-radius:10px}.imagePreviewClose{position:absolute;top:18px;right:18px;background:var(--card-background-color)}button.working{opacity:.65;cursor:wait}@media(max-width:850px){.brandIcon{width:30px;height:30px}}@media(max-width:520px){.sexChoices{grid-template-columns:1fr!important}.newGroupFields{grid-template-columns:1fr}.groupTools{flex-direction:column}}
`;
