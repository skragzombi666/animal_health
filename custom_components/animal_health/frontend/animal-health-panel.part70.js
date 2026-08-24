Object.assign(T,{
 quickCaptureCompactHint019:["Kompakte Schnellerfassung","Compact quick capture"],
 quickCaptureExpandedHint019:["Erweiterte Schnellerfassung","Expanded quick capture"]
});
const AH019=AnimalHealthPanel.prototype;
const AH019Base={render:AH019.render};
AH019.captureActions019=function(){return[
 ["record-weight","mdi:scale","recordWeight",true],
 ["record-symptom","mdi:alert-circle-outline","recordSymptom",false],
 ["record-product","mdi:pill","recordProduct",false],
 ["record-event","mdi:file-document-outline","recordGeneral",false],
 ["create-task","mdi:clipboard-outline","createTask",false],
 ["ai-assist","mdi:creation-outline","aiAssist",false]
]};
AH019.captureIcon019=function(icon){return`<span class="captureIcon019"><ha-icon icon="${icon}"></ha-icon><span class="capturePlus019" aria-hidden="true"><ha-icon icon="mdi:plus"></ha-icon></span></span>`};
AH019.quickCaptureCard091=function(){
 const compact=this.quickCaptureCompact091(),toggleLabel=this.t(compact?"quickCaptureExpand091":"quickCaptureCollapse091"),actions=this.captureActions019();
 const content=compact?`<div class="quickCaptureCompact091 quickCaptureCompact019" role="toolbar" aria-label="${esc(this.t("quickCaptureCompactHint019"))}">${actions.map(([action,icon,label,primary])=>`<button ${primary?'class="primary" ':""}data-action="${action}" title="${esc(this.t(label))}" aria-label="${esc(this.t(label))}">${this.captureIcon019(icon)}</button>`).join("")}</div>`:`<div class="quickCaptureGrid quickCaptureExpanded019" aria-label="${esc(this.t("quickCaptureExpandedHint019"))}">${actions.map(([action,icon,label])=>`<button data-action="${action}">${this.captureIcon019(icon)}<span class="quickCaptureLabel019">${this.t(label)}</span></button>`).join("")}</div>`;
 return`<section class="quickCaptureCard quickCaptureCard091 quickCaptureCard019 ${compact?"compact019":"expanded019"}"><div class="quickCaptureHead091"><h2>${this.t("quickCapture")}</h2><button class="quickCaptureToggle091" data-action="quick-capture-toggle-091" title="${esc(toggleLabel)}" aria-label="${esc(toggleLabel)}"><ha-icon icon="mdi:chevron-${compact?"down":"up"}"></ha-icon></button></div>${content}</section>`
};
AH019.decorateQuickCapture016=function(){
 for(const button of this.shadowRoot.querySelectorAll(".animalCaptureIcons090A7 [data-action]")){
  const definition=this.captureDefinitions016?.[button.dataset.action];if(!definition)continue;
  button.classList.remove("captureTile016");button.classList.add("animalCaptureButton019");
  button.innerHTML=this.captureIcon019(definition.icon);
 }
};
AH019.render=function(){
 AH019Base.render.call(this);
 this.shadowRoot.innerHTML+=`<style>
.quickCaptureCard019 .quickCaptureHead091{margin-bottom:12px!important}.quickCaptureCompact091.quickCaptureCompact019{display:grid!important;grid-template-columns:repeat(6,minmax(0,1fr))!important;justify-content:stretch!important;gap:6px!important;margin-top:0!important}.quickCaptureCompact019 button{position:relative!important;display:grid!important;place-items:center!important;width:100%!important;min-width:0!important;height:46px!important;min-height:46px!important;padding:0!important;border-radius:12px!important}.captureIcon019{position:relative;display:grid;place-items:center;width:30px;height:30px;flex:0 0 30px}.captureIcon019>ha-icon{width:25px!important;height:25px!important;margin:0!important}.capturePlus019{position:absolute;right:-5px;bottom:-3px;display:grid;place-items:center;width:16px;height:16px;border:2px solid var(--card-background-color);border-radius:50%;background:var(--primary-color);color:#fff;box-shadow:0 1px 2px #0005;pointer-events:none}.capturePlus019>ha-icon{width:11px!important;height:11px!important;margin:0!important}.quickCaptureExpanded019{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;justify-content:stretch!important;gap:9px!important}.quickCaptureExpanded019 button{display:flex!important;flex-direction:column!important;align-items:center!important;justify-content:center!important;gap:8px!important;min-width:0!important;min-height:78px!important;height:auto!important;padding:10px 8px!important;border-radius:12px!important;text-align:center!important}.quickCaptureExpanded019 .captureIcon019{width:34px;height:34px;flex-basis:34px}.quickCaptureExpanded019 .captureIcon019>ha-icon{width:28px!important;height:28px!important}.quickCaptureExpanded019 .capturePlus019{right:-5px;bottom:-2px;width:17px;height:17px}.quickCaptureLabel019{display:block!important;max-width:100%;font-size:.88rem!important;line-height:1.15!important;color:inherit!important;white-space:normal!important;text-align:center!important}.animalCaptureIcons090A7{display:grid!important;grid-template-columns:repeat(7,minmax(0,1fr))!important;gap:6px!important;align-items:stretch!important}.animalCaptureButton019{position:relative!important;display:grid!important;place-items:center!important;min-width:0!important;width:100%!important;height:46px!important;min-height:46px!important;padding:0!important;border-radius:12px!important}.animalCaptureButton019 .captureIcon019{width:28px;height:28px}.animalCaptureButton019 .captureIcon019>ha-icon{width:24px!important;height:24px!important}.animalCaptureButton019 .capturePlus019{right:-5px;bottom:-3px;width:15px;height:15px}.animalCaptureIcons090A7 .captureLabel016,.quickCaptureCompact019 .captureLabel016{display:none!important}@media(max-width:700px){.quickCaptureExpanded019{grid-template-columns:repeat(2,minmax(0,1fr))!important}.quickCaptureExpanded019 button{min-height:72px!important}.quickCaptureCompact091.quickCaptureCompact019{gap:4px!important}.quickCaptureCompact019 button{height:44px!important;min-height:44px!important;border-radius:10px!important}.captureIcon019{width:28px;height:28px;flex-basis:28px}.captureIcon019>ha-icon{width:23px!important;height:23px!important}.capturePlus019{right:-4px;bottom:-2px;width:15px;height:15px}.animalCaptureIcons090A7{gap:4px!important}.animalCaptureButton019{height:44px!important;min-height:44px!important;border-radius:10px!important}}@media(max-width:420px){.quickCaptureCard019{padding:12px!important}.quickCaptureCompact091.quickCaptureCompact019{gap:3px!important}.quickCaptureCompact019 button{height:42px!important;min-height:42px!important}.quickCaptureExpanded019{gap:7px!important}.quickCaptureExpanded019 button{min-height:68px!important;padding:8px 6px!important}.quickCaptureLabel019{font-size:.82rem!important}.animalCaptureIcons090A7{gap:3px!important}.animalCaptureButton019{height:42px!important;min-height:42px!important}}
</style>`
};
