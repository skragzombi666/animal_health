Object.assign(T,{
 taskInactive:["Deaktiviert","Inactive"],
 statusFrom:["Vorheriger Status","Previous status"],
 statusTo:["Neuer Status","New status"]
});
const AH075=AnimalHealthPanel.prototype;
const AH075Base={
 tasks:AH075.tasks,
 eventDetail:AH075.eventDetail,
 handleClick:AH075.handleClick
};
AH075.tasks=function(){
 const q=this.filter.toLowerCase(),occurrences=this.d.occurrences.filter(item=>!q||[item.task_title,item.animal_name,item.task_kind,item.status].some(value=>String(value||"").toLowerCase().includes(q)));
 const definitions=this.d.tasks.filter(task=>task.is_active===false||task.recurrence_type!=="once"||this.d.occurrences.some(item=>String(item.task_id)===String(task.id)&&item.status==="pending"));
 return`${this.heading("tasks",`<button class="primary" data-action="create-task"><ha-icon icon="mdi:clipboard-plus"></ha-icon>${this.t("createTask")}</button>`)}${this.group("overdue",occurrences.filter(item=>item.is_overdue))}${this.group("dueToday",occurrences.filter(item=>item.is_today))}${this.group("upcoming",occurrences.filter(item=>item.is_upcoming).slice(0,100))}${this.group("completed",occurrences.filter(item=>item.status!=="pending").slice(0,100))}<section class="card"><h2>${this.t("tasks")}</h2>${definitions.map(task=>`<div class="row ${task.is_active===false?"taskInactive":""}"><ha-icon icon="${I[task.task_kind]||I.reminder}"></ha-icon><div><b>${esc(task.title)}</b><span>${esc(task.animal_name||this.t("general"))} · ${this.l(task.task_kind)}${task.is_active===false?` · ${this.t("taskInactive")}`:""}</span></div><button data-action="toggle" data-id="${task.id}">${this.t(task.is_active?"deactivate":"activate")}</button></div>`).join("")||this.empty("noTasks")}</section>`
};
AH075.statusTransition=function(event){
 if(event?.event_type!=="status_change")return"";
 const previous=event.data?.previous_status,next=event.data?.new_status;
 if(!previous&&!next)return"";
 return`<section class="statusTransition"><div><small>${this.t("statusFrom")}</small><b>${esc(this.l(previous||"–"))}</b></div><ha-icon icon="mdi:arrow-right"></ha-icon><div><small>${this.t("statusTo")}</small><b>${esc(this.l(next||"–"))}</b></div></section>`
};
AH075.eventDetail=function(id){
 const event=this.eventById(id);if(!event)return AH075Base.eventDetail.call(this,id);
 let html=AH075Base.eventDetail.call(this,id),transition=this.statusTransition(event);
 if(transition)html=html.replace('<div class="eventDetail">',`<div class="eventDetail">${transition}`);
 return html
};
AH075.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset&&(node.dataset.action||node.dataset.view));if(!button)return;
 if(button.dataset.action==="animal-detail"&&this.modal?.type==="event-detail"){
  const id=button.dataset.id;this.modal=null;await this.loadDetail(id);return
 }
 return AH075Base.handleClick.call(this,event)
};
const AH075_CSS=`
.taskInactive{opacity:.72}.taskInactive>div>span{font-style:italic}.statusTransition{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:12px;padding:12px;border:1px solid var(--divider-color);border-radius:10px;background:var(--secondary-background-color)}.statusTransition>div{display:grid;gap:3px}.statusTransition small{color:var(--secondary-text-color)}.statusTransition b{font-size:1.05em}.statusTransition ha-icon{color:var(--primary-color)}
`;
const AH075Render=AH075.render;
AH075.render=function(){AH075Render.call(this);this.shadowRoot.innerHTML+=`<style>${AH075_CSS}</style>`};
