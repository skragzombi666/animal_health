from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AnimalHealthConfigEntry
from .const import ANIMAL_SEXES, ANIMAL_STATUSES, DOMAIN, NAME
from .coordinator import AnimalHealthCoordinator
from .models import Animal


@dataclass(frozen=True, kw_only=True)
class AnimalProfileSensorDescription(SensorEntityDescription):
    value_fn: Callable[[Animal], str | date | None]


SENSOR_DESCRIPTIONS = (
    AnimalProfileSensorDescription(
        key="status",
        translation_key="status",
        icon="mdi:paw",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda animal: animal.status,
    ),
    AnimalProfileSensorDescription(
        key="animal_id",
        translation_key="animal_id",
        icon="mdi:identifier",
        value_fn=lambda animal: animal.id,
    ),
    AnimalProfileSensorDescription(
        key="species",
        translation_key="species",
        icon="mdi:shape",
        value_fn=lambda animal: animal.species,
    ),
    AnimalProfileSensorDescription(
        key="breed",
        translation_key="breed",
        icon="mdi:format-list-text",
        value_fn=lambda animal: animal.breed,
    ),
    AnimalProfileSensorDescription(
        key="sex",
        translation_key="sex",
        icon="mdi:gender-male-female",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda animal: animal.sex,
    ),
    AnimalProfileSensorDescription(
        key="birth_date",
        translation_key="birth_date",
        icon="mdi:cake-variant",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda animal: animal.birth_date,
    ),
    AnimalProfileSensorDescription(
        key="arrival_date",
        translation_key="arrival_date",
        icon="mdi:home-import-outline",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda animal: animal.arrival_date,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AnimalHealthConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    known_animal_ids: set[str] = set()

    @callback
    def add_new_animal_entities() -> None:
        new_animal_ids = set(coordinator.data) - known_animal_ids
        if not new_animal_ids:
            return
        known_animal_ids.update(new_animal_ids)
        async_add_entities(
            AnimalProfileSensor(coordinator, animal_id, description)
            for animal_id in sorted(new_animal_ids)
            for description in SENSOR_DESCRIPTIONS
        )

    add_new_animal_entities()
    entry.async_on_unload(
        coordinator.async_add_listener(add_new_animal_entities)
    )


class AnimalProfileSensor(
    CoordinatorEntity[AnimalHealthCoordinator],
    SensorEntity,
):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AnimalHealthCoordinator,
        animal_id: str,
        description: AnimalProfileSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._animal_id = animal_id
        self._attr_unique_id = f"{animal_id}_{description.key}"

    @property
    def animal(self) -> Animal | None:
        return self.coordinator.data.get(self._animal_id)

    @property
    def available(self) -> bool:
        return super().available and self.animal is not None

    @property
    def native_value(self) -> str | date | None:
        animal = self.animal
        return self.entity_description.value_fn(animal) if animal else None

    @property
    def options(self) -> list[str] | None:
        if self.entity_description.key == "status":
            return list(ANIMAL_STATUSES)
        if self.entity_description.key == "sex":
            return list(ANIMAL_SEXES)
        return None

    @property
    def device_info(self) -> DeviceInfo | None:
        animal = self.animal
        if animal is None:
            return None
        return DeviceInfo(
            identifiers={(DOMAIN, animal.id)},
            name=animal.name,
            manufacturer=NAME,
            model=animal.species,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        animal = self.animal
        if animal is None:
            return {}
        return {"animal_id": animal.id}
