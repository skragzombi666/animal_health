Object.assign(T,{
 saveNewSymptom022:["Als neues eigenes Symptom speichern","Save as new custom symptom"]
});
const AH022=AnimalHealthPanel.prototype;
const AH022Base={
 eventDetail:AH022.eventDetail,
 treatmentBundle021:AH022.treatmentBundle021,
 medicationBatchBundle021:AH022.medicationBatchBundle021,
 renderSymptomSuggestions015:AH022.renderSymptomSuggestions015,
 handleClick:AH022.handleClick,
 render:AH022.render
};
AH022.rewriteAction022=function(html,action,icon,label){
 const expression=new RegExp(`<button([^>]*data-action="${action}"[^>]*)>[\\s\\S]*?<\\/button>`,"g"),text=this.t(label);
 return String(html||"").replace(expression,(_match,attrs)=>{const cleaned=String(attrs||"").replace(/\s+title="[^"]*"/g,"").replace(/\s+aria-label="[^"]*"/g,"");return`<button${cleaned} title="${esc(text)}" aria-label="${esc(text)}"><ha-icon icon="${icon}"></ha-icon><span class="actionLabel022">${esc(text)}</span></button>`})
};
AH022.removeCopyActions022=function(html){return String(html||"").replace(/<button[^>]*data-action="(?:med-copy-0817|treatment-copy-021|batch-copy-021)"[^>]*>[\s\S]*?<\/button>/g,"")};
AH022.responsiveEventActions022=function(html){
 let result=this.removeCopyActions022(html);
 result=this.rewriteAction022(result,"med-edit-0817","mdi:pencil-outline","editEntry0817");
 result=this.rewriteAction022(result,"med-repeat-0817","mdi:repeat","repeatMedication0817");
 result=this.rewriteAction022(result,"delete-event-013","mdi:delete-outline","deleteEntry013");
 result=this.rewriteAction022(result,"treatment-repeat-021","mdi:repeat","treatmentRepeat021");
 result=this.rewriteAction022(result,"batch-repeat-021","mdi:repeat","medicationGroupRepeat021");
 return result
};
AH022.eventDetail=function(id){return this.responsiveEventActions022(AH022Base.eventDetail.call(this,id))};
AH022.treatmentBundle021=function(event){return this.responsiveEventActions022(AH022Base.treatmentBundle021.call(this,event))};
AH022.medicationBatchBundle021=function(event){return this.responsiveEventActions022(AH022Base.medicationBatchBundle021.call(this,event))};
AH022.symptomExactKnown022=function(value){const clean=String(value||"").trim();if(!clean)return false;const norm=this.norm083?this.norm083(clean):clean.toLocaleLowerCase();for(const item of this.symptomOptions015?.("")||[]){const valueNorm=this.norm083?this.norm083(item.value):String(item.value||"").toLocaleLowerCase(),labelNorm=this.norm083?this.norm083(item.label):String(item.label||"").toLocaleLowerCase();if(norm===valueNorm||norm===labelNorm)return true}for(const item of this.v0915?.symptoms||[]){const nameNorm=this.norm083?this.norm083(item.name):String(item.name||"").toLocaleLowerCase();if(norm===nameNorm)return true}return false};
AH022.renderSymptomSuggestions015=function(input,open=true){AH022Base.renderSymptomSuggestions015.call(this,input,open);const menu=input?.form?.querySelector?.("[data-symptom-suggest015]"),clean=String(input?.value||"").trim();if(!menu||clean.length<2||this.symptomExactKnown022(clean))return;const create=`<button type="button" class="symptomOption015 symptomCreate022" data-action="symptom-save-new-022" data-value="${esc(clean)}"><ha-icon icon="mdi:plus-circle-outline"></ha-icon><span><b>${esc(clean)}</b><small>${esc(this.t("saveNewSymptom022"))}</small></span></button>`;if(menu.querySelector?.(".comboEmpty083"))menu.innerHTML=create;else menu.insertAdjacentHTML("beforeend",create);menu.hidden=!open};
AH022.handleClick=async function(event){const button=event.composedPath().find(node=>node?.dataset?.action),action=button?.dataset?.action;if(["med-copy-0817","treatment-copy-021","batch-copy-021"].includes(action))return;if(action==="symptom-save-new-022"){const name=String(button.dataset.value||"").trim();if(!name)return;try{await this.ws(`${D}/v0915/symptom/save`,{name});await this.loadV0915();this.addSymptomChoice015(name);this.notify(this.t("symptomSaved015"))}catch(error){this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}return}return AH022Base.handleClick.call(this,event)};
AH022.render=function(){AH022Base.render.call(this);this.shadowRoot.innerHTML+=`<style>
.eventActions0817 button,.eventActions021 button,.bundleActions021 button{display:inline-flex;align-items:center;justify-content:center;gap:6px}.eventActions0817 button ha-icon,.eventActions021 button ha-icon,.bundleActions021 button ha-icon{flex:0 0 auto}.actionLabel022{display:inline}.eventActions0817,.eventActions021,.bundleActions021{gap:6px}.symptomCreate022{display:flex!important;align-items:center!important;justify-content:flex-start!important;gap:8px!important;border-top:1px solid var(--divider-color)!important}.symptomCreate022>span{display:flex;flex-direction:column;align-items:flex-start;gap:1px}.symptomCreate022 small{color:var(--secondary-text-color);font-size:.72rem}
:host([narrow]) .eventActions0817,:host([narrow]) .eventActions021,:host([narrow]) .bundleActions021{justify-content:flex-end!important;align-items:center!important;flex-wrap:wrap!important}:host([narrow]) .eventActions0817 button,:host([narrow]) .eventActions021 button,:host([narrow]) .bundleActions021 button{width:42px!important;height:42px!important;min-width:42px!important;max-width:42px!important;min-height:42px!important;padding:0!important;display:grid!important;place-items:center!important;flex:0 0 42px!important}:host([narrow]) .eventActions0817 button ha-icon,:host([narrow]) .eventActions021 button ha-icon,:host([narrow]) .bundleActions021 button ha-icon{width:22px!important;height:22px!important;margin:0!important}:host([narrow]) .actionLabel022{display:none!important}
@media(max-width:700px){.eventActions0817,.eventActions021,.bundleActions021{justify-content:flex-end!important;align-items:center!important;flex-wrap:wrap!important}.eventActions0817 button,.eventActions021 button,.bundleActions021 button{width:42px!important;height:42px!important;min-width:42px!important;max-width:42px!important;min-height:42px!important;padding:0!important;display:grid!important;place-items:center!important;flex:0 0 42px!important}.eventActions0817 button ha-icon,.eventActions021 button ha-icon,.bundleActions021 button ha-icon{width:22px!important;height:22px!important;margin:0!important}.actionLabel022{display:none!important}}
</style>`};
