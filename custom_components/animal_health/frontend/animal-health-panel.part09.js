Object.assign(L,{
 reduced_appetite:["Verminderter Appetit","Reduced appetite"],
 lethargy:["Teilnahmslosigkeit","Lethargy"],
 diarrhea:["Durchfall","Diarrhea"],
 coughing:["Husten","Coughing"],
 sneezing:["Niesen","Sneezing"],
 lameness:["Lahmheit","Lameness"],
 weight_loss:["Gewichtsverlust","Weight loss"]
});
const AH072=AnimalHealthPanel.prototype;
const AH072Base={
 body:AH072.body,
 render:AH072.render,
 handleClick:AH072.handleClick,
 handleChange:AH072.handleChange,
 form:AH072.form,
 overview:AH072.overview,
 animals:AH072.animals,
 tasks:AH072.tasks,
 animalChecks:AH072.animalChecks
};
AH072.speciesItem=function(value){
 const needle=String(value||"").trim().toLocaleLowerCase();if(!needle)return null;
 return(this.c?.species||[]).find(item=>[item.id,item.name_de,item.name_en,...(item.aliases||[])].some(candidate=>String(candidate||"").trim().toLocaleLowerCase()===needle))||null
};
AH072.speciesLabel=function(value){const item=this.speciesItem(value);return item?(this.lang()?item.name_en:item.name_de)||item.name_de||item.name_en||item.id:String(value||"–")};
AH072.speciesIcon=function(value){
 const item=this.speciesItem(value),id=String(item?.id||value||"").trim().toLocaleLowerCase();
 if(["dog","hund","hunde"].includes(id))return"mdi:dog";
 if(["cat","katze","katzen"].includes(id))return"mdi:cat";
 if(["chicken","duck","goose","turkey","quail","pigeon","guinea_fowl","bird","huhn","hühner","ente","gans","truthuhn","pute","wachtel","taube","perlhuhn","vogel"].includes(id))return"mdi:bird";
 if(["rabbit","kaninchen"].includes(id))return"mdi:rabbit";
 if(["horse","donkey","pferd","esel"].includes(id))return"mdi:horse";
 if(["cattle","rind","kuh","kalb"].includes(id))return"mdi:cow";
 if(["sheep","goat","schaf","ziege"].includes(id))return"mdi:sheep";
 if(["pig","schwein"].includes(id))return"mdi:pig";
 if(["bee","biene","honigbiene"].includes(id))return"mdi:bee";
 if(["fish","fisch"].includes(id))return"mdi:fish";
 if(["tortoise_turtle","schildkröte"].includes(id))return"mdi:turtle";
 if(["snake","schlange"].includes(id))return"mdi:snake";
 return"mdi:paw"
};
AH072.speciesSelect=function(value="",required=true){
 const items=this.c?.species||[],matched=this.speciesItem(value),selected=matched?.id||String(value||"");
 const known=new Set(items.map(item=>String(item.id)));
 const legacy=selected&&!known.has(selected)?`<option value="${esc(selected)}" selected>${esc(value)}</option>`:"";
 const options=items.map(item=>`<option value="${esc(item.id)}" ${item.id===selected?"selected":""}>${esc((this.lang()?item.name_en:item.name_de)||item.name_de||item.name_en||item.id)}</option>`).join("");
 return`<label><span>${this.t("species")}</span><select name="species" ${required?"required":""}><option value="" ${selected?"":"selected"} disabled>–</option>${legacy}${options}</select></label>`
};
AH072.animalChecks=function(animals,selectedId=this.modal?.animalId||""){return`<div class="checks wide">${animals.map(animal=>`<label><input type="checkbox" name="device_ids" value="${esc(animal.device_id)}" ${animal.id===selectedId?"checked":""}><span>${esc(animal.name)}</span></label>`).join("")}</div>`};
AH072.body=function(){return AH072Base.body.call(this).replace('<b><ha-icon icon="mdi:paw"></ha-icon> Animal Health</b>','<b class="brand"><ha-icon icon="mdi:paw"></ha-icon><span>Animal Health</span></b>')};
AH072.render=function(){AH072Base.render.call(this);this.shadowRoot.innerHTML+=`<style>${AH072_CSS}</style>`};
AH072.download=async function(kind,resourceId=""){
 const result=await this.ws(`${D}/download`,{kind,...(resourceId?{resource_id:resourceId}:{})});
 const response=await fetch(result.url,{credentials:"same-origin"});if(!response.ok)throw Error((await response.text())||`HTTP ${response.status}`);
 const blob=await response.blob(),disposition=response.headers.get("Content-Disposition")||"";
 const encoded=disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1],basic=disposition.match(/filename="([^"]+)"/i)?.[1];
 let filename=basic||({json:"animal_health.json",backup:"animal_health_backup.zip",animal_pdf:`animal_health_${resourceId}.pdf`,attachment:`attachment_${resourceId}`}[kind]||"animal_health_download");
 if(encoded)try{filename=decodeURIComponent(encoded)}catch(_error){filename=encoded}
 const url=URL.createObjectURL(blob),link=document.createElement("a");link.href=url;link.download=filename;link.style.display="none";document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),0)
};
AH072.handleClick=async function(e){
 const button=e.composedPath().find(node=>node?.dataset&&(node.dataset.action||node.dataset.view));if(!button)return;
 const{action}=button.dataset;
 if(action==="create-animal"&&this.view==="animals"&&this.groupFilter&&!['all','ungrouped'].includes(this.groupFilter)){this.open("create-animal",{groupId:this.groupFilter});return}
 if(action==="weight-step"){
  const input=this.shadowRoot.querySelector('form[data-form="weight"] input[name="weight"]');if(!input)return;
  const unit=this.shadowRoot.querySelector('form[data-form="weight"] select[name="weight_unit"]')?.value||"kg",step=unit==="kg"?.01:1,decimals=unit==="kg"?2:0;
  const value=Number(input.value||0)+Number(button.dataset.delta||0)*step,rounded=Math.round((value+Number.EPSILON)/step)*step;
  input.value=Math.max(step,rounded).toFixed(decimals);input.focus();return
 }
 return AH072Base.handleClick.call(this,e)
};
AH072.prefillSpeciesFromGroup=function(form,groupId){const group=this.groupById(groupId),input=form?.elements?.species;if(group?.species&&input)input.value=this.speciesLabel(group.species)};
AH072.handleChange=function(e){AH072Base.handleChange.call(this,e);const input=e.composedPath()[0],form=input?.form;if(form?.dataset.form==="animal"&&input.name==="group_id")this.prefillSpeciesFromGroup(form,input.value)};
AH072.form=function(){
 const modal=this.modal;
 if(modal?.type==="create-group"||modal?.type==="edit-group"){
  const group=modal.type==="edit-group"?this.groupById(modal.groupId)||{}:{},icon=this.speciesIcon(group.species);
  return`<h2><ha-icon icon="${icon}"></ha-icon>${this.t(modal.type==="edit-group"?"editGroup":"createGroup")}</h2><form data-form="group">${group.id?`<input type="hidden" name="group_id" value="${esc(group.id)}">`:""}${this.field("groupName","name","text",group.name,"required autofocus")}${this.speciesSelect(group.species,true)}${this.area("groupDescription","description",group.description)}${this.buttons()}</form>`
 }
 let html=AH072Base.form.call(this);
 if(modal?.type==="create-animal"&&modal.groupId){
  html=html.replace(this.groupSelect(""),this.groupSelect(modal.groupId));
  const group=this.groupById(modal.groupId);if(group?.species)html=html.replace(this.field("species","species","text","",'required list="species"'),this.field("species","species","text",this.speciesLabel(group.species),'required list="species"'))
 }
 return html
};
AH072.overview=function(){
 const base=AH071Base.overview.call(this),groups=this.features?.groups||[];
 const cards=groups.map(group=>`<article class="groupCard"><button class="groupOpen" data-view="animals" data-action="group-filter" data-id="${esc(group.id)}"><ha-icon icon="${this.speciesIcon(group.species)}"></ha-icon><span><b>${esc(group.name)}</b><small>${esc(this.speciesLabel(group.species))} · ${group.animal_count} ${this.t("animals")}</small></span></button><button class="groupEdit" data-action="edit-group" data-id="${esc(group.id)}" title="${this.t("editGroup")}"><ha-icon icon="mdi:pencil-outline"></ha-icon></button></article>`).join("");
 return`${base}<section class="card"><div class="sectionHeading"><h2>${this.t("groups")}</h2><button data-action="create-group"><ha-icon icon="mdi:plus-circle-outline"></ha-icon>${this.t("createGroup")}</button></div><div class="groupCards">${cards||this.empty("noAnimals")}</div></section><section class="card"><h2>${this.t("exports")}</h2><p>${this.t("localStorage")}</p><div class="actions"><button data-action="export-json"><ha-icon icon="mdi:code-json"></ha-icon>${this.t("jsonExport")}</button><button data-action="export-backup"><ha-icon icon="mdi:backup-restore"></ha-icon>${this.t("backupExport")}</button></div></section>`
};
AH072.animals=function(){
 const q=this.filter.toLowerCase(),groups=this.features?.groups||[];let animals=this.d.animals.filter(animal=>!q||[animal.name,animal.species,animal.breed,animal.status,animal.id,animal.group_name].some(value=>String(value||"").toLowerCase().includes(q)));const selected=this.groupFilter||"all";
 if(selected==="ungrouped")animals=animals.filter(animal=>!animal.group_id);else if(selected!=="all")animals=animals.filter(animal=>animal.group_id===selected);
 const tabs=[`<button class="${selected==="all"?"on":""}" data-action="group-filter" data-id="all">${this.t("allAnimals")}</button>`,...groups.map(group=>`<button class="${selected===group.id?"on":""}" data-action="group-filter" data-id="${esc(group.id)}">${esc(group.name)} <small>${group.animal_count}</small></button>`),`<button class="${selected==="ungrouped"?"on":""}" data-action="group-filter" data-id="ungrouped">${this.t("ungrouped")}</button>`].join("");
 const editGroup=selected!=="all"&&selected!=="ungrouped"?`<button data-action="edit-group" data-id="${esc(selected)}"><ha-icon icon="mdi:pencil-outline"></ha-icon>${this.t("editGroup")}</button>`:"";
 return`${this.heading("animals",`${editGroup}<button data-action="create-group"><ha-icon icon="mdi:account-group-outline"></ha-icon>${this.t("createGroup")}</button><button class="primary" data-action="create-animal"><ha-icon icon="mdi:plus-circle-outline"></ha-icon>${this.t("createAnimal")}</button>`)}<div class="groupTabs">${tabs}</div><section class="grid">${animals.map(animal=>this.animalCard(animal)).join("")||this.empty("noAnimals")}</section>`
};
AH072.tasks=function(){
 const q=this.filter.toLowerCase(),occurrences=this.d.occurrences.filter(item=>!q||[item.task_title,item.animal_name,item.task_kind,item.status].some(value=>String(value||"").toLowerCase().includes(q)));
 const definitions=this.d.tasks.filter(task=>task.recurrence_type!=="once"||this.d.occurrences.some(item=>String(item.task_id)===String(task.id)&&item.status==="pending"));
 return`${this.heading("tasks",`<button class="primary" data-action="create-task"><ha-icon icon="mdi:clipboard-plus"></ha-icon>${this.t("createTask")}</button>`)}${this.group("overdue",occurrences.filter(item=>item.is_overdue))}${this.group("dueToday",occurrences.filter(item=>item.is_today))}${this.group("upcoming",occurrences.filter(item=>item.is_upcoming).slice(0,100))}${this.group("completed",occurrences.filter(item=>item.status!=="pending").slice(0,100))}<section class="card"><h2>${this.t("tasks")}</h2>${definitions.map(task=>`<div class="row"><ha-icon icon="${I[task.task_kind]||I.reminder}"></ha-icon><div><b>${esc(task.title)}</b><span>${esc(task.animal_name||this.t("general"))} · ${this.l(task.task_kind)}</span></div><button data-action="toggle" data-id="${task.id}">${this.t(task.is_active?"deactivate":"activate")}</button></div>`).join("")||this.empty("noTasks")}</section>`
};
const AH072_CSS=`
.brand{display:flex;align-items:center;gap:8px}.groupCard{display:grid;grid-template-columns:1fr auto;padding:0;overflow:hidden;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:10px}.groupOpen{border:0;border-radius:0;justify-content:flex-start;text-align:left;padding:14px;min-width:0}.groupOpen>span{display:flex;flex-direction:column;align-items:flex-start;min-width:0}.groupOpen b,.groupOpen small{max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.groupOpen small{color:var(--secondary-text-color)}.groupEdit{border:0;border-left:1px solid var(--divider-color);border-radius:0;padding:10px}
@media(max-width:850px){header .brand{font-size:inherit}.brand span{display:none}.brand ha-icon{font-size:inherit;width:28px;height:28px}}
`;
