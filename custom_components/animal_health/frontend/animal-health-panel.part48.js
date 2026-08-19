Object.assign(T,{
 upcoming096:["Anstehend","Upcoming"],
 currentVersion096:["Aktuelle Version","Current version"],
 openTasks096:["Aufgaben öffnen","Open tasks"],
 openCalendar096:["Kalender öffnen","Open calendar"]
});
const AH096=AnimalHealthPanel.prototype;
const AH096Base={dynamicRelevantCard095:AH096.dynamicRelevantCard095,settingsPage081:AH096.settingsPage081,render:AH096.render};
AH096.dynamicRelevantCard095=function(){
 let html=AH096Base.dynamicRelevantCard095.call(this);
 const oldHead=`<div class="actionNowHead actionNowHead0816"><div><h2>${this.t("todayRelevant0816")}</h2></div></div>`,tasksLabel=esc(this.t("openTasks096")),calendarLabel=esc(this.t("openCalendar096")),links=`<div class="upcomingLinks096" role="toolbar" aria-label="${esc(this.t("upcoming096"))}"><button class="homeIconTool092 upcomingLink096" data-view="tasks" title="${tasksLabel}" aria-label="${tasksLabel}"><ha-icon icon="mdi:clipboard-check"></ha-icon></button><button class="homeIconTool092 upcomingLink096" data-view="calendar" title="${calendarLabel}" aria-label="${calendarLabel}"><ha-icon icon="mdi:calendar"></ha-icon></button></div>`,newHead=`<div class="actionNowHead actionNowHead0816"><div><h2>${this.t("upcoming096")}</h2></div>${links}</div>`;
 return html.replace(oldHead,newHead)
};
AH096.settingsPage081=function(){
 let html=AH096Base.settingsPage081.call(this);
 const marker='<button data-action="open-updates-084">',version=`<p class="currentVersion096"><span>${this.t("currentVersion096")}</span><strong>${esc(this.d?.version||V)}</strong></p>`;
 return html.replace(marker,version+marker)
};
AH096.render=function(){
 AH096Base.render.call(this);
 this.shadowRoot.innerHTML+=`<style>.upcomingLinks096{display:flex;align-items:center;gap:6px}.upcomingLink096{width:40px!important;height:40px!important;min-width:40px!important;padding:0!important}.currentVersion096{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:9px 11px;border-radius:10px;background:var(--secondary-background-color)}.currentVersion096 span{color:var(--secondary-text-color)}.currentVersion096 strong{font-variant-numeric:tabular-nums}@media(max-width:420px){.upcomingLinks096{gap:4px}.upcomingLink096{width:38px!important;height:38px!important;min-width:38px!important}}</style>`
};
