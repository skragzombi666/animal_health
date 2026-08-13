from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"


def test_branding_uses_one_high_resolution_master_with_small_delivery_assets() -> None:
    master = INTEGRATION / "assets" / "animal-health-logo-master.png"
    brand = INTEGRATION / "brand" / "icon.png"
    ui = INTEGRATION / "brand" / "icon-ui.png"
    root_icon = ROOT / "icon.png"

    assert master.is_file()
    assert brand.is_file()
    assert ui.is_file()
    assert root_icon.read_bytes() == brand.read_bytes()

    with Image.open(master) as image:
        master_size = image.size
    with Image.open(brand) as image:
        assert max(image.size) <= 256
    with Image.open(ui) as image:
        assert max(image.size) <= 128

    assert max(master_size) > 256
    assert brand.stat().st_size < master.stat().st_size / 2
    assert ui.stat().st_size < master.stat().st_size / 4


def test_frontend_brand_endpoint_serves_small_ui_asset() -> None:
    panel = (INTEGRATION / "panel.py").read_text(encoding="utf-8")
    frontend = "".join(
        path.read_text(encoding="utf-8")
        for path in sorted((INTEGRATION / "frontend").glob("animal-health-panel.part*.js"))
    )

    assert '_BRAND_MASTER_PATH = Path(__file__).parent / "assets" / "animal-health-logo-master.png"' in panel
    assert '_BRAND_ICON_PATH = Path(__file__).parent / "brand" / "icon-ui.png"' in panel
    assert "_BRAND_CACHE_HEADERS" in panel
    assert "brandUrl0814" in frontend
    assert "brandLogo0814" in frontend
    assert "brandLoading0814" in frontend
    assert "animal-health-brand.svg" not in frontend
    assert not (INTEGRATION / "frontend" / "animal-health-brand.svg").exists()
