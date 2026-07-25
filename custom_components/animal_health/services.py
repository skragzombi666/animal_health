from __future__ import annotations

from datetime import date
from typing import Any, cast

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import (
    ANIMAL_STATUS_ACTIVE,
    ANIMAL_STATUS_INACTIVE,
    ATTR_ANIMAL_ID,
    ATTR_ARRIVAL_DATE,
    ATTR_BIRTH_DATE,
    ATTR_BREED,
    ATTR_NAME,
    ATTR_SEX,
    ATTR_SPECIES,
    DOMAIN,
    SERVICE_ARCHIVE_ANIMAL,
    SERVICE_CREATE_ANIMAL,
    SERVICE_RESTORE_ANIMAL,
    SERVICE_UPDATE_ANIMAL,
)
from .runtime import AnimalHealthRuntimeData


def _required_text(value: Any) -> str:
    text = cv.string(value).strip()
    if not text:
        raise vol.Invalid("value must not be empty")
    return text


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = cv.string(value).strip()
    return text or None


def _optional_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(cv.string(value))
    except ValueError as err:
        raise vol.Invalid("date must use YYYY-MM-DD") from err


CREATE_ANIMAL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NAME): _required_text,
        vol.Required(ATTR_SPECIES): _required_text,
        vol.Optional(ATTR_BREED): _optional_text,
        vol.Optional(ATTR_SEX): _optional_text,
        vol.Optional(ATTR_BIRTH_DATE): _optional_date,
        vol.Optional(ATTR_ARRIVAL_DATE): _optional_date,
    }
)

UPDATE_ANIMAL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ANIMAL_ID): _required_text,
        vol.Optional(ATTR_NAME): _required_text,
        vol.Optional(ATTR_SPECIES): _required_text,
        vol.Optional(ATTR_BREED): _optional_text,
        vol.Optional(ATTR_SEX): _optional_text,
        vol.Optional(ATTR_BIRTH_DATE): _optional_date,
        vol.Optional(ATTR_ARRIVAL_DATE): _optional_date,
    }
)

ANIMAL_ID_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ANIMAL_ID): _required_text,
    }
)

EDITABLE_FIELDS = {
    ATTR_NAME,
    ATTR_SPECIES,
    ATTR_BREED,
    ATTR_SEX,
    ATTR_BIRTH_DATE,
    ATTR_ARRIVAL_DATE,
}


def _get_runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise ServiceValidationError("Animal Health is not loaded")


async def _refresh_and_respond(
    runtime_data: AnimalHealthRuntimeData,
    animal_id: str,
) -> dict[str, Any]:
    await runtime_data.coordinator.async_request_refresh()
    animal = runtime_data.coordinator.data.get(animal_id)
    if animal is None:
        raise ServiceValidationError(f"Unknown animal ID: {animal_id}")
    return animal.as_dict()


def async_setup_services(hass: HomeAssistant) -> None:
    async def handle_create_animal(call: ServiceCall) -> dict[str, Any]:
        runtime_data = _get_runtime_data(hass)
        animal = await runtime_data.database.create_animal(
            name=call.data[ATTR_NAME],
            species=call.data[ATTR_SPECIES],
            breed=call.data.get(ATTR_BREED),
            sex=call.data.get(ATTR_SEX),
            birth_date=call.data.get(ATTR_BIRTH_DATE),
            arrival_date=call.data.get(ATTR_ARRIVAL_DATE),
        )
        return await _refresh_and_respond(runtime_data, animal.id)

    async def handle_update_animal(call: ServiceCall) -> dict[str, Any]:
        runtime_data = _get_runtime_data(hass)
        animal_id = call.data[ATTR_ANIMAL_ID]
        changes = {
            field: call.data[field]
            for field in EDITABLE_FIELDS
            if field in call.data
        }
        if not changes:
            raise ServiceValidationError("No animal fields were supplied")
        try:
            await runtime_data.database.update_animal(animal_id, changes)
        except KeyError as err:
            raise ServiceValidationError(
                f"Unknown animal ID: {animal_id}"
            ) from err
        return await _refresh_and_respond(runtime_data, animal_id)

    async def handle_archive_animal(call: ServiceCall) -> dict[str, Any]:
        runtime_data = _get_runtime_data(hass)
        animal_id = call.data[ATTR_ANIMAL_ID]
        try:
            await runtime_data.database.set_animal_status(
                animal_id, ANIMAL_STATUS_INACTIVE
            )
        except KeyError as err:
            raise ServiceValidationError(
                f"Unknown animal ID: {animal_id}"
            ) from err
        return await _refresh_and_respond(runtime_data, animal_id)

    async def handle_restore_animal(call: ServiceCall) -> dict[str, Any]:
        runtime_data = _get_runtime_data(hass)
        animal_id = call.data[ATTR_ANIMAL_ID]
        try:
            await runtime_data.database.set_animal_status(
                animal_id, ANIMAL_STATUS_ACTIVE
            )
        except KeyError as err:
            raise ServiceValidationError(
                f"Unknown animal ID: {animal_id}"
            ) from err
        return await _refresh_and_respond(runtime_data, animal_id)

    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_ANIMAL,
        handle_create_animal,
        schema=CREATE_ANIMAL_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_ANIMAL,
        handle_update_animal,
        schema=UPDATE_ANIMAL_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ARCHIVE_ANIMAL,
        handle_archive_animal,
        schema=ANIMAL_ID_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESTORE_ANIMAL,
        handle_restore_animal,
        schema=ANIMAL_ID_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
