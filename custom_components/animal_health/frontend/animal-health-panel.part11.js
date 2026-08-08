Object.assign(T,{
 eventDetails:["Eintragsdetails","Entry details"],
 eventValue:["Wert","Value"],
 eventSource:["Quelle / Aufgabe","Source / task"],
 openAnimal:["Tier öffnen","Open animal"],
 status_change:["Statusänderung","Status change"]
});
const AH074=AnimalHealthPanel.prototype;
const AH074Base={
 load:AH074.load,
 loadDetail:AH074.loadDetail,
 eventRow:AH074.eventRow,
 eventTitle:AH074.eventTitle,
 form:AH074.form,
 handleClick:AH074.handleClick
};
AH074.applyTaskVisibility=function(target,tasks){
 if(!target?.occurrences)return;
 const active=new Map((tasks||[]).map(task=>[String(task.id),task.is_active!==false]));
 target.occurrences=target.occurrences.filter(item=>item.status!=="pending"||active.get(String(item.task_id))!==false);
 if(target.summary){
  const pending=target.occurrences.filter(item=>item.status==="pending");
  target.summary.pending_tasks=pending.length;
  target.summary.overdue_tasks=pending.filter(item=>item.is_overdue).length;
  target.summary.today_tasks=pending.filter(item=>item.is_today).length;
  target.summary.upcoming_tasks=pending.filter(item=>item.is_upcoming).length
 }
};
AH074.load=async function(){
 await AH074Base.load.call(this);
 if(this.d){this.applyTaskVisibility(this.d,this.d.tasks);this.render()}
};
AH074.loadDetail=async function(id,r=true){
 await AH074Base.loadDetail.call(this,id,false);
 if(this.detail)this.applyTaskVisibility(this.detail,this.detail.tasks);
 if(r)this.render()
};
AH074.eventTitle=function(event){
 const key=String(event?.title||"");
 if(T[key])return this.t(key);
 if(L[key])return this.l(key);
 return AH074Base.eventTitle.call(this,event)
};
AH074.eventById=function(id){return(this.detail?.events||[]).find(event=>String(event.id)===String(id))||(this.d?.events||[]).find(event=>String(event.id)===String(id))||null};
AH074.eventRow=function(event){
 let html=AH074Base.eventRow.call(this,event);
 return html.replace('<div class="row event">',`<div class="row event eventOpen" role="button" tabindex="0" data-action="event-detail" data-id="${esc(event.id)}">`)
};
AH074.eventDetail=function(id){
 const event=this.eventById(id);if(!event)return`<h2>${this.t("eventDetails")}</h2>${this.empty("noEvents")}`;
 const value=event.value!=null?`${this.num(event.value)}${event.unit?` ${esc(event.unit)}`:""}`:null;
 const source=event.task_id||event.task_occurrence_id||null;
 const execution=event.data?.task_execution;
 const attachments=(this.detail?.attachments||[]).filter(item=>item.event_id===event.id);
 return`<h2>${esc(this.eventTitle(event))}</h2><div class="eventDetail">${this.obj({animal:event.animal_name,event_type:event.event_type,occurred_at:this.fmt(event.occurred_at,true),eventValue:value,notes:event.notes,eventSource:source})}${execution?this.execution(execution):""}${attachments.length?`<section><h3>${this.t("documents")}</h3>${this.attachmentList(attachments)}</section>`:""}${event.animal_id?`<div class="actions"><button type="button" class="primary" data-action="animal-detail" data-id="${esc(event.animal_id)}"><ha-icon icon="mdi:paw"></ha-icon>${this.t("openAnimal")}</button></div>`:""}</div>`
};
AH074.form=function(){if(this.modal?.type==="event-detail")return this.eventDetail(this.modal.eventId);return AH074Base.form.call(this)};
AH074.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset&&(node.dataset.action||node.dataset.view));if(!button)return;
 if(button.dataset.action==="event-detail"){this.open("event-detail",{eventId:button.dataset.id});return}
 return AH074Base.handleClick.call(this,event)
};
const AH074_CSS=`
.eventOpen{cursor:pointer}.eventOpen:hover,.eventOpen:focus-visible{background:var(--secondary-background-color);outline:2px solid color-mix(in srgb,var(--primary-color) 55%,transparent);outline-offset:-2px}.eventDetail{display:grid;gap:14px}.eventDetail dl{margin:0}.eventDetail section{display:grid;gap:8px}
`;
const AH074Render=AH074.render;
AH074.render=function(){AH074Render.call(this);this.shadowRoot.innerHTML+=`<style>${AH074_CSS}</style>`};
