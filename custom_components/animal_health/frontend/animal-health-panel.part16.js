Object.assign(T,{
 aiChooseFiles:["Fotos oder Dateien auswählen","Choose photos or files"],
 aiSelectedCount:["Ausgewählte Dateien","Selected files"],
 aiMoreInfo:["Zusätzliche Angaben","Additional information"],
 aiMoreInfoHint:["Optional: Ergänze Informationen, die auf den Dateien nicht sichtbar sind, z. B. welches Tier gemeint ist oder was du bereits weisst.","Optional: Add information not visible in the files, for example which animal is meant or what you already know."],
 aiDictate:["Diktieren (KI → Text)","Dictate (AI → text)"],
 aiStopDictation:["Diktat beenden","Stop dictation"],
 aiTranscribing:["Diktat wird durch die Home-Assistant-Spracherkennung transkribiert …","Transcribing dictation with Home Assistant speech-to-text …"],
 aiNoStt:["Keine Home-Assistant-Speech-to-Text-Entität verfügbar. Für KI-Diktat zuerst beim KI-Provider eine STT-Entität einrichten.","No Home Assistant speech-to-text entity is available. Configure an STT entity on the AI provider first."],
 aiSttEntity:["Speech-to-Text-Entität","Speech-to-text entity"],
 aiTooManyFiles:["Es können maximal 10 Dateien gemeinsam analysiert werden.","A maximum of 10 files can be analyzed together."],
 aiRecording:["Aufnahme läuft …","Recording …"],
 aiStopBeforeAnalyze:["Bitte das laufende Diktat zuerst beenden.","Stop the active dictation before analyzing."],
 aiRemoveFile:["Datei entfernen","Remove file"]
});
const AH080MULTI=AnimalHealthPanel.prototype;
const AH080MULTIBase={
 aiUploadForm:AH080MULTI.aiUploadForm,
 aiResultRows:AH080MULTI.aiResultRows,
 handleClick:AH080MULTI.handleClick,
 handleChange:AH080MULTI.handleChange,
 handleSubmit:AH080MULTI.handleSubmit,
 captureCamera:AH080MULTI.captureCamera,
 render:AH080MULTI.render
};
AH080MULTI.aiUploadForm=function(){
 let html=AH080MULTIBase.aiUploadForm.call(this).replace('name="ai_file" accept=','name="ai_file" multiple accept=').replace(this.t("aiChooseFile"),this.t("aiChooseFiles"));
 const sttEntities=this.aiStatus?.stt_entities||[];
 const sttSelect=sttEntities.length>1?`<label class="wide"><span>${this.t("aiSttEntity")}</span><select name="ai_stt_entity_id"><option value="">Home Assistant</option>${sttEntities.map(id=>`<option value="${esc(id)}">${esc(id)}</option>`).join("")}</select></label>`:"";
 const context=`<label class="wide aiContext"><span>${this.t("aiMoreInfo")}</span><textarea name="ai_context" rows="4" maxlength="4000" placeholder="${esc(this.t("aiMoreInfoHint"))}">${esc(this.aiContextDraft||"")}</textarea></label><div class="wide aiDictationBar">${sttSelect}<button type="button" data-action="ai-start-dictation" ${this.aiStatus?.stt_available?"":"disabled"}><ha-icon icon="mdi:microphone-outline"></ha-icon><span>${this.t("aiDictate")}</span></button>${this.aiStatus?.stt_available?"":`<small>${this.t("aiNoStt")}</small>`}</div>`;
 html=html.replace('<div class="buttons wide">',`${context}<div class="buttons wide">`);
 return html
};
AH080MULTI.aiResultRows=function(s){
 const copy={...s};if(Array.isArray(copy.source_filenames)&&copy.source_filenames.length)copy.source_filename=copy.source_filenames.join(", ");return AH080MULTIBase.aiResultRows.call(this,copy)
};
AH080MULTI.aiAddFiles=function(files){
 this.aiFiles=this.aiFiles||[];const incoming=[...files].filter(Boolean);if(this.aiFiles.length+incoming.length>10){this.notify(this.t("aiTooManyFiles"),true);return false}this.aiFiles.push(...incoming);return true
};
AH080MULTI.updateAIFileSelection=function(form){
 const target=form?.querySelector("[data-ai-file-selection]");if(!target)return;const files=this.aiFiles||[];
 if(!files.length){target.textContent=this.t("noFileSelected");target.classList.remove("hasFiles");return}
 target.classList.add("hasFiles");target.innerHTML=`<b>${this.t("aiSelectedCount")}: ${files.length}</b><div class="aiSelectedFiles">${files.map((file,index)=>`<span><ha-icon icon="${String(file.type||"").startsWith("image/")?"mdi:file-image-outline":"mdi:file-document-outline"}"></ha-icon><span>${esc(file.name||`Datei ${index+1}`)}</span><button type="button" data-action="ai-remove-file" data-index="${index}" title="${this.t("aiRemoveFile")}"><ha-icon icon="mdi:close"></ha-icon></button></span>`).join("")}</div>`
};
AH080MULTI.captureCamera=async function(){
 const form=this.cameraForm,isAI=form?.dataset?.form==="ai-upload";await AH080MULTIBase.captureCamera.call(this);if(!isAI)return;const input=form?.elements?.camera_file,file=input?.files?.[0];if(file){this.aiAddFiles([file]);input.value="";this.updateAIFileSelection(form)}
};
AH080MULTI.aiUploadOne=async function(file){
 const target=await this.ws(`${D}/ai/upload`);if(file.size>target.max_size_bytes)throw Error(this.t("fileTooLarge"));const payload=new FormData();payload.append("file",file,file.name||"animal-health-ai");const response=await fetch(target.url,{method:"POST",body:payload,credentials:"same-origin"});if(!response.ok){if(response.status===415)throw Error(this.t("aiUnsupported"));throw Error((await response.text())||`HTTP ${response.status}`)}return response.json()
};
AH080MULTI.flattenAudio=function(chunks){let length=0;for(const chunk of chunks)length+=chunk.length;const out=new Float32Array(length);let offset=0;for(const chunk of chunks){out.set(chunk,offset);offset+=chunk.length}return out};
AH080MULTI.resampleAudio=function(samples,sourceRate,targetRate=16000){
 if(sourceRate===targetRate)return samples;const ratio=sourceRate/targetRate,length=Math.max(1,Math.round(samples.length/ratio)),out=new Float32Array(length);for(let i=0;i<length;i++){const position=i*ratio,left=Math.floor(position),right=Math.min(samples.length-1,left+1),fraction=position-left;out[i]=(samples[left]||0)*(1-fraction)+(samples[right]||0)*fraction}return out
};
AH080MULTI.wavFile=function(samples){
 const buffer=new ArrayBuffer(44+samples.length*2),view=new DataView(buffer),write=(offset,text)=>{for(let i=0;i<text.length;i++)view.setUint8(offset+i,text.charCodeAt(i))};write(0,"RIFF");view.setUint32(4,36+samples.length*2,true);write(8,"WAVE");write(12,"fmt ");view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,16000,true);view.setUint32(28,32000,true);view.setUint16(32,2,true);view.setUint16(34,16,true);write(36,"data");view.setUint32(40,samples.length*2,true);let offset=44;for(const sample of samples){const value=Math.max(-1,Math.min(1,sample));view.setInt16(offset,value<0?value*0x8000:value*0x7fff,true);offset+=2}return new File([buffer],`animal-health-dictation-${Date.now()}.wav`,{type:"audio/wav"})
};
AH080MULTI.startAIDictation=async function(button){
 if(!this.aiStatus?.stt_available){this.notify(this.t("aiNoStt"),true);return}if(this.aiDictation)return;const form=button?.closest("form");if(!form)return;
 try{const stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false}),AudioContextClass=window.AudioContext||window.webkitAudioContext;if(!AudioContextClass)throw Error("Web Audio API unavailable");const context=new AudioContextClass(),source=context.createMediaStreamSource(stream),processor=context.createScriptProcessor(4096,1,1),mute=context.createGain();mute.gain.value=0;const chunks=[];processor.onaudioprocess=event=>chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));source.connect(processor);processor.connect(mute);mute.connect(context.destination);await context.resume();this.aiDictation={form,stream,context,source,processor,mute,chunks,sampleRate:context.sampleRate};button.dataset.action="ai-stop-dictation";button.classList.add("recording");button.innerHTML=`<ha-icon icon="mdi:stop-circle-outline"></ha-icon><span>${this.t("aiStopDictation")}</span>`;this.notify(this.t("aiRecording"))}catch(error){this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}
};
AH080MULTI.cancelAIDictation=async function(){const state=this.aiDictation;if(!state)return;this.aiDictation=null;try{state.processor.disconnect();state.source.disconnect();state.mute.disconnect()}catch(_error){}for(const track of state.stream?.getTracks?.()||[])track.stop();try{await state.context.close()}catch(_error){}};
AH080MULTI.stopAIDictation=async function(button){
 const state=this.aiDictation;if(!state)return;this.aiDictation=null;const form=state.form;try{state.processor.disconnect();state.source.disconnect();state.mute.disconnect()}catch(_error){}for(const track of state.stream?.getTracks?.()||[])track.stop();try{await state.context.close()}catch(_error){}button.disabled=true;button.classList.remove("recording");button.innerHTML=`<ha-icon icon="mdi:progress-clock"></ha-icon><span>${this.t("aiTranscribing")}</span>`;this.notify(this.t("aiTranscribing"));
 try{const raw=this.flattenAudio(state.chunks);if(!raw.length)throw Error("No audio recorded");const file=this.wavFile(this.resampleAudio(raw,state.sampleRate,16000)),uploaded=await this.aiUploadOne(file),sttEntity=form.elements.ai_stt_entity_id?.value||"",result=await this.ws(`${D}/ai/transcribe`,{upload_id:uploaded.upload_id,...(sttEntity?{entity_id:sttEntity}:{})}),area=form.elements.ai_context;if(area&&result.text){area.value=[area.value.trim(),result.text.trim()].filter(Boolean).join("\n");this.aiContextDraft=area.value}button.disabled=false;button.dataset.action="ai-start-dictation";button.innerHTML=`<ha-icon icon="mdi:microphone-outline"></ha-icon><span>${this.t("aiDictate")}</span>`}catch(error){button.disabled=false;button.dataset.action="ai-start-dictation";button.innerHTML=`<ha-icon icon="mdi:microphone-outline"></ha-icon><span>${this.t("aiDictate")}</span>`;this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}
};
AH080MULTI.handleClick=async function(event){
 const button=event.composedPath().find(node=>node?.dataset?.action),action=button?.dataset?.action;if(action==="ai-assist"){this.aiFiles=[];this.aiContextDraft=""}if(action==="ai-remove-file"){const index=Number(button.dataset.index);if(Number.isInteger(index)){this.aiFiles?.splice(index,1);this.updateAIFileSelection(button.closest("form"))}return}if(action==="ai-start-dictation"){await this.startAIDictation(button);return}if(action==="ai-stop-dictation"){await this.stopAIDictation(button);return}if(action==="close"&&this.aiDictation)await this.cancelAIDictation();return AH080MULTIBase.handleClick.call(this,event)
};
AH080MULTI.handleChange=function(event){
 const input=event.composedPath()[0],form=input?.form;if(form?.dataset?.form==="ai-upload"&&input.type==="file"){const files=[...input.files||[]];if(files.length)this.aiAddFiles(files);input.value="";this.updateAIFileSelection(form);return}return AH080MULTIBase.handleChange.call(this,event)
};
AH080MULTI.handleSubmit=async function(event){
 const form=event.composedPath().find(node=>node?.tagName==="FORM");if(form?.dataset?.form!=="ai-upload")return AH080MULTIBase.handleSubmit.call(this,event);event.preventDefault();if(this.aiDictation){this.notify(this.t("aiStopBeforeAnalyze"),true);return}const files=this.aiFiles||[];if(!files.length){this.notify(this.t("aiFileRequired"),true);return}const submit=form.querySelector('button[type="submit"]'),entityId=form.elements.ai_entity_id?.value||"",context=String(form.elements.ai_context?.value||"").trim();this.aiContextDraft=context;if(submit)submit.disabled=true;this.notify(this.t("aiAnalyzing"));
 try{const uploaded=[];for(const file of files)uploaded.push(await this.aiUploadOne(file));this.aiSuggestion=await this.ws(`${D}/ai/analyze`,{upload_ids:uploaded.map(item=>item.upload_id),context,...(entityId?{entity_id:entityId}:{})});this.aiFiles=[];this.aiContextDraft="";this.modal={type:"ai-result"};this.render()}catch(error){if(submit)submit.disabled=false;this.notify(`${this.t("failed")}: ${error?.message||error}`,true)}
};
AH080MULTI.render=function(){AH080MULTIBase.render.call(this);if(this.modal?.type==="ai-upload")this.updateAIFileSelection(this.shadowRoot.querySelector('form[data-form="ai-upload"]'));this.shadowRoot.innerHTML+=`<style>.aiContext textarea{min-height:92px}.aiDictationBar{display:flex;align-items:flex-end;gap:10px;flex-wrap:wrap}.aiDictationBar>label{flex:1 1 260px}.aiDictationBar>button{flex:0 0 auto}.aiDictationBar small{width:100%;color:var(--secondary-text-color)}.aiDictationBar .recording{border-color:var(--error-color);color:var(--error-color)}.aiSelectedFiles{display:flex;flex-direction:column;gap:5px;margin-top:7px}.aiSelectedFiles>span{display:flex;align-items:center;gap:7px;padding:5px 7px;border-radius:8px;background:var(--secondary-background-color)}.aiSelectedFiles>span>span{flex:1;min-width:0;overflow-wrap:anywhere}.aiSelectedFiles button{padding:3px;border:0;background:transparent}@media(max-width:520px){.aiDictationBar>button{width:100%}}</style>`};
