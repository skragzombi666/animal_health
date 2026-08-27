from __future__ import annotations

import json
import sqlite3
from typing import Any

from . import v0912_features as treatment_features
from . import v0920_features
from . import v0923_features
from . import v0924_features
from .database import AnimalHealthDatabase
from .task_records import TaskRecordStore

_PATCHED = False


def _json_dict(value: Any) -> dict[str, Any]:
    try:
        decoded = json.loads(str(value or "{}"))
    except (TypeError, json.JSONDecodeError):
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _merged_catalog_row(connection: sqlite3.Connection, product_name: str) -> dict[str, Any] | None:
    needle = v0924_features._normalise(product_name)
    rows = connection.execute(
        """
        SELECT p.source_id,p.item_id,p.name,p.active_ingredient,p.active_ingredients_json,
               p.concentration,p.dosage_form,p.aliases_json,p.target_species_json,
               m.active_ingredient_details_json,m.routes_json,m.default_route,
               o.hidden,o.override_json
        FROM v0920_catalog_products AS p
        LEFT JOIN v0924_catalog_meta AS m
          ON m.source_id=p.source_id AND m.item_id=p.item_id
        LEFT JOIN v0924_catalog_overrides AS o
          ON o.source_id=p.source_id AND o.item_id=p.item_id
        WHERE p.source_id='swissmedic_ch'
        ORDER BY p.name COLLATE NOCASE,p.item_id
        """
    ).fetchall()
    for row in rows:
        aliases = v0924_features._json(row["aliases_json"], [])
        candidates = [str(row["name"]), *(str(value) for value in aliases if value)]
        override = v0924_features._json(row["override_json"], {}) if row["override_json"] else {}
        if isinstance(override, dict) and override.get("name"):
            candidates.append(str(override["name"]))
        if not any(v0924_features._normalise(value) == needle for value in candidates):
            continue
        if bool(row["hidden"] or 0):
            return None
        result = {
            "source": "official_catalog",
            "catalog_source_id": str(row["source_id"]),
            "catalog_id": str(row["item_id"]),
            "product_name": str(row["name"]),
            "active_ingredient": str(row["active_ingredient"] or ""),
            "active_ingredients": v0924_features._json(row["active_ingredients_json"], []),
            "active_ingredient_details": v0924_features._json(row["active_ingredient_details_json"], []),
            "concentration": str(row["concentration"] or ""),
            "dosage_form": str(row["dosage_form"] or ""),
            "target_species": v0924_features._json(row["target_species_json"], []),
            "routes": v0924_features._json(row["routes_json"], []),
            "default_route": str(row["default_route"] or ""),
        }
        if isinstance(override, dict):
            result.update({key: value for key, value in override.items() if value not in (None, "")})
        return result
    return None


def _assign_task_treatment_group(path, event: dict[str, Any], component_events: list[dict[str, Any]]) -> None:
    event_id = str(event.get("id") or "")
    if not event_id:
        return
    tx_id = str(event.get("data", {}).get("treatment_execution_id") or f"TX-{event_id}")
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        for child_event, role in [(event, "parent"), *((item, "component") for item in component_events)]:
            child_id = str(child_event.get("id") or "")
            if not child_id:
                continue
            row = connection.execute("SELECT data_json FROM events WHERE id=?", (child_id,)).fetchone()
            if row is None:
                continue
            data = _json_dict(row["data_json"])
            data["treatment_execution_id"] = tx_id
            data["treatment_execution_role"] = role
            if role != "parent":
                data["treatment_parent_event_id"] = event_id
            connection.execute(
                "UPDATE events SET data_json=? WHERE id=?",
                (json.dumps(data, ensure_ascii=False, sort_keys=True), child_id),
            )
            child_event.setdefault("data", {}).update(data)
        connection.commit()
    finally:
        connection.close()


def _preserve_medication_correction_context(database, items: list[dict[str, Any]], results: list[dict[str, Any]]) -> None:
    if not results:
        return
    pairs: list[tuple[str, str, dict[str, Any]]] = []
    for raw, result in zip(items, results, strict=False):
        old_id = str(raw.get("correction_event_id") or "").strip()
        new_id = str(result.get("id") or "").strip()
        if old_id and new_id:
            pairs.append((old_id, new_id, result))
    if not pairs:
        return
    with database._connect() as connection:  # noqa: SLF001
        attachments = v0924_features._table_exists(connection, "attachments")
        for old_id, new_id, result in pairs:
            old = connection.execute("SELECT data_json FROM events WHERE id=?", (old_id,)).fetchone()
            new = connection.execute("SELECT data_json FROM events WHERE id=?", (new_id,)).fetchone()
            if old is not None and new is not None:
                old_data = _json_dict(old["data_json"])
                new_data = _json_dict(new["data_json"])
                for key, value in old_data.items():
                    if key.startswith("treatment_") or key in {"component_type", "source"}:
                        new_data[key] = value
                connection.execute(
                    "UPDATE events SET data_json=? WHERE id=?",
                    (json.dumps(new_data, ensure_ascii=False, sort_keys=True), new_id),
                )
                result.setdefault("data", {}).update(new_data)
            if attachments:
                connection.execute("UPDATE attachments SET event_id=? WHERE event_id=?", (new_id, old_id))


def apply_v0924_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    base_validate_component = treatment_features._validate_component

    def validate_component_with_optional(raw: Any) -> dict[str, Any]:
        item = dict(raw) if isinstance(raw, dict) else raw
        result = base_validate_component(item)
        result["optional"] = bool(raw.get("optional")) if isinstance(raw, dict) else False
        return result

    treatment_features._validate_component = validate_component_with_optional

    base_replace_catalog = v0920_features._replace_catalog_sync

    def replace_catalog_with_meta(path, snapshot_date: str, products: list[dict[str, Any]]) -> None:
        base_replace_catalog(path, snapshot_date, products)
        v0924_features._store_catalog_meta_sync(path, products)

    v0920_features._replace_catalog_sync = replace_catalog_with_meta

    base_create_event = AnimalHealthDatabase._create_event_in_connection

    def create_event_with_v0924_product_snapshot(
        database: AnimalHealthDatabase,
        connection: sqlite3.Connection,
        **kwargs: Any,
    ):
        if str(kwargs.get("event_type") or "") == "medication":
            data = dict(kwargs.get("data") or {})
            name = str(data.get("medication_name") or kwargs.get("title") or "").strip()
            official = _merged_catalog_row(connection, name) if name else None
            snapshot = data.get("medication_snapshot")
            if official:
                existing = dict(snapshot) if isinstance(snapshot, dict) else {}
                existing.update(official)
                data["medication_snapshot"] = existing
                data["catalog_source"] = "official"
                data["catalog_source_id"] = official["catalog_source_id"]
                data["catalog_id"] = official["catalog_id"]
                if not data.get("route") and official.get("default_route"):
                    data["route"] = official["default_route"]
                kwargs["title"] = str(official.get("product_name") or kwargs.get("title") or name)
            kwargs["data"] = data
        return base_create_event(database, connection, **kwargs)

    AnimalHealthDatabase._create_event_in_connection = create_event_with_v0924_product_snapshot  # type: ignore[method-assign]

    base_record_medications = v0923_features._record_medications_sync

    def record_medications_with_correction_context(
        database,
        animal_id: str,
        occurred_at,
        common_notes: str | None,
        items: list[dict[str, Any]],
    ):
        results = base_record_medications(database, animal_id, occurred_at, common_notes, items)
        _preserve_medication_correction_context(database, items, results)
        return results

    v0923_features._record_medications_sync = record_medications_with_correction_context

    base_task_execute = TaskRecordStore.execute

    async def task_execute_with_treatment_identity(self: TaskRecordStore, *args: Any, **kwargs: Any):
        result = await base_task_execute(self, *args, **kwargs)
        event = result.event
        if not isinstance(event, dict) or str(event.get("event_type") or "") != "treatment":
            return result
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        plan_id = data.get("treatment_plan_id")
        task_execution = data.get("task_execution")
        if plan_id in (None, "") and isinstance(task_execution, dict):
            plan_id = task_execution.get("treatment_plan_id")
        if plan_id in (None, ""):
            return result
        components = event.get("component_events") or []
        if not isinstance(components, list):
            components = []
        await self._hass.async_add_executor_job(  # noqa: SLF001
            _assign_task_treatment_group,
            self._database_path,  # noqa: SLF001
            event,
            components,
        )
        return result

    TaskRecordStore.execute = task_execute_with_treatment_identity
