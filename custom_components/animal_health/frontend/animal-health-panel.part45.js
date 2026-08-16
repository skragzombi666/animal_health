const AH094=AnimalHealthPanel.prototype;
const AH094Base={heading:AH094.heading};
AH094.heading=function(key,action=""){
 if(key==="overview")return"";
 return AH094Base.heading.call(this,key,action)
};
