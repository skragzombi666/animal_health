Object.assign(T,{
 calendarOpening099:["Fälligkeit wird geöffnet …","Opening due item …"],
 calendarOccurrenceMissing099:["Für diesen geplanten Termin konnte keine ausführbare Fälligkeit geladen werden.","No executable occurrence could be loaded for this scheduled date."]
});
const AH099=AnimalHealthPanel.prototype;
const AH099Base={
 render:AH099.render,
 handleClick:AH099.handleClick,
 calendarState097:AH099.calendarState097,
 calendarIcon097:AH099.calendarIcon097
};
AH099.pullScrollTop099=function(event){
 let maximum=0;
 for(const node of event?.composedPath?.()||[]){
  if(!node||typeof node!=="object")continue;
  const top=Number(node.scrollTop||0),height=Number(node.scrollHeight||0),client=Number(node.clientHeight||0);
  if(height>client+1&&top>maximum)maximum=top
 }
 if(maximum>0)return maximum;
 return Number(this.scrollTop098?.()||0)
};
AH099.pullStart099=function(event){
 if(this.busy||this.pullRefreshing098||this.modal||event.touches?.length!==1||this.pullScrollTop099(event)>1){this.pullReset098?.();return}
 this.pullStartY098=event.touches[0].clientY;this.pullStartX098=event.touches[0].clientX;this.pullDistance098=0
};
AH099.pullMove099=function(event){
 if(this.pullStartY098==null||event.touches?.length!==1)return;
 const dy=event.touches[0].clientY-this.pullStartY098,dx=event.touches[0].clientX-this.pullStartX098;
 if(dy<=0||this.pullScrollTop099(event)>1||Math.abs(dx)>dy){this.pullReset098?.();return}
 if(dy>4&&event.cancelable)event.preventDefault();
 this.pullDistance098=dy;
 const offset=Math.min(82,dy*.72),indicator=this.pullElement098?.();if(!indicator)return;
 indicator.classList.add("dragging098");indicator.classList.toggle("ready098",dy>=76);indicator.style.transform=`translate(-50%,${offset-58}px)`;indicator.style.opacity=String(Math.min(1,offset/34));
 const icon=indicator.querySelector?.("ha-icon");if(icon)icon.style.transform=`rotate(${Math.min(300,dy*2.8)}deg)`;
 const label=indicator.querySelector?.("span");if(label)label.textContent=this.t(dy>=76?"releaseToRefresh098":"pullToRefresh098")
};
AH099.pullEnd099=function(){const ready=Number(this.pullDistance098||0)>=76;this.pullReset098?.();if(ready)void this.refreshFromPull098?.()};
AH099.bindPullRefresh099=function(){
 if(this.pullRefreshBound099)return;
 this.pullRefreshBound099=true;
 this.addEventListener("touchstart",event=>this.pullStart099(event),{passive:true,capture:true});
 this.addEventListener("touchmove",event=>this.pullMove099(event),{passive:false,capture:true});
 this.addEventListener("touchend",()=>this.pullEnd099(),{passive:true,capture:true});
 this.addEventListener("touchcancel",()=>this.pullReset098?.(),{passive:true,capture:true})
};
AH099.calendarState097=function(task,key,todayKey){return{...AH099Base.calendarState097.call(this,task,key,todayKey),date:key,taskId:String(task.id)}};
AH099.calendarIcon097=function(task,state){
 if(["due","unconfirmed"].includes(state.key)&&!state.occurrence){
  const target=task.animal_name||task.group_name||this.t("general"),title=esc([state.label,task.title,target].filter(Boolean).join(" · ")),body=`<ha-icon icon="${I[task.task_kind]||I.reminder}"></ha-icon>`;
  return`<button type="button" class="calendarIcon0816 calendarIcon097 calendarVirtualExecute099 calendarState-${state.key}" data-action="calendar-execute-099" data-task-id="${esc(task.id)}" data-date="${esc(state.date||"")}" title="${title}" aria-label="${title}">${body}</button>`
 }
 return AH099Base.calendarIcon097.call(this,task,state)
};
AH099.findOccurrenceResponse099=function(value,seen=new Set()){
 if(!value||typeof value!=="object"||seen.has(value))return[];
 seen.add(value);
 if(Array.isArray(value.occurrences))return value.occurrences;
 for(const key of["response","result","data"]){const found=this.findOccurrenceResponse099(value[key],seen);if(found.length)return found}
 return[]
};
AH099.decorateOccurrence099=function(occurrence,task,date){
 const today=String(this.d?.today||""),scheduledDate=String(occurrence?.scheduled_date||date||"").slice(0,10);
 return{...occurrence,task_id:String(occurrence?.task_id||task.id),task_title:occurrence?.task_title||task.title,animal_id:occurrence?.animal_id??task.animal_id??null,animal_name:occurrence?.animal_name??task.animal_name??null,group_id:occurrence?.group_id??task.group_id??null,group_name:occurrence?.group_name??task.group_name??null,task_kind:occurrence?.task_kind||task.task_kind||"reminder",planned:occurrence?.planned||task.planned||{},scheduled_date:scheduledDate,status:occurrence?.status||"pending",is_overdue:scheduledDate<today,is_today:scheduledDate===today,is_upcoming:scheduledDate>today}
};
AH099.upsertOccurrence099=function(occurrence){
 if(!this.d)return;
 const list=[...(this.d.occurrences||[])],index=list.findIndex(item=>String(item.id)===String(occurrence.id));if(index>=0)list[index]=occurrence;else list.push(occurrence);this.d.occurrences=list;
 if(this.detail&&(String(this.detail.animal?.id||"")===String(occurrence.animal_id||""))){const detail=[...(this.detail.occurrences||[])],detailIndex=detail.findIndex(item=>String(item.id)===String(occurrence.id));if(detailIndex>=0)detail[detailIndex]=occurrence;else detail.push(occurrence);this.detail.occurrences=detail}
};
AH099.resolveCalendarOccurrence099=async function(taskId,date){
 const task=this.task(taskId);if(!task)throw Error(this.t("calendarOccurrenceMissing099"));
 const response=await this.svc("list_task_occurrences",{task_id:taskId,task_scope:"all",status:"pending",from_date:date,to_date:date,include_general:true,limit:20},true),rows=this.findOccurrenceResponse099(response),raw=rows.find(item=>String(item.task_id)===String(taskId)&&String(item.scheduled_date||item.scheduled_local||item.scheduled_for||"").slice(0,10)===date&&item.status==="pending")||rows.find(item=>item.status==="pending");
 if(!raw)throw Error(this.t("calendarOccurrenceMissing099"));
 return this.decorateOccurrence099(raw,task,date)
};
AH099.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset?.action),action=button?.dataset?.action;
 if(action==="calendar-execute-099"){
  event.preventDefault();const taskId=String(button.dataset.taskId||""),date=String(button.dataset.date||"");if(!taskId||!date)return;
  button.disabled=true;this.notify(this.t("calendarOpening099"));
  try{const occurrence=await this.resolveCalendarOccurrence099(taskId,date);this.upsertOccurrence099(occurrence);this.open("execute",{occurrenceId:occurrence.id})}catch(error){button.disabled=false;this.notify(`${this.t("failed")}: ${error?.message||error}`,true);this.render()}
  return
 }
 return AH099Base.handleClick.call(this,event)
};
AH099.render=function(){AH099Base.render.call(this);this.bindPullRefresh099();this.shadowRoot.innerHTML+=`<style>:host{overscroll-behavior-y:contain}.calendarVirtualExecute099{cursor:pointer}.calendarVirtualExecute099:active{transform:scale(.94)}</style>`};
