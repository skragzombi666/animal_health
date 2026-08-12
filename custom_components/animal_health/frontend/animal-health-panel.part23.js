Object.assign(T,{
 localSuggestions084:["Lokale Vorschläge","Local suggestions"],
 localSuggestionsHint084:["Häufig bzw. zuletzt verwendete Medikamente, Impfstoffe, Behandler und geeignete Freitextwerte aus der lokalen Animal-Health-Historie werden bei der Eingabe priorisiert. Freie Eingaben bleiben möglich.","Frequently or recently used medications, vaccines, providers and suitable free-text values from local Animal Health history are prioritized during data entry. Free input remains available."],
 diagnostics084:["Datenbankdiagnose","Database diagnostics"],
 diagnosticsHint084:["Prüft die lokale Animal-Health-Datenbank und Anhänge ohne Änderungen an den Daten.","Checks the local Animal Health database and attachments without changing data."],
 runDiagnostics084:["Diagnose ausführen","Run diagnostics"],
 diagnosticsOk084:["Keine Inkonsistenzen erkannt","No inconsistencies detected"],
 diagnosticsProblems084:["Auffälligkeiten erkannt","Problems detected"],
 dbSchemaVersion084:["Datenbankschema","Database schema"],
 missingTables084:["Fehlende Tabellen","Missing tables"],
 missingIndexes084:["Fehlende Indizes","Missing indexes"],
 foreignKeys084:["Fremdschlüsselverletzungen","Foreign-key violations"],
 missingAttachments084:["Fehlende Anhangsdateien","Missing attachment files"],
 orphanedAttachments084:["Nicht referenzierte Dateien","Unreferenced files"],
 updates084:["Updates","Updates"],
 updatesHint084:["Wird Animal Health über HACS verwaltet, erscheinen neue Versionen als normale Home-Assistant-Updates. Ein eigener Selbst-Updater überschreibt keine Integrationsdateien im laufenden Betrieb.","When Animal Health is managed by HACS, new versions appear as normal Home Assistant updates. No self-updater overwrites integration files while Home Assistant is running."],
 openUpdates084:["Home-Assistant-Updates öffnen","Open Home Assistant updates"]
});
const AH084=AnimalHealthPanel.prototype;
const AH084Base={
 load:AH084.load,
 settingsPage081:AH084.settingsPage081,
 comboCandidates083:AH084.comboCandidates083,
 productLists:AH084.productLists,
 taskForm:AH084.taskForm,
 execForm:AH084.execForm,
 handleClick:AH084.handleClick,
 render:AH084.render
};
AH084.loadV084=async function(){
 try{const result=await this.ws(`${D}/v084/history_suggestions`);this.v084={suggestions:result.suggestions||{}}}
 catch(_error){this.v084={suggestions:{}}}
};
AH084.load=async function(){await AH084Base.load.call(this);if(!this.h||!this.d)return;await this.loadV084();this.render()};
AH084.historyValues084=function(kind,species=""){
 const wanted=species?this.speciesId(species):"";
 return(this.v084?.suggestions?.[kind]||[]).filter(item=>!wanted||!item.species_id||this.speciesId(item.species_id)===wanted)
};
AH084.uniqueValues084=function(values){const seen=new Set;return values.filter(value=>{const text=String(value||"").trim(),key=text.toLocaleLowerCase();if(!text||seen.has(key))return false;seen.add(key);return true})};
AH084.comboCandidates083=function(kind,form){
 const base=AH084Base.comboCandidates083.call(this,kind,form);if(kind!=="medication")return base;
 const species=this.medicationContextSpecies083(form),history=this.historyValues084("medication_name",species).map(item=>({value:item.value,history:true,custom:false,offlabel:false,unknown:false})),seen=new Set;
 return[...history,...base].filter(item=>{const key=this.norm083(item.value);if(!key||seen.has(key))return false;seen.add(key);return true})
};
AH084.productLists=function(){
 const medications=this.uniqueValues084([...this.historyValues084("medication_name").map(item=>item.value),...(this.c?.medicine_names||[])]),vaccines=this.uniqueValues084([...this.historyValues084("vaccine_name").map(item=>item.value),...(this.c?.vaccine_names||[])]),providers=this.uniqueValues084(this.historyValues084("provider").map(item=>item.value)),care=this.uniqueValues084(this.historyValues084("care_action").map(item=>item.value)),reasons=this.uniqueValues084(this.historyValues084("visit_reason").map(item=>item.value)),focus=this.uniqueValues084(this.historyValues084("check_focus").map(item=>item.value)),antigens=this.uniqueValues084(this.historyValues084("antigen").map(item=>item.value));
 const list=(id,values)=>`<datalist id="${id}">${values.map(value=>`<option value="${esc(value)}">`).join("")}</datalist>`;
 return`${list("meds",medications)}${list("vaccines",vaccines)}${list("providers084",providers)}${list("care084",care)}${list("visitReasons084",reasons)}${list("checkFocus084",focus)}${list("antigens084",antigens)}`
};
AH084.taskForm=function(){
 let html=AH084Base.taskForm.call(this);html=html.replace('name="planned_provider"','name="planned_provider" list="providers084"').replace('name="planned_care_action"','name="planned_care_action" list="care084"').replace('name="planned_visit_reason"','name="planned_visit_reason" list="visitReasons084"').replace('name="planned_check_focus"','name="planned_check_focus" list="checkFocus084"').replace('name="planned_antigen"','name="planned_antigen" list="antigens084"');return html
};
AH084.execForm=function(item){
 let html=AH084Base.execForm.call(this,item);html=html.replace('name="provider"','name="provider" list="providers084"').replace('name="care_action"','name="care_action" list="care084"').replace('name="visit_reason"','name="visit_reason" list="visitReasons084"').replace('name="antigen"','name="antigen" list="antigens084"');return html
};
AH084.diagnosticList084=function(title,items,format=value=>String(value)){if(!items?.length)return"";return`<details><summary>${title}: ${items.length}</summary><ul>${items.slice(0,50).map(item=>`<li>${esc(format(item))}</li>`).join("")}</ul></details>`};
AH084.diagnosticReport084=function(){
 const report=this.v084Diagnostics;if(!report)return"";const status=report.ok?`<p class="diagnosticStatus084 ok"><ha-icon icon="mdi:check-circle-outline"></ha-icon>${this.t("diagnosticsOk084")}</p>`:`<p class="diagnosticStatus084 problem"><ha-icon icon="mdi:alert-circle-outline"></ha-icon>${this.t("diagnosticsProblems084")}</p>`;
 return`<div class="diagnosticReport084">${status}<p>${this.t("dbSchemaVersion084")}: <b>${esc(report.user_version)}</b> · ${esc(report.table_count)} Tabellen · ${esc(report.index_count)} Indizes</p>${this.diagnosticList084(this.t("missingTables084"),report.missing_tables)}${this.diagnosticList084(this.t("missingIndexes084"),report.missing_indexes)}${this.diagnosticList084(this.t("foreignKeys084"),report.foreign_key_violations,item=>`${item.table} → ${item.parent} (row ${item.rowid})`)}${this.diagnosticList084(this.t("missingAttachments084"),report.missing_attachment_files,item=>`${item.filename} (${item.attachment_id})`)}${this.diagnosticList084(this.t("orphanedAttachments084"),report.orphaned_attachment_files)}</div>`
};
AH084.settingsPage081=function(){
 const html=AH084Base.settingsPage081.call(this),suggestions=`<section class="card"><h2>${this.t("localSuggestions084")}</h2><p>${this.t("localSuggestionsHint084")}</p></section>`,updates=`<section class="card"><h2>${this.t("updates084")}</h2><p>${this.t("updatesHint084")}</p><button data-action="open-updates-084"><ha-icon icon="mdi:update"></ha-icon>${this.t("openUpdates084")}</button></section>`,diagnostics=this.h?.user?.is_admin?`<section class="card"><h2>${this.t("diagnostics084")}</h2><p>${this.t("diagnosticsHint084")}</p><button data-action="diagnostics-v084"><ha-icon icon="mdi:database-search-outline"></ha-icon>${this.t("runDiagnostics084")}</button>${this.diagnosticReport084()}</section>`:"";return`${html}${suggestions}${updates}${diagnostics}`
};
AH084.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset?.action),action=button?.dataset?.action;
 if(action==="open-updates-084"){history.pushState(null,"","/config/updates");window.dispatchEvent(new Event("location-changed"));return}
 if(action==="diagnostics-v084"){try{button.disabled=true;this.v084Diagnostics=await this.ws(`${D}/v084/diagnostics`);this.render()}catch(error){button.disabled=false;this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}return}
 return AH084Base.handleClick.call(this,event)
};
AH084.render=function(){AH084Base.render.call(this);this.shadowRoot.innerHTML+=`<style>.diagnosticReport084{margin-top:14px}.diagnosticStatus084{display:flex;align-items:center;gap:8px;font-weight:600}.diagnosticStatus084.ok{color:var(--success-color,#2e7d32)}.diagnosticStatus084.problem{color:var(--error-color,#c62828)}.diagnosticReport084 details{margin-top:8px}.diagnosticReport084 ul{margin:6px 0;padding-left:22px}</style>`};
