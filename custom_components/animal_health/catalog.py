from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

_CATALOG_DIR = Path(__file__).parent / "catalogs"
_BREED_CATALOG_FILES = ("breeds.json", "breeds_supplement.json")
_DECORATION_RE = re.compile(r"\b(?:ad\s+us\.?\s*vet\.?|für|for)\b", re.IGNORECASE)
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True, slots=True)
class CatalogMatch:
    catalog_id: str
    catalog_version: str
    catalog_scope: str
    item_id: str
    name: str
    item: dict[str, Any]
    source: dict[str, Any] | list[dict[str, Any]] | None

    def event_metadata(self) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "catalog_source": "catalog",
            "catalog_id": self.item_id,
            "catalog_name": self.catalog_id,
            "catalog_version": self.catalog_version,
            "catalog_scope": self.catalog_scope,
        }
        for key in ("active_ingredients", "target_species", "authorisation_number"):
            if value := self.item.get(key):
                metadata[key] = value
        if self.source:
            metadata["catalog_reference"] = self.source
        return metadata


@lru_cache(maxsize=None)
def _load_catalog(filename: str) -> dict[str, Any]:
    with (_CATALOG_DIR / filename).open(encoding="utf-8") as file:
        document = json.load(file)
    if not isinstance(document.get("items"), list):
        raise ValueError(f"Invalid Animal Health catalogue: {filename}")
    return document


def _normalise(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        character for character in value if not unicodedata.combining(character)
    )
    value = value.replace("®", " ").replace("™", " ")
    value = _DECORATION_RE.sub(" ", value)
    return _NON_ALNUM_RE.sub("", value.casefold())


def _item_names(item: dict[str, Any]) -> list[str]:
    names = [
        item.get("id"),
        item.get("name"),
        item.get("display"),
        item.get("name_de"),
        item.get("name_en"),
        *(item.get("aliases") or []),
    ]
    return [str(name) for name in names if name]


def _match(document: dict[str, Any], item: dict[str, Any]) -> CatalogMatch:
    name = (
        item.get("name")
        or item.get("name_de")
        or item.get("name_en")
        or item["id"]
    )
    return CatalogMatch(
        catalog_id=document["catalog_id"],
        catalog_version=str(document["version"]),
        catalog_scope=str(document.get("scope", "international")),
        item_id=item["id"],
        name=str(name),
        item=item,
        source=document.get("source") or document.get("sources"),
    )


def _resolve(filename: str, value: str | None) -> CatalogMatch | None:
    if value is None:
        return None
    requested = _normalise(value)
    if not requested:
        return None
    document = _load_catalog(filename)
    for item in document["items"]:
        if requested in {_normalise(name) for name in _item_names(item)}:
            return _match(document, item)
    return None


def _resolve_breed(
    value: str | None,
    species_id: str | None = None,
) -> CatalogMatch | None:
    if value is None:
        return None
    requested = _normalise(value)
    if not requested:
        return None
    for filename in _BREED_CATALOG_FILES:
        document = _load_catalog(filename)
        for item in document["items"]:
            if species_id is not None and item.get("species_id") != species_id:
                continue
            if requested in {_normalise(name) for name in _item_names(item)}:
                return _match(document, item)
    return None


def breed_catalog_items() -> list[dict[str, Any]]:
    """Return the complete bundled breed/fallback catalogue."""
    return [
        dict(item)
        for filename in _BREED_CATALOG_FILES
        for item in _load_catalog(filename)["items"]
    ]


def resolve_species(value: str | None) -> CatalogMatch | None:
    return _resolve("species.json", value)


def resolve_breed(
    value: str | None,
    species_id: str | None = None,
) -> CatalogMatch | None:
    return _resolve_breed(value, species_id)


def resolve_medicine(value: str | None) -> CatalogMatch | None:
    return _resolve("medicines_ch.json", value)


def resolve_vaccine(value: str | None) -> CatalogMatch | None:
    return _resolve("vaccines_ch.json", value)


def _catalog_product_names(filename: str) -> list[str]:
    names = [
        str(
            item.get("name")
            or item.get("name_de")
            or item.get("name_en")
            or item["id"]
        )
        for item in _load_catalog(filename)["items"]
    ]
    return sorted(names, key=str.casefold)


def medicine_catalog_names() -> list[str]:
    """Return all medication names offered by the bundled catalogue."""
    return _catalog_product_names("medicines_ch.json")


def vaccine_catalog_names() -> list[str]:
    """Return all vaccine names offered by the bundled catalogue."""
    return _catalog_product_names("vaccines_ch.json")


def canonical_species_name(value: str) -> tuple[str, str | None]:
    match = resolve_species(value)
    if match is None:
        return value.strip(), None
    return str(match.item.get("name_de") or match.name), match.item_id


def canonical_breed_name(
    value: str | None,
    species_id: str | None,
) -> tuple[str | None, str | None]:
    if value is None or not value.strip():
        return None, None
    match = resolve_breed(value, species_id)
    if match is not None:
        return match.name, match.item_id
    foreign_match = resolve_breed(value)
    if foreign_match is not None and species_id is not None:
        expected_species = foreign_match.item.get("species_id")
        raise ValueError(
            f"Breed {foreign_match.name} belongs to {expected_species}, not {species_id}"
        )
    return value.strip(), None


def product_event_metadata(
    value: str,
    *,
    vaccine: bool = False,
) -> tuple[str, dict[str, Any]]:
    match = resolve_vaccine(value) if vaccine else resolve_medicine(value)
    if match is None:
        return value.strip(), {
            "catalog_source": "custom",
            "catalog_scope": "custom",
            "catalog_id": None,
        }
    return match.name, match.event_metadata()
