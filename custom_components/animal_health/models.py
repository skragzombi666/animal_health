from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class Animal:
    id: str
    name: str
    species: str
    breed: str | None
    color: str | None
    sex: str | None
    birth_date: date | None
    arrival_date: date | None
    status: str
    status_changed_at: datetime
    is_archived: bool
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> Animal:
        return cls(
            id=row["id"],
            name=row["name"],
            species=row["species"],
            breed=row["breed"],
            color=row["color"],
            sex=row["sex"],
            birth_date=date.fromisoformat(row["birth_date"]) if row["birth_date"] else None,
            arrival_date=date.fromisoformat(row["arrival_date"]) if row["arrival_date"] else None,
            status=row["status"],
            status_changed_at=datetime.fromisoformat(row["status_changed_at"]),
            is_archived=bool(row["is_archived"]),
            archived_at=datetime.fromisoformat(row["archived_at"]) if row["archived_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "species": self.species,
            "breed": self.breed,
            "color": self.color,
            "sex": self.sex,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "arrival_date": self.arrival_date.isoformat() if self.arrival_date else None,
            "status": self.status,
            "status_changed_at": self.status_changed_at.isoformat(),
            "is_archived": self.is_archived,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class HealthEvent:
    id: str
    animal_id: str
    event_type: str
    occurred_at: datetime
    title: str
    notes: str | None
    value: float | None
    unit: str | None
    correction_of_event_id: str | None
    data: dict[str, Any]
    task_id: str | None
    task_occurrence_id: str | None
    created_at: datetime

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> HealthEvent:
        return cls(
            id=row["id"],
            animal_id=row["animal_id"],
            event_type=row["event_type"],
            occurred_at=datetime.fromisoformat(row["occurred_at"]),
            title=row["title"],
            notes=row["notes"],
            value=row["value"],
            unit=row["unit"],
            correction_of_event_id=row["correction_of_event_id"],
            data=json.loads(row["data_json"] or "{}"),
            task_id=row["task_id"],
            task_occurrence_id=row["task_occurrence_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "animal_id": self.animal_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "title": self.title,
            "notes": self.notes,
            "value": self.value,
            "unit": self.unit,
            "correction_of_event_id": self.correction_of_event_id,
            "data": self.data,
            "task_id": self.task_id,
            "task_occurrence_id": self.task_occurrence_id,
            "created_at": self.created_at.isoformat(),
        }
