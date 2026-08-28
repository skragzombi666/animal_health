Object.assign(T,{
 statusEdit024:["Statusänderung bearbeiten","Edit status change"],
 newStatus024:["Status","Status"]
});
const AH024Final=AnimalHealthPanel.prototype;
const AH024FinalBase={
 medicationGroupKey024:AH024Final.medicationGroupKey024,
 eventDetail:AH024Final.eventDetail,
 eventEditForm024:AH024Final.eventEditForm024,
 form:AH024Final.form,
 eventSummary021:AH024Final.eventSummary021,
 handleClick:AH024Final.handleClick,
 handleSubmit:AH024Final.handleSubmit
};
AH024Final.medicationGroupKey024=function(event){
 if(event?.event_type!=="medication")return"";
 if(event?.data?.treatment_execution_id||event?.data?.treatment_plan_id)return"";
 if(event?.data?.time_precision==="date")return"";
 const batch=String(event?.data?.batch_id||""),mode=String(event?.data?.entry_mode||"");
 if(batch&&mode==="batch")return`batch:${batch}`;
 const animal=String(event?.animal_id||""),when=String(event?.occurred_at||"");
 return animal&&when?`time:${animal}:${when}`:""
};
AH024Final.eventSummary021=function(event){const base=AH024FinalBase.eventSummary021?AH024FinalBase.eventSummary021.call(this,event):[this.eventTitle?.(event)||event?.title,event?.value!=null?`${this.num(event.value)} ${this.l(event.unit||"")}`:""].filter(Boolean).join(" · "),equivalent=this.activeIngredientEquivalent024?.(event);return equivalent?`${base} · ${this.t("equivalentActive024")} ${equivalent}`:base};
AH024Final.statusEditForm024=function(){const event=this.eventById?.(this.modal?.eventId);if(!event)return this.empty("noEvents");const when=this.localEventFields015?.(event)||{date:String(event.occurred_at||"").slice(0,10),time:""},statuses=this.c?.animal_statuses||["active","missing","sold","rehomed","deceased","other_departure"],current=String(event.data?.new_status||"");return`<h2><ha-icon icon="mdi:pencil-outline"></ha-icon>${this.t("statusEdit024")}</h2><form data-form="status-edit-024"><input type="hidden" name="event_id" value="${esc(event.id)}">${this.sel("newStatus024","new_status",statuses,current,"required")}${this.temporalPair023("occurred_date","occurred_time",this.t("occurred_at"),when.date,when.time)}${this.area("notes","notes",event.notes||"")}${this.fileFields()}${this.buttons()}</form>`};
AH024Final.eventEditForm024=function(){const event=this.eventById?.(this.modal?.eventId);if(!event)return this.empty("noEvents");const type=this.entryTypeForEvent024?.(event),known=Boolean(type||event.event_type==="weight");if(known)return AH024FinalBase.eventEditForm024.call(this);const when=this.localEventFields015?.(event)||{date:String(event.occurred_at||"").slice(0,10),time:""};return`<h2><ha-icon icon="mdi:pencil-outline"></ha-icon>${this.t("editEntry024")}</h2><form data-form="event-edit-024"><input type="hidden" name="event_id" value="${esc(event.id)}">${this.field("title","title","text",event.title||"","required")}${this.temporalPair023("occurred_date","occurred_time",this.t("occurred_at"),when.date,when.time)}${this.area("notes","notes",event.notes||"")}${this.fileFields()}${this.buttons()}</form>`};
AH024Final.form=function(){if(this.modal?.type==="status-edit-024")return this.statusEditForm024();return AH024FinalBase.form.call(this)};
AH024Final.eventDetail=function(id){const event=this.eventById?.(id),html=AH024FinalBase.eventDetail.call(this,id);if(!event||event.is_deleted||event.event_type!=="status_change")return html;if(html.includes('data-action="status-edit-024"'))return html;return`${html}<div class="buttons eventActions024"><button type="button" data-action="status-edit-024" data-id="${esc(event.id)}"><ha-icon icon="mdi:pencil-outline"></ha-icon><span class="actionLabel024">${this.t("statusEdit024")}</span></button></div>`};
AH024Final.handleClick=async function(event){const button=event.composedPath().find(node=>node?.dataset?.action),action=button?.dataset?.action;if(action==="status-edit-024"){this.modal={type:"status-edit-024",eventId:button.dataset.id};this.render();return}return AH024FinalBase.handleClick.call(this,event)};
AH024Final.handleSubmit=async function(event){const form=event.composedPath().find(node=>node?.tagName==="FORM");if(form?.dataset.form!=="status-edit-024")return AH024FinalBase.handleSubmit.call(this,event);event.preventDefault();const values=data(form),old=this.eventById?.(values.event_id);try{this.busy=true;this.render();const result=await this.ws(`${D}/v0924/status/edit`,{event_id:values.event_id,new_status:values.new_status,occurred_date:values.occurred_date,...(values.occurred_time?{occurred_time:values.occurred_time}:{}),...(values.notes?{notes:values.notes}:{})});if(this.filesFrom(form).length&&old)await this.uploadFiles(form,old.animal_id,result.id);this.busy=false;await this.after()}catch(error){this.busy=false;this.notify(`${this.t("failed")}: ${error?.message||error}`,true);this.render()}return};
