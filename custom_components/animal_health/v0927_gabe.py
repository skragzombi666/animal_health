from __future__ import annotations

import json
import math
import re
import sqlite3
from typing import Any

from . import v0923_features, v0926_features
from .models import HealthEvent
from .v0927_data import (
    GABE_DEWORMING,
    GABE_FEED,
    GABE_MEDICATION,
    GABE_SUPPLEMENT,
    GABE_TYPES,
    GABE_VACCINATION,
    connect,
    load_product_snapshot,
    required_text,
    text,
)

_MASS_TO_MG = {"mcg": 0.001, "ug": 0.001, "µg": 0.001, "mg": 1.0, "g": 1000.0, "kg": 1_000_000.0}
_UNIT_DIMENSIONS = {
    "ul": ("volume", 0.001), "µl": ("volume", 0.001), "ml": ("volume", 1.0), "l": ("volume", 1000.0),
    "mcg": ("mass", 0.000001), "ug": ("mass", 0.000001), "µg": ("mass", 0.000001),
    "mg": ("mass", 0.001), "g": ("mass", 1.0), "kg": ("mass", 1000.0),
    "tablet": ("count", 1.0), "dose": ("count", 1.0), "drop": ("drop", 1.0),
    "mark": ("count", 1.0), "pinch": ("count", 1.0), "coffee_spoon": ("count", 1.0),
}
_CONCENTRATION = re.compile(
    r"(?P<amount>\d+(?:[.,]\d+)?)\s*(?P<unit>mcg|µg|ug|mg|g)\s*/\s*(?P<per_unit>µl|ul|ml|mL|l|g|kg|tablet|Tablette|dose)",
    re.IGNORECASE,
)


def _normal(value: Any) -> str:
    return text(value).casefold()


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if value in (None, ""):
        return {}
    try:
        loaded = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return dict(loaded) if isinstance(loaded, dict) else {}


def _compatible_amount(value: float, from_unit: str, to_unit: str) -> float | None:
    source = _UNIT_DIMENSIONS.get(_normal(from_unit))
    target = _UNIT_DIMENSIONS.get(_normal(to_unit))
    if source is None or target is None or source[0] != target[0]:
        return None
    return value * source[1] / target[1]


def _active_details(data: dict[str, Any]) -> list[dict[str, Any]]:
    for snapshot_key in ("medication_snapshot", "product_snapshot"):
        snapshot = data.get(snapshot_key)
        if isinstance(snapshot, dict):
            details = snapshot.get("active_ingredient_details")
            if isinstance(details, list) and details:
                return [dict(item) for item in details if isinstance(item, dict)]
    details = data.get("active_ingredient_details")
    if isinstance(details, list) and details:
        return [dict(item) for item in details if isinstance(item, dict)]
    snapshot = data.get("medication_snapshot")
    concentration = text(snapshot.get("concentration") if isinstance(snapshot, dict) else data.get("concentration"))
    ingredient = text(snapshot.get("active_ingredient") if isinstance(snapshot, dict) else data.get("active_ingredient"))
    if not concentration or not ingredient or "," in ingredient:
        return []
    match = _CONCENTRATION.search(concentration)
    if not match:
        return []
    return [{
        "name": ingredient,
        "amount": float(match.group("amount").replace(",", ".")),
        "unit": _normal(match.group("unit")),
        "per": 1.0,
        "per_unit": _normal(match.group("per_unit")).replace("tablette", "tablet"),
    }]


def weight_snapshot(connection: sqlite3.Connection, animal_id: str, occurred_at: str) -> dict[str, Any] | None:
    event_columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(events)").fetchall()}
    active_clause = "AND COALESCE(e.is_deleted,0)=0" if "is_deleted" in event_columns else ""
    correction_clause = (
        "AND NOT EXISTS (SELECT 1 FROM events AS c WHERE c.correction_of_event_id=e.id AND COALESCE(c.is_deleted,0)=0)"
        if "is_deleted" in event_columns else
        "AND NOT EXISTS (SELECT 1 FROM events AS c WHERE c.correction_of_event_id=e.id)"
    )
    row = connection.execute(
        f"""
        SELECT e.id,e.occurred_at,e.value,e.unit FROM events AS e
        WHERE e.animal_id=? AND e.event_type='weight' AND e.occurred_at<=?
          AND e.value IS NOT NULL AND e.unit IS NOT NULL {active_clause} {correction_clause}
        ORDER BY e.occurred_at DESC,e.rowid DESC LIMIT 1
        """,
        (animal_id, occurred_at),
    ).fetchone()
    if row is None:
        return None
    value = float(row["value"])
    unit = _normal(row["unit"])
    kg = value if unit == "kg" else value / 1000.0 if unit == "g" else value / 1_000_000.0 if unit == "mg" else None
    if kg is None or not math.isfinite(kg) or kg <= 0:
        return None
    return {"event_id": str(row["id"]), "occurred_at": str(row["occurred_at"]), "original_value": value, "original_unit": str(row["unit"]), "kg": kg}


def active_amounts(data: dict[str, Any], dose: float, dose_unit: str, weight: dict[str, Any] | None) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for detail in _active_details(data):
        try:
            concentration_amount = float(detail.get("amount"))
            per = float(detail.get("per") or 1.0)
        except (TypeError, ValueError):
            continue
        if concentration_amount <= 0 or per <= 0:
            continue
        ingredient_unit = _normal(detail.get("unit"))
        per_unit = _normal(detail.get("per_unit")).replace("tablette", "tablet")
        matching_dose = _compatible_amount(dose, dose_unit, per_unit)
        if matching_dose is None:
            continue
        amount = concentration_amount * matching_dose / per
        item: dict[str, Any] = {
            "name": text(detail.get("name")), "amount": amount, "unit": ingredient_unit,
            "concentration_amount": concentration_amount, "concentration_unit": ingredient_unit,
            "per": per, "per_unit": per_unit,
        }
        mg_factor = _MASS_TO_MG.get(ingredient_unit)
        if mg_factor is not None:
            amount_mg = amount * mg_factor
            item["amount_mg"] = amount_mg
            if weight and float(weight.get("kg") or 0) > 0:
                item["mg_per_kg"] = amount_mg / float(weight["kg"])
        result.append(item)
    return result


def event_gabe_type(event_type: str, data: dict[str, Any]) -> str | None:
    direct = text(data.get("gabe_type"))
    if direct in GABE_TYPES:
        return direct
    if event_type == "vaccination":
        return GABE_VACCINATION
    if event_type == "medication":
        product_type = text(data.get("product_type") or data.get("component_type"))
        return product_type if product_type in (GABE_SUPPLEMENT, GABE_DEWORMING) else GABE_MEDICATION
    if event_type == "care" and text(data.get("component_type")) == GABE_FEED:
        return GABE_FEED
    return None


def enrich_event_in_connection(
    connection: sqlite3.Connection,
    event_id: str,
    *,
    forced_gabe_type: str | None = None,
    forced_source: str | None = None,
) -> HealthEvent | None:
    selected = ["id", "animal_id", "event_type", "occurred_at", "title", "notes", "value", "unit", "correction_of_event_id", "data_json", "task_id", "task_occurrence_id", "created_at"]
    row = connection.execute(f"SELECT {','.join(selected)} FROM events WHERE id=?", (event_id,)).fetchone()
    if row is None:
        return None
    data = _json_object(row["data_json"])
    gabe_type = forced_gabe_type or event_gabe_type(str(row["event_type"]), data)
    if gabe_type not in GABE_TYPES:
        return HealthEvent.from_mapping(row)
    data["gabe_type"] = gabe_type
    if forced_source:
        data["gabe_source"] = forced_source
    elif row["task_id"] or isinstance(data.get("task_execution"), dict):
        data["gabe_source"] = "task"
    elif text(data.get("treatment_execution_id")) or text(data.get("treatment_execution_role")):
        data["gabe_source"] = "treatment_plan"
    else:
        data.setdefault("gabe_source", "direct")
    dose = data.get("dose")
    dose_unit = text(data.get("dose_unit") or row["unit"])
    if dose is None and row["value"] is not None:
        dose = row["value"]
    try:
        dose_number = float(dose) if dose is not None else None
    except (TypeError, ValueError):
        dose_number = None
    if dose_number is not None and dose_number > 0 and dose_unit:
        weight = weight_snapshot(connection, str(row["animal_id"]), str(row["occurred_at"]))
        amounts = active_amounts(data, dose_number, dose_unit, weight)
        if amounts:
            data["active_amounts"] = amounts
        else:
            data.pop("active_amounts", None)
        if weight:
            data["weight_snapshot"] = weight
        else:
            data.pop("weight_snapshot", None)
    connection.execute("UPDATE events SET data_json=? WHERE id=?", (json.dumps(data, ensure_ascii=False, sort_keys=True), event_id))
    refreshed = connection.execute(f"SELECT {','.join(selected)} FROM events WHERE id=?", (event_id,)).fetchone()
    return HealthEvent.from_mapping(refreshed) if refreshed is not None else None


def backfill_gabe_events(path) -> None:
    with connect(path) as connection:
        rows = connection.execute("SELECT id FROM events WHERE event_type IN ('medication','vaccination','care') ORDER BY occurred_at,id").fetchall()
        for row in rows:
            enrich_event_in_connection(connection, str(row["id"]))


def record_gabe_sync(database, path, target_ids, metadata, occurred_at, occurred_date, precision, notes, items):
    results: list[dict[str, Any]] = []
    for raw in items:
        gabe_type = required_text(raw.get("gabe_type") or GABE_MEDICATION)
        if gabe_type not in GABE_TYPES:
            raise ValueError(f"Unsupported administration type: {gabe_type}")
        name = required_text(raw.get("product_name") or raw.get("name"))
        try:
            dose = float(raw.get("dose") or raw.get("amount"))
        except (TypeError, ValueError) as err:
            raise ValueError("Dose/amount must be a number") from err
        if dose <= 0:
            raise ValueError("Dose/amount must be greater than zero")
        dose_unit = required_text(raw.get("dose_unit") or raw.get("unit"))
        route, product_id = text(raw.get("route")), text(raw.get("product_id"))
        for animal_id in target_ids:
            if animal_id is None:
                continue
            with database._connect() as connection:  # noqa: SLF001
                product_snapshot = load_product_snapshot(connection, product_id)
                event_type = "vaccination" if gabe_type == GABE_VACCINATION else "care" if gabe_type == GABE_FEED else "medication"
                data: dict[str, Any] = {
                    "gabe_type": gabe_type, "gabe_source": "direct", "product_name": name,
                    "medication_name": name, "dose": dose, "dose_unit": dose_unit, "entry_mode": "gabe",
                }
                if route:
                    data["route"] = route
                if product_id:
                    data["product_id"] = product_id
                if product_snapshot:
                    data["product_snapshot"] = product_snapshot
                    for key in ("active_ingredient_details", "active_ingredient", "concentration"):
                        if product_snapshot.get(key):
                            data[key] = product_snapshot[key]
                    if gabe_type == GABE_VACCINATION:
                        data["vaccination_targets"] = list(product_snapshot.get("targets") or [])
                for key in ("dose_basis", "feed_status", "offered_amount", "consumed_amount", "batch_number", "active_ingredient", "concentration", "active_ingredient_details", "vaccination_targets"):
                    value = raw.get(key)
                    if value not in (None, "", []):
                        data[key] = value
                event = database._create_event_in_connection(  # noqa: SLF001
                    connection, animal_id=animal_id, event_type=event_type, occurred_at=occurred_at,
                    title=name, notes=text(notes) or None, value=dose, unit=dose_unit,
                    correction_of_event_id=None, data=data, task_id=None, task_occurrence_id=None,
                )
                enriched = enrich_event_in_connection(connection, event.id, forced_gabe_type=gabe_type, forced_source="direct") or event
                results.append(enriched.as_dict())
    ids = [str(item["id"]) for item in results]
    v0923_features._mark_precision_sync(path, ids, precision, occurred_date)  # noqa: SLF001
    for item in results:
        payload = dict(item.get("data") or {})
        payload.update(v0923_features._precision_data(precision, occurred_date))  # noqa: SLF001
        payload.update(metadata)
        item["data"] = payload
    return v0926_features._annotate_events_sync(path, results, metadata)  # noqa: SLF001


def catalog_metadata_fallback(item: dict[str, Any]) -> None:
    details = item.get("active_ingredient_details")
    if not isinstance(details, list):
        details = []
    if not text(item.get("active_ingredient")) and details:
        names = [text(detail.get("name")) for detail in details if isinstance(detail, dict) and text(detail.get("name"))]
        item["active_ingredient"] = ", ".join(dict.fromkeys(names))
    if not text(item.get("concentration")) and len(details) == 1:
        detail = details[0]
        if isinstance(detail, dict) and detail.get("amount") and detail.get("unit") and detail.get("per_unit"):
            per = float(detail.get("per") or 1)
            suffix = f"/{text(detail['per_unit'])}" if per == 1 else f"/{per:g} {text(detail['per_unit'])}"
            item["concentration"] = f"{float(detail['amount']):g} {text(detail['unit'])}{suffix}"
    routes = item.get("routes")
    if not text(item.get("default_route")) and isinstance(routes, list) and len(routes) == 1:
        item["default_route"] = text(routes[0])
