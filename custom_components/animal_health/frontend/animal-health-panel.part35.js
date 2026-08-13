Object.assign(T,{
 series0815:["Serie","Series"],
 recurringTasks0815:["Serienaufgaben","Recurring tasks"],
 oneTimeTasks0815:["Einmalige Aufgaben","One-time tasks"],
 calendarToday0815:["Heute","Today"],
 seriesMedication0815:["Serienmedikation","Recurring medication"],
 seriesHistory0815:["Rückwirkend ab {date} als Serie erfasst; Einzelgaben vor der Erfassung wurden nicht separat dokumentiert.","Recorded retrospectively as a series from {date}; individual administrations before entry were not documented separately."],
 noCalendarItems0815:["Keine geplanten Einträge an diesem Tag.","No planned items on this day."]
});
const AH0815=AnimalHealthPanel.prototype;
const AH0815Base={
 tasks:AH0815.tasks,
 calendar:AH0815.calendar,
 eventRow:AH0815.eventRow,
 handleClick:AH0815.handleClick,
 render:AH0815.render
};
AH0815.dateParts0815=function(value){const p=String(value||"").slice(0,10).split("-").map(Number);return p.length===3&&p.every(Number.isFinite)?p:null};
AH0815.dateKey0815=function(date){return`${date.getUTCFullYear()}-${String(date.getUTCMonth()+1).padStart(2,"0")}-${String(date.getUTCDate()).padStart(2,"0")}`};
AH0815.utcDate0815=function(value){const p=this.dateParts0815(value);return p?new Date(Date.UTC(p[0],p[1]-1,p[2])):null};
AH0815.addDays0815=function(date,days){const d=new Date(date);d.setUTCDate(d.getUTCDate()+days);return d};
AH0815.daysInMonth0815=function(year,month){return new Date(Date.UTC(year,month,0)).getUTCDate()};
AH0815.taskOccurs0815=function(task,key){
 if(!task?.is_active)return false;const start=this.utcDate0815(task.start_date),day=this.utcDate0815(key);if(!start||!day||day<start)return false;const end=this.utcDate0815(task.end_date);if(end&&day>end)return false;const type=task.recurrence_type||"once",interval=Math.max(1,Number(task.recurrence_interval)||1),delta=Math.round((day-start)/86400000);
 if(type==="once")return delta===0;if(type==="daily")return delta%interval===0;if(type==="weekly")return delta%(7*interval)===0;if(type==="monthly"){const months=(day.getUTCFullYear()-start.getUTCFullYear())*12+day.getUTCMonth()-start.getUTCMonth();if(months<0||months%interval!==0)return false;const expected=Math.min(start.getUTCDate(),this.daysInMonth0815(day.getUTCFullYear(),day.getUTCMonth()+1));return day.getUTCDate()===expected}return false
};
AH0815.recurrenceLabel0815=function(task){const n=Math.max(1,Number(task.recurrence_interval)||1),type=task.recurrence_type||"once";if(n===1)return this.l(type);const unit=type==="daily"?(this.lang()?"days":"Tage"):type==="weekly"?(this.lang()?"weeks":"Wochen"):(this.lang()?"months":"Monate");return`${this.lang()?"every":"alle"} ${n} ${unit}`};
AH0815.seriesTaskIds0815=function(){return new Set((this.d?.tasks||[]).filter(task=>task.recurrence_type&&task.recurrence_type!=="once").map(task=>task.id))};
AH0815.seriesRow0815=function(task){
 const occurrence=task.is_active?(this.d?.occurrences||[]).find(item=>item.task_id===task.id&&item.status==="pending"):null,planned=task.planned||{},detail=[task.animal_name||this.t("general"),this.recurrenceLabel0815(task),`${this.t("start_date")}: ${this.fmt(task.start_date)}`];if(task.end_date)detail.push(`${this.t("end_date")}: ${this.fmt(task.end_date)}`);if(planned.medication_name)detail.push(planned.medication_name);
 return`<div class="row seriesRow0815"><ha-icon icon="${I[task.task_kind]||I.reminder}"></ha-icon><div><b>${esc(task.title)} <span class="seriesBadge0815"><ha-icon icon="mdi:repeat"></ha-icon>${this.t("series0815")}</span></b><span>${detail.map(esc).join(" · ")}</span></div><div class="rowBtns">${occurrence?`<button class="primary" data-action="execute" data-id="${esc(occurrence.id)}">${this.t("execute")}</button>`:""}<button data-action="toggle" data-id="${esc(task.id)}">${this.t(task.is_active?"deactivate":"activate")}</button></div></div>`
};
AH0815.tasks=function(){
 const q=String(this.filter||"").toLowerCase(),seriesIds=this.seriesTaskIds0815(),series=(this.d?.tasks||[]).filter(task=>task.recurrence_type!=="once"&&(!q||[task.title,task.animal_name,task.task_kind,task.recurrence_type].some(value=>String(value||"").toLowerCase().includes(q)))),occurrences=(this.d?.occurrences||[]).filter(item=>!(item.status==="pending"&&seriesIds.has(item.task_id))).filter(item=>!q||[item.task_title,item.animal_name,item.task_kind,item.status].some(value=>String(value||"").toLowerCase().includes(q))),oneTime=(this.d?.tasks||[]).filter(task=>task.recurrence_type==="once"&&(!q||[task.title,task.animal_name,task.task_kind].some(value=>String(value||"").toLowerCase().includes(q))));
 const oneTimeRows=oneTime.map(task=>`<div class="row"><ha-icon icon="${I[task.task_kind]||I.reminder}"></ha-icon><div><b>${esc(task.title)}</b><span>${esc(task.animal_name||this.t("general"))} · ${this.l(task.task_kind)} · ${this.fmt(task.start_date)}</span></div><button data-action="toggle" data-id="${esc(task.id)}">${this.t(task.is_active?"deactivate":"activate")}</button></div>`).join("")||this.empty("noTasks");
 return`${this.heading("tasks",`<button class="primary" data-action="create-task"><ha-icon icon="mdi:clipboard-plus"></ha-icon>${this.t("createTask")}</button>`)}<section class="card"><h2>${this.t("recurringTasks0815")} <small>${series.length}</small></h2>${series.map(task=>this.seriesRow0815(task)).join("")||this.empty("noTasks")}</section>${this.group("overdue",occurrences.filter(item=>item.is_overdue))}${this.group("dueToday",occurrences.filter(item=>item.is_today))}${this.group("upcoming",occurrences.filter(item=>item.is_upcoming).slice(0,100))}${this.group("completed",occurrences.filter(item=>item.status!=="pending").slice(0,100))}<section class="card"><h2>${this.t("oneTimeTasks0815")}</h2>${oneTimeRows}</section>`
};
