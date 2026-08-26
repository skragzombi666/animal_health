from __future__ import annotations

from . import v0912_features as treatment_features
from . import v0923_features

_PATCHED = False


def apply_v0923_patches() -> None:
    """Bind 0.9.23 to the final treatment executor after legacy patch layers."""
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True
    v0923_features._execute_treatment_sync = treatment_features._execute_treatment_sync
