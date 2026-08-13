from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "custom_components" / "animal_health" / "brand" / "animal-health-logo-master.png"
UI = ROOT / "custom_components" / "animal_health" / "brand" / "animal-health-logo-ui.png"
HACS = ROOT / "icon.png"

with Image.open(MASTER) as source:
    source = source.convert("RGBA")
    source.thumbnail((128, 128), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (128, 128), (255, 255, 255, 0))
    x = (128 - source.width) // 2
    y = (128 - source.height) // 2
    canvas.alpha_composite(source, (x, y))
    canvas.save(UI, "PNG", optimize=True)
    canvas.save(HACS, "PNG", optimize=True)

print(f"generated {UI.relative_to(ROOT)} and {HACS.relative_to(ROOT)} from {MASTER.relative_to(ROOT)}")
