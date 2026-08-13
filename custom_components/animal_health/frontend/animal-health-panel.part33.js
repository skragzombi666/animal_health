Object.assign(T,{
 aiBatchFuzzyAnimal0813:["Tiername ähnlich erkannt – Zuordnung prüfen","Animal name matched approximately – verify assignment"]
});
const AH0813=AnimalHealthPanel.prototype;
const AH0813Base={
 handleSubmit:AH0813.handleSubmit,
 handleChange:AH0813.handleChange,
 handleInput:AH0813.handleInput,
 updateBatchField083:AH0813.updateBatchField083
};
AH0813.normAnimalName0813=function(value){
 return String(value||"").normalize("NFKD").replace(/[\u0300-\u036f]/g,"").toLocaleLowerCase().replace(/[^a-z0-9]+/g,"")
};
AH0813.nameDistance0813=function(left,right){
 const a=this.normAnimalName0813(left),b=this.normAnimalName0813(right);if(a===b)return 0;if(!a.length)return b.length;if(!b.length)return a.length;
 const previous=Array.from({length:b.length+1},(_,index)=>index),current=new Array(b.length+1);
 for(let i=1;i<=a.length;i++){
  current[0]=i;
  for(let j=1;j<=b.length;j++)current[j]=Math.min(current[j-1]+1,previous[j]+1,previous[j-1]+(a[i-1]===b[j-1]?0:1));
  for(let j=0;j<=b.length;j++)previous[j]=current[j]
 }
 return previous[b.length]
};
AH0813.fuzzyAnimalMatch0813=function(name){
 const needle=this.normAnimalName0813(name);if(!needle)return null;
 const animals=(this.d?.animals||[]).filter(animal=>!animal.is_archived&&this.normAnimalName0813(animal.name));
 const exact=animals.find(animal=>this.normAnimalName0813(animal.name)===needle);if(exact)return{animal:exact,distance:0,approximate:false};
 const ranked=animals.map(animal=>({animal,distance:this.nameDistance0813(name,animal.name),target:this.normAnimalName0813(animal.name)})).sort((a,b)=>a.distance-b.distance||a.target.length-b.target.length);
 if(!ranked.length)return null;const best=ranked[0],second=ranked[1],shortest=Math.min(needle.length,best.target.length),longest=Math.max(needle.length,best.target.length),maxDistance=shortest>=7?2:shortest>=5?1:0,similarity=longest?1-best.distance/longest:0;
 if(!maxDistance||best.distance>maxDistance||similarity<.75)return null;
 if(second&&second.distance<=best.distance+1)return null;
 return{animal:best.animal,distance:best.distance,approximate:true}
};
AH0813.prepareBatchNameMatches0813=function(){
 const entries=this.aiBatch083;if(!Array.isArray(entries)||!entries.length)return false;let changed=false;
 for(const entry of entries){
  if(!entry||entry.status==="saved"||entry.status==="discarded"||String(entry.matched_animal_id||"").trim()||String(entry.animal_id||"").trim())continue;
  const match=this.fuzzyAnimalMatch0813(entry.animal_name);if(!match)continue;
  entry.matched_animal_id=match.animal.id;entry.animal_id=match.animal.id;changed=true;
  if(match.approximate){
   entry.name_match_approximate0813=true;
   const warning=`${this.t("aiBatchFuzzyAnimal0813")}: ${match.animal.name}`;
   if(!String(entry.uncertainties||"").includes(warning))entry.uncertainties=[entry.uncertainties,warning].filter(Boolean).join("; ")
  }
 }
 return changed
};
AH0813.updateBatchField083=function(input){
 if(!input?.dataset?.batchField083||!this.aiBatch083?.length)return;
 const index=Number(input.dataset.batchIndex086??this.aiBatchIndex083??0),entry=this.aiBatch083[index];if(!entry)return;
 if(input.dataset.batchField083==="animal_id"){
  entry.animal_id=String(input.value||"");entry.manual_animal_selection0813=true;entry.reviewed=false;
  if(!entry.recognized_animal_name0813)entry.recognized_animal_name0813=entry.animal_name||"";
  return
 }
 AH0813Base.updateBatchField083.call(this,input)
};
AH0813.handleInput=function(event){
 const input=event.composedPath().find(node=>node?.dataset?.batchField083);if(input){this.updateBatchField083(input);return}
 return AH0813Base.handleInput.call(this,event)
};
AH0813.handleChange=function(event){
 const input=event.composedPath().find(node=>node?.dataset?.batchField083);if(input){this.updateBatchField083(input);this.render();return}
 return AH0813Base.handleChange.call(this,event)
};
AH0813.handleSubmit=async function(event){
 await AH0813Base.handleSubmit.call(this,event);
 if(this.modal?.type==="ai-batch-083"&&this.prepareBatchNameMatches0813())this.render()
};
