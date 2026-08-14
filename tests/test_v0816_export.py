from __future__ import annotations

from pathlib import Path
import runpy


def test_v0816_health_pdf_export() -> None:
    smoke = Path(__file__).with_name("v0816_export_smoke.py")
    namespace = runpy.run_path(str(smoke))
    namespace["main"]()
