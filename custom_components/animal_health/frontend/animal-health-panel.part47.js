const AH095SeriesFix=AnimalHealthPanel.prototype;
AH095SeriesFix.seriesRelevantItems095=function(today,horizonEnd){
 const result=[],todayKey=this.dateKey0815(today),endKey=this.dateKey0815(horizonEnd);
 for(const task of this.d?.tasks||[]){
  if(!this.isSeriesTask095(task))continue;
  const startKey=String(task.start_date||"").slice(0,10),taskEnd=String(task.end_date||"").slice(0,10);if(startKey&&startKey>endKey)continue;if(taskEnd&&taskEnd<todayKey)continue;
  const taskOccurrences=(this.d?.occurrences||[]).filter(item=>String(item.task_id)===String(task.id)),pending=taskOccurrences.filter(item=>item.status==="pending").sort((a,b)=>this.occurrenceDate0816(a).localeCompare(this.occurrenceDate0816(b)));
  let occurrence=pending.find(item=>item.is_overdue)||pending.find(item=>{const key=this.occurrenceDate0816(item);return key>=todayKey&&key<=endKey})||null,key=occurrence?this.occurrenceDate0816(occurrence):"";
  if(!key){
   for(let day=new Date(today);day<=horizonEnd;day=this.addDays0815(day,1)){
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
