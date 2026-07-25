from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class Animal:
    id: str
    name: str
    species: str
    breed: str | None
    sex: str | None
    birth_date: date | None
    arrival_date: date | None
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class HealthEvent:
    id: str
    animal_id: str
    event_type: str
    occurred_at: datetime
    title: str
    notes: str | None
    task_id: str | None
    task_occurrence_id: str | None
    created_at: datetime
