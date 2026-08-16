Object.assign(T,{
 resetHomeFilters093:["Alle Tierfilter zurücksetzen","Reset all animal filters"]
});
const AH093=AnimalHealthPanel.prototype;
const AH093Base={overview:AH093.overview,homeAnimalFilterState091:AH093.homeAnimalFilterState091,homeAnimalOverview091:AH093.homeAnimalOverview091,handleClick:AH093.handleClick};
AH093.restoreHomeFilters093=function(){
 if(this.homeFilterPrefsLoaded093)return;
 this.homeFilterPrefsLoaded093=true;
 try{
  const raw=globalThis.localStorage?.getItem("animal_health.home_animal_filters");
  if(!raw)return;
  const saved=JSON.parse(raw);
  if(this.homeGroupFilter091==null&&saved?.group!=null)this.homeGroupFilter091=String(saved.group);
  if(this.homeTagFilter091==null&&saved?.tag!=null)this.homeTagFilter091=String(saved.tag)
 }catch(_error){}
};
AH093.persistHomeFilters093=function(){
 const group=String(this.homeGroupFilter091||"all"),tag=String(this.homeTagFilter091||"all");
 try{globalThis.localStorage?.setItem("animal_health.home_animal_filters",JSON.stringify({group,tag}))}catch(_error){}
};
AH093.homeAnimalFilterState091=function(){
 this.restoreHomeFilters093();
 const state=AH093Base.homeAnimalFilterState091.call(this);
 if(String(this.homeGroupFilter091||"all")!==String(state.group)||String(this.homeTagFilter091||"all")!==String(state.tag)){
  this.homeGroupFilter091=state.group;this.homeTagFilter091=state.tag;this.persistHomeFilters093()
 }
 return state
};
AH093.resetHomeFilters093=function(){
 this.homeGroupFilter091="all";
 this.homeTagFilter091="all";
 this.homeAnimalSearch091="";
 this.homeFilterPanel091=null;
 this.homeSearchOpen091=false;
 this.persistHomeFilters093()
};
AH093.homeAnimalOverview091=function(){
 let html=AH093Base.homeAnimalOverview091.call(this);
 const state=this.homeAnimalFilterState091(),filtered=state.group!=="all"||state.tag!=="all"||Boolean(state.query);
 if(filtered){
  const label=esc(this.t("resetHomeFilters093"));
  const reset=`<button class="homeIconTool092 homeFilterReset093" data-action="home-filter-reset-093" title="${label}" aria-label="${label}"><ha-icon icon="mdi:close-circle-outline"></ha-icon></button>`;
  html=html.replace(/(<div class="homeAnimalTools092" role="toolbar">[\s\S]*?)(<\/div>)/,"$1"+reset+"$2")
 }
 return html
};
AH093.overview=function(){
 let html=AH093Base.overview.call(this);
 html=html.replace(/<div class="heading"><h1>[\s\S]*?<\/h1><div class="actions"><label class="search">[\s\S]*?<\/label><\/div><\/div>/,"");
 return html+`<style>.homeAnimalTile092{place-items:center!important;align-content:center!important;justify-content:center!important;text-align:center!important}.homeAnimalVisualSlot092{margin-inline:auto!important;align-self:center!important;justify-self:center!important}.homeAnimalName092{width:100%!important;text-align:center!important;align-self:center!important;justify-self:center!important}.homeFilterReset093{color:var(--error-color,#db4437)!important;border-color:var(--error-color,#db4437)!important}.homeFilterReset093:hover{box-shadow:inset 0 0 0 1px var(--error-color,#db4437)!important}</style>`
};
AH093.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset?.action),action=button?.dataset?.action;
 if(action==="home-filter-reset-093"){this.resetHomeFilters093();this.render();return}
 const result=await AH093Base.handleClick.call(this,event);
 if(action==="home-group-select-091"||action==="home-tag-select-091")this.persistHomeFilters093();
 return result
};
