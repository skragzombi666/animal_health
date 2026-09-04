from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "custom_components" / "animal_health" / "frontend" / "src"
ACTIVE_READ_PATHS = (
    SOURCE / "app" / "read-only-animals.js",
    SOURCE / "domain" / "animals" / "selectors.js",
    SOURCE / "ui" / "read-only" / "components.js",
    SOURCE / "ui" / "read-only" / "format.js",
    SOURCE / "ui" / "views" / "overview.js",
    SOURCE / "ui" / "views" / "animals.js",
    SOURCE / "ui" / "views" / "animal-detail.js",
)
RAW_BACKEND_ALIASES = (
    "animal_id",
    "group_id",
    "tag_ids",
    "latest_weight",
    "occurred_at",
    "scheduled_for",
    "target_scope",
    "is_overdue",
    "name_de",
    "name_en",
)


def test_active_read_slice_uses_only_canonical_dto_fields() -> None:
    for path in ACTIVE_READ_PATHS:
        source = path.read_text(encoding="utf-8")
        for alias in RAW_BACKEND_ALIASES:
            assert alias not in source, f"{path.relative_to(ROOT)}: {alias}"
