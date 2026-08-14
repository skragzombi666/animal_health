from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "android" / "app"


def test_android_bridge_is_valid_javascript() -> None:
    bridge = (APP / "src/main/assets/android-shared-ui.js").read_text(encoding="utf-8")
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(bridge)
        file.flush()
        subprocess.run(["node", "--check", file.name], check=True)


def test_alpha5_shell_regression_markers() -> None:
    bridge = (APP / "src/main/assets/android-shared-ui.js").read_text(encoding="utf-8")
    activity = (APP / "src/main/java/ch/animalhealth/app/MainActivity.java").read_text(encoding="utf-8")
    backend = (APP / "src/main/java/ch/animalhealth/app/StandaloneBackend.java").read_text(encoding="utf-8")

    assert "<svg viewBox=\"0 0 24 24\"" in bridge
    assert "removeStandaloneHaWarning" in bridge
    assert "standalone:true" in bridge
    assert "applySystemWindowInsets(webView)" in activity
    assert "getSafeInsetTop()" in activity
    assert "BuildConfig.ANIMAL_HEALTH_VERSION" in backend
