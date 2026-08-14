const AH0816Final=AnimalHealthPanel.prototype;
const AH0816FinalOverview=AH0816Final.overview;
AH0816Final.overview=function(){
 let html=AH0816FinalOverview.call(this);
 if((this.overviewScope0816||"today")==="today")html=html.replace(`<h2>${this.t("actionNow")}</h2>`,`<h2>${this.t("todayRelevant0816")}</h2>`);
 return html
};
