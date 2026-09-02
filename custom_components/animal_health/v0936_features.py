from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from . import task_record_creation, task_records

_PATCHED = False
_COPY_MODES = {"duplicate", "replan"}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _task_origin(
    data: dict[str, Any],
    current: dict[str, Any] | None,
) -> dict[str, str] | None:
    mode = _text(data.get("copy_mode"))
    source_task_id = _text(data.get("source_task_id"))
    source_task_title = _text(data.get("source_task_title"))
    source_root_task_id = _text(data.get("source_root_task_id"))

    current_origin = (current or {}).get("task_origin")
    if not mode and not source_task_id:
        return dict(current_origin) if isinstance(current_origin, dict) else None
    if mode not in _COPY_MODES:
        raise ValueError(f"Unsupported task copy mode: {mode}")
    if not source_task_id:
        raise ValueError("A source task is required when copying or replanning a task")

    origin = {
        "mode": mode,
        "source_task_id": source_task_id,
        "source_task_title": source_task_title or source_task_id,
    }
    if mode == "replan":
        root_task_id = source_root_task_id or source_task_id
        if not source_root_task_id and isinstance(current_origin, dict):
            root_task_id = _text(current_origin.get("root_task_id")) or root_task_id
        origin["root_task_id"] = root_task_id
    return origin


def _wrap_builder(
    builder: Callable[..., dict[str, Any]],
) -> Callable[..., dict[str, Any]]:
    @wraps(builder)
    def build_task_template_v0936(
        task_kind_value: str,
        data: dict[str, Any],
        *,
        title: str,
        current: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        template = dict(
            builder(
                task_kind_value,
                data,
                title=title,
                current=current,
            )
        )
        origin = _task_origin(data, current)
        if origin is not None:
            template["task_origin"] = origin
        return template

    return build_task_template_v0936


def apply_v0936_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    builder = _wrap_builder(task_record_creation.build_task_template)
    task_record_creation.build_task_template = builder
    task_records.build_task_template = builder
