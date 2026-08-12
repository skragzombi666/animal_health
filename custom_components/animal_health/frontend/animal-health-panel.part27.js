const AH086FIX=AnimalHealthPanel.prototype;
AH086FIX.batchDateTime086=function(entry){
 const occurred=String(entry?.occurred_at||""),parts=occurred.includes("T")?occurred.split("T"):[];
 return{
  date:String(entry?.document_date||entry?.scheduled_date||parts[0]||"").slice(0,10),
  time:String(entry?.due_time||parts[1]||"").slice(0,5)
 }
};
