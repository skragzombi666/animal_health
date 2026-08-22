from __future__ import annotations

from . import v0816_exports

_PATCHED = False


def apply_v0817_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    v0816_exports._VALUE_MAPS.setdefault("dose_unit", {}).update(
        {
            "mcg": "µg",
            "mg": "mg",
            "g": "g",
            "ul": "µl",
            "ml": "ml",
            "drop": "Tropfen",
            "tablet": "Tablette",
            "dose": "Dosis",
            "mark": "Teilstrich",
            "pinch": "Messerspitze",
        }
    )
    _PATCHED = True
