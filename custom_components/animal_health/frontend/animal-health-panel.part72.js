const AH020Link=AnimalHealthPanel.prototype;
const AH020LinkBase={eventCompact0817:AH020Link.eventCompact0817};
AH020Link.treatmentName020=function(value){return this.norm083?this.norm083(value):String(value||"").trim().toLocaleLowerCase()};
AH020Link.sameTreatmentOccurrence020=function(left,right){return String(left?.animal_id||"")===String(right?.animal_id||"")&&String(left?.occurred_at||"")===String(right?.occurred_at||"")};
AH020Link.treatmentParentMatches020=function(parent,child){
 if(parent?.event_type!=="treatment"||!this.sameTreatmentOccurrence020(parent,child))return false;
 const childPlanId=this.treatmentPlanId020(child);if(childPlanId==null)return false;
 const parentPlanId=this.treatmentPlanId020(parent);
 if(parentPlanId!=null)return String(parentPlanId)===String(childPlanId);
 const childPlanName=child?.data?.treatment_plan_name||child?.data?.task_execution?.treatment_plan_name||child?.data?.task_execution?.planned?.treatment_plan_name||"";
 return Boolean(childPlanName&&this.treatmentName020(parent?.title)===this.treatmentName020(childPlanName))
};
AH020Link.treatmentSummaryForChild020=function(event,list=null){
 if(!event||event.event_type==="treatment"||this.treatmentPlanId020(event)==null)return null;
 const source=list||this.eventSource020(event);
 return(source||[]).find(parent=>this.treatmentParentMatches020(parent,event))||null
};
AH020Link.treatmentChildren020=function(summary,list=null){
 if(!summary||summary.event_type!=="treatment")return[];
 const source=list||this.eventSource020(summary),parentPlanId=this.treatmentPlanId020(summary),parentName=this.treatmentName020(summary.title);
 return(source||[]).filter(child=>{
  if(child?.event_type==="treatment"||!this.sameTreatmentOccurrence020(summary,child))return false;
  const childPlanId=this.treatmentPlanId020(child);if(childPlanId==null)return false;
  if(parentPlanId!=null)return String(parentPlanId)===String(childPlanId);
  const childPlanName=child?.data?.treatment_plan_name||child?.data?.task_execution?.treatment_plan_name||child?.data?.task_execution?.planned?.treatment_plan_name||"";
  return Boolean(childPlanName&&parentName===this.treatmentName020(childPlanName))
 })
};
AH020Link.eventCompact0817=function(event){
 const list=this.eventSource020(event);
 if(this.treatmentSummaryForChild020(event,list))return"";
 if(event?.event_type==="treatment"&&(this.treatmentPlanId020(event)!=null||this.treatmentChildren020(event,list).length))return this.treatmentSummaryCompact020(event);
 return AH020LinkBase.eventCompact0817.call(this,event)
};
