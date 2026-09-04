from __future__ import annotations

import base64
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "android"
APP = ANDROID / "app"
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"
DIST = FRONTEND / "dist" / "animal-health-panel.js"


def test_android_alpha_uses_shared_frontend_and_full_local_adapter() -> None:
    android_version = "0.9.0-alpha.7"

    gradle = (APP / "build.gradle.kts").read_text(encoding="utf-8")
    activity = (APP / "src/main/java/ch/animalhealth/app/MainActivity.java").read_text(
        encoding="utf-8"
    )
    backend = (
        APP / "src/main/java/ch/animalhealth/app/StandaloneBackend.java"
    ).read_text(encoding="utf-8")
    bridge = (APP / "src/main/assets/android-shared-ui.js").read_text(
        encoding="utf-8"
    )
    index = (APP / "src/main/assets/index.html").read_text(encoding="utf-8")
    frontend = DIST.read_text(encoding="utf-8")

    assert f'val animalHealthVersion = "{android_version}"' in gradle
    assert "versionName = animalHealthVersion" in gradle
    assert "versionCode = 900007" in gradle
    assert 'buildConfigField("String", "ANIMAL_HEALTH_VERSION"' in gradle
    assert 'applicationId = "ch.animalhealth.app"' in gradle
    assert (
        'val sharedFrontendBundle = sharedFrontendRoot.resolve("dist/animal-health-panel.js")'
        in gradle
    )
    assert (
        'val sharedFrontendBrand = sharedFrontendRoot.resolve("animal-health-brand.svg")'
        in gradle
    )
    assert "prepareSharedFrontendAssets" in gradle
    assert 'target.resolve("animal-health-panel.js")' in gradle
    assert 'target.resolve("animal-health-brand.svg")' in gradle
    assert "sharedFrontendBundle.copyTo" in gradle
    assert "sharedFrontendBrand.copyTo" in gradle
    assert "dependsOn(prepareSharedFrontendAssets, prepareAlphaSigning)" in gradle
    assert "animal-health-panel.part*.js" not in gradle
    assert "bundleSharedFrontend" not in gradle
    assert "ordered.size == 99" not in gradle
    assert "ordered.joinToString" not in gradle
    assert "../../custom_components/animal_health/catalogs" in gradle
    assert (
        "public static final String VERSION = BuildConfig.ANIMAL_HEALTH_VERSION;"
        in backend
    )
    assert 'public static final String VERSION = "0.9.0-alpha.2";' not in backend
    assert "file:///android_asset/index.html" in activity
    assert "addJavascriptInterface" in activity
    assert "WebView" in activity
    assert "animal-health-panel" in index
    assert 'await loadScript("animal-health-panel.js")' in bridge
    assert "for(let i=1;i<=40;i++)" not in bridge
    assert 'animal-health-panel.part${String(i).padStart(2,"0")}.js' not in bridge
    assert "frontendErrors" in bridge
    assert "callWS:request=>nativeCall(request)" in bridge
    assert "callService:" in bridge

    subprocess.run(["node", "--check", str(DIST)], check=True)

    for marker in (
        "animal_health/dashboard",
        "animal_health/catalog",
        "animal_health/features",
        "animal_health/animal_detail",
        "animal_health/groups/create",
        "animal_health/animal_group/set",
        "animal_health/tags/create",
        "animal_health/tags/set",
        "animal_health/animal_photo/set",
        "animal_health/v081/state",
        "animal_health/v081/group_event/create",
        "animal_health/v081/group_task/create",
        "animal_health/v083/state",
        "animal_health/v083/animal_metadata/set",
        "animal_health/v0817/state",
        "animal_health/v0817/medications/batch_record",
        "CREATE TABLE groups",
        "CREATE TABLE tags",
        "CREATE TABLE occurrences",
        "CREATE TABLE attachments",
        "recurrence_type",
        "exportJson",
    ):
        assert marker in backend, marker

    for visible_marker in (
        "Tiergruppen",
        "Tags",
        "Kalender",
        "Medikamente verwalten",
        "Gesundheitschronik",
        "day-repeat-0817",
        "animalCaptureIcons090A7",
    ):
        assert visible_marker in frontend, visible_marker


def test_android_shell_respects_system_bars_and_cutouts() -> None:
    activity = (APP / "src/main/java/ch/animalhealth/app/MainActivity.java").read_text(
        encoding="utf-8"
    )
    index = (APP / "src/main/assets/index.html").read_text(encoding="utf-8")

    assert "getWindow().setNavigationBarColor(Color.WHITE)" in activity
    assert (
        "View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | "
        "View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR"
    ) in activity
    assert "applySystemWindowInsets(webView)" in activity
    assert "setOnApplyWindowInsetsListener" in activity
    assert "getSystemWindowInsetTop()" in activity
    assert "getDisplayCutout()" in activity
    assert "getSafeInsetTop()" in activity
    assert "view.setPadding(left, top, right, bottom)" in activity
    assert "target.requestApplyInsets()" in activity
    assert "viewport-fit=cover" in index
    assert "padding-top:max(32px,env(safe-area-inset-top,0px))" in index
    assert "padding-left:env(safe-area-inset-left,0px)" in index
    assert "padding-right:env(safe-area-inset-right,0px)" in index


def test_android_uses_local_vector_icons_and_mobile_overrides() -> None:
    bridge = (APP / "src/main/assets/android-shared-ui.js").read_text(
        encoding="utf-8"
    )
    index = (APP / "src/main/assets/index.html").read_text(encoding="utf-8")
    overrides = (APP / "src/main/assets/android-shell-overrides.js").read_text(
        encoding="utf-8"
    )

    assert "class HaIcon extends HTMLElement" in bridge
    assert "resolveIcon(icon)" in bridge
    assert '<svg viewBox="0 0 24 24"' in bridge
    assert '"mdi:account-group-outline":"users"' in bridge
    assert '"mdi:view-dashboard":"dashboard"' in bridge
    assert '"mdi:pill":"pill"' in bridge
    assert "👥" not in bridge
    assert '"mdi:pill":"◆"' not in bridge
    assert "removeStandaloneHaWarning" in bridge
    assert "reloadForFrontendMismatch089=function(){return false}" in bridge
    assert "standalone:true" in bridge
    assert "ha-icon svg" in index
    assert '<script src="android-shell-overrides.js" defer></script>' in index
    assert "header nav button ha-icon" in overrides
    assert ".heading .search ha-icon" in overrides
    assert 'style[data-android-shell="alpha6"]' in overrides
    assert "MutationObserver" in overrides
    subprocess.run(
        ["node", "--check", str(APP / "src/main/assets/android-shell-overrides.js")],
        check=True,
    )


def test_android_alpha_uses_stable_test_signing_key() -> None:
    gradle = (APP / "build.gradle.kts").read_text(encoding="utf-8")
    encoded = (ANDROID / "alpha-signing-keystore.b64").read_text(encoding="utf-8")
    decoded = base64.b64decode("".join(encoded.split()))

    assert (
        hashlib.sha256(decoded).hexdigest()
        == "e954d951ad42420648ad1c463ad10596db9446a2a4f03cb7107fe91aba257ac3"
    )
    assert 'create("alpha")' in gradle
    assert 'keyAlias = "animal-health-alpha"' in gradle
    assert 'signingConfig = signingConfigs.getByName("alpha")' in gradle
    assert "alpha-signing-keystore.b64" in gradle
    assert "Base64.getDecoder().decode(encoded)" in gradle


def test_ha_release_workflow_is_decoupled_from_android() -> None:
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    android_workflow = (ROOT / ".github/workflows/android.yml").read_text(
        encoding="utf-8"
    )

    assert "gh release create" in release
    assert "gradle -p android :app:assembleDebug" not in release
    assert "Standalone Android APK" not in release
    assert "--prerelease" not in release
    assert ".github/workflows/release.yml" not in android_workflow
    assert "gradle -p android :app:assembleDebug" in android_workflow
    assert "actions/upload-artifact@v4" in android_workflow
