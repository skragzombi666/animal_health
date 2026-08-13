const AH0812=AnimalHealthPanel.prototype;
const AH0812Base={render:AH0812.render};
AH0812.prepareBatchAssociations0812=function(){
 const entries=this.aiBatch083;
 if(!Array.isArray(entries)||entries.length<2||this.aiBatchAssociationSource0812===entries)return;
 this.aiBatchAssociationSource0812=entries;
 const contextIds=new Set([this.aiContextReturn086?.animalId,this.weightAIReturn?.animal_id].map(value=>String(value||"").trim()).filter(Boolean));
 if(!contextIds.size)return;
 for(const entry of entries){
  if(entry?.capture_mode!=="weight")continue;
  if(String(entry?.matched_animal_id||"").trim())continue;
  const current=String(entry?.animal_id||"").trim();
  if(contextIds.has(current))entry.animal_id=""
 }
};
AH0812.render=function(){
 this.prepareBatchAssociations0812();
 AH0812Base.render.call(this);
 this.shadowRoot.innerHTML+=`<style>.aiBatchSummary086{display:flex!important;flex-direction:column!important;align-items:stretch!important;gap:7px!important;overflow-y:auto!important;overflow-x:hidden!important}.aiBatchCard086,.aiBatchCard086.expanded{display:block!important;position:relative!important;flex:0 0 auto!important;height:auto!important;min-height:0!important;overflow:hidden!important}.aiBatchCard086.expanded>.aiBatchDetails086{display:block!important;position:static!important;inset:auto!important;transform:none!important;width:auto!important;height:auto!important;max-height:none!important;visibility:visible!important;opacity:1!important;overflow:visible!important}.aiBatchCard086.expanded>.aiBatchRow086{position:relative!important}.aiBatchCard086.expanded>.aiBatchDetails086>.formgrid083,.aiBatchCard086.expanded>.aiBatchDetails086>.aiBatchFields086{position:static!important;height:auto!important;max-height:none!important;visibility:visible!important}</style>`
};
