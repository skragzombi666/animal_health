Object.assign(T,{
 databaseLoadFailed030:["Produktdatenbanken konnten nicht geladen werden.","Product databases could not be loaded."],
 databaseLoadRetry030:["Erneut laden","Reload"],
 databaseEmpty030:["Es sind noch keine Produktdatenbanken registriert. Die mitgelieferten Datenbanken werden beim erneuten Laden wiederhergestellt.","No product databases are registered yet. Bundled databases are restored on reload."],
 databaseFilterEmpty030:["Für diesen Filter ist keine Datenbank vorhanden.","No database matches this filter."],
 databaseOverview030:["Datenbanken","databases"],
 databaseEntries030:["Produkte insgesamt","products in total"],
 databaseAutomatic030:["Automatisch aus Verlauf und Aufgaben","Automatically derived from history and tasks"]
});
const AH030=AnimalHealthPanel.prototype;
const AH030Base={
 loadV0928:AH030.loadV0928,
 productDatabases028:AH030.productDatabases028,
 handleClick:AH030.handleClick,
 render:AH030.render
};
AH030.loadV0928=async function(){
 this.v0928Error030="";
 try{
  const state=await this.ws(`${D}/v0928/state`);
  this.v0928=state&&Array.isArray(state.databases)?state:{databases:[],products:[],merged_products:[],views:{}}
 }catch(error){
  this.v0928={databases:[],products:[],merged_products:[],views:{}};
  this.v0928Error030=String(error?.message||error||this.t("databaseLoadFailed030"))
 }
};
AH030.databaseOrder030=function(id){
 const order=[
  "swissmedic_ch",
  "swissmedic_dewormers",
  "animal_health_medications_ch",
  "vaccines_ch",
  "animal_health_supplements",
  "animal_health_feed_chicken",
  "local_history_suggestions",
  "user_curated"
 ];
 const index=order.indexOf(String(id||""));
 return index<0?1000:index
};
AH030.databaseList030=function(filter="all"){
 const all=[...(this.v0928?.databases||[])];
 return all.filter(db=>{
  const types=Array.isArray(db?.product_types)?db.product_types:[];
  if(filter==="all")return true;
  if(filter==="user")return db?.source_type==="user";
  return types.includes(filter)
 }).sort((a,b)=>this.databaseOrder030(a?.id)-this.databaseOrder030(b?.id)||Number(b?.priority||0)-Number(a?.priority||0)||String(a?.name||"").localeCompare(String(b?.name||""),undefined,{sensitivity:"base"}))
};
AH030.databaseMessage030=function(all,filtered){
 if(this.v0928Error030)return`<div class="databaseState030 error030"><ha-icon icon="mdi:database-alert-outline"></ha-icon><div><b>${this.t("databaseLoadFailed030")}</b><small>${esc(this.v0928Error030)}</small></div><button type="button" data-action="db-retry-030"><ha-icon icon="mdi:refresh"></ha-icon>${this.t("databaseLoadRetry030")}</button></div>`;
 if(!all.length)return`<div class="databaseState030"><ha-icon icon="mdi:database-off-outline"></ha-icon><div><b>${this.t("databaseEmpty030")}</b></div><button type="button" data-action="db-retry-030"><ha-icon icon="mdi:refresh"></ha-icon>${this.t("databaseLoadRetry030")}</button></div>`;
 if(!filtered.length)return`<div class="databaseState030"><ha-icon icon="mdi:filter-off-outline"></ha-icon><div><b>${this.t("databaseFilterEmpty030")}</b></div></div>`;
 return""
};
AH030.databaseCard030=function(db){
 const types=Array.isArray(db?.product_types)?db.product_types:[];
 const source=[db?.source_name||db?.source_type,types.map(kind=>this.kindLabel028(kind)).filter(Boolean).join(" · ")].filter(Boolean).join(" · ");
 const revision=[db?.version?`${this.t("databaseVersion028")}: ${db.version}`:"",db?.data_as_of?`${this.t("databaseAsOf028")}: ${db.data_as_of}`:""].filter(Boolean).join(" · ");
 const history=db?.id==="local_history_suggestions"?`<small class="databaseHistory030"><ha-icon icon="mdi:history"></ha-icon>${this.t("databaseAutomatic030")}</small>`:"";
 return`<article class="dbCard028 databaseCard030 ${db?.enabled?"":"off"}"><div><h3>${esc(db?.name||db?.id||"")}</h3><p>${esc(db?.description||"")}</p>${source?`<small>${esc(source)}</small>`:""}<small>${this.t("databaseProducts028")}: <b>${Number(db?.item_count||0)}</b>${revision?` · ${esc(revision)}`:""}</small>${history}</div><div><button type="button" data-action="db-toggle-028" data-id="${esc(db?.id||"")}" data-enabled="${db?.enabled?0:1}" title="${esc(this.t(db?.enabled?"databaseEnabled028":"databaseDisabled028"))}" aria-label="${esc(this.t(db?.enabled?"databaseEnabled028":"databaseDisabled028"))}"><ha-icon icon="mdi:${db?.enabled?"toggle-switch":"toggle-switch-off-outline"}"></ha-icon></button><button type="button" data-action="db-open-028" data-id="${esc(db?.id||"")}"><ha-icon icon="mdi:database-search-outline"></ha-icon>${this.t("databaseOpen028")}</button></div></article>`
};
AH030.productDatabases028=function(){
 if(this.dbOpen028){
  const database=this.db028(this.dbOpen028);
  if(database)return this.dbDetail028(database);
  this.dbOpen028=null
 }
 const active=this.dbFilter028||"all";
 const filters=["all","medication","vaccination","deworming","supplement","feed","user"];
 const all=this.databaseList030("all");
 const databases=this.databaseList030(active);
 const products=(this.v0928?.products||[]).length;
 const state=this.databaseMessage030(all,databases);
 return`<section class="card productDatabases028 productDatabases030"><div class="dbHead028"><div><h2>${this.t("productDatabases028")}</h2><p>${this.t("productDatabasesHint028")}</p>${all.length?`<small class="databaseOverview030"><b>${all.length}</b> ${this.t("databaseOverview030")} · <b>${products}</b> ${this.t("databaseEntries030")}</small>`:""}</div><div><button type="button" data-action="db-add-028"><ha-icon icon="mdi:database-plus-outline"></ha-icon>${this.t("databaseAdd028")}</button><button type="button" data-action="db-import-028"><ha-icon icon="mdi:database-import-outline"></ha-icon>${this.t("databaseImport028")}</button><input type="file" accept=".json,application/json" data-db-file028 hidden></div></div>${this.dbEdit028?this.dbEditor028():""}<div class="dbFilters028">${filters.map(filter=>`<button type="button" data-action="db-filter-028" data-filter="${filter}" class="${active===filter?"on":""}">${this.t(filter==="all"?"databaseAll028":filter==="user"?"databaseUser028":`database${filter[0].toUpperCase()+filter.slice(1)}028`)}</button>`).join("")}</div>${state||`<div class="dbList028">${databases.map(database=>this.databaseCard030(database)).join("")}</div>`}</section>`
};
AH030.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset?.action);
 if(button?.dataset?.action==="db-retry-030"){
  button.disabled=true;
  await this.loadV0928();
  this.render();
  return
 }
 return AH030Base.handleClick.call(this,event)
};
AH030.render=function(){
 AH030Base.render.call(this);
 this.shadowRoot.innerHTML+=`<style>
.productDatabases030 .databaseOverview030{display:block;margin-top:7px;color:var(--secondary-text-color)}.databaseState030{display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:12px;padding:14px;border:1px solid var(--divider-color);border-radius:12px;background:var(--secondary-background-color)}.databaseState030>ha-icon{width:30px;height:30px}.databaseState030>div{display:grid;gap:3px;min-width:0}.databaseState030 small{color:var(--secondary-text-color);overflow-wrap:anywhere}.databaseState030.error030{border-color:var(--error-color,#db4437)}.databaseHistory030{display:flex!important;align-items:center;gap:4px}.databaseHistory030 ha-icon{width:15px;height:15px}.databaseCard030>div:first-child{display:grid;gap:3px}.databaseCard030 h3,.databaseCard030 p{margin:0}.databaseCard030 p{margin-bottom:2px}@media(max-width:620px){.databaseState030{grid-template-columns:auto minmax(0,1fr)}.databaseState030>button{grid-column:2;justify-self:start}.productDatabases030 .dbHead028>div:last-child{width:100%;justify-content:flex-start;flex-wrap:wrap}}
</style>`
};
