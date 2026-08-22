from __future__ import annotations

from datetime import datetime
from typing import Any

from . import task_record_creation
from .const import EVENT_TYPE_CARE, EVENT_TYPE_MEDICATION
from .database import AnimalHealthDatabase
from .task_kinds import TASK_KIND_TREATMENT
from .task_records import TaskRecordStore

_PATCHED = False


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
            component_type = str(component.get("type") or "")
            if component_type not in {"medication", "supplement", "feed"}:
                continue
            name = str(component.get("name") or "").strip()
            dose = component.get("dose")
            unit = str(component.get("unit") or "").strip()
            if not name or dose in (None, "") or not unit:
                continue
            event = database._create_event_in_connection(  # noqa: SLF001
                connection,
                animal_id=animal_id,
                event_type=(
                    EVENT_TYPE_MEDICATION
                    if component_type in {"medication", "supplement"}
                    else EVENT_TYPE_CARE
                ),
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
                    **(
                        {"route": str(component["route"])}
                        if component.get("route")
                        else {}
                    ),
                },
            )
            results.append(event.as_dict())
    return results


def apply_v0912_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    original_template = task_record_creation.build_task_template

    def build_task_template(
        task_kind: str,
        data: dict[str, Any],
        *,
        title: str,
        current: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = original_template(task_kind, data, title=title, current=current)
        if task_kind == TASK_KIND_TREATMENT:
            plan_id = data.get("planned_treatment_plan_id")
            if plan_id not in (None, ""):
                result["treatment_plan_id"] = int(plan_id)
        return result

    task_record_creation.build_task_template = build_task_template

    original_execute = TaskRecordStore.execute

    async def execute(self: TaskRecordStore, *args: Any, **kwargs: Any) -> Any:
        result = await original_execute(self, *args, **kwargs)
        if str(kwargs.get("expected_kind") or "") != TASK_KIND_TREATMENT:
            return result
        planned = result.occurrence.get("planned") or {}
        plan_id = planned.get("treatment_plan_id")
        plan_name = str(planned.get("treatment_plan_name") or result.occurrence.get("task_title") or "Behandlung")
        components = planned.get("treatment_plan_components") or []
        animal_id = result.occurrence.get("animal_id")
        performed_at = kwargs.get("performed_at")
        if (
            not plan_id
            or not animal_id
            or not isinstance(performed_at, datetime)
            or not isinstance(components, list)
        ):
            return result
        database = AnimalHealthDatabase(self._hass, self._database_path)  # noqa: SLF001
        component_events = await self._hass.async_add_executor_job(  # noqa: SLF001
            _record_plan_components_sync,
            database,
            int(plan_id),
            plan_name,
            components,
            str(animal_id),
            performed_at,
        )
        if result.event is not None:
            result.event.setdefault("data", {})["treatment_plan_id"] = int(plan_id)
            result.event["data"]["treatment_plan_name"] = plan_name
            result.event["data"]["treatment_plan_components"] = components
            result.event["component_events"] = component_events
        return result

    TaskRecordStore.execute = execute
