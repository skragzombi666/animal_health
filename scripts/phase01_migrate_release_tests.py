from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TESTS = {
    "tests/test_v0934_features.py": "test_034_release_version_and_shared_bundle_count_are_consistent",
    "tests/test_v0936_features.py": "test_036_release_version_and_shared_bundle_count_are_consistent",
    "tests/test_v0937_features.py": "test_037_release_version_and_shared_bundle_count_are_consistent",
    "tests/test_v0938_features.py": "test_038_release_version_and_shared_bundle_count_are_consistent",
    "tests/test_v0939_features.py": "test_039_release_version_and_shared_bundle_count_are_consistent",
}


def _replacement(function_name: str) -> str:
    return f'''def {function_name}() -> None:
    version = str(json.loads(MANIFEST.read_text(encoding="utf-8"))["version"])
    assert f'const V="{{version}}"' in DIST.read_text(encoding="utf-8")

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
'''


def main() -> None:
    for relative, function_name in TESTS.items():
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        if "LEGACY_MANIFEST =" not in text:
            anchor = 'ANDROID = ROOT / "android" / "app" / "build.gradle.kts"'
            constants = (
                'LEGACY_MANIFEST = FRONTEND / "legacy" / "manifest.json"\n'
                'DIST = FRONTEND / "dist" / "animal-health-panel.js"\n'
            )
            if anchor not in text:
                raise RuntimeError(f"Missing Android constant anchor in {relative}")
            text = text.replace(anchor, constants + anchor, 1)

        pattern = re.compile(
            rf"def {re.escape(function_name)}\(\) -> None:\n.*?(?=\ndef |\Z)",
            re.DOTALL,
        )
        text, count = pattern.subn(_replacement(function_name), text, count=1)
        if count != 1:
            raise RuntimeError(f"Could not replace {function_name} in {relative}")
        path.write_text(text, encoding="utf-8")
        print(f"Updated {relative}")


if __name__ == "__main__":
    main()
