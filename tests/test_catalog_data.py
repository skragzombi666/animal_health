from __future__ import annotations

import json
from pathlib import Path

CATALOG_DIR = Path(__file__).parents[1] / "custom_components" / "animal_health" / "catalogs"


def load_catalog(name: str) -> dict:
    with (CATALOG_DIR / name).open(encoding="utf-8") as file:
        return json.load(file)


def test_catalogue_ids_are_unique() -> None:
    names = ("species.json", "breeds.json", "medicines_ch.json", "vaccines_ch.json")
    for name in names:
        items = load_catalog(name)["items"]
        identifiers = [item["id"] for item in items]
        assert len(identifiers) == len(set(identifiers))


def test_breeds_reference_known_species() -> None:
    species_ids = {item["id"] for item in load_catalog("species.json")["items"]}
    for breed in load_catalog("breeds.json")["items"]:
        assert breed["species_id"] in species_ids
        assert breed["display"]
        assert breed["name"]


def test_swiss_products_have_scope_and_source_date() -> None:
    for name in ("medicines_ch.json", "vaccines_ch.json"):
        document = load_catalog(name)
        assert document["scope"] == "CH"
        assert document["source"]["as_of"]
        for item in document["items"]:
            assert item["name"]
            assert item["target_species"]
