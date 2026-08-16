from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_branding_keeps_full_resolution_master_and_small_runtime_asset() -> None:
    master = INTEGRATION / "brand" / "icon.png"
    ui = FRONTEND / "animal-health-brand.svg"
    root_icon = ROOT / "icon.png"

    assert master.is_file()
    assert ui.is_file()
    assert root_icon.is_file()
    assert root_icon.read_bytes() == master.read_bytes()
    assert master.stat().st_size > 100_000
    assert ui.stat().st_size < 50_000

    source = ui.read_text(encoding="utf-8")
    assert 'aria-label="Animal Health"' in source
    assert "data:image/png;base64," in source


def test_frontend_brand_endpoint_serves_lightweight_versioned_asset() -> None:
    panel = (INTEGRATION / "panel.py").read_text(encoding="utf-8")
    frontend = "".join(
        path.read_text(encoding="utf-8")
        for path in sorted(FRONTEND.glob("animal-health-panel.part*.js"))
    )
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))

    assert '_BRAND_MASTER_PATH = Path(__file__).parent / "brand" / "icon.png"' in panel
    assert '_BRAND_UI_PATH = _FRONTEND_DIR / "animal-health-brand.svg"' in panel
    assert "_BRAND_CACHE_HEADERS" in panel
    assert "BRAND_REVISION" in panel
    assert "brand_url = f" in panel
    assert "brandUrl0814" in frontend
    assert "brandLogo0814" in frontend
    assert "brandLoading0814" in frontend
    assert manifest["version"]
    assert f'const V="{manifest["version"]}",D="animal_health"' in frontend
