Object.assign(T,{
 frontendRefreshing089:["Frontend wird nach dem Update aktualisiert …","Refreshing frontend after update …"]
});
const AH089=AnimalHealthPanel.prototype;
const AH089Base={load:AH089.load};
AH089.frontendReloadKey089=function(){return`${D}:frontend-reload-target`};
AH089.clearFrontendReload089=function(){
 try{
  sessionStorage.removeItem(this.frontendReloadKey089());
  const url=new URL(window.location.href);
  if(url.searchParams.has("_animal_health_frontend")){
   url.searchParams.delete("_animal_health_frontend");
   history.replaceState(history.state,"",`${url.pathname}${url.search}${url.hash}`)
  }
 }catch(_error){}
};
AH089.reloadForFrontendMismatch089=function(backendVersion){
 const target=String(backendVersion||"").trim();
 if(!target||target===V)return false;
 try{
  const key=this.frontendReloadKey089();
  if(sessionStorage.getItem(key)===target)return false;
  sessionStorage.setItem(key,target);
  const url=new URL(window.location.href);
  url.searchParams.set("_animal_health_frontend",target);
  window.location.replace(url.toString());
  return true
 }catch(_error){return false}
};
AH089.load=async function(){
 await AH089Base.load.call(this);
 const backendVersion=String(this.d?.version||"").trim();
 if(backendVersion&&backendVersion!==V){
  if(this.reloadForFrontendMismatch089(backendVersion))return
 }else if(backendVersion===V)this.clearFrontendReload089()
};
