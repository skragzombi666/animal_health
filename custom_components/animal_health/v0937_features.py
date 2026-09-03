from __future__ import annotations

import io
import re
import secrets
from functools import wraps
from pathlib import Path
from typing import Any

from . import feature_store, v0924_features

_PATCHED = False
_THUMBNAIL_SIZE = (96, 96)
_PREVIEW_SIZE = (1600, 1600)
_VARIANT_CACHE_DIR = ".variants"


def _safe_attachment_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "attachment"))
    return safe[:120] or "attachment"


def _variant_cache_root(path: Path) -> Path:
    return path.parent / _VARIANT_CACHE_DIR


def _variant_cache_path(path: Path, attachment_id: str, variant: str) -> Path:
    stat = path.stat()
    name = (
        f"{_safe_attachment_id(attachment_id)}.{variant}."
        f"{stat.st_size}.{stat.st_mtime_ns}.jpg"
    )
    return _variant_cache_root(path) / name


def _remove_cached_variants(root: Path, attachment_id: str) -> None:
    safe_id = _safe_attachment_id(attachment_id)
    cache_root = root / _VARIANT_CACHE_DIR
    if not cache_root.is_dir():
        return
    for cached in cache_root.glob(f"{safe_id}.*.jpg"):
        cached.unlink(missing_ok=True)


def _render_image_variant(path: Path, variant: str) -> bytes:
    from PIL import Image, ImageOps

    max_size = _THUMBNAIL_SIZE if variant == "thumbnail" else _PREVIEW_SIZE
    quality = 52 if variant == "thumbnail" else 84
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        if image.mode not in {"RGB", "L"}:
            background = Image.new("RGB", image.size, "white")
            if "A" in image.getbands():
                background.paste(image, mask=image.getchannel("A"))
            else:
                background.paste(image.convert("RGB"))
            image = background
        elif image.mode == "L":
            image = image.convert("RGB")
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=quality, optimize=True)
        return output.getvalue()


def _image_variant_v0937(
    path: Path,
    attachment_id: str,
    variant: str,
) -> tuple[bytes, str]:
    if variant == "original":
        return path.read_bytes(), "application/octet-stream"
    if variant not in {"thumbnail", "preview"}:
        raise ValueError(f"Unsupported attachment image variant: {variant}")

    target = _variant_cache_path(path, attachment_id, variant)
    try:
        return target.read_bytes(), "image/jpeg"
    except FileNotFoundError:
        pass

    content = _render_image_variant(path, variant)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f"{target.name}.{secrets.token_hex(6)}.tmp")
    temporary.write_bytes(content)
    temporary.replace(target)
    safe_id = _safe_attachment_id(attachment_id)
    for stale in target.parent.glob(f"{safe_id}.{variant}.*.jpg"):
        if stale != target:
            stale.unlink(missing_ok=True)
    return content, "image/jpeg"


def apply_v0937_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    v0924_features._image_variant = _image_variant_v0937  # type: ignore[assignment]  # noqa: SLF001

    original_create = feature_store.AnimalHealthFeatureStore._create_attachment_sync

    @wraps(original_create)
    def create_attachment_v0937(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        item = original_create(self, *args, **kwargs)
        if str(item.get("media_type") or "").startswith("image/"):
            try:
                _stored, path = self._attachment_file_sync(str(item["id"]))
                _image_variant_v0937(path, str(item["id"]), "thumbnail")
            except Exception:  # noqa: BLE001
                pass
        return item

    feature_store.AnimalHealthFeatureStore._create_attachment_sync = create_attachment_v0937

    original_delete = feature_store.AnimalHealthFeatureStore._delete_attachment_sync

    @wraps(original_delete)
    def delete_attachment_v0937(self, attachment_id: str) -> None:
        original_delete(self, attachment_id)
        _remove_cached_variants(self._attachment_root, attachment_id)

    feature_store.AnimalHealthFeatureStore._delete_attachment_sync = delete_attachment_v0937
