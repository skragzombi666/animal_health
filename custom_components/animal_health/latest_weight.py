from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from homeassistant.core import HomeAssistant

from .const import DATABASE_NAME


@dataclass(frozen=True, slots=True)
class LatestWeight:
    event_id: str
    value_kg: float
    original_value: float
    original_unit: str
    occurred_at: datetime


_UNIT_TO_KG = {
    "mg": 0.000001,
    "g": 0.001,
    "kg": 1.0,
}


async def async_get_latest_weights(hass: HomeAssistant) -> dict[str, LatestWeight]:
    database_path = Path(hass.config.path(DATABASE_NAME))
    return await hass.async_add_executor_job(_get_latest_weights_sync, database_path)


def _get_latest_weights_sync(database_path: Path) -> dict[str, LatestWeight]:
    if not database_path.exists():
        return {}

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        rows = connection.execute(
            """
            WITH RECURSIVE weight_versions AS (
                SELECT
                    event.id,
                    event.animal_id,
                    event.occurred_at AS measured_at,
                    event.value,
                    event.unit,
                    event.created_at
                FROM events AS event
                WHERE event.event_type = 'weight'
                  AND event.correction_of_event_id IS NULL
                  AND event.value IS NOT NULL
                  AND event.unit IN ('mg', 'g', 'kg')

                UNION ALL

                SELECT
                    correction.id,
                    correction.animal_id,
                    previous.measured_at,
                    correction.value,
                    correction.unit,
                    correction.created_at
                FROM events AS correction
                JOIN weight_versions AS previous
                  ON correction.correction_of_event_id = previous.id
                WHERE correction.event_type = 'weight'
                  AND correction.value IS NOT NULL
                  AND correction.unit IN ('mg', 'g', 'kg')
            ),
            valid_weights AS (
                SELECT version.*
                FROM weight_versions AS version
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM events AS later_correction
                    WHERE later_correction.correction_of_event_id = version.id
                      AND later_correction.event_type = 'weight'
                )
            ),
            ranked_weights AS (
                SELECT
                    valid_weights.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY valid_weights.animal_id
                        ORDER BY valid_weights.measured_at DESC,
                                 valid_weights.created_at DESC
                    ) AS row_number
                FROM valid_weights
            )
            SELECT id, animal_id, measured_at, value, unit
            FROM ranked_weights
            WHERE row_number = 1
            """
        ).fetchall()
    finally:
        connection.close()

    latest_weights: dict[str, LatestWeight] = {}
    for row in rows:
        original_value = float(row["value"])
        original_unit = str(row["unit"])
        latest_weights[str(row["animal_id"])] = LatestWeight(
            event_id=str(row["id"]),
            value_kg=original_value * _UNIT_TO_KG[original_unit],
            original_value=original_value,
            original_unit=original_unit,
            occurred_at=datetime.fromisoformat(str(row["measured_at"])),
        )
    return latest_weights
