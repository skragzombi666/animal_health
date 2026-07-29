from __future__ import annotations

from dataclasses import dataclass

from .coordinator import AnimalHealthCoordinator
from .database import AnimalHealthDatabase
from .feature_store import AnimalHealthFeatureStore


@dataclass(slots=True)
class AnimalHealthRuntimeData:
    database: AnimalHealthDatabase
    coordinator: AnimalHealthCoordinator
    feature_store: AnimalHealthFeatureStore
