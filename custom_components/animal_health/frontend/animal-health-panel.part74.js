const AH022=AnimalHealthPanel.prototype;
const AH022Base={
 eventDetail:AH022.eventDetail,
 treatmentBundle021:AH022.treatmentBundle021,
 medicationBatchBundle021:AH022.medicationBatchBundle021,
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
AH022.render=function(){AH022Base.render.call(this);this.shadowRoot.innerHTML+=`<style>
.eventActions0817 button,.eventActions021 button,.bundleActions021 button{display:inline-flex;align-items:center;justify-content:center;gap:6px}.eventActions0817 button ha-icon,.eventActions021 button ha-icon,.bundleActions021 button ha-icon{flex:0 0 auto}.actionLabel022{display:inline}.eventActions0817,.eventActions021,.bundleActions021{gap:6px}
@media(max-width:700px){.eventActions0817,.eventActions021,.bundleActions021{justify-content:flex-end!important;align-items:center!important;flex-wrap:wrap!important}.eventActions0817 button,.eventActions021 button,.bundleActions021 button{width:42px!important;height:42px!important;min-width:42px!important;max-width:42px!important;min-height:42px!important;padding:0!important;display:grid!important;place-items:center!important;flex:0 0 42px!important}.eventActions0817 button ha-icon,.eventActions021 button ha-icon,.bundleActions021 button ha-icon{width:22px!important;height:22px!important;margin:0!important}.actionLabel022{display:none!important}}
</style>`};
