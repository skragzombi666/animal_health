const AH083Catalog=AnimalHealthPanel.prototype;
const AH083CatalogLoad=AH083Catalog.loadV083;
AH083Catalog.loadV083=async function(){
 await AH083CatalogLoad.call(this);
 this.v083=this.v083||{};this.v083.medicines=this.v083.medicines||[];
 const additions=[
  {id:"doxycare_40_mg_tablets",name:"Doxycare 40 mg ad us. vet., teilbare Tabletten",active_ingredients:["doxycycline"],target_species:["dog","cat"],aliases:["Doxycare 40 mg"],authorisation_number:"68137-01",catalog_source:"standard"},
  {id:"doxycare_200_mg_tablets",name:"Doxycare 200 mg ad us. vet., teilbare Tabletten",active_ingredients:["doxycycline"],target_species:["dog","cat"],aliases:["Doxycare 200 mg"],authorisation_number:"68137-02",catalog_source:"standard"}
 ];
 const known=new Set(this.v083.medicines.map(item=>String(item.id||"").toLocaleLowerCase()));
 for(const item of additions)if(!known.has(item.id.toLocaleLowerCase()))this.v083.medicines.push(item);
 this.v083.medicines.sort((a,b)=>String(a.name||"").localeCompare(String(b.name||""),undefined,{sensitivity:"base"}));
 this.decorateV083()
};
