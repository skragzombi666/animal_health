from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AnimalHealthConfigEntry
from .const import DOMAIN, NAME
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
            entity
            for animal_id in sorted(new_animal_ids)
            for entity in (
                AnimalArchiveButton(coordinator, animal_id),
                AnimalRestoreButton(coordinator, animal_id),
            )
        )

    add_new_animal_entities()
    entry.async_on_unload(
        coordinator.async_add_listener(add_new_animal_entities)
    )


class AnimalActionButton(
    CoordinatorEntity[AnimalHealthCoordinator],
    ButtonEntity,
):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AnimalHealthCoordinator,
        animal_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._animal_id = animal_id

    @property
    def animal(self) -> Animal | None:
        return self.coordinator.data.get(self._animal_id)

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


class AnimalArchiveButton(AnimalActionButton):
    _attr_translation_key = "archive"

    def __init__(
        self,
        coordinator: AnimalHealthCoordinator,
        animal_id: str,
    ) -> None:
        super().__init__(coordinator, animal_id)
        self._attr_unique_id = f"{animal_id}_archive"

    @property
    def available(self) -> bool:
        animal = self.animal
        return super().available and animal is not None and not animal.is_archived

    async def async_press(self) -> None:
        await self.coordinator.database.set_animal_archived(self._animal_id, True)
        await self.coordinator.async_request_refresh()


class AnimalRestoreButton(AnimalActionButton):
    _attr_translation_key = "restore"

    def __init__(
        self,
        coordinator: AnimalHealthCoordinator,
        animal_id: str,
    ) -> None:
        super().__init__(coordinator, animal_id)
        self._attr_unique_id = f"{animal_id}_restore"

    @property
    def available(self) -> bool:
        animal = self.animal
        return super().available and animal is not None and animal.is_archived

    async def async_press(self) -> None:
        await self.coordinator.database.set_animal_archived(self._animal_id, False)
        await self.coordinator.async_request_refresh()
