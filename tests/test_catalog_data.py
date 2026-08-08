from __future__ import annotations

import json
from pathlib import Path

CATALOG_DIR = Path(__file__).parents[1] / "custom_components" / "animal_health" / "catalogs"
BREED_CATALOGS = ("breeds.json", "breeds_supplement.json")


def load_catalog(name: str) -> dict:
    with (CATALOG_DIR / name).open(encoding="utf-8") as file:
        return json.load(file)


def breed_items() -> list[dict]:
    return [
        item
        for name in BREED_CATALOGS
        for item in load_catalog(name)["items"]
    ]


def test_catalogue_ids_are_unique() -> None:
    for name in ("species.json", "medicines_ch.json", "vaccines_ch.json"):
        items = load_catalog(name)["items"]
        identifiers = [item["id"] for item in items]
        assert len(identifiers) == len(set(identifiers))
    breed_identifiers = [item["id"] for item in breed_items()]
    assert len(breed_identifiers) == len(set(breed_identifiers))


def test_breeds_reference_known_species() -> None:
    species_ids = {item["id"] for item in load_catalog("species.json")["items"]}
    for breed in breed_items():
        assert breed["species_id"] in species_ids
        assert breed["display"]
        assert breed["name"]


def test_every_species_has_breed_or_fallback_options() -> None:
    species_ids = {item["id"] for item in load_catalog("species.json")["items"]}
    covered = {item["species_id"] for item in breed_items()}
    assert covered == species_ids
    for species_id in species_ids:
        assert any(
            item["species_id"] == species_id and item["id"].endswith(".other")
            for item in breed_items()
        )


def test_swiss_products_have_scope_and_source_date() -> None:
    for name in ("medicines_ch.json", "vaccines_ch.json"):
        document = load_catalog(name)
        assert document["scope"] == "CH"
        assert document["source"]["as_of"]
        for item in document["items"]:
            assert item["name"]
            assert item["target_species"]
