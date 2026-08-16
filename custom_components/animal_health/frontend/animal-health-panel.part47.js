const AH095SeriesFix=AnimalHealthPanel.prototype;
AH095SeriesFix.seriesRelevantItems095=function(today,_horizonEnd){
 const result=[],todayKey=this.dateKey0815(today);
 for(const task of this.d?.tasks||[]){
  if(!this.isSeriesTask095(task))continue;
  const taskEndKey=String(task.end_date||"").slice(0,10);if(taskEndKey&&taskEndKey<todayKey)continue;
  const taskOccurrences=(this.d?.occurrences||[]).filter(item=>String(item.task_id)===String(task.id)),pending=taskOccurrences.filter(item=>item.status==="pending").sort((a,b)=>this.occurrenceDate0816(a).localeCompare(this.occurrenceDate0816(b)));
  let occurrence=pending.find(item=>item.is_overdue)||pending.find(item=>this.occurrenceDate0816(item)>=todayKey)||null,key=occurrence?this.occurrenceDate0816(occurrence):"";
  if(!key){
   const start=this.utcDate0815(task.start_date)||new Date(today),scanStart=start>today?start:new Date(today),interval=Math.max(1,Number(task.recurrence_interval||1)),type=String(task.recurrence_type||"daily"),span=type==="monthly"?interval*32+35:type==="weekly"?interval*7+8:interval+2,calculatedEnd=this.addDays0815(scanStart,span),taskEnd=taskEndKey?this.utcDate0815(taskEndKey):null,scanEnd=taskEnd&&taskEnd<calculatedEnd?taskEnd:calculatedEnd;
   for(let day=new Date(scanStart);day<=scanEnd;day=this.addDays0815(day,1)){
    const candidate=this.dateKey0815(day);if(!this.taskOccurs0815(task,candidate))continue;
    const existing=taskOccurrences.find(item=>this.occurrenceDate0816(item)===candidate);
    if(existing&&existing.status!=="pending")continue;
    key=candidate;occurrence=existing?.status==="pending"?existing:null;break
   }
  }
  if(!key)continue;result.push({task,key,occurrence,isOverdue:Boolean(occurrence?.is_overdue)})
 }
 return result.sort((a,b)=>(a.isOverdue===b.isOverdue?a.key.localeCompare(b.key):a.isOverdue?-1:1))
};
