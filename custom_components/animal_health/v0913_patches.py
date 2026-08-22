from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from homeassistant.core import HomeAssistant

from . import coordinator as coordinator_module
from .const import DATABASE_NAME
from .database import AnimalHealthDatabase
from .latest_weight import LatestWeight
from .models import HealthEvent
from .v0913_features import medication_snapshot_for_name

_PATCHED = False


def _get_events_sync_013(
    database: AnimalHealthDatabase,
    animal_id: str,
    limit: int,
) -> list[HealthEvent]:
    with database._connect() as connection:  # noqa: SLF001
        rows = connection.execute(
            """
            SELECT id,animal_id,event_type,occurred_at,title,notes,value,unit,
                   correction_of_event_id,data_json,task_id,task_occurrence_id,created_at
            FROM events
            WHERE animal_id=? AND is_deleted=0
            ORDER BY occurred_at DESC,created_at DESC,id DESC
            LIMIT ?
            """,
            (animal_id, limit),
        ).fetchall()
    return [HealthEvent.from_mapping(row) for row in rows]


_UNIT_TO_KG = {"mg": 0.000001, "g": 0.001, "kg": 1.0}


def _get_latest_weights_sync_013(database_path: Path) -> dict[str, LatestWeight]:
    if not database_path.exists():
        return {}
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        rows = connection.execute(
            """
            WITH RECURSIVE weight_versions AS (
                SELECT event.id,event.animal_id,event.occurred_at AS measured_at,
                       event.value,event.unit,event.created_at,event.is_deleted
                FROM events AS event
                WHERE event.event_type='weight'
                  AND event.correction_of_event_id IS NULL
                  AND event.value IS NOT NULL
                  AND event.unit IN ('mg','g','kg')
                UNION ALL
                SELECT correction.id,correction.animal_id,previous.measured_at,
                       correction.value,correction.unit,correction.created_at,
                       correction.is_deleted
                FROM events AS correction
                JOIN weight_versions AS previous
                  ON correction.correction_of_event_id=previous.id
                WHERE correction.event_type='weight'
                  AND correction.value IS NOT NULL
                  AND correction.unit IN ('mg','g','kg')
            ),
            valid_weights AS (
                SELECT version.*
                FROM weight_versions AS version
                WHERE version.is_deleted=0
                  AND NOT EXISTS (
                    SELECT 1 FROM events AS later_correction
                    WHERE later_correction.correction_of_event_id=version.id
                      AND later_correction.event_type='weight'
                      AND later_correction.is_deleted=0
                  )
            ),
            ranked_weights AS (
                SELECT valid_weights.*,
                       ROW_NUMBER() OVER (
                           PARTITION BY valid_weights.animal_id
                           ORDER BY valid_weights.measured_at DESC,
                                    valid_weights.created_at DESC,
                                    valid_weights.id DESC
                       ) AS row_number
                FROM valid_weights
            )
            SELECT id,animal_id,measured_at,value,unit
            FROM ranked_weights
            WHERE row_number=1
            """
        ).fetchall()
    finally:
        connection.close()
    result: dict[str, LatestWeight] = {}
    for row in rows:
        value = float(row["value"])
        unit = str(row["unit"])
        result[str(row["animal_id"])] = LatestWeight(
            event_id=str(row["id"]),
            value_kg=value * _UNIT_TO_KG[unit],
            original_value=value,
            original_unit=unit,
            occurred_at=datetime.fromisoformat(str(row["measured_at"])),
        )
    return result


async def _async_get_latest_weights_013(
    hass: HomeAssistant,
) -> dict[str, LatestWeight]:
    database_path = Path(hass.config.path(DATABASE_NAME))
    return await hass.async_add_executor_job(_get_latest_weights_sync_013, database_path)


def apply_v0913_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    AnimalHealthDatabase._get_events_sync = _get_events_sync_013  # type: ignore[method-assign]
    coordinator_module.async_get_latest_weights = _async_get_latest_weights_013

    base_create = AnimalHealthDatabase._create_event_in_connection

    def _create_event_with_snapshot(
        database: AnimalHealthDatabase,
        connection: sqlite3.Connection,
        **kwargs,
    ) -> HealthEvent:
        if str(kwargs.get("event_type") or "") == "medication":
            data = dict(kwargs.get("data") or {})
            if "medication_snapshot" not in data:
                product_name = str(
                    data.get("medication_name") or kwargs.get("title") or ""
                ).strip()
                data["medication_snapshot"] = medication_snapshot_for_name(
                    connection, product_name
                )
            kwargs["data"] = data
        return base_create(database, connection, **kwargs)

    AnimalHealthDatabase._create_event_in_connection = _create_event_with_snapshot  # type: ignore[method-assign]
