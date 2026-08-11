const AH083Date=AnimalHealthPanel.prototype;
const AH083DateField=AH083Date.fieldBatch083;
const AH083DateSave=AH083Date.saveAIEntry083;
AH083Date.fieldBatch083=function(label,field,value="",type="text"){
 if(field==="occurred_at"&&type==="datetime-local"&&/^\d{4}-\d{2}-\d{2}$/.test(String(value||"")))type="date";
 return AH083DateField.call(this,label,field,value,type)
};
AH083Date.saveAIEntry083=async function(entry){
 if((entry?.suggested_record_type||"other")!=="weight")return AH083DateSave.call(this,entry);
 const animal=this.animal(entry.animal_id||entry.matched_animal_id);if(!animal?.device_id)throw Error(this.t("selectOne"));
 const payload={device_id:animal.device_id,weight:Number(entry.weight),weight_unit:entry.weight_unit},occurred=String(entry.occurred_at||entry.document_date||"").trim();
 if(occurred)payload.occurred_at=occurred;
 if(entry.notes)payload.notes=entry.notes;
 return this.svc("record_weight",payload,true)
};
