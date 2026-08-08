const AH080AIFinal=AnimalHealthPanel.prototype;
const AH080AIFinalRender=AH080AIFinal.render;
AH080AIFinal.render=function(){const draft=this.aiTaskDraft;AH080AIFinalRender.call(this);if(draft&&this.modal?.type==="create-task"){this.aiTaskDraft=draft;this.applyAITaskDraft()}};
