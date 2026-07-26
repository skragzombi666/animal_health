from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
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
            AnimalStatusSelect(coordinator, animal_id)
            for animal_id in sorted(new_animal_ids)
        )

    add_new_animal_entities()
    entry.async_on_unload(
        coordinator.async_add_listener(add_new_animal_entities)
    )


class AnimalStatusSelect(
    CoordinatorEntity[AnimalHealthCoordinator],
    SelectEntity,
):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_options = list(ANIMAL_STATUSES)
    _attr_translation_key = "status_control"

    def __init__(
        self,
        coordinator: AnimalHealthCoordinator,
        animal_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._animal_id = animal_id
        self._attr_unique_id = f"{animal_id}_status_control"

    @property
    def animal(self) -> Animal | None:
        return self.coordinator.data.get(self._animal_id)

    @property
    def available(self) -> bool:
        return super().available and self.animal is not None

    @property
    def current_option(self) -> str | None:
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

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.database.set_animal_status(self._animal_id, option)
        await self.coordinator.async_request_refresh()
