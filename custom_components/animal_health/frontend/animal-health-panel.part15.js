const AH080AIFinal=AnimalHealthPanel.prototype;
const AH080AIFinalRender=AH080AIFinal.render;
const AH080AIFinalUploadForm=AH080AIFinal.aiUploadForm;
AH080AIFinal.aiUploadForm=function(){return AH080AIFinalUploadForm.call(this).replace('data-ai-file-selection','data-ai-file-selection data-file-selection')};
AH080AIFinal.render=function(){const draft=this.aiTaskDraft;AH080AIFinalRender.call(this);if(draft&&this.modal?.type==="create-task"){this.aiTaskDraft=draft;this.applyAITaskDraft()}};
