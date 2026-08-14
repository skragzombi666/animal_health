(()=>{
const S='fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"';
const F='fill="currentColor" stroke="none"';
const icons={
 menu:`<g ${S}><path d="M4 7h16M4 12h16M4 17h16"/></g>`,
 paw:`<g ${F}><ellipse cx="12" cy="16.4" rx="4.8" ry="3.8"/><circle cx="6.4" cy="10" r="2"/><circle cx="10.1" cy="7.1" r="2"/><circle cx="13.9" cy="7.1" r="2"/><circle cx="17.6" cy="10" r="2"/></g>`,
 refresh:`<g ${S}><path d="M20 7v5h-5"/><path d="M18.4 8.1A8 8 0 1 0 20 15"/></g>`,
 dashboard:`<g ${S}><rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/></g>`,
 tasks:`<g ${S}><rect x="5" y="5" width="14" height="16" rx="2"/><path d="M9 5V3h6v2M8.5 13l2 2 4.5-5"/></g>`,
 calendar:`<g ${S}><rect x="3.5" y="5" width="17" height="16" rx="2"/><path d="M7.5 3v4M16.5 3v4M3.5 10h17M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01M16 18h.01"/></g>`,
 clock:`<g ${S}><circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3.5 2"/></g>`,
 users:`<g ${S}><circle cx="9" cy="9" r="3"/><circle cx="17" cy="10" r="2.4"/><path d="M3.5 20c.5-4 2.4-6 5.5-6s5 2 5.5 6M14.5 15c3.4-.7 5.3 1 6 4"/></g>`,
 settings:`<g ${S}><circle cx="12" cy="12" r="3"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6 7 7M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4"/><circle cx="12" cy="12" r="7"/></g>`,
 plusCircle:`<g ${S}><circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/></g>`,
 plus:`<g ${S}><path d="M12 5v14M5 12h14"/></g>`,
 clipboardPlus:`<g ${S}><rect x="5" y="5" width="14" height="16" rx="2"/><path d="M9 5V3h6v2M12 10v6M9 13h6"/></g>`,
 scale:`<g ${S}><path d="M4 20h16M7 20l1-10h8l1 10M9 10a3 3 0 0 1 6 0M12 10l2-2"/></g>`,
 alert:`<g ${S}><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 17h.01"/></g>`,
 alertPlus:`<g ${S}><circle cx="10" cy="11" r="7.5"/><path d="M10 7v5M10 15h.01M18 15v6M15 18h6"/></g>`,
 pill:`<g ${S}><path d="M8.2 19.2a4.2 4.2 0 0 1-5.9-5.9l8.9-8.9a4.2 4.2 0 1 1 5.9 5.9z"/><path d="m7.5 8.1 5.9 5.9"/></g>`,
 notePlus:`<g ${S}><path d="M5 3h10l4 4v14H5zM15 3v5h4M12 11v6M9 14h6"/></g>`,
 sparkle:`<g ${S}><path d="m12 3 1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5zM18.5 15.5l.7 2.1 2.1.7-2.1.7-.7 2.1-.7-2.1-2.1-.7 2.1-.7z"/></g>`,
 search:`<g ${S}><circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/></g>`,
 close:`<g ${S}><path d="M6 6l12 12M18 6 6 18"/></g>`,
 edit:`<g ${S}><path d="M4 20h4l11-11-4-4L4 16zM13.5 6.5l4 4"/></g>`,
 trash:`<g ${S}><path d="M4 7h16M9 7V4h6v3M7 7l1 14h8l1-14M10 11v6M14 11v6"/></g>`,
 file:`<g ${S}><path d="M6 3h8l4 4v14H6zM14 3v5h4M9 12h6M9 16h6"/></g>`,
 code:`<g ${S}><path d="m9 8-4 4 4 4M15 8l4 4-4 4M13 6l-2 12"/></g>`,
 pdf:`<g ${S}><path d="M6 3h8l4 4v14H6zM14 3v5h4M9 12h6M9 16h4"/></g>`,
 archive:`<g ${S}><path d="M4 7h16v14H4zM3 3h18v4H3zM9 12h6"/></g>`,
 download:`<g ${S}><path d="M12 3v12M8 11l4 4 4-4M4 20h16"/></g>`,
 upload:`<g ${S}><path d="M12 17V5M8 9l4-4 4 4M4 20h16"/></g>`,
 image:`<g ${S}><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8" cy="9" r="1.5"/><path d="m4 17 5-5 4 4 2-2 5 5"/></g>`,
 chevronRight:`<g ${S}><path d="m9 5 7 7-7 7"/></g>`,
 chevronLeft:`<g ${S}><path d="m15 5-7 7 7 7"/></g>`,
 chevronDown:`<g ${S}><path d="m5 9 7 7 7-7"/></g>`,
 arrowLeft:`<g ${S}><path d="M20 12H5M11 6l-6 6 6 6"/></g>`,
 arrowRight:`<g ${S}><path d="M4 12h15M13 6l6 6-6 6"/></g>`,
 checkCircle:`<g ${S}><circle cx="12" cy="12" r="9"/><path d="m8 12 2.7 2.7L16.5 9"/></g>`,
 check:`<g ${S}><path d="m5 12 4 4L19 6"/></g>`,
 medicalBag:`<g ${S}><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V4h6v3M12 10v7M8.5 13.5h7"/></g>`,
 stethoscope:`<g ${S}><path d="M6 4v5a4 4 0 0 0 8 0V4M4 4h4M12 4h4M10 13v2a5 5 0 0 0 10 0v-1"/><circle cx="20" cy="12" r="2"/></g>`,
 syringe:`<g ${S}><path d="m5 19 10-10M13 5l6 6M15 3l6 6M9 9l6 6M4 20l-1 1M7 17l-3-3"/></g>`,
 bell:`<g ${S}><path d="M5 17h14l-2-3V10a5 5 0 0 0-10 0v4zM10 20h4"/></g>`,
 tag:`<g ${S}><path d="M3 12V4h8l10 10-7 7z"/><circle cx="8" cy="8" r="1.2"/></g>`,
 copy:`<g ${S}><rect x="8" y="8" width="11" height="12" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h3"/></g>`,
 repeat:`<g ${S}><path d="M17 3l4 4-4 4M21 7H9a5 5 0 0 0-5 5M7 21l-4-4 4-4M3 17h12a5 5 0 0 0 5-5"/></g>`,
 eye:`<g ${S}><path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z"/><circle cx="12" cy="12" r="2.5"/></g>`,
 info:`<g ${S}><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/></g>`,
 dog:`<g ${S}><path d="M6 8 3 5v7l3 2M18 8l3-3v7l-3 2M6 8c2-3 10-3 12 0v7c0 4-3 6-6 6s-6-2-6-6z"/><circle cx="9" cy="12" r=".6" ${F}/><circle cx="15" cy="12" r=".6" ${F}/><path d="M10 16h4M12 14v2"/></g>`,
 cat:`<g ${S}><path d="M6 8 4 3l5 3c2-1 4-1 6 0l5-3-2 5v7c0 4-2.5 6-6 6s-6-2-6-6zM8.5 12h.01M15.5 12h.01M10 16h4M3 14h5M16 14h5"/></g>`,
 bird:`<g ${S}><path d="M4 15c5 1 6-7 12-7 3 0 5 2 5 5-4 0-5 2-7 4-3 3-7 2-10-2zM16 8l1-3M20 10l2-1"/><circle cx="17.5" cy="11" r=".5" ${F}/></g>`,
 rabbit:`<g ${S}><path d="M8 8C6 2 8 1 10 7M14 7c2-6 4-5 2 1M7 11c1-5 9-5 10 0v5c0 3-2 5-5 5s-5-2-5-5zM9.5 13h.01M14.5 13h.01M11 17h2"/></g>`,
 horse:`<g ${S}><path d="M7 20V9l4-6 7 4-2 4 2 3-4 2-2 5M8 9l-4 2 3 3M13 8h.01"/></g>`,
 cow:`<g ${S}><path d="M6 8 3 5M18 8l3-3M6 8c1-3 11-3 12 0v8c0 3-2 5-6 5s-6-2-6-5zM8.5 12h.01M15.5 12h.01M8 16h8M10 18h.01M14 18h.01"/></g>`,
 sheep:`<g ${S}><path d="M7 8a3 3 0 0 1 5-2 3 3 0 0 1 5 2 3 3 0 0 1 1 5 4 4 0 0 1-1 6H7a4 4 0 0 1-1-6 3 3 0 0 1 1-5zM9 12h.01M15 12h.01M10 16h4"/></g>`,
 pig:`<g ${S}><path d="M6 8 4 5v6M18 8l2-3v6M6 8c2-3 10-3 12 0v7c0 4-2 6-6 6s-6-2-6-6z"/><ellipse cx="12" cy="15" rx="3" ry="2"/><path d="M11 15h.01M13 15h.01M9 11h.01M15 11h.01"/></g>`,
 bee:`<g ${S}><ellipse cx="12" cy="13" rx="4" ry="6"/><path d="M8.5 10h7M8 14h8M9 18h6M9 8C5 4 3 7 6 11M15 8c4-4 6-1 3 3M12 7V4"/></g>`,
 fish:`<g ${S}><path d="M4 12c3-5 9-6 14-2l3-3v10l-3-3c-5 4-11 3-14-2z"/><circle cx="9" cy="11" r=".6" ${F}/></g>`,
 turtle:`<g ${S}><ellipse cx="12" cy="13" rx="6" ry="5"/><path d="M6 11 3 9M6 16l-3 2M18 11l3-2M18 16l3 2M12 8V5M12 18v3M8 13h8M12 8v10"/></g>`,
 snake:`<g ${S}><path d="M6 5c0 5 12 2 12 7s-12 2-12 7c0 2 2 3 4 2M6 5l-2 1M6 5 4 3M10 21h5"/></g>`,
 dot:`<circle cx="12" cy="12" r="2" ${F}/>`
};
const exact={
 "mdi:paw":"paw","mdi:menu":"menu","mdi:refresh":"refresh","mdi:view-dashboard":"dashboard","mdi:home":"dashboard","mdi:home-outline":"dashboard","mdi:clipboard-check":"tasks","mdi:clipboard-check-outline":"tasks","mdi:calendar":"calendar","mdi:calendar-today":"calendar","mdi:calendar-month":"calendar","mdi:calendar-range":"calendar","mdi:timeline-clock":"clock","mdi:clock-outline":"clock","mdi:clipboard-clock":"clock","mdi:account-group-outline":"users","mdi:account-group":"users","mdi:cog-outline":"settings","mdi:cog":"settings","mdi:plus-circle-outline":"plusCircle","mdi:plus":"plus","mdi:clipboard-plus":"clipboardPlus","mdi:scale":"scale","mdi:scale-bathroom":"scale","mdi:alert-circle-outline":"alert","mdi:alert-circle":"alert","mdi:alert":"alert","mdi:alert-plus":"alertPlus","mdi:pill":"pill","mdi:note-plus-outline":"notePlus","mdi:creation-outline":"sparkle","mdi:creation":"sparkle","mdi:magnify":"search","mdi:close":"close","mdi:pencil-outline":"edit","mdi:pencil":"edit","mdi:delete-outline":"trash","mdi:delete":"trash","mdi:file-pdf-box":"pdf","mdi:archive-outline":"archive","mdi:download-outline":"download","mdi:download":"download","mdi:upload":"upload","mdi:image-plus-outline":"image","mdi:image-remove-outline":"image","mdi:image-outline":"image","mdi:camera-outline":"image","mdi:chevron-right":"chevronRight","mdi:chevron-left":"chevronLeft","mdi:chevron-down":"chevronDown","mdi:arrow-left":"arrowLeft","mdi:arrow-right":"arrowRight","mdi:check-circle-outline":"checkCircle","mdi:check":"check","mdi:medical-bag":"medicalBag","mdi:stethoscope":"stethoscope","mdi:needle":"syringe","mdi:syringe":"syringe","mdi:bell-outline":"bell","mdi:tag-outline":"tag","mdi:content-copy":"copy","mdi:repeat":"repeat","mdi:replay":"repeat","mdi:backup-restore":"repeat","mdi:code-json":"code","mdi:eye-outline":"eye","mdi:information-outline":"info","mdi:dog":"dog","mdi:cat":"cat","mdi:bird":"bird","mdi:rabbit":"rabbit","mdi:horse":"horse","mdi:cow":"cow","mdi:sheep":"sheep","mdi:pig":"pig","mdi:bee":"bee","mdi:fish":"fish","mdi:turtle":"turtle","mdi:snake":"snake"
};
function resolveIcon(icon){
 const raw=String(icon||""),name=raw.replace(/^mdi:/,"");if(exact[raw])return exact[raw];
 if(name.includes("calendar"))return"calendar";if(name.includes("clock")||name.includes("timeline"))return"clock";if(name.includes("account")||name.includes("group"))return"users";if(name.includes("cog")||name.includes("setting"))return"settings";if(name.includes("magnify")||name.includes("search"))return"search";if(name.includes("pencil")||name.includes("edit"))return"edit";if(name.includes("delete")||name.includes("trash"))return"trash";if(name.includes("archive"))return"archive";if(name.includes("backup")||name.includes("restore")||name.includes("repeat")||name.includes("replay"))return"repeat";if(name.includes("download"))return"download";if(name.includes("upload"))return"upload";if(name.includes("image")||name.includes("photo")||name.includes("camera"))return"image";if(name.includes("pdf"))return"pdf";if(name.includes("json")||name.includes("code"))return"code";if(name.includes("file")||name.includes("note")||name.includes("document"))return"file";if(name.includes("copy"))return"copy";if(name.includes("chevron-right"))return"chevronRight";if(name.includes("chevron-left"))return"chevronLeft";if(name.includes("chevron"))return"chevronDown";if(name.includes("arrow-left"))return"arrowLeft";if(name.includes("arrow"))return"arrowRight";if(name.includes("plus"))return"plusCircle";if(name.includes("check"))return"checkCircle";if(name.includes("alert"))return"alert";if(name.includes("pill"))return"pill";if(name.includes("needle")||name.includes("syringe"))return"syringe";if(name.includes("stethoscope"))return"stethoscope";if(name.includes("medical"))return"medicalBag";if(name.includes("bell"))return"bell";if(name.includes("tag"))return"tag";if(name.includes("eye"))return"eye";if(name.includes("info"))return"info";return"dot"
}
class HaIcon extends HTMLElement{static get observedAttributes(){return["icon"]}connectedCallback(){this.draw()}attributeChangedCallback(){this.draw()}draw(){const icon=this.getAttribute("icon")||"",key=resolveIcon(icon);this.innerHTML=`<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">${icons[key]||icons.dot}</svg>`;this.title=icon}}
if(!customElements.get("ha-icon"))customElements.define("ha-icon",HaIcon);
const nativeCall=request=>new Promise((resolve,reject)=>{try{const raw=AndroidBridge.call(JSON.stringify(request||{})),value=raw?JSON.parse(raw):null;if(value&&value.__error)reject(new Error(value.__error));else resolve(value)}catch(error){reject(error)}});
const loadScript=src=>new Promise((resolve,reject)=>{const script=document.createElement("script");script.src=src;script.onload=resolve;script.onerror=()=>reject(new Error(`Frontend asset fehlt oder ist ungültig: ${src}`));document.head.appendChild(script)});
const fileBase64=file=>new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result||"").split(",",2)[1]||"");reader.onerror=()=>reject(reader.error||new Error("Datei konnte nicht gelesen werden"));reader.readAsDataURL(file)});
async function uploadFiles(form,animalId,eventId=null){const files=[...form.querySelectorAll('input[type="file"]')].flatMap(input=>[...(input.files||[])]),title=form.elements.document_title?.value||null,result=[];for(const file of files){if(file.size>15728640)throw Error("Die Datei überschreitet die maximale Grösse von 15 MB.");result.push(await nativeCall({type:"animal_health/attachments/upload_direct",animal_id:animalId,event_id:eventId,filename:file.name||"document",media_type:file.type||"application/octet-stream",title,content_base64:await fileBase64(file)}))}return result}
function removeStandaloneHaWarning(panel){const warning=panel?.shadowRoot?.querySelector(".warn");if(warning&&/Home Assistant|Frontend und Backend|Frontend and backend/i.test(warning.textContent||""))warning.remove()}
async function install(){
 const frontendErrors=[];
 const onFrontendError=event=>frontendErrors.push(event?.error?.message||event?.message||"Unbekannter JavaScript-Fehler");
 window.addEventListener("error",onFrontendError);
 await loadScript("animal-health-panel.js");
 window.removeEventListener("error",onFrontendError);
 const Panel=customElements.get("animal-health-panel");
 if(!Panel)throw Error(frontendErrors.at(-1)||"Animal-Health-Frontend konnte nicht geladen werden");
 const p=Panel.prototype;
 p.download=async function(kind,resourceId=""){AndroidBridge.exportData(String(kind||""),String(resourceId||""))};
 p.uploadFiles=uploadFiles;
 p.uploadAnimalPhoto=async function(form,animalId){const file=form.elements.profile_image?.files?.[0];if(!file)return;const item=await nativeCall({type:"animal_health/attachments/upload_direct",animal_id:animalId,filename:file.name||"animal-photo.jpg",media_type:file.type||"image/jpeg",title:this.t?this.t("animalPhoto"):"Tierbild",content_base64:await fileBase64(file)});await nativeCall({type:"animal_health/animal_photo/set",animal_id:animalId,attachment_id:item.id})};
 p.aiUploadOne=async function(file){return nativeCall({type:"animal_health/ai/upload_direct",filename:file.name||"input",media_type:file.type||"application/octet-stream",content_base64:await fileBase64(file)})};
 if(typeof p.reloadForFrontendMismatch089==="function")p.reloadForFrontendMismatch089=function(){return false};
 const sharedRender=p.render;p.render=function(){const result=sharedRender.call(this);removeStandaloneHaWarning(this);return result};
 const oldNotify=p.notify;p.notify=function(message,bad=false){try{AndroidBridge.toast(String(message||""),Boolean(bad))}catch(_error){}return oldNotify?oldNotify.call(this,message,bad):undefined};
 const hass={language:"de-CH",standalone:true,user:{is_admin:true,name:"Android"},callWS:request=>nativeCall(request),callService:(domain,service,serviceData)=>nativeCall({type:"call_service",domain,service,service_data:serviceData||{}})};
 const panel=new Panel();panel.panel={title:"Animal Health",icon:"mdi:paw"};document.body.appendChild(panel);panel.hass=hass;
 window.addEventListener("error",event=>{try{AndroidBridge.toast(`UI-Fehler: ${event.message}`,true)}catch(_error){}});
}
install().catch(error=>{document.body.innerHTML=`<main style="padding:24px"><h2>Animal Health</h2><p>Die gemeinsame Oberfläche konnte nicht geladen werden.</p><pre style="white-space:pre-wrap">${String(error?.message||error)}</pre></main>`;try{AndroidBridge.toast(String(error?.message||error),true)}catch(_error){}});
})();
