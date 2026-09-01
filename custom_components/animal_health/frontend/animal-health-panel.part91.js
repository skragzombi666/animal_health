const AH032=AnimalHealthPanel.prototype;
const AH032Base={render:AH032.render};
AH032.render=function(){
 AH032Base.render.call(this);
 this.shadowRoot.innerHTML+=`<style>
.timelinePeriod029>.dayHeader023,.homeTimelineGroups029 .timelinePeriod029>.dayHeader023{display:flex!important;flex-direction:row!important;align-items:center!important;justify-content:space-between!important;gap:12px!important;width:100%!important;box-sizing:border-box!important}.timelinePeriod029>.dayHeader023>strong,.homeTimelineGroups029 .timelinePeriod029>.dayHeader023>strong{display:block!important;flex:1 1 auto!important;min-width:0!important;margin:0!important;line-height:1.2!important}.timelinePeriod029>.dayHeader023>span,.homeTimelineGroups029 .timelinePeriod029>.dayHeader023>span{display:inline-flex!important;flex:0 0 auto!important;align-items:center!important;justify-content:flex-end!important;align-self:center!important;width:auto!important;margin:0 0 0 auto!important;padding:0!important;line-height:1.2!important;text-align:right!important}
</style>`
};
