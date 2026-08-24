from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

from . import v0912_features as treatment_features
from . import v0912_patches as treatment_patches
from .database import AnimalHealthDatabase
from .v0913_features import medication_snapshot_for_name

_PATCHED = False


def _snapshot_with_category(
    connection: sqlite3.Connection,
    product_name: str,
) -> dict[str, Any]:
    snapshot = medication_snapshot_for_name(connection, product_name)
    category = "medication"
    medication_id = snapshot.get("medication_id")
    if medication_id is not None:
        row = connection.execute(
            "SELECT category FROM v0917_product_categories WHERE medication_id=?",
            (int(medication_id),),
        ).fetchone()
        if row is not None:
            category = str(row["category"])
    snapshot["product_category"] = category
    return snapshot


def _normalise_component_type(value: Any) -> str:
    component_type = str(value or "").strip()
    if component_type in {"medication", "supplement", "product"}:
        return "product"
    return component_type


def apply_v0917_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    base_create = AnimalHealthDatabase._create_event_in_connection

    def _create_event_with_product_category(
        database: AnimalHealthDatabase,
        connection: sqlite3.Connection,
        **kwargs: Any,
    ):
        if str(kwargs.get("event_type") or "") == "medication":
            data = dict(kwargs.get("data") or {})
            snapshot = data.get("medication_snapshot")
            if not isinstance(snapshot, dict):
                name = str(data.get("medication_name") or kwargs.get("title") or "").strip()
                snapshot = _snapshot_with_category(connection, name)
            elif "product_category" not in snapshot:
                snapshot = dict(snapshot)
                medication_id = snapshot.get("medication_id")
                category = "medication"
                if medication_id is not None:
                    row = connection.execute(
                        "SELECT category FROM v0917_product_categories WHERE medication_id=?",
                        (int(medication_id),),
                    ).fetchone()
                    if row is not None:
                        category = str(row["category"])
                snapshot["product_category"] = category
            data["medication_snapshot"] = snapshot
            data.setdefault("product_category", snapshot.get("product_category", "medication"))
            kwargs["data"] = data
        return base_create(database, connection, **kwargs)

    AnimalHealthDatabase._create_event_in_connection = _create_event_with_product_category  # type: ignore[method-assign]

    base_validate_component = treatment_features._validate_component

    def _validate_component(raw: Any) -> dict[str, Any]:
        if not isinstance(raw, dict):
            return base_validate_component(raw)
        item = dict(raw)
        original_type = str(item.get("type") or "").strip()
        normalized = _normalise_component_type(original_type)
        if normalized == "product":
            item["type"] = "medication"
            result = base_validate_component(item)
            result["type"] = "product"
            return result
        return base_validate_component(item)

    treatment_features.COMPONENT_TYPES = ("product", "feed", "action")
    treatment_features._validate_component = _validate_component

    def _execute_treatment_sync(
        runtime,
        plan_id: int,
        animal_id: str,
        occurred_at: datetime,
        notes: str | None,
    ) -> list[dict[str, Any]]:
        database = runtime.database
        results: list[dict[str, Any]] = []
        with database._connect() as connection:  # noqa: SLF001
            animal = database._get_animal_from_connection(connection, animal_id)  # noqa: SLF001
            if animal is None:
                raise KeyError(animal_id)
            row = connection.execute(
                """
                SELECT id,name,species_id,list_as,description,default_unit,
                       default_route,components_json
                FROM v0911_treatment_plans WHERE id=?
                """,
                (plan_id,),
            ).fetchone()
            if row is None:
                raise KeyError(plan_id)
            plan = treatment_features._plan_dict(row)
            components = plan["components"]
            action_steps = [item for item in components if item["type"] == "action"]
            summary = database._create_event_in_connection(  # noqa: SLF001
                connection,
                animal_id=animal_id,
                event_type="treatment",
                occurred_at=occurred_at,
                title=plan["name"],
                notes=notes or plan["description"] or None,
                data={
                    "source": "treatment_plan",
                    "treatment_plan_id": plan_id,
                    "treatment_plan_name": plan["name"],
                    "components": components,
                    "action_steps": action_steps,
                },
            )
            results.append(summary.as_dict())
            for item in components:
                component_type = _normalise_component_type(item.get("type"))
                if component_type not in {"product", "feed"}:
                    continue
                event = database._create_event_in_connection(  # noqa: SLF001
                    connection,
                    animal_id=animal_id,
                    event_type="medication" if component_type == "product" else "care",
                    occurred_at=occurred_at,
                    title=item["name"],
                    notes=item.get("instructions"),
                    value=float(item["dose"]),
                    unit=str(item["unit"]),
                    data={
                        "source": "treatment_plan",
                        "treatment_plan_id": plan_id,
                        "treatment_plan_name": plan["name"],
                        "component_type": component_type,
                        "product_type": component_type,
                        **({"route": item["route"]} if item.get("route") else {}),
                    },
                )
                results.append(event.as_dict())
        return results

    treatment_features._execute_treatment_sync = _execute_treatment_sync

    def _record_plan_components_sync(
        database: AnimalHealthDatabase,
        plan_id: int,
        plan_name: str,
        components: list[dict[str, Any]],
        animal_id: str,
        occurred_at: datetime,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        with database._connect() as connection:  # noqa: SLF001
            for component in components:
                if not isinstance(component, dict):
                    continue
                component_type = _normalise_component_type(component.get("type"))
                if component_type not in {"product", "feed"}:
                    continue
                name = str(component.get("name") or "").strip()
                dose = component.get("dose")
                unit = str(component.get("unit") or "").strip()
                if not name or dose in (None, "") or not unit:
                    continue
                event = database._create_event_in_connection(  # noqa: SLF001
                    connection,
                    animal_id=animal_id,
                    event_type="medication" if component_type == "product" else "care",
                    occurred_at=occurred_at,
                    title=name,
                    notes=str(component.get("instructions") or "").strip() or None,
                    value=float(dose),
                    unit=unit,
                    data={
                        "source": "treatment_plan_task",
                        "treatment_plan_id": plan_id,
                        "treatment_plan_name": plan_name,
                        "component_type": component_type,
                        "product_type": component_type,
                        **({"route": str(component["route"])} if component.get("route") else {}),
                    },
                )
                results.append(event.as_dict())
        return results

    treatment_patches._record_plan_components_sync = _record_plan_components_sync
