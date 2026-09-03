const AH037=AnimalHealthPanel.prototype;
const AH037Base={
 attachmentList:AH037.attachmentList,
 attachmentStrip026:AH037.attachmentStrip026,
 refreshAttachmentUrls024:AH037.refreshAttachmentUrls024,
 render:AH037.render
};
for(const name of[
 "cloneNavValue033","navSnapshot033","navSignature033","navMarker033","currentNavMarker033",
 "writeNavEntry033","restoreNavSnapshot033","bindInternalHistory033","backwardControl033",
 "navMarker034","currentNavMarker034","writeNavEntry034","requestBack034",
 "restoreNavSnapshot034","bindInternalHistory034"
])delete AH037[name];
AH037.removeInternalHistory037=function(){
 if(this._ahNavPopHandler033){globalThis.removeEventListener?.("popstate",this._ahNavPopHandler033);this._ahNavPopHandler033=null}
 if(this._ahNavPopHandler034){globalThis.removeEventListener?.("popstate",this._ahNavPopHandler034);this._ahNavPopHandler034=null}
 clearTimeout(this._ahBackTimer034);
 clearTimeout(this._attachmentUrlRetryTimer037);
 this._ahBackPending034=false;
 this._ahNavRestoring033=false;
 this._ahNavRestoring034=false;
 if(globalThis.__animalHealthHandleBack034===this._nativeBackHandler034)delete globalThis.__animalHealthHandleBack034;
 this._nativeBackHandler034=null
};
AH037.connectedCallback=function(){
 this.removeInternalHistory037();
 return AH033Base.connectedCallback.call(this)
};
AH037.disconnectedCallback=function(){
 this.removeInternalHistory037();
 if(AH033Base.disconnectedCallback)return AH033Base.disconnectedCallback.call(this)
};
AH037.handleClick=function(event){
 const button=event.composedPath().find(node=>node?.dataset&&(node.dataset.action||node.dataset.view));
 if(!button)return AH033Base.handleClick.call(this,event);
 const action=String(button.dataset.action||""),id=String(button.dataset.id||"");
 if(action==="target-animal-remove-034"){
  const key=button.dataset.key,state=this.ensureTargetState026(key);
  state.animalIds=(state.animalIds||[]).filter(value=>String(value)!==id);
  this.updateTargetCompatibility026(key);
  this.refreshTaskOptions012?.(this.shadowRoot.querySelector(".modal form"));
  return
 }
 if(action==="target-animal-create-034"){this.beginAnimalCreation034(button.dataset.key);return}
 if(action==="multi-remove-034"){
  const root=button.closest("[data-multi-choice034]");
  if(root){
   const input=[...root.querySelectorAll("[data-multi-option034]")].find(item=>String(item.value)===String(button.dataset.value));
   if(input)input.checked=false;
   this.refreshMultiChoice034(root)
  }
  return
 }
 if(action==="multi-custom-034"){this.addCustomChoice034(button.closest("[data-multi-choice034]"));return}
 if(action==="task-duplicate-034"||action==="task-continue-034"){
  const task=this.taskById036?.(id)||this.task?.(id)||(this.d?.tasks||[]).find(item=>String(item.id)===id);
  this.openTaskCopy034(task,action==="task-continue-034"?"replan":"duplicate");
  return
 }
 if(action==="task-overview-036"){
  this.taskCopyMeta036=null;
  this.aiTaskDraft=null;
  this.modal=null;
  this.detail=null;
  this.view="tasks";
  this.filter="";
  this.taskSearch097="";
  this.render();
  return
 }
 if(action==="create-task"||action==="edit-task-097"){
  this.taskCopyMeta036=null;
  this.aiTaskDraft=null
 }
 return AH033Base.handleClick.call(this,event)
};
AH037.handleSubmit=async function(event){
 const form=event.composedPath().find(node=>node?.tagName==="FORM"),animalResume=form?.dataset.form==="animal"&&Boolean(this._resumeAfterAnimal034),taskForm=form?.dataset.form==="task";
 const result=await AH033Base.handleSubmit.call(this,event);
 if(animalResume&&this.modal?.type!=="create-animal"){
  this._animalCreationCompleted034=false;
  this.finishAnimalCreation034?.()
 }
 if(taskForm&&this.modal?.type!=="create-task")this.aiTaskDraft=null;
 return result
};
AH037.syncAttachmentContext037=function(){
 const context=String(this.detail?.animal?.id||"");
 if(this._attachmentImageContext037!==context){
  this._attachmentImageContext037=context;
  this._attachmentImageIds037=new Set;
  this.attachmentUrls024={};
  this._attachmentUrlKey037="";
  this._attachmentUrlPromise037=null;
  clearTimeout(this._attachmentUrlRetryTimer037)
 }
};
AH037.noteAttachmentImages037=function(items){
 this.syncAttachmentContext037();
 for(const item of items||[])if(String(item?.media_type||"").startsWith("image/")&&item?.id)this._attachmentImageIds037.add(String(item.id))
};
AH037.attachmentImageIds037=function(){
 this.syncAttachmentContext037();
 const ids=new Set(this._attachmentImageIds037);
 for(const item of this.detail?.attachments||[])if(String(item?.media_type||"").startsWith("image/")&&item?.id)ids.add(String(item.id));
 return[...ids]
};
AH037.fetchAttachmentUrls037=async function(ids){
 const urls={};
 for(let index=0;index<ids.length;index+=100){
  const result=await this.ws(`${D}/v0924/attachment/urls`,{attachment_ids:ids.slice(index,index+100)});
  Object.assign(urls,result?.urls||{})
 }
 return urls
};
AH037.scheduleAttachmentUrlRetry037=function(){
 clearTimeout(this._attachmentUrlRetryTimer037);
 const context=this._attachmentImageContext037;
 this._attachmentUrlRetryTimer037=setTimeout(()=>{
  if(this.isConnected===false||this._attachmentImageContext037!==context)return;
  void this.ensureAttachmentUrls037()
 },1600)
};
AH037.refreshAttachmentUrls024=async function(){
 const ids=this.attachmentImageIds037();
 if(!ids.length){this.attachmentUrls024={};return}
 const animalId=String(this.detail?.animal?.id||"");
 try{
  const urls=await this.fetchAttachmentUrls037(ids);
  if(animalId&&String(this.detail?.animal?.id||"")!==animalId)return;
  this.attachmentUrls024={...(this.attachmentUrls024||{}),...urls};
  this._attachmentUrlRetryAt037=0;
  clearTimeout(this._attachmentUrlRetryTimer037)
 }catch(_error){
  this._attachmentUrlRetryAt037=Date.now()+1500;
  this.scheduleAttachmentUrlRetry037()
 }
};
AH037.ensureAttachmentUrls037=async function(){
 const ids=this.attachmentImageIds037(),missing=ids.filter(id=>!this.attachmentUrls024?.[id]?.thumbnail);
 if(!missing.length||Date.now()<Number(this._attachmentUrlRetryAt037||0))return;
 const key=missing.slice().sort().join("|");
 if(this._attachmentUrlPromise037&&this._attachmentUrlKey037===key)return this._attachmentUrlPromise037;
 const animalId=String(this.detail?.animal?.id||"");
 this._attachmentUrlKey037=key;
 this._attachmentUrlPromise037=(async()=>{
  try{
   const urls=await this.fetchAttachmentUrls037(missing);
   if(animalId&&String(this.detail?.animal?.id||"")!==animalId)return;
   this.attachmentUrls024={...(this.attachmentUrls024||{}),...urls};
   this._attachmentUrlRetryAt037=0;
   clearTimeout(this._attachmentUrlRetryTimer037);
   if(missing.some(id=>urls[id]?.thumbnail))this.render()
  }catch(_error){
   this._attachmentUrlRetryAt037=Date.now()+1500;
   this.scheduleAttachmentUrlRetry037()
  }finally{
   if(this._attachmentUrlKey037===key){
    this._attachmentUrlKey037="";
    this._attachmentUrlPromise037=null
   }
  }
 })();
 return this._attachmentUrlPromise037
};
AH037.thumbnailMarkup037=function(html){
 return String(html||"").replace(/<img\s+/g,'<img loading="eager" decoding="async" width="48" height="48" ')
};
AH037.attachmentList=function(items){
 this.noteAttachmentImages037(items);
 return this.thumbnailMarkup037(AH037Base.attachmentList.call(this,items))
};
AH037.attachmentStrip026=function(event,expanded=false){
 const items=(this.detail?.attachments||[]).filter(item=>String(item.event_id||"")===String(event?.id||""));
 this.noteAttachmentImages037(items);
 return this.thumbnailMarkup037(AH037Base.attachmentStrip026.call(this,event,expanded))
};
AH037.render=function(){
 AH037Base.render.call(this);
 queueMicrotask(()=>void this.ensureAttachmentUrls037())
};
