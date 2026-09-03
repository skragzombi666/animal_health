const AH038=AnimalHealthPanel.prototype;
const AH038Base={
 targetSelector026:AH038.targetSelector026,
 handleClick:AH038.handleClick
};
AH038.ensureTargetState026=function(key,defaultScope="animals",initialAnimalId=""){
 const name=String(key||""),fallback=["general","group","animals"].includes(String(defaultScope||""))?String(defaultScope):"animals",initial=String(initialAnimalId||"");
 this._targetStates026=this._targetStates026||{};
 let state=this._targetStates026[name];
 if(!state||typeof state!=="object"){
  state={scope:fallback,groupId:"",animalIds:[],open:false};
  this._targetStates026[name]=state
 }
 state.scope=["general","group","animals"].includes(String(state.scope||""))?String(state.scope):fallback;
 state.groupId=String(state.groupId||"");
 state.animalIds=[...new Set((Array.isArray(state.animalIds)?state.animalIds:[]).map(String).filter(Boolean))];
 state.open=Boolean(state.open);
 if(initial&&state.scope==="animals"&&!state.animalIds.length)state.animalIds=[initial];
 return state
};
AH038.targetSelector026=function(key,options={}){
 const initialAnimalId=String(options.initialAnimalId||options.animalId||""),defaultScope=String(options.defaultScope||"animals"),allowGeneral=options.allowGeneral!==undefined?Boolean(options.allowGeneral):options.includeGeneral!==undefined?Boolean(options.includeGeneral):String(key)==="task";
 this.ensureTargetState026(key,defaultScope,initialAnimalId);
 return AH038Base.targetSelector026.call(this,key,{...options,defaultScope,allowGeneral})
};
AH038.openPrimaryCapture038=function(action,animalId=""){
 const target=String(animalId||this.detail?.animal?.id||"");
 if(action==="record-product"){
  this.clearTargetState026?.("medication");
  this.openMedicationBatch0817({animalId:target});
  return true
 }
 if(action==="record-symptom"){
  this.clearTargetState026?.("symptom");
  this.open("record-symptom",{animalId:target});
  return true
 }
 if(action==="create-task"){
  this.taskCopyMeta036=null;
  this.aiTaskDraft=null;
  this.clearTargetState026?.("task");
  this.open("create-task",{animalId:target});
  return true
 }
 return false
};
AH038.handleClick=function(event){
 const button=event.composedPath().find(node=>node?.dataset&&(node.dataset.action||node.dataset.view));
 if(!button)return AH038Base.handleClick.call(this,event);
 const action=String(button.dataset.action||"");
 if(button.disabled)return;
 if(action==="record-product"||action==="record-symptom"||action==="create-task"){
  this.openPrimaryCapture038(action,button.dataset.id);
  return
 }
 return AH038Base.handleClick.call(this,event)
};
