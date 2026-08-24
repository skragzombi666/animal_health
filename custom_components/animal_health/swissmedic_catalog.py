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
    rows = _records(data, ("USER_DEFINED_CODE", "CODE_VALUE"))
    for row in rows:
        key = (row["USER_DEFINED_CODE"].upper(), row["CODE_VALUE"].upper())
        descriptions = [
            row.get("BESCHREIBUNG_1", ""),
            row.get("BESCHREIBUNG_2", ""),
            row.get("BESCHREIBUNG_LANG", ""),
        ]
        for value in descriptions:
            clean = _text(value)
            if clean and clean not in result[key]:
                result[key].append(clean)
    return dict(result)


def _udc_text(
    mapping: dict[tuple[str, str], list[str]],
    table: str,
    value: str,
) -> str:
    entries = mapping.get((table.upper(), value.upper()), [])
    if not entries:
        return ""
    german = next(
        (entry for entry in entries if any(token in entry.casefold() for token in ("lösung", "tablette", "suspension", "salbe", "pulver", "paste", "zugelassen"))),
        None,
    )
    return german or entries[0]


def _is_current(
    row: dict[str, str],
    udc: dict[tuple[str, str], list[str]],
    snapshot_date: str,
) -> bool:
    status = " ".join(udc.get(("MA_STATUS", row.get("ZULASSUNGSSTATUS", "").upper()), []))
    lowered = status.casefold()
    if any(token in lowered for token in _NEGATIVE_STATUS):
        return False
    expiry = row.get("ABLAUFDATUM", "")
    if expiry and snapshot_date and expiry < snapshot_date:
        return False
    return True


def _concentration(*values: str) -> str:
    pattern = re.compile(
        r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(mg|mcg|µg|g|iu|i\.u\.)\s*/\s*(ml|g|kg|tablette|tablet)",
        re.IGNORECASE,
    )
    for value in values:
        match = pattern.search(value or "")
        if match:
            amount, numerator, denominator = match.groups()
            return f"{amount.replace(',', '.')} {numerator}/{denominator}"
    return ""


def _alias(name: str) -> list[str]:
    stripped = re.sub(r"\s+ad\s+us\.?\s*vet\.?", "", name, flags=re.IGNORECASE).strip(" ,")
    return [stripped] if stripped and stripped.casefold() != name.casefold() else []


def parse_swissmedic_ogd_zip(data: bytes) -> tuple[str, list[dict[str, Any]]]:
    """Parse the official Swissmedic OGD ZIP and return current veterinary products."""
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
        udc = _udc_descriptions(_optional_member(archive, "User-Defined-Codes.XML"))
        export_data = _optional_member(archive, "Export-Datum.XML")
        export_rows = _records(export_data, ("EXPORT_DATUM",)) if export_data else []
        snapshot_date = export_rows[0].get("EXPORT_DATUM", "") if export_rows else ""

    sequence_by_product: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in sequences:
        sequence_by_product[row["ZULASSUNGSNUMMER"]].append(row)

    substance_name: dict[str, str] = {}
    for row in substances:
        if row.get("SYNONYM_CODE", "LN").upper() == "LN" or row["STOFF_ID"] not in substance_name:
            substance_name[row["STOFF_ID"]] = row["STOFFSYNONYM"]

    active_by_product: dict[str, list[str]] = defaultdict(list)
    for row in declarations:
        substance_id = row.get("STOFF_ID", "")
        if not substance_id:
            continue
        category_code = row.get("STOFFKATEGORIE", "")
        category = " ".join(udc.get(("SUBSTANCE_CATEGORY", category_code.upper()), []))
        if category and not any(token in category.casefold() for token in _ACTIVE_SUBSTANCE):
            continue
        name = substance_name.get(substance_id, "")
        if name and name not in active_by_product[row["ZULASSUNGSNUMMER"]]:
            active_by_product[row["ZULASSUNGSNUMMER"]].append(name)

    products: list[dict[str, Any]] = []
    for row in preparations:
        if row.get("VERWENDUNG", "").upper() != "TAM":
            continue
        if not _is_current(row, udc, snapshot_date):
            continue
        authorisation = row["ZULASSUNGSNUMMER"]
        name = row["PRAEPARATENAME"]
        sequence_names = [item.get("SEQUENZNAME", "") for item in sequence_by_product.get(authorisation, [])]
        dosage_form = _udc_text(udc, "DF", row.get("ARZNEIFORM", ""))
        status = _udc_text(udc, "MA_STATUS", row.get("ZULASSUNGSSTATUS", "")) or row.get("ZULASSUNGSSTATUS", "")
        ingredients = active_by_product.get(authorisation, [])
        products.append(
            {
                "id": f"swissmedic.{authorisation}",
                "source_id": SWISSMEDIC_SOURCE_ID,
                "authorisation_number": authorisation,
                "name": name,
                "active_ingredient": ", ".join(ingredients),
                "active_ingredients": ingredients,
                "concentration": _concentration(name, *sequence_names),
                "dosage_form": dosage_form,
                "target_species": [],
                "aliases": _alias(name),
                "authorisation_status": status,
                "application_area": row.get("ANWENDUNGSGEBIET", ""),
                "source": "swissmedic_ogd",
            }
        )
    products.sort(key=lambda item: item["name"].casefold())
    return snapshot_date, products
