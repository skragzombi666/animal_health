from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"
SOURCE = FRONTEND / "animal-health-panel.part97.js"
FEATURES = INTEGRATION / "v0937_features.py"
PANEL = INTEGRATION / "panel.py"
MANIFEST = INTEGRATION / "manifest.json"
LEGACY_MANIFEST = FRONTEND / "legacy" / "manifest.json"
DIST = FRONTEND / "dist" / "animal-health-panel.js"
ANDROID = ROOT / "android" / "app" / "build.gradle.kts"


def test_037_navigation_uses_a_direct_synchronous_click_path() -> None:
    frontend = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "AH037.handleClick=function(event)",
        "AH033Base.handleClick.call(this,event)",
        'action==="create-task"',
        'action==="task-duplicate-034"',
        'action==="task-overview-036"',
        "removeInternalHistory037",
        "AH037.connectedCallback=function()",
        "AH037.disconnectedCallback=function()",
    ):
        assert marker in frontend
    for marker in (
        "AH037.handleClick=async",
        "history.pushState",
        "history.replaceState",
        "history.back()",
        "this.navSnapshot033(",
        "this.requestBack034(",
        "this.restoreNavSnapshot034(",
    ):
        assert marker not in frontend


def test_037_thumbnails_are_requested_before_manual_opening() -> None:
    frontend = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "attachmentImageIds037",
        "fetchAttachmentUrls037",
        "refreshAttachmentUrls024=async function",
        "ensureAttachmentUrls037",
        "attachment_ids:ids.slice(index,index+100)",
        "urls[id]?.thumbnail",
        "queueMicrotask(()=>void this.ensureAttachmentUrls037())",
        'loading="eager"',
        'decoding="async"',
        'width="48"',
        'height="48"',
    ):
        assert marker in frontend


def test_037_server_uses_small_persistent_thumbnail_variants() -> None:
    backend = FEATURES.read_text(encoding="utf-8")
    for marker in (
        "_THUMBNAIL_SIZE = (96, 96)",
        '_VARIANT_CACHE_DIR = ".variants"',
        'quality = 52 if variant == "thumbnail" else 84',
        "_variant_cache_path",
        "temporary.replace(target)",
        "_create_attachment_sync",
        '_image_variant_v0937(path, str(item["id"]), "thumbnail")',
        "_delete_attachment_sync",
        "_remove_cached_variants",
        "v0924_features._image_variant = _image_variant_v0937",
    ):
        assert marker in backend
    panel = PANEL.read_text(encoding="utf-8")
    assert "from .v0937_features import apply_v0937_patches" in panel
    assert "apply_v0937_patches()" in panel


def test_037_frontend_behaviour_is_immediate_and_retry_safe() -> None:
    frontend = SOURCE.read_text(encoding="utf-8")
    harness = r'''
const D="animal_health";
class AnimalHealthPanel{}
const AH033Base={
 connectedCallback:function(){this.connected=true},
 disconnectedCallback:function(){this.disconnected=true},
 handleClick:function(event){this.baseAction=event.composedPath()[0]?.dataset?.action||"";return "base"},
 handleSubmit:async function(){return "submitted"}
};
AnimalHealthPanel.prototype.attachmentList=function(items){
 return(items||[]).map(item=>this.attachmentUrls024?.[item.id]?.thumbnail?`<img src="${this.attachmentUrls024[item.id].thumbnail}">`:"<ha-icon></ha-icon>").join("")
};
AnimalHealthPanel.prototype.attachmentStrip026=function(event){
 const item=(this.detail?.attachments||[]).find(value=>value.event_id===event.id);
 return item&&this.attachmentUrls024?.[item.id]?.thumbnail?`<img src="${this.attachmentUrls024[item.id].thumbnail}">`:"<ha-icon></ha-icon>"
};
AnimalHealthPanel.prototype.refreshAttachmentUrls024=async function(){};
AnimalHealthPanel.prototype.render=function(){this.baseRenderCount=(this.baseRenderCount||0)+1};
globalThis.removeEventListener=function(){};
'''
    checks = r'''
(async()=>{
 const panel=new AnimalHealthPanel();
 panel.detail={animal:{id:"AH-1"},attachments:[{id:"AT-1",event_id:"EV-1",media_type:"image/jpeg"}]};
 panel.attachmentUrls024={};
 let calls=0;
 panel.ws=async(type,payload)=>{
  calls++;
  if(type!=="animal_health/v0924/attachment/urls")throw new Error("unexpected command");
  if(payload.attachment_ids.join(",")!=="AT-1")throw new Error("wrong attachment ids");
  return{urls:{"AT-1":{thumbnail:"/thumb/AT-1"}}}
 };
 panel.render();
 await new Promise(resolve=>setTimeout(resolve,0));
 await new Promise(resolve=>setTimeout(resolve,0));
 if(calls!==1)throw new Error(`expected one thumbnail URL request, got ${calls}`);
 if(panel.attachmentUrls024["AT-1"]?.thumbnail!=="/thumb/AT-1")throw new Error("thumbnail URL was not stored");
 if(panel.baseRenderCount!==2)throw new Error(`expected one recovery render, got ${panel.baseRenderCount}`);
 const markup=panel.attachmentList(panel.detail.attachments);
 if(!markup.includes('loading="eager"')||!markup.includes('decoding="async"'))throw new Error("thumbnail loading attributes missing");
 const create={dataset:{action:"create-task"}};
 const result=panel.handleClick({composedPath:()=>[create]});
 if(result&&typeof result.then==="function")throw new Error("normal click path became asynchronous");
 if(panel.baseAction!=="create-task")throw new Error("create task did not reach the base click handler immediately");
 panel.taskById036=()=>({id:"TK-1"});
 panel.openTaskCopy034=(task,mode)=>{panel.copy=[task.id,mode]};
 const duplicate={dataset:{action:"task-duplicate-034",id:"TK-1"}};
 panel.handleClick({composedPath:()=>[duplicate]});
 if(panel.copy?.join(",")!=="TK-1,duplicate")throw new Error("task duplicate was not handled synchronously");
 process.stdout.write("ok");
})().catch(error=>{console.error(error);process.exit(1)});
'''
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as script:
        script.write(harness)
        script.write("\n")
        script.write(frontend)
        script.write("\n")
        script.write(checks)
        script.flush()
        result = subprocess.run(
            ["node", script.name],
            check=False,
            capture_output=True,
            text=True,
        )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "ok"


def test_037_release_version_and_shared_bundle_count_are_consistent() -> None:
    version = str(json.loads(MANIFEST.read_text(encoding="utf-8"))["version"])
    assert f'const V="{version}"' in DIST.read_text(encoding="utf-8")

    legacy_manifest = json.loads(LEGACY_MANIFEST.read_text(encoding="utf-8"))
    parts = legacy_manifest["parts"]
    assert legacy_manifest["reference_version"] == "0.9.41"
    assert len(parts) == 99
    assert parts[0].endswith("animal-health-panel.part01.js")
    assert parts[-1].endswith("animal-health-panel.part99.js")

    android = ANDROID.read_text(encoding="utf-8")
    assert 'val animalHealthVersion = "0.9.0-alpha.7"' in android
    assert "versionCode = 900007" in android
    assert 'resolve("dist/animal-health-panel.js")' in android
    assert "prepareSharedFrontendAssets" in android
    assert "animal-health-panel.part*.js" not in android
    assert "ordered.size ==" not in android
