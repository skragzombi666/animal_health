if(typeof T!=="undefined")Object.assign(T,{
 settingsDeveloper039:["Entwickleroptionen","Developer options"],
 settingsDeveloperHint039:["KI, Datenverwaltung und bewusst getrennte administrative Funktionen","AI, data management and deliberately separated administrative functions"],
 settingsMasterHint039:["Tiergruppen, Kalenderdarstellung und fachliche Stammdaten gezielt verwalten","Manage animal groups, calendar display and domain master data"],
 settingsMedicationHint039:["Produktquellen, Favoriten, Off-Label-Regeln, Medikamente und Behandlungspläne","Product sources, favourites, off-label rules, medicines and treatment plans"],
 settingGroupOrder039:["Reihenfolge der Tiergruppen","Animal group order"],
 settingGroupOrderHint039:["Legt die Reihenfolge in Übersichten, Filtern und Auswahllisten fest.","Defines the order in overviews, filters and selectors."],
 settingWeekStart039:["Darstellung Wochenanfang","Week start display"],
 settingWeekStartHint039:["Bestimmt den ersten Wochentag in Kalender- und Aufgabenansichten.","Defines the first weekday in calendar and task views."],
 settingEntryTypes039:["Eintragsarten","Record types"],
 settingEntryTypesHint039:["Vordefinierte und eigene Arten für Chronikeinträge verwalten.","Manage built-in and personal timeline record types."],
 settingSymptoms039:["Symptome verwalten","Manage symptoms"],
 settingSymptomsHint039:["Symptomkatalog, eigene Begriffe und ausgeblendete Einträge verwalten.","Manage the symptom catalogue, personal terms and hidden entries."],
 settingLocalSuggestions039:["Lokale Vorschläge","Local suggestions"],
 settingLocalSuggestionsHint039:["Aus Verlauf und Nutzung abgeleitete lokale Vorschläge kontrollieren.","Control local suggestions derived from history and usage."],
 settingProductDatabases039:["Produktdatenbanken","Product databases"],
 settingProductDatabasesHint039:["Offizielle, mitgelieferte und eigene Produktquellen verwalten.","Manage official, bundled and personal product sources."],
 settingFavourites039:["Favoriten","Favourites"],
 settingFavouritesHint039:["Bevorzugte Produkte und Behandlungen für die Schnellauswahl festlegen.","Define preferred products and treatments for quick selection."],
 settingOffLabel039:["Off-Label-Anzeige","Off-label display"],
 settingOffLabelHint039:["Regelt separat, wie nicht passend zugelassene Produkte angezeigt werden.","Separately controls how products without a matching authorisation are displayed."],
 settingMedicines039:["Medikamente verwalten","Manage medicines"],
 settingMedicinesHint039:["Eigene Medikamente anlegen, bearbeiten, ausblenden oder archivieren.","Create, edit, hide or archive personal medicines."],
 settingTreatments039:["Behandlungen & Behandlungspläne verwalten","Manage treatments and treatment plans"],
 settingTreatmentsHint039:["Behandlungen, Planbestandteile und wiederverwendbare Behandlungspläne verwalten.","Manage treatments, plan components and reusable treatment plans."],
 settingAi039:["KI-Konfiguration","AI configuration"],
 settingAiHint039:["KI-Anbieter, Modelle, Sprache und Erfassungsverhalten konfigurieren.","Configure AI providers, models, language and capture behaviour."],
 settingAdministration039:["Verwaltung & Daten","Administration and data"],
 settingAdministrationHint039:["Export, Sicherung, Diagnose und technische Verwaltungsfunktionen bündeln.","Bundle export, backup, diagnostics and technical administration."],
 settingDanger039:["Test & Gefahrenbereich","Test and danger zone"],
 settingDangerHint039:["Destruktive Rücksetzungen klar getrennt und mit vollständiger Löschwirkung ausführen.","Run destructive resets separately with their full deletion scope shown."],
 settingsBackOverview039:["Zur Einstellungsübersicht","Back to settings overview"],
 settingsBackGroup039:["Zur Bereichsübersicht","Back to section overview"],
 settingsNoContent039:["Für diesen Punkt ist derzeit kein Inhalt verfügbar.","No content is currently available for this item."],
 selectTreatmentPlan039:["Behandlungsplan auswählen","Select treatment plan"],
 noTreatmentPlans039:["Keine Behandlungspläne vorhanden","No treatment plans available"],
 plannedTreatment039:["Behandlung / zusätzliche Anweisung","Treatment / additional instruction"],
 taskRequiredField039:["Pflichtfeld ausfüllen","Complete the required field"],
 taskTargetMissing039:["Ziel für die Aufgabe auswählen","Select a target for the task"],
 resetIntegration039:["Integration zurücksetzen","Reset integration"],
 resetIntegrationHint039:["Alle Tiere, Tiergruppen, Tags, Aufgaben, Chronikeinträge, Gewichte, Anhänge und Einstellungen von Animal Health werden gelöscht. Die Integration bleibt installiert und startet danach leer.","Deletes all Animal Health animals, groups, tags, tasks, timeline records, weights, attachments and settings. The integration remains installed and starts empty."],
 resetActivity039:["Verlaufs- und Aufgabendaten zurücksetzen","Reset timeline and task data"],
 resetActivityHint039:["Löscht Chronik, Gewichte, Symptome, Medikamentengaben, Aufgaben, Serien und zugehörige Anhänge. Tiere, Tiergruppen, Zuordnungen, Tags, Stammdaten und Tierbilder bleiben erhalten.","Deletes timeline records, weights, symptoms, medication administrations, tasks, series and related attachments. Animals, groups, assignments, tags, master data and animal images remain."],
 destructiveConfirm039:["Diese Aktion löscht Daten dauerhaft. Die oben beschriebene Löschwirkung muss vor der Ausführung ausdrücklich bestätigt werden.","This action permanently deletes data. The deletion scope described above must be explicitly confirmed before execution."]
});
const AH039=AnimalHealthPanel.prototype;
const AH039Base={
 taskForm:AH039.taskForm,
 syncTask:AH039.syncTask,
 applyAITaskDraft:AH039.applyAITaskDraft,
 settingsPage081:AH039.settingsPage081,
 handleClick:AH039.handleClick,
 handleChange:AH039.handleChange,
 handleSubmit:AH039.handleSubmit,
 render:AH039.render
};
AH039.taskProducts039=function(kind){
 const source=typeof this.gabeProducts027==="function"?this.gabeProducts027(kind):[],seen=new Set(),items=[];
 for(const item of source||[]){const name=String(item?.name||item?.product_name||"").trim(),key=name.toLocaleLowerCase();if(!name||seen.has(key))continue;seen.add(key);items.push(item)}
 return items.sort((a,b)=>String(a?.name||"").localeCompare(String(b?.name||""),undefined,{sensitivity:"base"}))
};
AH039.taskProductOptions039=function(kind){return this.taskProducts039(kind).map(item=>`<option value="${esc(item.name||item.product_name||"")}">${esc([item.active_ingredient,item.concentration,item.dosage_form].filter(Boolean).join(" · "))}</option>`).join("")};
AH039.treatmentPlans039=function(){
 const candidates=[];
 for(const container of[this.v0918,this.v0912,this.v0924,this.d,this.features])for(const key of["treatment_plans","treatmentPlans","plans"]){const list=container?.[key];if(Array.isArray(list))candidates.push(...list)}
 for(const name of["treatmentPlans012","treatmentPlans018","availableTreatmentPlans012"]){try{const value=typeof this[name]==="function"?this[name]():null;if(Array.isArray(value))candidates.push(...value)}catch(_error){}}
 const seen=new Set(),result=[];
 for(const raw of candidates){if(!raw||typeof raw!=="object"||raw.is_archived)continue;const id=String(raw.id??raw.plan_id??""),name=String(raw.name||raw.title||raw.plan_name||"").trim();if(!id||!name||seen.has(id))continue;seen.add(id);result.push({...raw,id,name})}
 return result.sort((a,b)=>a.name.localeCompare(b.name,undefined,{sensitivity:"base"}))
};
AH039.taskUnits039=function(selected=""){
 const units=this.c?.dose_units||["mcg","mg","g","ul","ml","drop","tablet","dose","mark","pinch","coffee_spoon"];
 return units.map(value=>`<option value="${esc(value)}" ${String(value)===String(selected||"")?"selected":""}>${esc(this.l(value))}</option>`).join("")
};
AH039.taskRoutes039=function(selected=""){
 const routes=this.c?.administration_routes||[];
 return`<option value="">–</option>${routes.map(value=>`<option value="${esc(value)}" ${String(value)===String(selected||"")?"selected":""}>${esc(this.l(value))}</option>`).join("")}`
};
AH039.taskDoseFields039=function(prefix="planned",options={}){
 const draft=this.aiTaskDraft||{},doseName=options.doseName||`${prefix}_dose`,unitName=options.unitName||`${prefix}_dose_unit`,routeName=options.routeName||`${prefix}_route`,dose=draft[doseName]??draft.planned_dose??"",unit=draft[unitName]||draft.planned_dose_unit||"dose",route=draft[routeName]||draft.planned_route||"",required=options.required!==false,withRoute=options.withRoute!==false;
 return`<label><span>${this.t("dose")}</span><input type="number" min="0.000001" step="any" name="${doseName}" value="${esc(dose)}" ${required?"required":""}></label><label><span>${this.t("dose_unit")}</span><select name="${unitName}" ${required?"required":""}>${this.taskUnits039(unit)}</select></label>${withRoute?`<label><span>${this.t("route")}</span><select name="${routeName}">${this.taskRoutes039(route)}</select></label>`:""}`
};
AH039.taskKindFieldsets039=function(){
 const draft=this.aiTaskDraft||{},medication=esc(draft.planned_medication_name||draft.planned_product_name||""),product=esc(draft.planned_product_name||draft.planned_medication_name||""),plans=this.treatmentPlans039(),selectedPlan=String(draft.planned_treatment_plan_id||""),selectedPlanName=String(draft.treatment_plan_name||""),planOptions=plans.map(plan=>`<option value="${esc(plan.id)}" data-name="${esc(plan.name)}" ${String(plan.id)===selectedPlan?"selected":""}>${esc(plan.name)}</option>`).join("");
 const targetOptions=this.c?.vaccination_targets||[],selectedTargets=new Set((Array.isArray(draft.planned_vaccination_targets)?draft.planned_vaccination_targets:[draft.planned_vaccination_targets]).filter(Boolean).map(String));
 const fieldset=(kind,body)=>`<fieldset class="wide taskKindFields039" data-task-kind039="${kind}" hidden>${body}</fieldset>`;
 const medicationFields=fieldset("medication",`<legend>${this.t("gabeMedication027")}</legend><label class="wide"><span>${this.t("medication_name")}</span><input name="planned_medication_name" value="${medication}" list="task-products-039-medication" required></label>${this.taskDoseFields039("planned")}`);
 const dewormingFields=fieldset("deworming",`<legend>${this.t("gabeDeworming027")}</legend><label class="wide"><span>${this.t("taskProduct027")}</span><input name="planned_medication_name" value="${medication}" list="task-products-039-deworming" required></label>${this.taskDoseFields039("planned")}`);
 const supplementFields=fieldset("supplement",`<legend>${this.t("gabeSupplement027")}</legend><label class="wide"><span>${this.t("taskProduct027")}</span><input name="planned_product_name" value="${product}" list="task-products-039-supplement" required></label>${this.taskDoseFields039("planned")}<label><span>${this.t("doseBasis027")}</span><select name="dose_basis"><option value="per_animal" ${draft.dose_basis==="per_animal"?"selected":""}>${this.t("dosePerAnimal027")}</option><option value="per_kg" ${draft.dose_basis==="per_kg"?"selected":""}>${this.t("dosePerKg027")}</option><option value="per_l_water" ${draft.dose_basis==="per_l_water"?"selected":""}>${this.t("dosePerWater027")}</option><option value="per_kg_feed" ${draft.dose_basis==="per_kg_feed"?"selected":""}>${this.t("dosePerFeed027")}</option></select></label>`);
 const feedFields=fieldset("feed",`<legend>${this.t("gabeFeed027")}</legend><label class="wide"><span>${this.t("taskProduct027")}</span><input name="planned_product_name" value="${product}" list="task-products-039-feed" required></label>${this.taskDoseFields039("planned",{withRoute:false})}<label><span>${this.t("feedStatus027")}</span><select name="feed_status"><option value="offered" ${draft.feed_status!=="consumed"?"selected":""}>${this.t("feedOffered027")}</option><option value="consumed" ${draft.feed_status==="consumed"?"selected":""}>${this.t("feedConsumed027")}</option></select></label>`);
 const vaccine=esc(draft.planned_vaccine_name||""),antigen=esc(draft.planned_antigen||""),customTarget=esc(draft.planned_custom_vaccination_target||"");
 const vaccinationFields=fieldset("vaccination",`<legend>${this.t("gabeVaccination027")}</legend><label class="wide"><span>${this.t("vaccine_name")}</span><input name="planned_vaccine_name" value="${vaccine}" list="task-products-039-vaccination"></label>${targetOptions.length?`<div class="wide checks taskVaccination039">${targetOptions.map(raw=>{const value=String(raw?.id??raw?.value??raw),label=String(raw?.name??raw?.label??this.l(value));return`<label><input type="checkbox" name="planned_vaccination_targets" value="${esc(value)}" ${selectedTargets.has(value)?"checked":""}><span>${esc(label)}</span></label>`}).join("")}</div>`:""}<label class="wide"><span>${this.t("custom_vaccination_target")}</span><input name="planned_custom_vaccination_target" value="${customTarget}"></label><label class="wide"><span>${this.t("antigen")}</span><input name="planned_antigen" value="${antigen}"></label>${this.taskDoseFields039("planned_vaccination",{doseName:"planned_vaccination_dose",unitName:"planned_vaccination_dose_unit",routeName:"planned_vaccination_route",required:false})}`);
 const treatmentFields=fieldset("treatment",`<legend>${this.t("settingTreatments039")}</legend><label class="wide"><span>${this.t("treatmentPlan011")}</span><select name="planned_treatment_plan_id" data-treatment-plan039 ${plans.length?"required":"disabled data-no-plans039"}><option value="">${this.t(plans.length?"selectTreatmentPlan039":"noTreatmentPlans039")}</option>${planOptions}</select></label><input type="hidden" name="treatment_plan_name" value="${esc(selectedPlanName)}"><label class="wide"><span>${this.t("plannedTreatment039")}</span><input name="planned_treatment_action" value="${esc(draft.planned_treatment_action||"")}"></label>`);
 const healthFields=fieldset("health_check",`<legend>${this.l("health_check")}</legend><label class="wide"><span>${this.t("check_focus")}</span><input name="planned_check_focus" value="${esc(draft.planned_check_focus||"")}"></label>`);
 const careFields=fieldset("care",`<legend>${this.l("care")}</legend><label class="wide"><span>${this.t("care_action")}</span><input name="planned_care_action" value="${esc(draft.planned_care_action||"")}"></label>`);
 const vetFields=fieldset("veterinary_visit",`<legend>${this.l("veterinary_visit")}</legend><label class="wide"><span>${this.t("visit_reason")}</span><input name="planned_visit_reason" value="${esc(draft.planned_visit_reason||"")}"></label><label class="wide"><span>${this.t("provider")}</span><input name="planned_provider" value="${esc(draft.planned_provider||"")}"></label>`);
 const lists=`<datalist id="task-products-039-medication">${this.taskProductOptions039("medication")}</datalist><datalist id="task-products-039-deworming">${this.taskProductOptions039("deworming")}</datalist><datalist id="task-products-039-supplement">${this.taskProductOptions039("supplement")}</datalist><datalist id="task-products-039-feed">${this.taskProductOptions039("feed")}</datalist><datalist id="task-products-039-vaccination">${this.taskProductOptions039("vaccination")}</datalist>`;
 return medicationFields+vaccinationFields+dewormingFields+supplementFields+feedFields+treatmentFields+healthFields+careFields+vetFields+lists
};
AH039.syncTaskElement039=function(form){
 if(!form)return;
 const kind=String(form.elements?.task_kind?.value||"reminder");
 for(const fieldset of form.querySelectorAll("[data-task-kind039]")){
  const active=String(fieldset.dataset.taskKind039)===kind;
  fieldset.hidden=!active;
  fieldset.setAttribute("aria-hidden",active?"false":"true");
  for(const field of fieldset.querySelectorAll("input,select,textarea,button"))field.disabled=!active||field.dataset.noPlans039!==undefined
 }
 const plan=form.querySelector("[data-treatment-plan039]"),name=form.elements?.treatment_plan_name;
 if(plan&&name){const option=plan.selectedOptions?.[0];name.value=plan.value?(option?.dataset?.name||option?.textContent?.trim()||""):""}
 form.noValidate=true
};
AH039.taskForm=function(){
 let html=AH039Base.taskForm.call(this),template=document.createElement("template");template.innerHTML=html;
 const form=template.content.querySelector('form[data-form="task"]');if(!form)return html;
 const kindSelect=form.elements?.task_kind;if(kindSelect){for(const value of["deworming","supplement","feed","treatment"]){if(!kindSelect.querySelector(`option[value="${value}"]`)){const option=document.createElement("option");option.value=value;option.textContent=this.l(value);kindSelect.append(option)}}}
 for(const node of[...form.querySelectorAll("[data-kind]")])if(node.closest("form")===form)node.remove();
 for(const node of[...form.querySelectorAll("[data-task-kind039],datalist[id^='task-products-039-']")])node.remove();
 const content=document.createElement("template");content.innerHTML=this.taskKindFieldsets039();
 const anchor=form.querySelector(".confirmationField010")||form.querySelector(".buttons")||form.lastElementChild;
 if(anchor)form.insertBefore(content.content,anchor);else form.append(content.content);
 this.syncTaskElement039(form);
 return template.innerHTML
};
AH039.syncTask=function(form){try{AH039Base.syncTask.call(this,form)}catch(_error){}this.syncTaskElement039(form)};
AH039.applyAITaskDraft=function(){const result=AH039Base.applyAITaskDraft.call(this);this.syncTaskElement039(this.shadowRoot.querySelector('form[data-form="task"]'));return result};
AH039.settingsGroups039=function(){return[
 {id:"master",icon:"mdi:paw",title:"settingsMaster027",hint:"settingsMasterHint039",items:[
  {id:"group-order",icon:"mdi:sort",title:"settingGroupOrder039",hint:"settingGroupOrderHint039"},
  {id:"week-start",icon:"mdi:calendar-week-begin",title:"settingWeekStart039",hint:"settingWeekStartHint039"},
  {id:"entry-types",icon:"mdi:format-list-bulleted-type",title:"settingEntryTypes039",hint:"settingEntryTypesHint039"},
  {id:"symptoms",icon:"mdi:alert-circle-outline",title:"settingSymptoms039",hint:"settingSymptomsHint039"},
  {id:"local-suggestions",icon:"mdi:lightbulb-on-outline",title:"settingLocalSuggestions039",hint:"settingLocalSuggestionsHint039"}
 ]},
 {id:"medications",icon:"mdi:pill",title:"settingsMedication027",hint:"settingsMedicationHint039",items:[
  {id:"product-databases",icon:"mdi:database-outline",title:"settingProductDatabases039",hint:"settingProductDatabasesHint039"},
  {id:"favourites",icon:"mdi:star-outline",title:"settingFavourites039",hint:"settingFavouritesHint039"},
  {id:"off-label",icon:"mdi:label-off-outline",title:"settingOffLabel039",hint:"settingOffLabelHint039"},
  {id:"medicines",icon:"mdi:pill-multiple",title:"settingMedicines039",hint:"settingMedicinesHint039"},
  {id:"treatments",icon:"mdi:medical-bag",title:"settingTreatments039",hint:"settingTreatmentsHint039"}
 ]},
 {id:"developer",icon:"mdi:code-braces",title:"settingsDeveloper039",hint:"settingsDeveloperHint039",items:[
  {id:"ai",icon:"mdi:creation-outline",title:"settingAi039",hint:"settingAiHint039"},
  {id:"administration",icon:"mdi:database-cog-outline",title:"settingAdministration039",hint:"settingAdministrationHint039"},
  {id:"danger",icon:"mdi:alert-outline",title:"settingDanger039",hint:"settingDangerHint039",danger:true}
 ]}
]};
AH039.settingsGroup039=function(id){return this.settingsGroups039().find(item=>item.id===String(id||""))||null};
AH039.settingsItem039=function(group,id){return group?.items?.find(item=>item.id===String(id||""))||null};
AH039.settingsHeading039=function(title,hint,back=""){
 return`<div class="settingsHead039">${back?`<button type="button" data-action="settings-back-039" data-level="${back}" title="${esc(this.t(back==="group"?"settingsBackGroup039":"settingsBackOverview039"))}"><ha-icon icon="mdi:arrow-left"></ha-icon></button>`:""}<div><h1>${this.t(title)}</h1>${hint?`<p>${this.t(hint)}</p>`:""}</div></div>`
};
AH039.settingsNav039=function(items,action){return`<section class="settingsGrid039">${items.map(item=>`<button type="button" class="settingsNav039 ${item.danger?"danger039":""}" data-action="${action}" data-id="${item.id}"><ha-icon icon="${item.icon}"></ha-icon><span><b>${this.t(item.title)}</b><small>${this.t(item.hint)}</small></span><ha-icon icon="mdi:chevron-right"></ha-icon></button>`).join("")}</section>`};
AH039.settingsLegacyTemplate039=function(){
 const current=this.settingsSection027;this.settingsSection027=null;let html="";
 try{html=typeof AH027Base!=="undefined"?AH027Base.settingsPage081.call(this):""}catch(_error){}
 this.settingsSection027=current;
 const template=document.createElement("template");template.innerHTML=html;return template
};
AH039.settingsLegacyCards039=function(){const template=this.settingsLegacyTemplate039();return[...template.content.querySelectorAll("section.card")].filter(node=>!node.parentElement?.closest?.("section.card"))};
AH039.settingsCardKind039=function(card){
 const cls=String(card.className||"").toLocaleLowerCase(),text=String(card.textContent||"").replace(/\s+/g," ").trim().toLocaleLowerCase(),actions=[...card.querySelectorAll("[data-action]")].map(node=>String(node.dataset.action||"")).join(" ");
 if(/groupordersettings017/.test(cls)||/(reihenfolge der tiergruppen|animal group order)/.test(text))return"group-order";
 if(/(wochenanfang|wochenbeginn|week start|first day of week)/.test(text))return"week-start";
 if(/mastermanager024/.test(cls)&&/(eintragsart|entry type)/.test(text))return"entry-types";
 if(/mastermanager024/.test(cls)&&/(symptom)/.test(text))return"symptoms";
 if(/(lokale vorschläge|local suggestions|history suggestions)/.test(text))return"local-suggestions";
 if(/(favorit|favourite|favorite)/.test(`${cls} ${text}`))return"favourites";
 if(/(behandlungsplan|treatment plan)/.test(text)||/treatmentsettings|managedtreatment/.test(cls))return"treatments";
 if(/(\bki\b|\bai\b|künstliche intelligenz|artificial intelligence|sprachmodell|language model|speech-to-text|stt)/.test(text))return"ai";
 if(/reset-activity-085/.test(actions)||/(verlaufs- und aufgabendaten|chronik.*aufgaben.*zurücksetzen|timeline and task data)/.test(text))return"danger-activity";
 if(/reset/.test(actions)&&/(integration|alle tiere|all animals|vollständig|complete)/.test(text))return"danger-integration";
 if(/danger|resetactivity|reset/.test(cls)&&/(zurücksetzen|reset)/.test(text))return"danger-other";
 if(/medicationsettings|managedmed|offlabel/.test(cls)||/(medikamente verwalten|manage medicines|off-label)/.test(text))return"medicines";
 return"administration"
};
AH039.settingsCards039=function(kind){return this.settingsLegacyCards039().filter(card=>this.settingsCardKind039(card)===kind).map(card=>card.outerHTML).join("")};
AH039.callSettingsMethod039=function(pattern){
 for(const name of Object.getOwnPropertyNames(AnimalHealthPanel.prototype)){
  if(!pattern.test(name)||["settingsPage081","settingsContent039"].includes(name))continue;
  try{const value=this[name]();if(typeof value==="string"&&value.includes("<"))return value}catch(_error){}
 }
 return""
};
AH039.offLabelSettings039=function(){
 let html="";try{html=typeof this.medicationSettings0817==="function"?this.medicationSettings0817():""}catch(_error){}
 const template=document.createElement("template");template.innerHTML=html;const form=template.content.querySelector(".offLabelPolicy012");
 if(!form)return this.settingsCards039("medicines")||`<section class="card"><p>${this.t("settingsNoContent039")}</p></section>`;
 return`<section class="card offLabelStandalone039"><h2>${this.t("settingOffLabel039")}</h2><p>${this.t("settingOffLabelHint039")}</p>${form.outerHTML}</section>`
};
AH039.medicineSettings039=function(){
 let html="";try{html=typeof this.medicationSettings0817==="function"?this.medicationSettings0817():""}catch(_error){}
 const template=document.createElement("template");template.innerHTML=html;template.content.querySelectorAll(".offLabelPolicy012").forEach(node=>node.remove());const heading=template.content.querySelector("h2");if(heading)heading.textContent=this.t("settingMedicines039");
 return template.innerHTML||this.settingsCards039("medicines")||`<section class="card"><p>${this.t("settingsNoContent039")}</p></section>`
};
AH039.treatmentSettings039=function(){return this.settingsCards039("treatments")||this.callSettingsMethod039(/^(?:treatment|managedTreatment).*(?:Settings|Manager)/i)||`<section class="card"><p>${this.t("settingsNoContent039")}</p></section>`};
AH039.simpleSettings039=function(kind,methodPattern){return this.settingsCards039(kind)||this.callSettingsMethod039(methodPattern)||`<section class="card"><p>${this.t("settingsNoContent039")}</p></section>`};
AH039.localSuggestionsSettings039=function(){const existing=this.settingsCards039("local-suggestions")||this.callSettingsMethod039(/(local|history).*Suggestion/i);if(existing)return existing;if(typeof this.productDatabases028!=="function")return`<section class="card"><p>${this.t("settingsNoContent039")}</p></section>`;const before=this.dbOpen028;this.dbOpen028="local_history_suggestions";let html="";try{html=this.productDatabases028()}finally{this.dbOpen028=before}return html};
AH039.dangerButton039=function(kind){
 const cards=this.settingsLegacyCards039(),wanted=kind==="activity"?["danger-activity"]:["danger-integration","danger-other"];
 for(const card of cards){if(!wanted.includes(this.settingsCardKind039(card)))continue;const buttons=[...card.querySelectorAll("button[data-action]")],button=kind==="activity"?buttons.find(node=>node.dataset.action==="reset-activity-085")||buttons[0]:buttons.find(node=>node.dataset.action!=="reset-activity-085")||buttons[0];if(button)return button.outerHTML}
 return""
};
AH039.dangerSettings039=function(){
 const integration=this.dangerButton039("integration"),activity=this.dangerButton039("activity"),card=(title,hint,button)=>`<section class="card dangerCard039"><h2>${this.t(title)}</h2><p>${this.t(hint)}</p><small>${this.t("destructiveConfirm039")}</small>${button?`<div class="dangerAction039">${button}</div>`:""}</section>`;
 const built=card("resetIntegration039","resetIntegrationHint039",integration)+card("resetActivity039","resetActivityHint039",activity);
 return integration||activity?built:this.settingsCards039("danger-integration")+this.settingsCards039("danger-activity")+this.settingsCards039("danger-other")||built
};
AH039.settingsContent039=function(group,item){
 const id=item?.id||"";
 if(id==="group-order")return this.simpleSettings039("group-order",/groupOrder.*Settings/i);
 if(id==="week-start")return this.simpleSettings039("week-start",/(week|calendar).*Settings/i);
 if(id==="entry-types")return this.simpleSettings039("entry-types",/entryType.*(?:Settings|Manager|Editor)/i);
 if(id==="symptoms")return this.simpleSettings039("symptoms",/symptom.*(?:Settings|Manager|Editor)/i);
 if(id==="local-suggestions")return this.localSuggestionsSettings039();
 if(id==="product-databases")return typeof this.productDatabases028==="function"?this.productDatabases028():`<section class="card"><p>${this.t("settingsNoContent039")}</p></section>`;
 if(id==="favourites")return this.simpleSettings039("favourites",/favou?rite.*(?:Settings|Manager)/i);
 if(id==="off-label")return this.offLabelSettings039();
 if(id==="medicines")return this.medicineSettings039();
 if(id==="treatments")return this.treatmentSettings039();
 if(id==="ai")return this.simpleSettings039("ai",/(ai|ki|speech|stt).*(?:Settings|Config)/i);
 if(id==="administration")return this.settingsLegacyCards039().filter(card=>this.settingsCardKind039(card)==="administration").map(card=>card.outerHTML).join("")||`<section class="card"><p>${this.t("settingsNoContent039")}</p></section>`;
 if(id==="danger")return this.dangerSettings039();
 return`<section class="card"><p>${this.t("settingsNoContent039")}</p></section>`
};
AH039.settingsPage081=function(){
 const group=this.settingsGroup039(this.settingsGroupId039),item=this.settingsItem039(group,this.settingsItemId039);
 if(!group)return`${this.settingsHeading039("settingsOverview027","")}${this.settingsNav039(this.settingsGroups039(),"settings-group-039")}`;
 if(!item)return`${this.settingsHeading039(group.title,group.hint,"overview")}${this.settingsNav039(group.items,"settings-item-039")}`;
 return`${this.settingsHeading039(item.title,item.hint,"group")}<div class="settingsContent039">${this.settingsContent039(group,item)}</div>`
};
AH039.taskInvalid039=function(form){
 this.syncTaskElement039(form);
 const kind=String(form.elements?.task_kind?.value||"");
 if(kind==="treatment"){const select=form.elements?.planned_treatment_plan_id;if(!select||!select.value)return{field:select||null,message:select?.disabled?this.t("noTreatmentPlans039"):`${this.t("taskRequiredField039")}: ${this.t("treatmentPlan011")}`}}
 if(form.checkValidity()){
  try{this.targetPayload026?.("task");return null}catch(error){return{message:error?.message||this.t("taskTargetMissing039")}}
 }
 const field=form.querySelector(":invalid:not([disabled])"),label=field?.closest("label")?.querySelector("span")?.textContent?.trim()||field?.name||this.t("taskRequiredField039");return{field,message:`${this.t("taskRequiredField039")}: ${label}`}
};
AH039.handleClick=function(event){
 const button=event.composedPath().find(node=>node?.dataset&&(node.dataset.action||node.dataset.view));if(!button)return AH039Base.handleClick.call(this,event);
 const action=String(button.dataset.action||"");
 if(button.dataset.view==="settings081"){this.settingsGroupId039=null;this.settingsItemId039=null;this.settingsSection027=null}
 if(action==="settings-group-039"){this.settingsGroupId039=button.dataset.id;this.settingsItemId039=null;this.settingsSection027=null;this.render();return}
 if(action==="settings-item-039"){this.settingsItemId039=button.dataset.id;this.settingsSection027=null;this.render();return}
 if(action==="settings-back-039"){if(button.dataset.level==="group")this.settingsItemId039=null;else{this.settingsGroupId039=null;this.settingsItemId039=null}this.settingsSection027=null;this.render();return}
 if(button.disabled)return;
 return AH039Base.handleClick.call(this,event)
};
AH039.handleChange=function(event){
 const input=event.composedPath()[0],form=input?.closest?.('form[data-form="task"]');
 if(form&&input?.name==="task_kind"){this.syncTask(form);return}
 if(form&&input?.dataset?.treatmentPlan039!==undefined){const hidden=form.elements.treatment_plan_name,option=input.selectedOptions?.[0];if(hidden)hidden.value=input.value?(option?.dataset?.name||option?.textContent?.trim()||""):"";return}
 return AH039Base.handleChange.call(this,event)
};
AH039.handleSubmit=async function(event){
 const form=event.composedPath().find(node=>node?.tagName==="FORM");
 if(form?.dataset.form!=="task")return AH039Base.handleSubmit.call(this,event);
 const invalid=this.taskInvalid039(form);
 if(invalid){event.preventDefault();this.notify(invalid.message,true);invalid.field?.reportValidity?.();invalid.field?.focus?.();return}
 try{return await AH039Base.handleSubmit.call(this,event)}catch(error){event.preventDefault();this.busy=false;this.notify(`${this.t("failed")}: ${error?.message||error}`,true);this.render()}
};
AH039.render=function(){
 AH039Base.render.call(this);
 this.syncTaskElement039(this.shadowRoot.querySelector('form[data-form="task"]'));
 this.shadowRoot.innerHTML+=`<style>
.taskKindFields039{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.taskKindFields039[hidden]{display:none!important}.taskKindFields039>.wide,.taskVaccination039{grid-column:1/-1}.taskKindFields039 label{display:flex;flex-direction:column;gap:3px}.settingsHead039{display:grid;grid-template-columns:auto minmax(0,1fr);align-items:start;gap:10px;margin-bottom:14px}.settingsHead039>button{display:grid;place-items:center;width:42px;height:42px;padding:0}.settingsHead039>div{grid-column:2}.settingsHead039:not(:has(>button))>div{grid-column:1/-1}.settingsHead039 h1,.settingsHead039 p{margin:0}.settingsHead039 p{margin-top:4px;color:var(--secondary-text-color)}.settingsGrid039{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.settingsNav039{display:grid!important;grid-template-columns:auto minmax(0,1fr) auto!important;align-items:center!important;gap:12px!important;min-height:86px!important;padding:14px!important;text-align:left!important;border-radius:12px!important}.settingsNav039>ha-icon:first-child{width:30px;height:30px}.settingsNav039>span{display:grid;gap:4px;min-width:0}.settingsNav039 b{font-size:1rem}.settingsNav039 small{color:var(--secondary-text-color);white-space:normal;line-height:1.3}.settingsNav039.danger039{border-color:var(--error-color,#db4437)}.settingsContent039{display:grid;gap:14px}.offLabelStandalone039>p,.dangerCard039>p{color:var(--secondary-text-color)}.dangerCard039{border-color:color-mix(in srgb,var(--error-color,#db4437) 45%,var(--divider-color))}.dangerCard039>small{display:block;color:var(--error-color,#db4437);font-weight:600}.dangerAction039{margin-top:12px}.dangerAction039 button{border-color:var(--error-color,#db4437);color:var(--error-color,#db4437)}
@media(max-width:700px){.taskKindFields039,.settingsGrid039{grid-template-columns:1fr}.taskKindFields039>.wide,.taskVaccination039{grid-column:1}.settingsNav039{min-height:78px}.settingsHead039 h1{font-size:1.35rem}}
</style>`
};
