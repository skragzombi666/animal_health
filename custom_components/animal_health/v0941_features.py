from __future__ import annotations

from . import v0815_features
from .task_store import TaskStore
from .v0941_migration import (
    initialize_sync as _initialize_v0941_sync,
    recover_legacy_required_occurrences_once,
)
from .v0941_occurrences import ensure_preserving_occurrences

_PATCHED = False


def apply_v0941_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    TaskStore._ensure_occurrences_for_task = ensure_preserving_occurrences
    v0815_features._initialize_v0815_sync = _initialize_v0941_sync
    _PATCHED = True
