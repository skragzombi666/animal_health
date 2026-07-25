from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AnimalHealthConfigEntry
from .const import ANIMAL_STATUSES, DOMAIN, NAME
from .coordinator import AnimalHealthCoordinator
from .models import Animal


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
            AnimalStatusSensor(coordinator, animal_id)
            for animal_id in sorted(new_animal_ids)
        )

    add_new_animal_entities()
    entry.async_on_unload(
        coordinator.async_add_listener(add_new_animal_entities)
    )


class AnimalStatusSensor(
    CoordinatorEntity[AnimalHealthCoordinator],
    SensorEntity,
):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_has_entity_name = True
    _attr_icon = "mdi:paw"
    _attr_options = list(ANIMAL_STATUSES)
    _attr_translation_key = "status"

    def __init__(
        self,
        coordinator: AnimalHealthCoordinator,
        animal_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._animal_id = animal_id
        self._attr_unique_id = f"{animal_id}_status"

    @property
    def animal(self) -> Animal | None:
        return self.coordinator.data.get(self._animal_id)

    @property
    def available(self) -> bool:
        return super().available and self.animal is not None

    @property
    def native_value(self) -> str | None:
        animal = self.animal
        return animal.status if animal else None

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
        return {
            "animal_id": animal.id,
            "species": animal.species,
            "breed": animal.breed,
            "sex": animal.sex,
            "birth_date": (
                animal.birth_date.isoformat() if animal.birth_date else None
            ),
            "arrival_date": (
                animal.arrival_date.isoformat() if animal.arrival_date else None
            ),
            "created_at": animal.created_at.isoformat(),
            "updated_at": animal.updated_at.isoformat(),
        }
