const AH023Daily=AnimalHealthPanel.prototype;
const AH023DailyBase={timelineDaySections023:AH023Daily.timelineDaySections023};
AH023Daily.activeEpisodesForTimeline023=function(source){
 const today=this.d?.today||this.nowTemporal023(false).date,q=String(this.filter||"").trim().toLocaleLowerCase(),animalId=this.view==="animal-detail"?String(this.detail?.animal?.id||""):"";
 return(this.v0923?.episodes||[]).filter(episode=>{
  if(episode.state!=="active"||String(episode.started_date||"")>today)return false;
  if(animalId&&String(episode.animal_id)!==animalId)return false;
  if(q&&!`${episode.symptom||""} ${episode.animal_name||""} ${this.l(episode.latest_severity||"")}`.toLocaleLowerCase().includes(q))return false;
  return true
 })
};
AH023Daily.episodeCarryEvent023=function(episode,today){return{id:String(episode.start_event_id||`episode-${episode.id}`),animal_id:episode.animal_id,animal_name:episode.animal_name,event_type:"symptom",occurred_at:`${today}T12:00:00`,title:episode.symptom,notes:null,data:{symptom_episode_id:episode.id,symptom_episode_action:"start",symptom_episode_state:"active",severity:episode.latest_severity,time_precision:"date",occurred_date:today,episode_carry_forward:true}}};
AH023Daily.timelineDaySections023=function(source){
 let html=AH023DailyBase.timelineDaySections023.call(this,source),today=this.d?.today||this.nowTemporal023(false).date,episodes=this.activeEpisodesForTimeline023(source),sourceList=source||[];
 if(!episodes.length)return html;
 const alreadyShown=new Set(sourceList.filter(event=>this.dayKey023(event)===today&&event?.data?.symptom_episode_id).map(event=>String(event.data.symptom_episode_id))),carry=episodes.filter(episode=>!alreadyShown.has(String(episode.id))).map(episode=>this.timelineEntry023(this.episodeCarryEvent023(episode,today))).join("");
 if(!carry)return html;
 const label=`${this.t("today023")} · ${this.dateLabel023(today)}`,header=`<div class="dayHeader023"><strong>${esc(label)}</strong><span>${episodes.length} ${esc(this.t("currentSymptoms023"))}</span></div>`,sectionStart=`<section class="timelineDay023">${header}<div class="timelineDayRows023">`;
 const marker=`<section class="timelineDay023"><div class="dayHeader023"><strong>${esc(label)}</strong>`;
 const start=html.indexOf(marker);
 if(start<0)return`${sectionStart}${carry}</div></section>${html}`;
 const rows=html.indexOf('<div class="timelineDayRows023">',start);
 if(rows<0)return html;
 const insert=rows+'<div class="timelineDayRows023">'.length;
 return html.slice(0,insert)+carry+html.slice(insert)
};
