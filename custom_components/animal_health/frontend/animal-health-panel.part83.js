Object.assign(T,{
 gabeType027:["Art der Gabe","Administration type"],
 gabeMedication027:["Medikament","Medication"],
 gabeVaccination027:["Impfung","Vaccination"],
 gabeDeworming027:["Entwurmung","Deworming"],
 gabeSupplement027:["Ergänzung","Supplement"],
 gabeFeed027:["Futter","Feed"],
 doseBasis027:["Dosierungsbezug","Dose basis"],
 dosePerAnimal027:["pro Tier","per animal"],
 dosePerKg027:["pro kg KG","per kg body weight"],
 dosePerWater027:["pro Liter Trinkwasser","per litre drinking water"],
 dosePerFeed027:["pro kg Futter","per kg feed"],
 feedStatus027:["Dokumentation","Documentation"],
 feedOffered027:["angeboten","offered"],
 feedConsumed027:["aufgenommen","consumed"],
 fromTask027:["Aus Aufgabe","From task"],
 origin027:["Ursprung","Origin"],
 taskOrigin027:["Aufgabe","Task"],
 scheduled027:["Geplant","Scheduled"],
 completed027:["Erledigt","Completed"],
 taskId027:["Aufgaben-ID","Task ID"],
 groupOverview027:["Übersicht","Overview"],
 defaultSelected027:["Standardmässig ausgewählt","Selected by default"],
 settingsOverview027:["Einstellungen","Settings"],
 settingsGeneral027:["Allgemein","General"],
 settingsGeneralHint027:["Allgemeines Verhalten und weitere globale Optionen","General behaviour and remaining global options"],
 settingsMaster027:["Tiere & Stammdaten","Animals & master data"],
 settingsMasterHint027:["Tiergruppen, Reihenfolge und fachliche Stammdaten","Animal groups, ordering and master data"],
 settingsMedication027:["Medikamente & Behandlungen","Medicines & treatments"],
 settingsMedicationHint027:["Medikamente, Impfstoffe, Ergänzungen, Futter und Behandlungspläne","Medicines, vaccines, supplements, feed and treatment plans"],
 settingsTasks027:["Aufgaben & Planung","Tasks & planning"],
 settingsTasksHint027:["Aufgaben, Wiederholungen und Planung","Tasks, recurrence and planning"],
 settingsAi027:["KI & Erfassung","AI & capture"],
 settingsAiHint027:["KI-gestützte und kontextbezogene Erfassung","AI-assisted and contextual capture"],
 settingsData027:["Dokumente & Daten","Documents & data"],
 settingsDataHint027:["Anhänge, Export und Datensicherung","Attachments, export and backup"],
 settingsSystem027:["System & Integration","System & integration"],
 settingsSystemHint027:["Home Assistant, Diagnose und technische Optionen","Home Assistant, diagnostics and technical options"],
 settingsDanger027:["Test & Gefahrenbereich","Test & danger zone"],
 settingsDangerHint027:["Testfunktionen und destruktive Aktionen","Test functions and destructive actions"],
 settingsEmpty027:["Für diesen Bereich sind derzeit keine separaten Optionen vorhanden.","There are currently no separate options in this section."],
 backSettings027:["Zur Einstellungsübersicht","Back to settings overview"],
 vaccineDatabase027:["Impfstoffe","Vaccines"],
 supplementDatabase027:["Nahrungsergänzungen","Supplements"],
 feedDatabase027:["Futtermittel","Feed products"],
 productDatabaseHint027:["Gleiche Auswahl- und Verwaltungslogik wie bei Medikamenten; vorgegebene Einträge bleiben als Quelle unverändert und lokale Anpassungen sind rücksetzbar.","Uses the same selection and management logic as medicines; supplied source records remain unchanged and local overrides can be reset."],
 productTargets027:["Ziele / Antigene","Targets / antigens"],
 productSpecies027:["Tierarten","Species"],
 productAdd027:["Eintrag hinzufügen","Add entry"],
 productHide027:["Ausblenden","Hide"],
 productShow027:["Einblenden","Show"],
 official027:["Vorgegeben","Provided"],
 manual027:["Manuell","Manual"],
 taskProduct027:["Produkt","Product"]
});
Object.assign(L,{
 deworming:["Entwurmung","Deworming"],
 supplement:["Ergänzung","Supplement"],
 feed:["Futter","Feed"],
 vaccination:["Impfung","Vaccination"],
 per_animal:["pro Tier","per animal"],
 per_kg:["pro kg KG","per kg body weight"],
 per_l_water:["pro Liter Trinkwasser","per litre drinking water"],
 per_kg_feed:["pro kg Futter","per kg feed"],
 offered:["angeboten","offered"],
 consumed:["aufgenommen","consumed"]
});
Object.assign(I,{
 deworming:"mdi:bug-outline",
 supplement:"mdi:leaf-circle-outline",
 feed:"mdi:food-apple-outline"
});
const AH027=AnimalHealthPanel.prototype;
const AH027Base={
 load:AH027.load,
 targetSelector026:AH027.targetSelector026,
 animalDetail:AH027.animalDetail,
 taskForm:AH027.taskForm,
 syncTask:AH027.syncTask,
 execForm:AH027.execForm,
 medicationBatchForm0817:AH027.medicationBatchForm0817,
 planComponentRow012:AH027.planComponentRow012,
 openTreatmentPlanExecution012:AH027.openTreatmentPlanExecution012,
 settingsPage081:AH027.settingsPage081,
 eventCompact0817:AH027.eventCompact0817,
 eventDetail:AH027.eventDetail,
 handleInput:AH027.handleInput,
 handleChange:AH027.handleChange,
 handleClick:AH027.handleClick,
 handleSubmit:AH027.handleSubmit,
 render:AH027.render
};

AH027.loadV0927=async function(){try{this.v0927=await this.ws(`${D}/v0927/state`)}catch(_error){this.v0927={gabe_types:["medication","vaccination","deworming","supplement","feed"],products:[],vaccines:[],supplements:[],feeds:[]}}};
AH027.load=async function(){await AH027Base.load.call(this);if(!this.h||!this.d)return;await this.loadV0927();this.render()};

AH027.gabeKinds027=function(){return["medication","vaccination","deworming","supplement","feed"]};
AH027.gabeKindLabel027=function(kind){return this.t({medication:"gabeMedication027",vaccination:"gabeVaccination027",deworming:"gabeDeworming027",supplement:"gabeSupplement027",feed:"gabeFeed027"}[kind]||"gabeMedication027")};
AH027.gabeKindIcon027=function(kind){return{medication:"mdi:pill",vaccination:"mdi:needle",deworming:"mdi:bug-outline",supplement:"mdi:leaf-circle-outline",feed:"mdi:food-apple-outline"}[kind]||"mdi:pill"};
AH027.gabeProducts027=function(kind){
 const active=(items)=>items.filter(item=>!item.is_hidden&&!item.is_archived);
 if(kind==="vaccination")return active(this.v0927?.vaccines||[]);
 if(kind==="supplement")return active([...(this.v0927?.supplements||[]),...(this.v0913?.medications||[]).filter(item=>item.product_category==="supplement")]);
 if(kind==="feed")return active(this.v0927?.feeds||[]);
 const products=active([...(this.v0924?.catalog_products||[]),...(this.v0913?.medications||[])]),keywords=/fluben|fenbend|flubend|milbem|praziquant|pyrantel|moxidect|ivermect|anthelm|worm|wurm/i;
 return kind==="deworming"?[...products].sort((a,b)=>Number(!keywords.test(a.name||""))-Number(!keywords.test(b.name||""))||String(a.name||"").localeCompare(String(b.name||""))):products
};
AH027.gabeProductByName027=function(kind,name){const needle=String(name||"").trim().toLocaleLowerCase();return this.gabeProducts027(kind).find(item=>String(item.name||"").trim().toLocaleLowerCase()===needle)||null};
AH027.gabeOptions027=function(kind){return this.gabeProducts027(kind).map(item=>`<option value="${esc(item.name||"")}">${esc([item.active_ingredient,item.concentration].filter(Boolean).join(" · "))}</option>`).join("")};

AH027.targetSelector026=function(key,options={}){let html=AH027Base.targetSelector026.call(this,key,options);return html.replace(/(<div class="targetPanel026" data-target-panel026="animals"[^>]*>)(<details)/,`$1<span class="targetFieldLabel027">${this.t("targetAnimal026")}</span>$2`)};

AH027.animalDetail=function(){let html=AH027Base.animalDetail.call(this);const groupId=this.detail?.animal?.group_id;if(!groupId)return html;const tile=`<button class="animalTile groupOverviewTile027" data-action="group-filter" data-id="${esc(groupId)}" data-view="animals" title="${esc(this.t("groupOverview027"))}"><ha-icon icon="mdi:account-group-outline"></ha-icon><span>${this.t("groupOverview027")}</span></button>`;return html.replace('<div class="animalTiles">',`<div class="animalTiles">${tile}`)};
