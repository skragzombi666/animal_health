from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class Animal:
    id: str
    animal_code: str
    name: str
    species: str
    breed: str | None
    sex: str | None
    birth_date: date | None
    arrival_date: date | None
    status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> Animal:
        return cls(
            id=row["id"],
            animal_code=row["animal_code"],
            name=row["name"],
            species=row["species"],
            breed=row["breed"],
            sex=row["sex"],
            birth_date=(
                date.fromisoformat(row["birth_date"]) if row["birth_date"] else None
            ),
            arrival_date=(
                date.fromisoformat(row["arrival_date"])
                if row["arrival_date"]
                else None
            ),
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.animal_code,
            "name": self.name,
            "species": self.species,
            "breed": self.breed,
            "sex": self.sex,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "arrival_date": self.arrival_date.isoformat() if self.arrival_date else None,
            "status": self.status,
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
    task_id: str | None
    task_occurrence_id: str | None
    created_at: datetime
