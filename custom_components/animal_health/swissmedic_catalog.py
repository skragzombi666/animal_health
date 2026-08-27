from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from typing import Any

SWISSMEDIC_SOURCE_ID = "swissmedic_ch"
SWISSMEDIC_DATASET_ID = "ZL172@swissmedic"
SWISSMEDIC_OGD_URL = "https://ogd.swissmedic.cloud/ogd-arzneimittel/Daten/OGD.zip"
SWISSMEDIC_LANDING_URL = "https://opendata.swiss/de/dataset/daten-von-human-und-tierarzneimitteln"

_NEGATIVE_STATUS = (
    "nicht mehr zugelassen",
    "widerruf",
    "abgelaufen",
    "no longer authorised",
    "not authorised",
    "revoked",
    "expired",
)
_ACTIVE_SUBSTANCE = (
    "wirkstoff",
    "active substance",
    "active ingredient",
    "principe actif",
    "principio attivo",
)
_SPECIES = (
    (("pferd", "equine", "horse"), "horse"),
    (("hund", "canine", "dog"), "dog"),
    (("katze", "feline", "cat"), "cat"),
    (("rind", "kalb", "bovine", "cattle", "calf"), "cattle"),
    (("schwein", "porcine", "pig"), "pig"),
    (("huhn", "hühner", "geflügel", "poultry", "chicken"), "chicken"),
    (("kaninchen", "rabbit"), "rabbit"),
    (("schaf", "ovine", "sheep"), "sheep"),
    (("ziege", "caprine", "goat"), "goat"),
)
_ROUTE_MAP = (
    (("intraven", "intravenous"), "intravenous"),
    (("intramusk", "intramuscular"), "intramuscular"),
    (("subkutan", "subcutan", "subcutaneous"), "subcutaneous"),
    (("oral", "per os", "zum eingeben", "by mouth"), "oral"),
    (("topisch", "topical", "kutan", "cutaneous", "dermal"), "topical"),
    (("auge", "ophthalm", "ocular"), "eye"),
    (("ohr", "otic", "auricular"), "ear"),
    (("spray", "sprühen", "spraying"), "spray"),
)
_CONCENTRATION = re.compile(
    r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(mg|mcg|µg|ug|g|iu|i\.u\.|ie)\s*/\s*"
    r"(ml|l|g|kg|tablette|tabletten|tablet|dose)",
    re.IGNORECASE,
)


def _tag(value: str) -> str:
    return value.rsplit("}", 1)[-1].strip().upper()


def _text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _records(xml_data: bytes, required: tuple[str, ...]) -> list[dict[str, str]]:
    root = ET.fromstring(xml_data)
    rows: list[dict[str, str]] = []
    for element in root.iter():
        children = list(element)
        if not children:
            continue
        row: dict[str, str] = {}
        for child in children:
            if list(child):
                continue
            row[_tag(child.tag)] = _text(child.text)
        if all(key in row for key in required):
            rows.append(row)
    return rows


def _member(archive: zipfile.ZipFile, suffix: str) -> bytes:
    requested = suffix.casefold()
    for name in archive.namelist():
        if name.replace("\\", "/").split("/")[-1].casefold() == requested:
            return archive.read(name)
    raise ValueError(f"Swissmedic OGD archive is missing {suffix}")


def _optional_member(archive: zipfile.ZipFile, suffix: str) -> bytes | None:
    try:
        return _member(archive, suffix)
    except ValueError:
        return None


def _udc_descriptions(data: bytes | None) -> dict[tuple[str, str], list[str]]:
    if not data:
        return {}
    result: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in _records(data, ("USER_DEFINED_CODE", "CODE_VALUE")):
        key = (row["USER_DEFINED_CODE"].upper(), row["CODE_VALUE"].upper())
        for field in ("BESCHREIBUNG_1", "BESCHREIBUNG_2", "BESCHREIBUNG_LANG"):
            clean = _text(row.get(field, ""))
            if clean and clean not in result[key]:
                result[key].append(clean)
    return dict(result)


def _udc_text(mapping: dict[tuple[str, str], list[str]], table: str, value: str) -> str:
    entries = mapping.get((table.upper(), value.upper()), [])
    if not entries:
        return ""
    german = next(
        (
            entry
            for entry in entries
            if any(
                token in entry.casefold()
                for token in (
                    "lösung",
                    "tablette",
                    "suspension",
                    "salbe",
                    "pulver",
                    "paste",
                    "zugelassen",
                    "oral",
                    "intraven",
                    "intramusk",
                    "subkutan",
                )
            )
        ),
        None,
    )
    return german or entries[0]


def _status_is_current(code: str, udc: dict[tuple[str, str], list[str]]) -> bool:
    descriptions = " ".join(udc.get(("MA_STATUS", str(code or "").upper()), []))
    lowered = descriptions.casefold()
    return not any(token in lowered for token in _NEGATIVE_STATUS)


def _is_current(row: dict[str, str], udc: dict[tuple[str, str], list[str]], _snapshot_date: str) -> bool:
    # The OGD dataset itself contains the current authorised/temporary/suspended
    # records plus recently revoked records. The explicit authorisation status is
    # therefore authoritative; ABLAUFDATUM is not used as an additional filter.
    return _status_is_current(row.get("ZULASSUNGSSTATUS", ""), udc)


def _concentration(*values: str) -> str:
    for value in values:
        match = _CONCENTRATION.search(value or "")
        if match:
            amount, numerator, denominator = match.groups()
            numerator = "mcg" if numerator.casefold() in {"µg", "ug"} else numerator
            denominator = {"tabletten": "tablet", "tablette": "tablet"}.get(
                denominator.casefold(), denominator
            )
            return f"{amount.replace(',', '.')} {numerator}/{denominator}"
    return ""


def _concentration_detail(concentration: str, ingredient: str) -> dict[str, Any] | None:
    match = _CONCENTRATION.search(concentration or "")
    if not match:
        return None
    amount, numerator, denominator = match.groups()
    numerator = "mcg" if numerator.casefold() in {"µg", "ug"} else numerator.casefold()
    denominator = {"tabletten": "tablet", "tablette": "tablet"}.get(
        denominator.casefold(), denominator.casefold()
    )
    return {
        "name": ingredient,
        "amount": float(amount.replace(",", ".")),
        "unit": numerator,
        "per": 1.0,
        "per_unit": denominator,
    }


def _alias(name: str) -> list[str]:
    stripped = re.sub(r"\s+ad\s+us\.?\s*vet\.?", "", name, flags=re.IGNORECASE).strip(" ,")
    return [stripped] if stripped and stripped.casefold() != name.casefold() else []


def _species_from_text(*values: str) -> list[str]:
    text = " ".join(values).casefold()
    result: list[str] = []
    for needles, species_id in _SPECIES:
        if any(needle in text for needle in needles) and species_id not in result:
            result.append(species_id)
    return result


def _route_id(value: str) -> str:
    lowered = value.casefold()
    for needles, route_id in _ROUTE_MAP:
        if any(needle in lowered for needle in needles):
            return route_id
    return ""


def _sequence_name(product_name: str, sequence_name: str, sequence_number: str) -> str:
    base = _text(product_name)
    sequence = _text(sequence_name)
    if not sequence or sequence.casefold() == base.casefold():
        return base
    base_key = re.sub(r"\W+", " ", base.casefold()).strip()
    seq_key = re.sub(r"\W+", " ", sequence.casefold()).strip()
    if base_key and base_key in seq_key:
        return sequence
    if sequence_number and _concentration(sequence):
        return f"{base}, {sequence}"
    return sequence if len(sequence) >= len(base) else f"{base}, {sequence}"


def parse_swissmedic_ogd_zip(data: bytes) -> tuple[str, list[dict[str, Any]]]:
    """Parse Swissmedic OGD as one selectable record per veterinary dosage strength."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        preparations = _records(
            _member(archive, "Praeparate.XML"),
            ("ZULASSUNGSNUMMER", "PRAEPARATENAME", "VERWENDUNG"),
        )
        sequences_data = _optional_member(archive, "Sequenzen.XML")
        sequences = (
            _records(sequences_data, ("ZULASSUNGSNUMMER", "SEQUENZNUMMER"))
            if sequences_data
            else []
        )
        declarations_data = _optional_member(archive, "Deklarationen.XML")
        declarations = (
            _records(declarations_data, ("ZULASSUNGSNUMMER", "SEQUENZNUMMER"))
            if declarations_data
            else []
        )
        substances_data = _optional_member(archive, "Stoff-Synonyme.XML")
        substances = (
            _records(substances_data, ("STOFF_ID", "STOFFSYNONYM"))
            if substances_data
            else []
        )
        routes_data = _optional_member(archive, "Applikationsarten_pro_Sequenz.XML")
        routes = (
            _records(routes_data, ("ZULASSUNGSNUMMER", "SEQUENZNUMMER"))
            if routes_data
            else []
        )
        udc = _udc_descriptions(_optional_member(archive, "User-Defined-Codes.XML"))
        export_data = _optional_member(archive, "Export-Datum.XML")
        export_rows = _records(export_data, ("EXPORT_DATUM",)) if export_data else []
        snapshot_date = export_rows[0].get("EXPORT_DATUM", "") if export_rows else ""

    sequences_by_product: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in sequences:
        sequences_by_product[row["ZULASSUNGSNUMMER"]].append(row)

    substance_name: dict[str, str] = {}
    for row in substances:
        if row.get("SYNONYM_CODE", "LN").upper() == "LN" or row["STOFF_ID"] not in substance_name:
            substance_name[row["STOFF_ID"]] = row["STOFFSYNONYM"]

    active_by_sequence: dict[tuple[str, str], list[str]] = defaultdict(list)
    declaration_rows: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in declarations:
        key = (row["ZULASSUNGSNUMMER"], row["SEQUENZNUMMER"])
        declaration_rows[key].append(row)
        substance_id = row.get("STOFF_ID", "")
        if not substance_id:
            continue
        category_code = row.get("STOFFKATEGORIE", "")
        category = " ".join(udc.get(("SUBSTANCE_CATEGORY", category_code.upper()), []))
        if category and not any(token in category.casefold() for token in _ACTIVE_SUBSTANCE):
            continue
        name = substance_name.get(substance_id, "")
        if name and name not in active_by_sequence[key]:
            active_by_sequence[key].append(name)

    routes_by_sequence: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in routes:
        key = (row["ZULASSUNGSNUMMER"], row["SEQUENZNUMMER"])
        code = row.get("APPLIKATIONSART_CODE") or row.get("APPLIKATIONSART") or row.get("ROUTE_ADMIN") or ""
        description = _udc_text(udc, "ROUTE_ADMIN", code) or code
        if description and description not in routes_by_sequence[key]:
            routes_by_sequence[key].append(description)

    products: list[dict[str, Any]] = []
    for row in preparations:
        if row.get("VERWENDUNG", "").upper() != "TAM" or not _is_current(row, udc, snapshot_date):
            continue
        authorisation = row["ZULASSUNGSNUMMER"]
        base_name = row["PRAEPARATENAME"]
        product_sequences = sequences_by_product.get(authorisation) or [
            {
                "ZULASSUNGSNUMMER": authorisation,
                "SEQUENZNUMMER": "",
                "SEQUENZNAME": base_name,
                "ANWENDUNGSGEBIET": row.get("ANWENDUNGSGEBIET", ""),
                "ZULASSUNGSSTATUS": row.get("ZULASSUNGSSTATUS", ""),
            }
        ]
        for sequence in product_sequences:
            if sequence.get("ZULASSUNGSSTATUS") and not _status_is_current(sequence.get("ZULASSUNGSSTATUS", ""), udc):
                continue
            sequence_number = sequence.get("SEQUENZNUMMER", "")
            key = (authorisation, sequence_number)
            name = _sequence_name(base_name, sequence.get("SEQUENZNAME", ""), sequence_number)
            ingredients = active_by_sequence.get(key, [])
            concentration = _concentration(sequence.get("SEQUENZNAME", ""), name, base_name)
            ingredient_details: list[dict[str, Any]] = []
            if len(ingredients) == 1 and concentration:
                detail = _concentration_detail(concentration, ingredients[0])
                if detail:
                    ingredient_details.append(detail)
            route_descriptions = routes_by_sequence.get(key, [])
            route_ids = [route for route in (_route_id(value) for value in route_descriptions) if route]
            route_ids = list(dict.fromkeys(route_ids))
            indication = sequence.get("ANWENDUNGSGEBIET", "") or row.get("ANWENDUNGSGEBIET", "")
            target_species = _species_from_text(indication, name)
            dosage_form = _udc_text(udc, "DF", row.get("ARZNEIFORM", ""))
            status = _udc_text(
                udc,
                "MA_STATUS",
                sequence.get("ZULASSUNGSSTATUS", "") or row.get("ZULASSUNGSSTATUS", ""),
            ) or sequence.get("ZULASSUNGSSTATUS", "") or row.get("ZULASSUNGSSTATUS", "")
            item_id = f"swissmedic.{authorisation}.{sequence_number or '00'}"
            aliases = list(dict.fromkeys([*_alias(name), *_alias(base_name), base_name]))
            aliases = [value for value in aliases if value and value.casefold() != name.casefold()]
            products.append(
                {
                    "id": item_id,
                    "source_id": SWISSMEDIC_SOURCE_ID,
                    "authorisation_number": authorisation,
                    "sequence_number": sequence_number,
                    "name": name,
                    "official_product_name": base_name,
                    "active_ingredient": ", ".join(ingredients),
                    "active_ingredients": ingredients,
                    "active_ingredient_details": ingredient_details,
                    "concentration": concentration,
                    "dosage_form": dosage_form,
                    "target_species": target_species,
                    "aliases": aliases,
                    "authorisation_status": status,
                    "application_area": indication,
                    "routes": route_ids,
                    "route_descriptions": route_descriptions,
                    "default_route": route_ids[0] if len(route_ids) == 1 else "",
                    "source": "swissmedic_ogd",
                }
            )
    products.sort(key=lambda item: (item["name"].casefold(), item["id"]))
    return snapshot_date, products
