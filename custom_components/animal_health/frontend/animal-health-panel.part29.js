Object.assign(T,{
 aiBatchWeightDate088:["Gewogen am","Weighed on"],
 aiBatchActualTime088:["Uhrzeit","Time"]
});
const AH088=AnimalHealthPanel.prototype;
const AH088Base={
 ws:AH088.ws,
 aiBatchEntryFields086:AH088.aiBatchEntryFields086,
 aiBatchForm083:AH088.aiBatchForm083
};
AH088.ws=function(type,p={}){
 const routed=type===`${D}/v086/ai/analyze`&&p?.mode==="weight"?`${D}/v083/ai/analyze`:type;
 return AH088Base.ws.call(this,routed,p)
};
AH088.batchActualDateLabel088=function(type){return type==="weight"?"aiBatchWeightDate088":"performed_at"};
AH088.aiBatchEntryFields086=function(entry,index){
 let html=AH088Base.aiBatchEntryFields086.call(this,entry,index),label=this.batchActualDateLabel088(entry?.suggested_record_type||"other");
 html=html.replace(`<span>${this.t("start_date")}</span><input type="date"`,`<span>${this.t(label)}</span><input type="date"`);
 html=html.replace(`<span>${this.t("due_time")}</span><input type="time"`,`<span>${this.t("aiBatchActualTime088")}</span><input type="time"`);
 return html
};
AH088.aiBatchForm083=function(){
 let html=AH088Base.aiBatchForm083.call(this),active=(this.aiBatch083||[]).filter(entry=>entry.status!=="discarded"&&entry.status!=="saved"),types=new Set(active.map(entry=>entry.suggested_record_type||"other")),label=types.size===1&&types.has("weight")?"aiBatchWeightDate088":"performed_at";
 html=html.replace(`<span>${this.t("start_date")}</span><input type="date" data-global-date086`,`<span>${this.t(label)}</span><input type="date" data-global-date086`);
 html=html.replace(`<span>${this.t("due_time")}</span><input type="time" data-global-time086`,`<span>${this.t("aiBatchActualTime088")}</span><input type="time" data-global-time086`);
 return html
};
