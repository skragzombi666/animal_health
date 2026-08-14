(()=>{
const CSS=`
ha-icon{display:inline-grid!important;place-items:center!important;width:24px!important;height:24px!important;min-width:24px!important;color:inherit!important;visibility:visible!important;opacity:1!important}
ha-icon svg{display:block!important;width:100%!important;height:100%!important;overflow:visible!important}
@media(max-width:850px){
header{display:flex!important;align-items:center!important;gap:2px!important;min-height:64px!important;padding:8px!important;overflow:visible!important}
header .menuButton,header>button[data-action="refresh"]{display:inline-flex!important;align-items:center!important;justify-content:center!important;flex:0 0 44px!important;width:44px!important;height:44px!important;min-width:44px!important;padding:10px!important;visibility:visible!important;opacity:1!important}
header .brand,header .brand0814,header .brandOriginal085{display:flex!important;align-items:center!important;justify-content:center!important;flex:0 0 36px!important;width:36px!important;min-width:36px!important;margin:0 2px!important;overflow:visible!important}
header .brandLogo0814,header .brandOriginal085 img{display:block!important;width:34px!important;height:34px!important;max-width:34px!important}
header nav{display:flex!important;align-items:stretch!important;justify-content:space-evenly!important;flex:1 1 auto!important;min-width:0!important;gap:0!important;overflow:visible!important}
header nav button{display:flex!important;position:relative!important;align-items:center!important;justify-content:center!important;flex:1 1 0!important;min-width:34px!important;max-width:54px!important;width:auto!important;height:48px!important;padding:10px 4px!important;visibility:visible!important;opacity:1!important;color:var(--primary-text-color,#212121)!important}
header nav button ha-icon,header .menuButton ha-icon,header>button[data-action="refresh"] ha-icon{display:inline-grid!important;width:24px!important;height:24px!important;min-width:24px!important;visibility:visible!important;opacity:1!important;color:currentColor!important}
header nav button span{display:none!important}
.heading .search ha-icon,.heading button ha-icon{display:inline-grid!important;width:24px!important;height:24px!important;min-width:24px!important;visibility:visible!important;opacity:1!important;color:currentColor!important}
.heading .search{overflow:visible!important}
}
`;
let shadowObserver=null;
function install(){
 const panel=document.querySelector('animal-health-panel');
 if(!panel?.shadowRoot)return;
 const root=panel.shadowRoot;
 if(!root.querySelector('style[data-android-shell="alpha6"]')){
  const style=document.createElement('style');style.dataset.androidShell='alpha6';style.textContent=CSS;root.appendChild(style);
 }
 if(!shadowObserver){
  shadowObserver=new MutationObserver(()=>{if(!root.querySelector('style[data-android-shell="alpha6"]')){const style=document.createElement('style');style.dataset.androidShell='alpha6';style.textContent=CSS;root.appendChild(style)}});
  shadowObserver.observe(root,{childList:true});
 }
}
new MutationObserver(install).observe(document.documentElement,{childList:true,subtree:true});
document.addEventListener('DOMContentLoaded',install);
})();
