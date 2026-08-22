AH013.eventDetail=function(id){
 const event=this.eventById(id);
 let html=AH013Base.eventDetail.call(this,id);
 if(!event)return html;
 if(event.is_deleted)html=html.replace(/<div class="buttons eventActions0817">[\s\S]*?<\/div>/g,"");
 const snapshot=event.data?.medication_snapshot;
 if(snapshot&&event.event_type==="medication"){
  const details=[
   snapshot.active_ingredient?`<div><small>${this.t("activeIngredient013")}</small><b>${esc(snapshot.active_ingredient)}</b></div>`:"",
   snapshot.concentration?`<div><small>${this.t("concentration013")}</small><b>${esc(snapshot.concentration)}</b></div>`:"",
   snapshot.dosage_form?`<div><small>${this.t("dosageForm013")}</small><b>${esc(snapshot.dosage_form)}</b></div>`:""
  ].filter(Boolean).join("");
  if(details)html=html.replace('<div class="eventDetail">',`<div class="eventDetail"><section class="medSnapshot013"><h3>${this.t("medicationHistorySnapshot013")}</h3><div>${details}</div></section>`)
 }
 if(event.is_deleted){
  return html.replace('<div class="eventDetail">',`<div class="eventDetail"><p class="deletedNotice013"><ha-icon icon="mdi:delete-clock-outline"></ha-icon><b>${this.t("deletedEntry013")}</b>${event.deleted_at?` · ${esc(this.fmt(event.deleted_at,true))}`:""}</p>`)
 }
 return html+`<div class="buttons deleteEntryActions013"><button type="button" class="danger013" data-action="delete-event-013" data-id="${esc(event.id)}"><ha-icon icon="mdi:delete-outline"></ha-icon>${this.t("deleteEntry013")}</button></div>`
};
