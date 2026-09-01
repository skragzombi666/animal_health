Object.assign(T,{
 internalBack033:["Zurück innerhalb von Animal Health","Back within Animal Health"]
});
const AH033=AnimalHealthPanel.prototype;
const AH033Base={
 eventCompact0817:AH033.eventCompact0817,
 connectedCallback:AH033.connectedCallback,
 disconnectedCallback:AH033.disconnectedCallback,
 handleClick:AH033.handleClick,
 handleSubmit:AH033.handleSubmit,
 render:AH033.render
};
AH033.eventCompact0817=function(event){
 const gabeType=this.gabeTypeForEvent027?.(event);
 if(!gabeType)return AH033Base.eventCompact0817.call(this,event);
 const snapshot=event.data?.medication_snapshot||event.data?.gabe_snapshot||{},product=event.data?.product_name||event.data?.medication_name||snapshot.name||event.title||this.gabeKindLabel027?.(gabeType)||"",dose=event.value!=null?`${this.num(event.value)} ${this.l(event.unit||"")}`:"",route=event.data?.route||snapshot.route||"",task=Boolean(event.task_id||event.data?.task_id||event.data?.source_task_id),extraTitle=this.taskTitleExtra027?.(event,product)||"",parts=this.activeSummary027?.(event)||[];
 if(route&&!parts.includes(this.l(route)))parts.push(this.l(route));
 if(extraTitle&&!parts.includes(extraTitle))parts.push(extraTitle);
 const global=this.view!=="animal-detail",animalName=global?(event.animal_name||this.animal?.(event.animal_id)?.name||""):"",typeBadge=gabeType!=="medication"?`<span class="gabeTypeBadge027">${esc(this.gabeKindLabel027(gabeType))}</span>`:"",scopeBadge=this.scopeBadge026?.(event)||"",taskIcon=task?`<ha-icon class="taskSource027" icon="mdi:clipboard-check-outline" title="${esc(this.t("fromTask027"))}" aria-label="${esc(this.t("fromTask027"))}"></ha-icon>`:"",meta=parts.length?`<i>${parts.map(esc).join(" · ")}</i>`:"",metaLine=task?`${taskIcon}${meta}`:meta?`<span class="gabeMetaDot033">·</span>${meta}`:"";
 return`<div class="row event eventOpen eventCompact0817 gabeCompact033 gabe-${gabeType} ${global?"global033":"local033"}" role="button" tabindex="0" data-action="event-detail" data-id="${esc(event.id)}"><ha-icon icon="${this.gabeKindIcon027?.(gabeType)||"mdi:pill"}"></ha-icon><div class="gabeContent033"><div class="gabeTop033">${animalName?`<span class="gabeAnimal033">${esc(animalName)}</span>`:""}${animalName&&dose?`<span class="gabeTopSep033">·</span>`:""}${dose?`<span class="gabeDose033">${esc(dose)}</span>`:""}</div><div class="gabeTitleLine033"><b class="gabeTitleText033">${esc(product)}</b>${typeBadge}${scopeBadge}</div>${metaLine?`<div class="gabeMetaLine033">${metaLine}</div>`:""}${event.notes?`<small>${esc(event.notes)}</small>`:""}</div></div>`
};
AH033.layoutGabe033=function(){
 for(const row of this.shadowRoot.querySelectorAll(".gabeCompact033")){
  const dose=row.querySelector(".gabeDose033"),title=row.querySelector(".gabeTitleText033"),titleLine=row.querySelector(".gabeTitleLine033");
  if(!dose||!title||!titleLine)continue;
  const wraps=title.getClientRects().length>1||title.getBoundingClientRect().height>parseFloat(getComputedStyle(title).lineHeight||"0")*1.45;
  if(!wraps)continue;
  titleLine.insertBefore(dose,title);
  row.classList.add("doseInline033")
 }
};
AH033.cloneNavValue033=function(value){
 try{
  const text=JSON.stringify(value);
  if(text===undefined||text.length>16000)return undefined;
  return JSON.parse(text)
 }catch(_error){return undefined}
};
AH033.navSnapshot033=function(){
 const props={},exact=new Set(["filter","groupDetailId","groupFilter","tagFilter","settingsSection027"]),pattern=/(?:Filter|Section|Tab|Page|Detail(?:Id)?|Selected(?:Id)?|ViewMode|Subpage)\d*$/i;
 for(const key of Object.keys(this)){
  if(!exact.has(key)&&!pattern.test(key))continue;
  const value=this.cloneNavValue033(this[key]);
  if(value!==undefined)props[key]=value
 }
 return{view:String(this.view||"overview"),animalId:String(this.detail?.animal?.id||""),modal:this.cloneNavValue033(this.modal)||null,props}
};
AH033.navSignature033=function(snapshot){return JSON.stringify(snapshot||{})};
AH033.navMarker033=function(snapshot,depth){return{version:1,depth:Math.max(0,Number(depth||0)),snapshot}};
AH033.currentNavMarker033=function(){const state=globalThis.history?.state;return state&&typeof state==="object"?state.__animalHealthNav033:null};
AH033.writeNavEntry033=function(snapshot,{push=false,depth=this._ahNavDepth033||0}={}){
 try{
  const current=globalThis.history?.state,state=current&&typeof current==="object"?{...current}:{},marker=this.navMarker033(snapshot,depth);
  state.__animalHealthNav033=marker;
  if(push)globalThis.history.pushState(state,"",globalThis.location.href);else globalThis.history.replaceState(state,"",globalThis.location.href);
  this._ahNavDepth033=marker.depth
 }catch(_error){}
};
AH033.restoreNavSnapshot033=async function(marker){
 if(!marker?.snapshot)return;
 const snapshot=marker.snapshot;
 this._ahNavRestoring033=true;
 this._ahNavDepth033=Math.max(0,Number(marker.depth||0));
 try{
  for(const[key,value]of Object.entries(snapshot.props||{}))this[key]=this.cloneNavValue033(value);
  this.modal=this.cloneNavValue033(snapshot.modal)||null;
  if(snapshot.animalId){
   await this.loadDetail(snapshot.animalId,false)
  }else this.detail=null;
  this.view=String(snapshot.view||"overview");
  this.render()
 }finally{this._ahNavRestoring033=false}
};
AH033.bindInternalHistory033=function(){
 if(this._ahNavPopHandler033)return;
 this._ahNavPopHandler033=event=>{const marker=event.state?.__animalHealthNav033;if(marker)void this.restoreNavSnapshot033(marker)};
 globalThis.addEventListener("popstate",this._ahNavPopHandler033);
 const current=this.currentNavMarker033();
 if(current){this._ahNavDepth033=Math.max(0,Number(current.depth||0))}else this.writeNavEntry033(this.navSnapshot033(),{depth:0})
};
AH033.connectedCallback=function(){AH033Base.connectedCallback.call(this);queueMicrotask(()=>this.bindInternalHistory033())};
AH033.disconnectedCallback=function(){
 if(this._ahNavPopHandler033){globalThis.removeEventListener("popstate",this._ahNavPopHandler033);this._ahNavPopHandler033=null}
 if(AH033Base.disconnectedCallback)AH033Base.disconnectedCallback.call(this)
};
AH033.backwardControl033=function(button){
 const action=String(button?.dataset?.action||"");
 return action==="close"||/(^|-)back(-|$)/.test(action)||Boolean(button?.querySelector?.('ha-icon[icon="mdi:arrow-left"],ha-icon[icon="mdi:chevron-left"]'))
};
AH033.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset&&(node.dataset.action||node.dataset.view)),before=this.navSnapshot033(),backward=this.backwardControl033(button),result=await AH033Base.handleClick.call(this,event),after=this.navSnapshot033();
 if(this._ahNavRestoring033||this.navSignature033(before)===this.navSignature033(after))return result;
 const current=this.currentNavMarker033(),depth=Math.max(0,Number(current?.depth??this._ahNavDepth033??0));
 if(backward&&depth>0){this.writeNavEntry033(before,{depth});globalThis.history.back();return result}
 if(before.modal&&!after.modal&&before.view===after.view){this.writeNavEntry033(after,{depth});return result}
 this.writeNavEntry033(before,{depth});
 this.writeNavEntry033(after,{push:true,depth:depth+1});
 return result
};
AH033.handleSubmit=async function(event){
 const result=await AH033Base.handleSubmit.call(this,event);
 if(!this._ahNavRestoring033){const current=this.currentNavMarker033();if(current)this.writeNavEntry033(this.navSnapshot033(),{depth:current.depth})}
 return result
};
AH033.render=function(){
 AH033Base.render.call(this);
 this.shadowRoot.innerHTML+=`<style>
.gabeCompact033{align-items:flex-start!important}.gabeContent033{display:block;min-width:0;width:100%}.gabeTop033{display:flex;align-items:baseline;gap:5px;min-height:1.05em;margin-bottom:2px;color:var(--secondary-text-color);font-size:.82rem;line-height:1.1}.gabeTop033:empty{display:none}.gabeAnimal033{font-weight:650;color:var(--primary-text-color)}.gabeDose033{font-weight:650;color:var(--secondary-text-color);white-space:nowrap}.gabeTitleLine033{display:block;min-width:0;line-height:1.22;overflow-wrap:anywhere}.gabeTitleText033{display:inline!important;font-weight:700}.gabeTitleLine033>.gabeTypeBadge027,.gabeTitleLine033>.scopeBadge026{margin-left:5px}.gabeMetaLine033{display:flex;align-items:center;gap:5px;min-width:0;margin-top:2px;color:var(--secondary-text-color);font-size:.8rem;line-height:1.2}.gabeMetaLine033 i{min-width:0;overflow-wrap:anywhere}.gabeMetaLine033 .taskSource027{flex:0 0 auto;margin:0}.gabeMetaDot033{flex:0 0 auto}.doseInline033 .gabeTopSep033{display:none}.doseInline033.local033 .gabeTop033,.doseInline033 .gabeTop033:empty{display:none}.gabeTitleLine033>.gabeDose033{display:inline;margin-right:5px}@media(max-width:600px){.gabeTop033{font-size:.78rem}.gabeMetaLine033{font-size:.76rem}}
</style>`;
 requestAnimationFrame(()=>this.layoutGabe033())
};
