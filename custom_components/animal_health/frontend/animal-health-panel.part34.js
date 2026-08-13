const AH0814=AnimalHealthPanel.prototype;
const AH0814Base={body:AH0814.body,render:AH0814.render};
AH0814.brandUrl0814=function(){return this.p?.config?.brand_url||this.p?.brand_url||`/api/${D}/frontend/animal-health-brand.png?v=${V}`};
AH0814.brandMarkup0814=function(){return`<b class="brand brand0814"><img class="brandLogo0814" src="${esc(this.brandUrl0814())}" alt="Animal Health"><span>Animal Health</span></b>`};
AH0814.body=function(){
 let html=AH0814Base.body.call(this),brand=this.brandMarkup0814();
 if(/<b class="brand[^"]*">[\s\S]*?<\/b>/.test(html))html=html.replace(/<b class="brand[^"]*">[\s\S]*?<\/b>/,brand);
 else html=html.replace(/<b><ha-icon icon="mdi:paw"><\/ha-icon>\s*Animal Health<\/b>/,brand);
 return html
};
AH0814.render=function(){
 AH0814Base.render.call(this);
 this.shadowRoot.innerHTML+=`<style>.brand0814{display:flex!important;align-items:center!important;gap:8px!important}.brandLogo0814{width:36px;height:36px;display:block;object-fit:contain;border-radius:50%}.brandLoading0814{width:56px;height:56px;display:block;object-fit:contain;border-radius:50%;margin:0 auto 10px}@media(max-width:850px){.brandLogo0814{width:30px;height:30px}.brand0814 span{display:none}}</style>`;
 if(typeof document!=="undefined"){
  const label=this.t("loading"),nodes=[...this.shadowRoot.querySelectorAll("div,p,section")],target=nodes.find(node=>node.textContent?.trim()===label);
  if(target&&!target.querySelector(".brandLoading0814")){
   const image=document.createElement("img");image.className="brandLoading0814";image.src=this.brandUrl0814();image.alt="Animal Health";target.prepend(image)
  }
 }
};
