from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from . import swissmedic_catalog
from . import v0920_features
from . import v0923_features
from . import v0924_features
from .const import ANIMAL_STATUSES, DOMAIN

_PATCHED = False
_STATUS_EDIT_COMMAND = f"{DOMAIN}/v0924/status/edit"


def _normalise(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def _json(value: Any, fallback: Any) -> Any:
    try:
        result = json.loads(str(value or ""))
    except (TypeError, json.JSONDecodeError):
        return fallback
    return result


def _number(value: Any) -> float | None:
    match = re.search(r"[-+]?\d+(?:[.,]\d+)?", str(value or ""))
    if not match:
        return None
    try:
        return float(match.group(0).replace(",", "."))
    except ValueError:
        return None


def _unit(value: Any) -> str:
    raw = re.sub(r"[.\s]+", " ", str(value or "").strip()).casefold()
    aliases = {
        "mg": "mg",
        "milligramm": "mg",
        "milligram": "mg",
        "g": "g",
        "gramm": "g",
        "gram": "g",
        "kg": "kg",
        "kilogramm": "kg",
        "kilogram": "kg",
        "ml": "ml",
        "milliliter": "ml",
        "millilitre": "ml",
        "l": "l",
        "liter": "l",
        "litre": "l",
        "mcg": "mcg",
        "µg": "mcg",
        "ug": "mcg",
        "mikrogramm": "mcg",
        "microgram": "mcg",
        "ie": "IU",
        "iu": "IU",
        "i u": "IU",
        "internationale einheiten": "IU",
        "international units": "IU",
        "tablette": "tablet",
        "tabletten": "tablet",
        "tablet": "tablet",
        "dose": "dose",
    }
    if raw in aliases:
        return aliases[raw]
    for key, result in aliases.items():
        if raw.startswith(key + " ") or raw.endswith(" " + key):
            return result
    return str(value or "").strip()


def _enriched_swissmedic_parser(data: bytes) -> tuple[str, list[dict[str, Any]]]:
    """Add declaration-based substance amounts to the sequence-complete OGD parser."""
    snapshot, products = swissmedic_catalog.parse_swissmedic_ogd_zip(data)
    try:
        import io
        import zipfile

        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            declarations_data = swissmedic_catalog._optional_member(archive, "Deklarationen.XML")
            substances_data = swissmedic_catalog._optional_member(archive, "Stoff-Synonyme.XML")
            udc = swissmedic_catalog._udc_descriptions(
                swissmedic_catalog._optional_member(archive, "User-Defined-Codes.XML")
            )
            declarations = (
                swissmedic_catalog._records(
                    declarations_data,
                    ("ZULASSUNGSNUMMER", "SEQUENZNUMMER"),
                )
                if declarations_data
                else []
            )
            substances = (
                swissmedic_catalog._records(substances_data, ("STOFF_ID", "STOFFSYNONYM"))
                if substances_data
                else []
            )
    except Exception:  # noqa: BLE001
        return snapshot, products

    substance_names: dict[str, str] = {}
    for row in substances:
        substance_id = str(row.get("STOFF_ID") or "")
        if not substance_id:
            continue
        if str(row.get("SYNONYM_CODE") or "LN").upper() == "LN" or substance_id not in substance_names:
            substance_names[substance_id] = str(row.get("STOFFSYNONYM") or "").strip()

    by_sequence: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in declarations:
        by_sequence[(str(row.get("ZULASSUNGSNUMMER") or ""), str(row.get("SEQUENZNUMMER") or ""))].append(row)

    for product in products:
        key = (str(product.get("authorisation_number") or ""), str(product.get("sequence_number") or ""))
        rows = by_sequence.get(key, [])
        if not rows:
            continue
        reference_amount: float | None = None
        reference_unit = ""
        for row in reversed(rows):
            if str(row.get("ZEILENTYP") or "").strip().upper() != "G":
                continue
            reference_amount = _number(row.get("MENGE"))
            code = str(row.get("MENGEN_EINHEIT") or "")
            description = swissmedic_catalog._udc_text(udc, "UNIT", code) or code
            reference_unit = _unit(description)
            if reference_amount and reference_unit:
                break
        if not reference_amount or not reference_unit:
            existing = product.get("active_ingredient_details")
            if existing:
                continue
            # Many Swissmedic sequence names carry the exact strength even when
            # the galenic reference row is not quantitatively exported.
            continue

        details: list[dict[str, Any]] = []
        ingredients: list[str] = []
        for row in rows:
            if str(row.get("ZEILENTYP") or "").strip().upper() != "S":
                continue
            category_code = str(row.get("STOFFKATEGORIE") or "")
            category = " ".join(udc.get(("SUBSTANCE_CATEGORY", category_code.upper()), []))
            if category and not any(token in category.casefold() for token in swissmedic_catalog._ACTIVE_SUBSTANCE):
                continue
            substance_id = str(row.get("STOFF_ID") or "")
            name = substance_names.get(substance_id, "").strip()
            amount = _number(row.get("MENGE"))
            code = str(row.get("MENGEN_EINHEIT") or "")
            description = swissmedic_catalog._udc_text(udc, "UNIT", code) or code
            amount_unit = _unit(description)
            if name and name not in ingredients:
                ingredients.append(name)
            if name and amount and amount_unit:
                details.append(
                    {
                        "name": name,
                        "amount": amount,
                        "unit": amount_unit,
                        "per": reference_amount,
                        "per_unit": reference_unit,
                    }
                )
        if ingredients:
            product["active_ingredients"] = ingredients
            product["active_ingredient"] = ", ".join(ingredients)
        if details:
            product["active_ingredient_details"] = details
            if len(details) == 1:
                item = details[0]
                per = float(item["per"])
                per_text = "" if per == 1 else f"{per:g} "
                product["concentration"] = f"{float(item['amount']):g} {item['unit']}/{per_text}{item['per_unit']}"
    return snapshot, products


def _component_signature(component: dict[str, Any]) -> tuple[str, str, str, str, str] | None:
    component_type = str(component.get("type") or "product")
    if component_type == "action":
        return None
    event_type = "medication" if component_type in {"product", "medication", "supplement"} else "care"
    dose = component.get("dose")
    dose_key = "" if dose in (None, "") else f"{float(dose):.12g}"
    return (
        event_type,
        _normalise(component.get("name")),
        dose_key,
        str(component.get("unit") or ""),
        str(component.get("route") or ""),
    )


def _child_signature(row: sqlite3.Row, data: dict[str, Any]) -> tuple[str, str, str, str, str]:
    dose = row["value"]
    dose_key = "" if dose is None else f"{float(dose):.12g}"
    return (
        str(row["event_type"]),
        _normalise(row["title"]),
        dose_key,
        str(row["unit"] or ""),
        str(data.get("route") or ""),
    )


def _dedupe_legacy_treatment_components_sync(path: Path) -> None:
    """Soft-delete only surplus legacy children beyond the plan snapshot multiplicity."""
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(events)").fetchall()}
        if "is_deleted" not in columns:
            return
        parents = connection.execute(
            "SELECT rowid,* FROM events WHERE event_type='treatment' AND is_deleted=0 ORDER BY rowid"
        ).fetchall()
        for parent in parents:
            pdata = v0924_features._parse_event_data(parent)
            tx_id = str(pdata.get("treatment_execution_id") or "")
            if not tx_id or str(pdata.get("treatment_execution_role") or "") != "parent":
                continue
            template = pdata.get("components") or pdata.get("treatment_plan_components") or []
            if not isinstance(template, list) or not template:
                continue
            expected = Counter(
                signature
                for signature in (_component_signature(item) for item in template if isinstance(item, dict))
                if signature is not None
            )
            if not expected:
                continue
            current = v0924_features._current_execution_rows(connection, tx_id)
            grouped: dict[tuple[str, str, str, str, str], list[sqlite3.Row]] = defaultdict(list)
            for child in current:
                if str(child["event_type"]) == "treatment":
                    continue
                cdata = v0924_features._parse_event_data(child)
                if cdata.get("treatment_component_extra") or cdata.get("treatment_component_index") is not None:
                    continue
                grouped[_child_signature(child, cdata)].append(child)
            for signature, children in grouped.items():
                allowed = int(expected.get(signature, 0))
                if allowed <= 0 or len(children) <= allowed:
                    continue
                def _priority(row: sqlite3.Row) -> tuple[int, int]:
                    attachments = 0
                    try:
                        attachments = int(
                            connection.execute(
                                "SELECT COUNT(*) FROM attachments WHERE event_id=?",
                                (row["id"],),
                            ).fetchone()[0]
                        )
                    except sqlite3.OperationalError:
                        pass
                    return (-attachments, int(row["rowid"]))
                ordered = sorted(children, key=_priority)
                keep = {str(row["id"]) for row in ordered[:allowed]}
                kept_id = next(iter(keep), "")
                for duplicate in ordered[allowed:]:
                    duplicate_id = str(duplicate["id"])
                    ddata = v0924_features._parse_event_data(duplicate)
                    ddata["v0924_auto_deduplicated"] = True
                    ddata["v0924_duplicate_of"] = kept_id
                    connection.execute(
                        "UPDATE events SET is_deleted=1,deleted_at=?,data_json=? WHERE id=?",
                        (now, json.dumps(ddata, ensure_ascii=False, sort_keys=True), duplicate_id),
                    )
        connection.commit()
    finally:
        connection.close()


def _move_medication_correction_attachments(database, items: list[dict[str, Any]], results: list[dict[str, Any]]) -> None:
    pairs = []
    for item, result in zip(items, results, strict=False):
        old_id = str(item.get("correction_event_id") or "").strip()
        new_id = str(result.get("id") or "").strip()
        if old_id and new_id:
            pairs.append((new_id, old_id))
    if not pairs:
        return
    with database._connect() as connection:  # noqa: SLF001
        try:
            connection.executemany("UPDATE attachments SET event_id=? WHERE event_id=?", pairs)
        except sqlite3.OperationalError:
            pass


def _recompute_status(connection: sqlite3.Connection, animal_id: str) -> None:
    rows = connection.execute(
        "SELECT id,occurred_at,created_at,correction_of_event_id,data_json FROM events "
        "WHERE animal_id=? AND event_type='status_change' AND is_deleted=0 "
        "ORDER BY occurred_at,created_at,id",
        (animal_id,),
    ).fetchall()
    corrected = {str(row["correction_of_event_id"]) for row in rows if row["correction_of_event_id"]}
    effective = [row for row in rows if str(row["id"]) not in corrected]
    latest = effective[-1] if effective else None
    if latest is None:
        return
    data = _json(latest["data_json"], {})
    status = str(data.get("new_status") or "") if isinstance(data, dict) else ""
    if status not in ANIMAL_STATUSES:
        return
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    connection.execute(
        "UPDATE animals SET status=?,status_changed_at=?,updated_at=? WHERE id=?",
        (status, str(latest["occurred_at"]), now, animal_id),
    )


def _edit_status_sync(
    database,
    event_id: str,
    new_status: str,
    occurred_at: datetime,
    day: str,
    precision: str,
    notes: str | None,
) -> dict[str, Any]:
    if new_status not in ANIMAL_STATUSES:
        raise ValueError(f"Unsupported animal status: {new_status}")
    with database._connect() as connection:  # noqa: SLF001
        row = connection.execute("SELECT rowid,* FROM events WHERE id=?", (event_id,)).fetchone()
        if row is None or str(row["event_type"]) != "status_change":
            raise KeyError(event_id)
        data = v0924_features._parse_event_data(row)
        data["new_status"] = new_status
        data["effective_at"] = occurred_at.isoformat()
        data.update(v0924_features._precision_data(precision, day))
        corrected = v0924_features._create_correction(
            database,
            connection,
            row,
            occurred_at=occurred_at,
            data=data,
            notes=notes,
        )
        _recompute_status(connection, str(row["animal_id"]))
        return corrected.as_dict()


def apply_v0924_polish() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    base_assign = v0924_features._assign_treatment_execution_ids_sync

    def assign_and_dedupe(path: Path) -> None:
        base_assign(path)
        _dedupe_legacy_treatment_components_sync(path)

    v0924_features._assign_treatment_execution_ids_sync = assign_and_dedupe

    base_record_medications = v0923_features._record_medications_sync

    def record_medications_with_attachment_corrections(
        database,
        animal_id: str,
        occurred_at: datetime,
        common_notes: str | None,
        items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        raw_items = [dict(item) for item in items]
        result = base_record_medications(database, animal_id, occurred_at, common_notes, raw_items)
        _move_medication_correction_attachments(database, raw_items, result)
        return result

    v0923_features._record_medications_sync = record_medications_with_attachment_corrections
    v0920_features.parse_swissmedic_ogd_zip = _enriched_swissmedic_parser


def async_setup_v0924_polish(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command(
        {
            vol.Required("type"): _STATUS_EDIT_COMMAND,
            vol.Required("event_id"): v0924_features._required_text,
            vol.Required("new_status"): vol.In(ANIMAL_STATUSES),
            vol.Optional("notes"): v0924_features._optional_text,
            vol.Optional("occurred_date"): v0924_features._optional_text,
            vol.Optional("occurred_time"): v0924_features._optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_status_edit(hass, connection, msg) -> None:
        runtime = v0924_features._runtime_data(hass)
        try:
            when, precision, day = v0924_features._event_when(
                hass,
                msg.get("occurred_date"),
                msg.get("occurred_time"),
            )
            result = await hass.async_add_executor_job(
                _edit_status_sync,
                runtime.database,
                msg["event_id"],
                msg["new_status"],
                when,
                day,
                precision,
                msg.get("notes"),
            )
            await runtime.coordinator.async_request_refresh()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0924_status_edit_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    websocket_api.async_register_command(hass, websocket_status_edit)
