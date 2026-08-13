from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "custom_components" / "animal_health" / "assets" / "animal-health-logo-master.png"
BRAND_ICON = ROOT / "custom_components" / "animal_health" / "brand" / "icon.png"
UI_ICON = ROOT / "custom_components" / "animal_health" / "brand" / "icon-ui.png"
ROOT_ICON = ROOT / "icon.png"


def resized_pixels(size: int) -> tuple[tuple[int, int], bytes]:
    with Image.open(MASTER) as source:
        image = source.convert("RGBA")
        image.thumbnail((size, size), Image.Resampling.LANCZOS)
        return image.size, image.tobytes()


def write_variant(size: int, target: Path) -> None:
    with Image.open(MASTER) as source:
        image = source.convert("RGBA")
        image.thumbnail((size, size), Image.Resampling.LANCZOS)
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(target, "PNG", optimize=True, compress_level=9)


def check_variant(size: int, target: Path) -> None:
    expected_size, expected_pixels = resized_pixels(size)
    with Image.open(target) as current:
        actual = current.convert("RGBA")
        assert actual.size == expected_size, f"{target}: expected {expected_size}, got {actual.size}"
        assert actual.tobytes() == expected_pixels, f"{target}: not derived from canonical master"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    assert MASTER.is_file(), f"Missing canonical logo: {MASTER}"

    if args.check:
        check_variant(256, BRAND_ICON)
        check_variant(128, UI_ICON)
        assert ROOT_ICON.read_bytes() == BRAND_ICON.read_bytes(), "Root icon must mirror generated 256 px brand icon"
        master_size = MASTER.stat().st_size
        assert BRAND_ICON.stat().st_size < master_size / 2, "256 px brand icon is unexpectedly large"
        assert UI_ICON.stat().st_size < master_size / 4, "128 px UI icon is unexpectedly large"
        print("Animal Health branding assets are synchronized")
        return

    write_variant(256, BRAND_ICON)
    write_variant(128, UI_ICON)
    shutil.copyfile(BRAND_ICON, ROOT_ICON)
    print("Updated Animal Health branding assets from canonical master")


if __name__ == "__main__":
    main()
