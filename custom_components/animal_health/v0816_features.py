from __future__ import annotations

from . import feature_api
from .v0816_exports import animal_health_pdf_bytes

_PATCHED = False


def apply_v0816_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    feature_api.animal_health_pdf_bytes = animal_health_pdf_bytes
    _PATCHED = True
