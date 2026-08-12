const AH0810=AnimalHealthPanel.prototype;
const AH0810Base={render:AH0810.render};
AH0810.render=function(){
 AH0810Base.render.call(this);
 this.shadowRoot.innerHTML+=`<style>.aiBatchCard086.expanded>.aiBatchDetails086{display:block!important;position:static!important;visibility:visible!important;opacity:1!important;height:auto!important;max-height:none!important;overflow:visible!important}.aiBatchCard086.expanded>.aiBatchDetails086>.formgrid083,.aiBatchCard086.expanded>.aiBatchDetails086>.aiBatchFields086{display:grid!important;visibility:visible!important;height:auto!important;max-height:none!important;overflow:visible!important}.aiBatchCard086.expanded{overflow:visible!important}.aiBatchSummary086{align-items:start}</style>`
};
