from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "android"
APP = ANDROID / "app"
INTEGRATION = ROOT / "custom_components" / "animal_health"


def test_android_alpha_uses_exact_shared_frontend_and_full_local_adapter() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    version = manifest["version"]
    assert version == "0.9.0-alpha.5"

    gradle = (APP / "build.gradle.kts").read_text(encoding="utf-8")
    activity = (APP / "src/main/java/ch/animalhealth/app/MainActivity.java").read_text(encoding="utf-8")
    backend = (APP / "src/main/java/ch/animalhealth/app/StandaloneBackend.java").read_text(encoding="utf-8")
    bridge = (APP / "src/main/assets/android-shared-ui.js").read_text(encoding="utf-8")
    index = (APP / "src/main/assets/index.html").read_text(encoding="utf-8")
    frontend_parts = sorted((INTEGRATION / "frontend").glob("animal-health-panel.part*.js"))
    frontend = "".join(path.read_text(encoding="utf-8") for path in frontend_parts)

    assert f'val animalHealthVersion = "{version}"' in gradle
    assert 'versionName = animalHealthVersion' in gradle
    assert 'versionCode = 900005' in gradle
    assert 'buildConfigField("String", "ANIMAL_HEALTH_VERSION"' in gradle
    assert 'applicationId = "ch.animalhealth.app"' in gradle
    assert '../../custom_components/animal_health/frontend' in gradle
    assert '../../custom_components/animal_health/catalogs' in gradle
    assert 'bundleSharedFrontend' in gradle
    assert 'animal-health-panel.part*.js' in gradle
    assert 'animal-health-panel.js' in gradle
    assert 'ordered.joinToString(separator = "")' in gradle
    assert 'Expected 40 Animal Health frontend parts' in gradle
    assert 'dependsOn(bundleSharedFrontend, prepareAlphaSigning)' in gradle
    assert 'public static final String VERSION = BuildConfig.ANIMAL_HEALTH_VERSION;' in backend
    assert 'public static final String VERSION = "0.9.0-alpha.2";' not in backend
    assert 'file:///android_asset/index.html' in activity
    assert 'addJavascriptInterface' in activity
    assert 'WebView' in activity
    assert 'animal-health-panel' in index
    assert 'await loadScript("animal-health-panel.js")' in bridge
    assert 'for(let i=1;i<=40;i++)' not in bridge
    assert 'animal-health-panel.part${String(i).padStart(2,"0")}.js' not in bridge
    assert 'frontendErrors' in bridge
    assert 'callWS:request=>nativeCall(request)' in bridge
    assert 'callService:' in bridge

    # The source files are chunks of one JavaScript program, not standalone scripts.
    # part01 alone is intentionally syntactically incomplete; the concatenated source is valid.
    assert len(frontend_parts) == 40
    part01 = frontend_parts[0].read_text(encoding="utf-8")
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(part01)
        file.flush()
        assert subprocess.run(["node", "--check", file.name], check=False).returncode != 0
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(frontend)
        file.flush()
        subprocess.run(["node", "--check", file.name], check=True)

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
    ):
        assert visible_marker in frontend, visible_marker


def test_android_shell_respects_system_bars_and_cutouts() -> None:
    activity = (APP / "src/main/java/ch/animalhealth/app/MainActivity.java").read_text(encoding="utf-8")
    index = (APP / "src/main/assets/index.html").read_text(encoding="utf-8")

    assert 'getWindow().setNavigationBarColor(Color.WHITE)' in activity
    assert 'View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR' in activity
    assert 'applySystemWindowInsets(webView)' in activity
    assert 'setOnApplyWindowInsetsListener' in activity
    assert 'getSystemWindowInsetTop()' in activity
    assert 'getDisplayCutout()' in activity
    assert 'getSafeInsetTop()' in activity
    assert 'view.setPadding(left, top, right, bottom)' in activity
    assert 'target.requestApplyInsets()' in activity
    assert 'viewport-fit=cover' in index


def test_android_uses_local_vector_icons_and_no_ha_only_banner() -> None:
    bridge = (APP / "src/main/assets/android-shared-ui.js").read_text(encoding="utf-8")
    index = (APP / "src/main/assets/index.html").read_text(encoding="utf-8")

    assert 'class HaIcon extends HTMLElement' in bridge
    assert 'resolveIcon(icon)' in bridge
    assert '<svg viewBox="0 0 24 24"' in bridge
    assert '"mdi:account-group-outline":"users"' in bridge
    assert '"mdi:view-dashboard":"dashboard"' in bridge
    assert '"mdi:pill":"pill"' in bridge
    assert '👥' not in bridge
    assert '"mdi:pill":"◆"' not in bridge
    assert 'removeStandaloneHaWarning' in bridge
    assert 'reloadForFrontendMismatch089=function(){return false}' in bridge
    assert 'standalone:true' in bridge
    assert 'ha-icon svg' in index


def test_android_alpha_uses_stable_test_signing_key() -> None:
    gradle = (APP / "build.gradle.kts").read_text(encoding="utf-8")
    encoded = (ANDROID / "alpha-signing-keystore.b64").read_text(encoding="utf-8")
    decoded = base64.b64decode("".join(encoded.split()))

    # Public test key: stable on purpose so alpha APKs can update in place.
    assert hashlib.sha256(decoded).hexdigest() == "e954d951ad42420648ad1c463ad10596db9446a2a4f03cb7107fe91aba257ac3"
    assert 'create("alpha")' in gradle
    assert 'keyAlias = "animal-health-alpha"' in gradle
    assert 'signingConfig = signingConfigs.getByName("alpha")' in gradle
    assert 'alpha-signing-keystore.b64' in gradle
    assert 'Base64.getDecoder().decode(encoded)' in gradle


def test_android_release_workflow_builds_and_attaches_apk() -> None:
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    android_workflow = (ROOT / ".github/workflows/android.yml").read_text(encoding="utf-8")
    assert "gradle -p android :app:assembleDebug" in release
    assert "Standalone Android APK" in release
    assert "--prerelease" in release
    assert "gradle -p android :app:assembleDebug" in android_workflow
    assert "actions/upload-artifact@v4" in android_workflow
