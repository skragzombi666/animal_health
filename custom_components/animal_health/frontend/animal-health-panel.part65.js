Object.assign(T,{
 quickWeight016:["Gewicht","Weight"],
 quickSymptom016:["Symptom","Symptom"],
 quickMedication016:["Medikation","Medication"],
 quickRecord016:["Eintrag","Record"],
 quickTask016:["Aufgabe","Task"],
 quickAi016:["KI","AI"],
 quickAttachment016:["Anhang","Attachment"]
});
const AH016=AnimalHealthPanel.prototype;
const AH016Base={render:AH016.render};
AH016.captureDefinitions016={
 "record-weight":{icon:"mdi:scale",label:"quickWeight016"},
 "record-symptom":{icon:"mdi:alert-circle-outline",label:"quickSymptom016"},
 "record-product":{icon:"mdi:pill",label:"quickMedication016"},
 "record-event":{icon:"mdi:file-document-outline",label:"quickRecord016"},
 "create-task":{icon:"mdi:clipboard-outline",label:"quickTask016"},
 "ai-assist":{icon:"mdi:creation-outline",label:"quickAi016"},
 "attach-document":{icon:"mdi:paperclip",label:"quickAttachment016"}
};
AH016.decorateCaptureButton016=function(button){
 const definition=this.captureDefinitions016?.[button?.dataset?.action];if(!definition)return;
 button.classList.add("captureTile016");
 button.innerHTML=`<span class="captureIcon016"><ha-icon icon="${definition.icon}"></ha-icon><span class="capturePlus016"><ha-icon icon="mdi:plus"></ha-icon></span></span><span class="captureLabel016">${esc(this.t(definition.label))}</span>`
};
AH016.decorateQuickCapture016=function(){
 const selectors=[".quickCaptureCard091 [data-action]",".animalCaptureIcons090A7 [data-action]"];
 for(const button of this.shadowRoot.querySelectorAll(selectors.join(",")))this.decorateCaptureButton016(button)
};
AH016.render=function(){
 AH016Base.render.call(this);
 this.decorateQuickCapture016();
 this.shadowRoot.innerHTML+=`<style>
.quickCaptureCompact091,.quickCaptureGrid{display:grid!important;grid-template-columns:repeat(6,minmax(0,1fr))!important;gap:6px!important}.animalCaptureIcons090A7{display:grid!important;grid-template-columns:repeat(7,minmax(0,1fr))!important;gap:6px!important;align-items:stretch!important}.captureTile016{position:relative!important;overflow:visible!important;min-width:0!important;width:100%!important;height:auto!important;min-height:68px!important;padding:7px 3px 5px!important;display:grid!important;grid-template-rows:34px minmax(14px,auto)!important;place-items:center!important;align-content:center!important;gap:4px!important;border-radius:12px!important}.captureIcon016{position:relative;display:grid;place-items:center;width:32px;height:32px}.captureIcon016>ha-icon{width:26px!important;height:26px!important}.capturePlus016{position:absolute;right:-8px;bottom:-7px;display:grid;place-items:center;width:18px;height:18px;border:2px solid var(--card-background-color);border-radius:50%;background:var(--primary-color);color:var(--primary-background-color,#111);box-shadow:0 1px 3px #0006}.capturePlus016 ha-icon{width:12px!important;height:12px!important}.captureLabel016{display:block;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:.68rem;line-height:1.05;color:var(--secondary-text-color);text-align:center}.captureTile016.primary .captureLabel016{color:var(--text-primary-color,#fff)}.captureTile016.primary .capturePlus016{border-color:var(--card-background-color)}@media(max-width:520px){.quickCaptureCompact091,.quickCaptureGrid{gap:4px!important}.animalCaptureIcons090A7{gap:4px!important}.captureTile016{min-height:64px!important;padding:6px 2px 4px!important;border-radius:10px!important}.captureIcon016{width:30px;height:30px}.captureIcon016>ha-icon{width:24px!important;height:24px!important}.capturePlus016{right:-7px;bottom:-6px;width:17px;height:17px}.captureLabel016{font-size:.61rem}.animalCaptureIcons090A7 .captureLabel016{font-size:.57rem}}
</style>`
};
