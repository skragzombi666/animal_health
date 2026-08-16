Object.assign(T,{
 selectedCount095:["ausgewählt","selected"],
 seriesRelevant095:["Serienelemente","Recurring items"],
 thisWeekRelevant095:["Diese Woche","This week"],
 nextWeekRelevant095:["Nächste Woche","Next week"],
 thisMonthRelevant095:["Diesen Monat","This month"],
 nextMonthRelevant095:["Nächsten Monat","Next month"],
 nothingUpcoming095:["Bis Ende nächsten Monats ist nichts relevant.","Nothing is relevant through the end of next month."],
 nextDue095:["Nächste Fälligkeit","Next due"],
 displaySettings095:["Darstellung","Display"],
 weekStart095:["Wochenanfang","First day of week"],
 weekStartHint095:["Steuert die Wochenabschnitte auf der Startseite und im Kalender.","Controls week sections on the dashboard and in the calendar."],
 weekdayMonday095:["Montag","Monday"],
 weekdayTuesday095:["Dienstag","Tuesday"],
 weekdayWednesday095:["Mittwoch","Wednesday"],
 weekdayThursday095:["Donnerstag","Thursday"],
 weekdayFriday095:["Freitag","Friday"],
 weekdaySaturday095:["Samstag","Saturday"],
 weekdaySunday095:["Sonntag","Sunday"]
});
const AH095=AnimalHealthPanel.prototype;
const AH095Base={overview:AH095.overview,calendar:AH095.calendar,settingsPage081:AH095.settingsPage081,handleClick:AH095.handleClick,handleChange:AH095.handleChange};
AH095.restoreHomeFilters095=function(){
 if(this.homeFilterPrefsLoaded095)return;
 this.homeFilterPrefsLoaded095=true;
 let groups=[],tags=[];
 try{
  const raw=globalThis.localStorage?.getItem("animal_health.home_animal_filters");
  if(raw){
   const saved=JSON.parse(raw);
   if(Array.isArray(saved?.groups))groups=saved.groups.map(String);else if(saved?.group&&saved.group!=="all")groups=[String(saved.group)];
   if(Array.isArray(saved?.tags))tags=saved.tags.map(String);else if(saved?.tag&&saved.tag!=="all")tags=[String(saved.tag)]
  }
 }catch(_error){}
 this.homeGroupFilters095=[...new Set(groups)];this.homeTagFilters095=[...new Set(tags)];this.homeGroupFilter091="all";this.homeTagFilter091="all"
};
AH095.persistHomeFilters095=function(){this.restoreHomeFilters095();try{globalThis.localStorage?.setItem("animal_health.home_animal_filters",JSON.stringify({groups:this.homeGroupFilters095||[],tags:this.homeTagFilters095||[]}))}catch(_error){}};
AH095.homeAnimalFilterState091=function(){
 this.restoreHomeFilters095();
 const groups=this.activeGroups?this.activeGroups():this.features?.groups||[],groupIds=new Set(groups.map(group=>String(group.id))),tags=this.v080?.tags||[],tagIds=new Set(tags.map(tag=>String(tag.id))),groupFilters=[...new Set((this.homeGroupFilters095||[]).map(String).filter(id=>id==="ungrouped"||groupIds.has(id)))],tagFilters=[...new Set((this.homeTagFilters095||[]).map(String).filter(id=>tagIds.has(id)))];
 if(groupFilters.length!==(this.homeGroupFilters095||[]).length||tagFilters.length!==(this.homeTagFilters095||[]).length){this.homeGroupFilters095=groupFilters;this.homeTagFilters095=tagFilters;this.persistHomeFilters095()}
 return{groups,tags,groupFilters,tagFilters,query:String(this.homeAnimalSearch091||"").trim().toLocaleLowerCase()}
};
AH095.resetHomeFilters093=function(){this.homeGroupFilters095=[];this.homeTagFilters095=[];this.homeGroupFilter091="all";this.homeTagFilter091="all";this.homeAnimalSearch091="";this.homeFilterPanel091=null;this.homeSearchOpen091=false;this.persistHomeFilters095()};
AH095.homeAnimalOverview091=function(){
 const state=this.homeAnimalFilterState091(),all=(this.d?.animals||[]).filter(animal=>!animal.is_archived),groupSet=new Set(state.groupFilters),tagSet=new Set(state.tagFilters),matches=animal=>{
  const groupId=animal.group_id?String(animal.group_id):"ungrouped",groupMatch=!groupSet.size||groupSet.has(groupId),animalTags=(animal.tag_ids||[]).map(String),tagMatch=!tagSet.size||animalTags.some(id=>tagSet.has(id));
  if(!groupMatch||!tagMatch)return false;
  if(state.query&&![animal.name,animal.species,animal.breed,animal.color,animal.group_name,...(animal.tags||[]).map(tag=>tag.name)].some(value=>String(value||"").toLocaleLowerCase().includes(state.query)))return false;
  return true
 },animals=all.filter(matches).sort((a,b)=>String(a.name||"").localeCompare(String(b.name||""),undefined,{sensitivity:"base"})),groupAll=!state.groupFilters.length,tagAll=!state.tagFilters.length;
 const groupPanel=this.homeFilterPanel091==="group"?`<div class="homeFilterOptions091 homeFilterOptions092" role="group" aria-label="${esc(this.t("filterGroups091"))}">${this.homeFilterOption092("home-group-select-091","all",this.t("allAnimals"),groupAll)}${this.homeFilterOption092("home-group-select-091","ungrouped",this.t("ungrouped"),groupSet.has("ungrouped"))}${state.groups.map(group=>this.homeFilterOption092("home-group-select-091",group.id,group.name,groupSet.has(String(group.id)))).join("")}</div>`:"";
 const tagPanel=this.homeFilterPanel091==="tag"?`<div class="homeFilterOptions091 homeFilterOptions092" role="group" aria-label="${esc(this.t("filterTags091"))}">${this.homeFilterOption092("home-tag-select-091","all",this.t("allTags"),tagAll)}${state.tags.map(tag=>this.homeFilterOption092("home-tag-select-091",tag.id,`#${tag.name}`,tagSet.has(String(tag.id)))).join("")}</div>`:"";
 const search=this.homeSearchOpen091?`<label class="homeAnimalSearch091"><ha-icon icon="mdi:magnify"></ha-icon><input data-home-search091 value="${esc(this.homeAnimalSearch091||"")}" placeholder="${this.t("search")}" autocomplete="off"></label>`:"",ungrouped=animals.filter(animal=>!animal.group_id),sections=[];
 if((groupAll||groupSet.has("ungrouped"))&&ungrouped.length)sections.push(`<div class="homeUngroupedTiles092" aria-label="${esc(this.t("ungrouped"))}"><div class="homeAnimalTiles091">${ungrouped.map(animal=>this.homeAnimalTile091(animal)).join("")}</div></div>`);
 for(const group of state.groups){if(!groupAll&&!groupSet.has(String(group.id)))continue;const members=animals.filter(animal=>String(animal.group_id)===String(group.id));if(members.length)sections.push(this.homeAnimalGroup091(group.id,group.name,members))}
 const groupLabel=groupAll?this.t("allAnimals"):`${state.groupFilters.length} ${this.t("selectedCount095")}`,tagLabel=tagAll?this.t("allTags"):`${state.tagFilters.length} ${this.t("selectedCount095")}`,searchLabel=this.t("searchAnimals091"),filtered=!groupAll||!tagAll||Boolean(state.query),resetLabel=esc(this.t("resetHomeFilters093")),reset=filtered?`<button class="homeIconTool092 homeFilterReset093" data-action="home-filter-reset-093" title="${resetLabel}" aria-label="${resetLabel}"><ha-icon icon="mdi:close-circle-outline"></ha-icon></button>`:"";
 return`<section class="card homeAnimalsCard091 homeAnimalsCard092"><div class="homeAnimalsHead092"><h2>${this.t("animals")}</h2><div class="homeAnimalTools092" role="toolbar">${reset}<button class="homeIconTool092 ${!groupAll||this.homeFilterPanel091==="group"?"on":""}" data-action="home-group-toggle-091" title="${esc(`${this.t("filterGroups091")}: ${groupLabel}`)}" aria-label="${esc(`${this.t("filterGroups091")}: ${groupLabel}`)}" aria-expanded="${this.homeFilterPanel091==="group"?"true":"false"}"><ha-icon icon="mdi:account-group-outline"></ha-icon></button><button class="homeIconTool092 ${!tagAll||this.homeFilterPanel091==="tag"?"on":""}" data-action="home-tag-toggle-091" title="${esc(`${this.t("filterTags091")}: ${tagLabel}`)}" aria-label="${esc(`${this.t("filterTags091")}: ${tagLabel}`)}" aria-expanded="${this.homeFilterPanel091==="tag"?"true":"false"}"><ha-icon icon="mdi:tag-multiple-outline"></ha-icon></button><button class="homeIconTool092 ${this.homeSearchOpen091||state.query?"on":""}" data-action="home-search-toggle-091" title="${esc(searchLabel)}" aria-label="${esc(searchLabel)}" aria-expanded="${this.homeSearchOpen091?"true":"false"}"><ha-icon icon="mdi:magnify"></ha-icon></button></div></div>${groupPanel}${tagPanel}${search}<div class="homeAnimalGroups091 homeAnimalGroups092">${sections.join("")||this.empty("noAnimals")}</div></section>`
};
AH095.weekStartKeys095=["monday","tuesday","wednesday","thursday","friday","saturday","sunday"];
AH095.weekStart095=function(){if(this.weekStartState095)return this.weekStartState095;let value="monday";try{const stored=globalThis.localStorage?.getItem("animal_health.week_start");if(this.weekStartKeys095.includes(stored))value=stored}catch(_error){}this.weekStartState095=value;return value};
AH095.setWeekStart095=function(value){const normalized=this.weekStartKeys095.includes(value)?value:"monday";this.weekStartState095=normalized;try{globalThis.localStorage?.setItem("animal_health.week_start",normalized)}catch(_error){}};
AH095.weekStartIndex095=function(){return{monday:1,tuesday:2,wednesday:3,thursday:4,friday:5,saturday:6,sunday:0}[this.weekStart095()]??1};
AH095.weekBounds095=function(day){const offset=(day.getUTCDay()-this.weekStartIndex095()+7)%7,start=this.addDays0815(day,-offset);return{start,end:this.addDays0815(start,6)}};
AH095.settingsPage081=function(){
 const html=AH095Base.settingsPage081.call(this),value=this.weekStart095(),options=this.weekStartKeys095.map(key=>`<option value="${key}" ${value===key?"selected":""}>${this.t(`weekday${key[0].toUpperCase()+key.slice(1)}095`)}</option>`).join(""),field=`<label class="wide weekStartSetting095"><span>${this.t("weekStart095")}</span><select data-week-start095>${options}</select><small>${this.t("weekStartHint095")}</small></label>`;
 return`${html}<section class="card displaySettings095"><h2>${this.t("displaySettings095")}</h2>${field}</section>`
};
AH095.isSeriesTask095=function(task){return Boolean(task?.is_active)&&String(task?.recurrence_type||"once")!=="once"};
AH095.seriesRelevantItems095=function(today,horizonEnd){
 const result=[],todayKey=this.dateKey0815(today),endKey=this.dateKey0815(horizonEnd);
 for(const task of this.d?.tasks||[]){
  if(!this.isSeriesTask095(task))continue;
  const startKey=String(task.start_date||"").slice(0,10),taskEnd=String(task.end_date||"").slice(0,10);if(startKey&&startKey>endKey)continue;if(taskEnd&&taskEnd<todayKey)continue;
  const pending=(this.d?.occurrences||[]).filter(item=>item.status==="pending"&&String(item.task_id)===String(task.id)).sort((a,b)=>this.occurrenceDate0816(a).localeCompare(this.occurrenceDate0816(b)));
  let occurrence=pending.find(item=>item.is_overdue)||pending.find(item=>{const key=this.occurrenceDate0816(item);return key>=todayKey&&key<=endKey})||null,key=occurrence?this.occurrenceDate0816(occurrence):"";
  if(!key){for(let day=new Date(today);day<=horizonEnd;day=this.addDays0815(day,1)){const candidate=this.dateKey0815(day);if(this.taskOccurs0815(task,candidate)){key=candidate;break}}}
  if(!key)continue;result.push({task,key,occurrence,isOverdue:Boolean(occurrence?.is_overdue)})
 }
 return result.sort((a,b)=>(a.isOverdue===b.isOverdue?a.key.localeCompare(b.key):a.isOverdue?-1:1))
};
AH095.recurrenceLabel095=function(task){const type=String(task?.recurrence_type||"once"),interval=Math.max(1,Number(task?.recurrence_interval||1));if(interval===1)return this.l(type);const units=this.lang()?{daily:"days",weekly:"weeks",monthly:"months"}:{daily:"Tage",weekly:"Wochen",monthly:"Monate"};return this.lang()?`Every ${interval} ${units[type]||type}`:`Alle ${interval} ${units[type]||type}`};
AH095.seriesRow095=function(item){const task=item.task,target=task.animal_name||task.group_name||this.t("general"),recurrence=this.recurrenceLabel095(task),date=item.key?`${this.t("nextDue095")}: ${this.fmt(item.key)}`:"",canExecute=Boolean(item.occurrence&&(item.isOverdue||item.key===String(this.d?.today||""))),urgent=item.isOverdue?" urgent":"";return`<div class="nextTask seriesTask095${urgent}"><div class="nextTaskIcon"><ha-icon icon="${I[task.task_kind]||I.reminder}"></ha-icon></div><div class="nextTaskMain static0816"><b>${esc(task.title)}</b><span>${esc(target)} · ${esc(recurrence)}${date?` · ${esc(date)}`:""}</span></div>${canExecute?`<button class="primary compactExecute" data-action="execute" data-id="${esc(item.occurrence.id)}">${this.t("execute")}</button>`:""}</div>`};
AH095.oneOffVirtual095=function(start,end){return this.virtualRelevantItems0816(start,end).filter(item=>String(item.task?.recurrence_type||"once")==="once")};
AH095.todayOneOff095=function(today){
 const items=this.oneOffVirtual095(today,today),seen=new Set(items.map(item=>`${item.task.id}|${item.key}`));
 for(const occurrence of(this.d?.occurrences||[]).filter(item=>item.status==="pending"&&item.is_overdue)){const task=(this.d?.tasks||[]).find(candidate=>String(candidate.id)===String(occurrence.task_id));if(!task||String(task.recurrence_type||"once")!=="once")continue;const key=this.occurrenceDate0816(occurrence),id=`${task.id}|${key}`;if(seen.has(id))continue;seen.add(id);items.unshift({task,key,occurrence,isOverdue:true})}
 return items
};
AH095.dynamicRelevantGroups095=function(){
 const today=this.utcDate0815(this.d?.today)||new Date(),thisWeek=this.weekBounds095(today),nextWeekStart=this.addDays0815(thisWeek.end,1),nextWeekEnd=this.addDays0815(nextWeekStart,6),nextMonthEnd=new Date(Date.UTC(today.getUTCFullYear(),today.getUTCMonth()+2,0)),series=this.seriesRelevantItems095(today,nextMonthEnd),buckets={today:this.todayOneOff095(today),thisWeek:[],nextWeek:[],thisMonth:[],nextMonth:[]};
 for(let day=this.addDays0815(today,1);day<=nextMonthEnd;day=this.addDays0815(day,1)){
  const items=this.oneOffVirtual095(day,day);if(!items.length)continue;
  if(day<=thisWeek.end)buckets.thisWeek.push(...items);else if(day>=nextWeekStart&&day<=nextWeekEnd)buckets.nextWeek.push(...items);else if(day.getUTCFullYear()===today.getUTCFullYear()&&day.getUTCMonth()===today.getUTCMonth())buckets.thisMonth.push(...items);else buckets.nextMonth.push(...items)
 }
 return[{label:this.t("seriesRelevant095"),items:series,series:true},{label:this.t("scopeToday0816"),items:buckets.today},{label:this.t("thisWeekRelevant095"),items:buckets.thisWeek},{label:this.t("nextWeekRelevant095"),items:buckets.nextWeek},{label:this.t("thisMonthRelevant095"),items:buckets.thisMonth},{label:this.t("nextMonthRelevant095"),items:buckets.nextMonth}].filter(group=>group.items.length)
};
AH095.dynamicRelevantCard095=function(){const groups=this.dynamicRelevantGroups095(),urgent=groups.some(group=>group.items.some(item=>item.isOverdue)),content=groups.length?groups.map(group=>`<div class="relevantGroup095 ${group.series?"seriesGroup095":""}"><div class="relevantGroupHead095"><h3>${esc(group.label)}</h3><span>${group.items.length}</span></div>${group.items.map(item=>group.series?this.seriesRow095(item):this.relevantRow0816(item)).join("")}</div>`).join(""):`<div class="nothingDue"><ha-icon icon="mdi:check-circle-outline"></ha-icon><span>${this.t("nothingUpcoming095")}</span></div>`;return`<section class="actionNow actionNow0816 actionNow095 ${urgent?"hasUrgent":""}"><div class="actionNowHead actionNowHead0816"><div><h2>${this.t("todayRelevant0816")}</h2></div></div>${content}</section>`};
AH095.overview=function(){let html=AH095Base.overview.call(this);html=html.replace(/<section class="actionNow[^"]*"[\s\S]*?<\/section>/,this.dynamicRelevantCard095());return html+`<style>.actionNow095 .actionNowHead0816{margin-bottom:2px}.relevantGroup095{padding-top:10px;margin-top:8px;border-top:1px solid var(--divider-color)}.relevantGroup095:first-of-type{border-top:0;margin-top:0}.relevantGroupHead095{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:2px 0 3px}.relevantGroupHead095 h3{margin:0;font-size:.88rem;color:var(--secondary-text-color);font-weight:700}.relevantGroupHead095 span{display:grid;place-items:center;min-width:24px;height:24px;padding:0 7px;border-radius:12px;background:var(--secondary-background-color);font-size:.76rem;color:var(--secondary-text-color)}.seriesGroup095 .relevantGroupHead095 h3{color:var(--primary-color)}.seriesTask095 .nextTaskIcon{color:var(--primary-color)}.displaySettings095 .weekStartSetting095{display:flex;flex-direction:column;gap:5px}.displaySettings095 small{color:var(--secondary-text-color)}@media(max-width:520px){.relevantGroup095{padding-top:8px;margin-top:6px}}</style>`};
AH095.calendar=function(){
 const monthStart=this.calendarMonthStart0816(),today=this.utcDate0815(this.d?.today)||new Date(),weekStart=this.weekStartIndex095(),offset=(monthStart.getUTCDay()-weekStart+7)%7,gridStart=this.addDays0815(monthStart,-offset),locale=this.lang()?"en-GB":"de-CH",monthLabel=new Intl.DateTimeFormat(locale,{month:"long",year:"numeric",timeZone:"UTC"}).format(monthStart),sunday=new Date(Date.UTC(2026,7,9)),weekdays=Array.from({length:7},(_,index)=>new Intl.DateTimeFormat(locale,{weekday:"short",timeZone:"UTC"}).format(this.addDays0815(sunday,(weekStart+index)%7))),tasks=this.calendarFilteredTasks0816(),todayKey=this.dateKey0815(today),kindValue=this.calendarKind0816||"all",animalValue=this.calendarAnimal0816||"all",kinds=[...new Set((this.d?.tasks||[]).map(task=>String(task.task_kind||"reminder")))].sort((a,b)=>this.l(a).localeCompare(this.l(b))),animals=[...(this.d?.animals||[])].sort((a,b)=>String(a.name||"").localeCompare(String(b.name||"")));
 const cells=Array.from({length:42},(_,index)=>{const day=this.addDays0815(gridStart,index),key=this.dateKey0815(day),dim=day.getUTCMonth()!==monthStart.getUTCMonth(),items=tasks.filter(task=>this.taskOccurs0815(task,key)),icons=items.slice(0,8).map(task=>{const target=task.animal_name||task.group_name||this.t("general"),title=[task.title,target].filter(Boolean).join(" · ");return`<span class="calendarIcon0816" title="${esc(title)}"><ha-icon icon="${I[task.task_kind]||I.reminder}"></ha-icon></span>`}).join("");return`<div class="calendarCell0816 ${dim?"dim0816":""} ${key===todayKey?"today0816":""}"><time>${day.getUTCDate()}</time><div class="calendarIcons0816">${icons}${items.length>8?`<small>+${items.length-8}</small>`:""}</div></div>`}).join("");
 return`${this.heading("calendar")}<section class="card calendarCard0816"><div class="calendarToolbar0816"><div class="calendarNav0816"><button data-action="calendar-prev-0816" title="${this.t("calendarPrevious0816")}"><ha-icon icon="mdi:chevron-left"></ha-icon></button><button data-action="calendar-today-0816">${this.t("calendarToday0815")}</button><button data-action="calendar-next-0816" title="${this.t("calendarNext0816")}"><ha-icon icon="mdi:chevron-right"></ha-icon></button></div><h2>${esc(monthLabel)}</h2><div class="calendarFilters0816"><label><span>${this.t("calendarEntries0816")}</span><select data-calendar-kind><option value="all" ${kindValue==="all"?"selected":""}>${this.t("allEntryTypes0816")}</option>${kinds.map(kind=>`<option value="${esc(kind)}" ${kindValue===kind?"selected":""}>${esc(this.l(kind))}</option>`).join("")}</select></label><label><span>${this.t("calendarAnimals0816")}</span><select data-calendar-animal><option value="all" ${animalValue==="all"?"selected":""}>${this.t("allAnimals0816")}</option>${animals.map(animal=>`<option value="${esc(animal.id)}" ${animalValue===String(animal.id)?"selected":""}>${esc(animal.name)}</option>`).join("")}</select></label></div></div><div class="calendarWeekdays0816">${weekdays.map(day=>`<b>${esc(day)}</b>`).join("")}</div><div class="calendarGrid0816">${cells}</div></section><style>.calendarToolbar0816{display:grid;grid-template-columns:auto 1fr auto;align-items:end;gap:14px;margin-bottom:12px}.calendarToolbar0816 h2{text-align:center;margin:0 0 5px}.calendarNav0816{display:flex;gap:5px;align-items:center}.calendarNav0816 button{padding:7px 9px}.calendarFilters0816{display:flex;gap:8px;align-items:end;justify-content:flex-end}.calendarFilters0816 label{display:flex;flex-direction:column;gap:3px;min-width:145px}.calendarFilters0816 label span{font-size:.72rem;color:var(--secondary-text-color)}.calendarFilters0816 select{min-height:35px}.calendarWeekdays0816,.calendarGrid0816{display:grid;grid-template-columns:repeat(7,minmax(0,1fr))}.calendarWeekdays0816 b{text-align:center;padding:5px;font-size:.78rem;opacity:.65}.calendarCell0816{min-height:76px;padding:6px;border:1px solid var(--divider-color);display:flex;flex-direction:column;gap:5px}.calendarCell0816.dim0816{opacity:.42}.calendarCell0816.today0816{box-shadow:inset 0 0 0 2px var(--primary-color)}.calendarCell0816 time{font-weight:600}.calendarIcons0816{display:flex;flex-wrap:wrap;gap:3px}.calendarIcon0816{padding:3px;border-radius:5px;background:var(--secondary-background-color)}@media(max-width:760px){.calendarToolbar0816{grid-template-columns:1fr}.calendarToolbar0816 h2{grid-row:1;text-align:left}.calendarNav0816{grid-row:2}.calendarFilters0816{grid-row:3;justify-content:stretch}.calendarFilters0816 label{flex:1;min-width:0}.calendarCell0816{min-height:56px;padding:3px}.calendarIcon0816{padding:1px}.calendarIcon0816 ha-icon{width:18px;height:18px}}</style>`
};
AH095.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset?.action),action=button?.dataset?.action,id=String(button?.dataset?.id||"");
 if(action==="home-filter-reset-093"){this.resetHomeFilters093();this.render();return}
 if(action==="home-group-select-091"){this.restoreHomeFilters095();if(id==="all")this.homeGroupFilters095=[];else{const set=new Set(this.homeGroupFilters095||[]);set.has(id)?set.delete(id):set.add(id);this.homeGroupFilters095=[...set]}this.persistHomeFilters095();this.render();return}
 if(action==="home-tag-select-091"){this.restoreHomeFilters095();if(id==="all")this.homeTagFilters095=[];else{const set=new Set(this.homeTagFilters095||[]);set.has(id)?set.delete(id):set.add(id);this.homeTagFilters095=[...set]}this.persistHomeFilters095();this.render();return}
 return AH095Base.handleClick.call(this,event)
};
AH095.handleChange=function(event){const input=event.composedPath()[0];if(input?.dataset&&"weekStart095" in input.dataset){this.setWeekStart095(input.value);this.render();return}return AH095Base.handleChange.call(this,event)};
