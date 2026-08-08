from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).parents[1]
COMPONENT_DIR = ROOT / "custom_components" / "animal_health"
CATALOG_DIR = COMPONENT_DIR / "catalogs"
PACKAGE = "custom_components.animal_health"
BREED_FILES = ("breeds.json", "breeds_supplement.json")
GENERIC_SUFFIXES = (".unknown", ".other", ".mixed")
BREED_BEARING_SPECIES = {
    "dog",
    "cat",
    "chicken",
    "duck",
    "goose",
    "turkey",
    "quail",
    "pigeon",
    "rabbit",
    "guinea_pig",
    "horse",
    "donkey",
    "cattle",
    "sheep",
    "goat",
    "pig",
    "alpaca",
    "llama",
    "bee",
}


def _load_json(name: str) -> dict:
    return json.loads((CATALOG_DIR / name).read_text(encoding="utf-8"))


def _load_catalog_module() -> types.ModuleType:
    custom_components = types.ModuleType("custom_components")
    custom_components.__path__ = [str(ROOT / "custom_components")]
    sys.modules["custom_components"] = custom_components
    package = types.ModuleType(PACKAGE)
    package.__path__ = [str(COMPONENT_DIR)]
    sys.modules[PACKAGE] = package
    spec = importlib.util.spec_from_file_location(
        f"{PACKAGE}.catalog", COMPONENT_DIR / "catalog.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    species = _load_json("species.json")["items"]
    species_ids = {item["id"] for item in species}
    breeds = [
        item
        for filename in BREED_FILES
        for item in _load_json(filename)["items"]
    ]

    breed_ids = [item["id"] for item in breeds]
    assert len(breed_ids) == len(set(breed_ids)), "Breed IDs must be globally unique"
    assert all(item["species_id"] in species_ids for item in breeds)

    covered_species = {item["species_id"] for item in breeds}
    assert covered_species == species_ids, (
        "Every selectable species must have actual breeds or explicit generic fallbacks; "
        f"missing={sorted(species_ids - covered_species)}"
    )

    for species_id in species_ids:
        assert any(
            item["species_id"] == species_id and item["id"].endswith(".other")
            for item in breeds
        ), f"Missing 'other' fallback for {species_id}"

    for species_id in BREED_BEARING_SPECIES:
        actual = [
            item
            for item in breeds
            if item["species_id"] == species_id
            and not item["id"].endswith(GENERIC_SUFFIXES)
        ]
        assert actual, f"Expected real breed/recognized type entries for {species_id}"

    sheep_names = {
        item["name"] for item in breeds if item["species_id"] == "sheep"
    }
    assert {
        "Weisses Alpenschaf",
        "Braunköpfiges Fleischschaf",
        "Schwarzbraunes Bergschaf",
        "Walliser Schwarznasenschaf",
        "Engadinerschaf",
    } <= sheep_names

    catalog = _load_catalog_module()
    assert catalog.canonical_breed_name("Mischling", "cat")[1] == "cat.mixed"
    assert (
        catalog.canonical_breed_name("Andere / nicht aufgeführt", "sheep")[1]
        == "sheep.other"
    )
    assert catalog.canonical_breed_name("Weisses Alpenschaf", "sheep")[1] == "sheep.white_alpine"
    try:
        catalog.canonical_breed_name("Angora", "sheep")
    except ValueError:
        pass
    else:
        raise AssertionError("A rabbit breed must still be rejected for sheep")

    print(
        "breed catalogue smoke test passed: "
        f"{len(species_ids)} species, {len(breeds)} breed/fallback entries"
    )


if __name__ == "__main__":
    main()
