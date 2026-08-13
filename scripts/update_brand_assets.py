from __future__ import annotations

import argparse
import base64
import io
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "custom_components" / "animal_health" / "brand" / "icon.png"
UI_ASSET = ROOT / "custom_components" / "animal_health" / "frontend" / "animal-health-brand.svg"
ROOT_ICON = ROOT / "icon.png"
UI_SIZE = 48


def build_ui_svg() -> str:
    with Image.open(MASTER) as source:
        image = source.convert("RGBA")
        image.thumbnail((UI_SIZE, UI_SIZE), Image.Resampling.LANCZOS)
        width, height = image.size
        buffer = io.BytesIO()
        image.save(buffer, "PNG", optimize=True, compress_level=9)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        'role="img" aria-label="Animal Health">'
        f'<image width="{width}" height="{height}" href="data:image/png;base64,{encoded}"/>'
        '</svg>'
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    assert MASTER.is_file(), f"Missing canonical logo: {MASTER}"

    if args.check:
        assert ROOT_ICON.is_file(), f"Missing HACS/repository icon: {ROOT_ICON}"
        assert ROOT_ICON.read_bytes() == MASTER.read_bytes(), "Root icon must mirror the canonical master"
        assert UI_ASSET.is_file(), f"Missing UI logo: {UI_ASSET}"
        ui_source = UI_ASSET.read_text(encoding="utf-8")
        assert 'aria-label="Animal Health"' in ui_source
        assert "data:image/png;base64," in ui_source
        assert UI_ASSET.stat().st_size < 50_000, "Runtime logo is unexpectedly large"
        print("Animal Health branding asset layout is valid")
        return

    UI_ASSET.write_text(build_ui_svg(), encoding="utf-8")
    shutil.copyfile(MASTER, ROOT_ICON)
    print("Updated Animal Health branding assets from canonical master")


if __name__ == "__main__":
    main()
