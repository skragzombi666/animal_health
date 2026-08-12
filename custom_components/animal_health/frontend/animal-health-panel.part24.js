Object.assign(T,{
 resetActivity085:["Verlaufs- und Aufgabendaten zurücksetzen","Reset activity and task data"],
 resetActivityHint085:["Löscht Chronik, Gewichte, Symptome, Medikamentengaben, Aufgaben, Serien und zugehörige Anhänge. Tiere, Tiergruppen, Zuordnungen, Tags, Stammdaten und Tierbilder bleiben erhalten.","Deletes timeline records, weights, symptoms, medication administrations, tasks, recurring series and related attachments. Animals, groups, assignments, tags, master data and animal profile images are kept."],
 resetActivityConfirm085:["Wirklich alle Verlaufs- und Aufgabendaten löschen? Tiere, Tiergruppen und Stammdaten bleiben erhalten. Diese Aktion kann nicht rückgängig gemacht werden.","Really delete all activity and task data? Animals, groups and master data will be kept. This cannot be undone."],
 resetActivityDone085:["Verlaufs- und Aufgabendaten wurden zurückgesetzt.","Activity and task data were reset."],
 diagnosticErrors085:["Diagnosefehler","Diagnostic errors"]
});
const AH085=AnimalHealthPanel.prototype;
const AH085Base={
 body:AH085.body,
 settingsPage081:AH085.settingsPage081,
 diagnosticReport084:AH085.diagnosticReport084,
 handleClick:AH085.handleClick,
 render:AH085.render
};
AH085.errorText085=function(error){return String(error?.message||error?.code||error||"Unknown error")};
AH085.body=function(){
 let html=AH085Base.body.call(this);
 const brand=`<b class="brand brandOriginal085"><img src="/api/${D}/frontend/animal-health-brand.png?v=${V}" alt="Animal Health"><span>Animal Health</span></b>`;
 html=html.replace(/<b class="brand"><ha-icon icon="mdi:paw"><\/ha-icon><span>Animal Health<\/span><\/b>/,brand);
 html=html.replace(/<b><ha-icon icon="mdi:paw"><\/ha-icon> Animal Health<\/b>/,brand);
 return html
};
AH085.diagnosticReport084=function(){
 const report=this.v084Diagnostics;if(!report)return"";
 let html=AH085Base.diagnosticReport084.call(this);
 if(report.errors?.length)html+=this.diagnosticList084(this.t("diagnosticErrors085"),report.errors);
 return html
};
AH085.settingsPage081=function(){
 const html=AH085Base.settingsPage081.call(this);
 if(!this.h?.user?.is_admin)return html;
 const reset=`<section class="card resetActivity085"><h2>${this.t("resetActivity085")}</h2><p>${this.t("resetActivityHint085")}</p><button class="dangerSecondary085" data-action="reset-activity-085"><ha-icon icon="mdi:history"></ha-icon>${this.t("resetActivity085")}</button></section>`;
 return`${html}${reset}`
};
AH085.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset?.action),action=button?.dataset?.action;
 if(action==="diagnostics-v084"){
  try{button.disabled=true;this.v084Diagnostics=await this.ws(`${D}/v084/diagnostics`);this.render()}
  catch(error){button.disabled=false;this.notify(`${this.t("failed")}: ${this.errorText085(error)}`,true)}
  return
 }
 if(action==="reset-activity-085"){
  if(!window.confirm(this.t("resetActivityConfirm085")))return;
  try{button.disabled=true;await this.ws(`${D}/v084/reset_activity`,{confirm:"RESET_ACTIVITY"});this.detail=null;this.v084Diagnostics=null;await this.load();this.notify(this.t("resetActivityDone085"))}
  catch(error){button.disabled=false;this.notify(`${this.t("failed")}: ${this.errorText085(error)}`,true)}
  return
 }
 return AH085Base.handleClick.call(this,event)
};
AH085.render=function(){
 AH085Base.render.call(this);
 this.shadowRoot.innerHTML+=`<style>.brandOriginal085 img{width:34px;height:34px;border-radius:50%;object-fit:cover;display:block}.dangerSecondary085{border-color:var(--error-color,#c62828);color:var(--error-color,#c62828)}.resetActivity085{border:1px solid color-mix(in srgb,var(--error-color,#c62828) 45%,var(--divider-color))}@media(max-width:850px){.brandOriginal085 img{width:38px;height:38px}}</style>`
};
