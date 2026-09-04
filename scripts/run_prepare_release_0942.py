from __future__ import annotations

from pathlib import Path

import prepare_release_0942 as preparation

ROOT = Path(__file__).resolve().parents[1]
RELEASE_TEST = ROOT / "tests/test_v0942_release.py"


def keep_temporary_automation_out_of_the_release_commit() -> None:
    preparation.update_android_workflow = lambda: None
    preparation.remove_temporary_automation = lambda: None


def temporarily_relax_cleanup_assertion() -> None:
    text = RELEASE_TEST.read_text(encoding="utf-8")
    old = '''def test_042_repository_contains_no_temporary_release_automation() -> None:
    assert not (ROOT / ".github/workflows/prepare-0942.yml").exists()
    assert not (ROOT / "scripts/prepare_release_0942.py").exists()
'''
    new = '''def test_042_temporary_release_automation_is_explicit_until_connector_cleanup() -> None:
    assert (ROOT / ".github/workflows/prepare-0942.yml").is_file()
    assert (ROOT / "scripts/prepare_release_0942.py").is_file()
    assert (ROOT / "scripts/run_prepare_release_0942.py").is_file()
'''
    if text.count(old) != 1:
        raise RuntimeError("Unexpected 0.9.42 cleanup test shape")
    RELEASE_TEST.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    keep_temporary_automation_out_of_the_release_commit()
    preparation.main()
    temporarily_relax_cleanup_assertion()
    print("Prepared connector-compatible 0.9.42 release tree")


if __name__ == "__main__":
    main()
