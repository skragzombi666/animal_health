const AH090A7=AnimalHealthPanel.prototype;
const AH090A7Base={animalDetail:AH090A7.animalDetail};
AH090A7.animalCaptureActions090A7=function(animalId){
 const id=esc(animalId||"");
 const button=(action,icon,label,primary=false)=>`<button ${primary?'class="primary" ':""}data-action="${action}" data-id="${id}" title="${esc(label)}" aria-label="${esc(label)}"><ha-icon icon="${icon}"></ha-icon></button>`;
 return`<div class="quick animalCaptureIcons090A7" role="toolbar" aria-label="${esc(this.t("quickCapture"))}">${button("record-weight","mdi:scale",this.t("recordWeight"),true)}${button("record-symptom","mdi:alert-plus",this.t("recordSymptom"))}${button("record-product","mdi:pill",this.t("recordProduct"))}${button("create-task","mdi:clipboard-plus",this.t("createTask"))}${button("ai-assist","mdi:creation-outline",this.t("aiAssist"))}${button("record-event","mdi:note-plus-outline",this.t("recordGeneral"))}${button("attach-document","mdi:paperclip",this.t("attachDocument"))}</div>`
};
AH090A7.animalDetail=function(){
 let html=AH090A7Base.animalDetail.call(this),animal=this.detail?.animal;
 if(!animal)return html;
 html=html.replace(/<div class="quick quick082">[\s\S]*?<\/div>/,this.animalCaptureActions090A7(animal.id));
 html=html.replace(/<div class="quick quickMore082">[\s\S]*?<\/div>/g,"");
 return html+`<style>.animalCaptureIcons090A7{display:grid!important;grid-template-columns:repeat(7,minmax(0,1fr))!important;gap:6px!important;margin:12px 0!important;align-items:stretch!important}.animalCaptureIcons090A7 button{display:grid!important;place-items:center!important;min-width:0!important;width:100%!important;min-height:46px!important;height:46px!important;padding:0!important;border-radius:12px!important}.animalCaptureIcons090A7 button ha-icon{width:24px!important;height:24px!important;margin:0!important}@media(max-width:420px){.animalCaptureIcons090A7{gap:4px!important}.animalCaptureIcons090A7 button{min-height:44px!important;height:44px!important;border-radius:10px!important}.animalCaptureIcons090A7 button ha-icon{width:22px!important;height:22px!important}}</style>`
};
