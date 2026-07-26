from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any, cast

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.util import dt as dt_util

from .catalog import (
    canonical_breed_name,
    canonical_species_name,
    product_event_metadata,
)
from .const import (
    ADMINISTRATION_ROUTES,
    ANIMAL_SEXES,
    ANIMAL_STATUSES,
    ATTR_ARRIVAL_DATE,
    ATTR_BATCH_NUMBER,
    ATTR_BIRTH_DATE,
    ATTR_BREED,
    ATTR_COLOR,
    ATTR_CORRECTION_OF_EVENT_ID,
    ATTR_DEVICE_ID,
    ATTR_DOSE,
    ATTR_DOSE_UNIT,
    ATTR_EVENT_TYPE,
    ATTR_LIMIT,
    ATTR_MEDICATION_NAME,
    ATTR_NAME,
    ATTR_NOTES,
    ATTR_OCCURRED_AT,
    ATTR_ROUTE,
    ATTR_SEVERITY,
    ATTR_SEX,
    ATTR_SPECIES,
    ATTR_STATUS,
    ATTR_SYMPTOM,
    ATTR_TITLE,
    ATTR_VACCINE_NAME,
    ATTR_WEIGHT,
    ATTR_WEIGHT_UNIT,
    DOSE_UNITS,
    DOMAIN,
    EVENT_TYPE_MEDICATION,
    EVENT_TYPE_SYMPTOM,
    EVENT_TYPE_VACCINATION,
    EVENT_TYPE_WEIGHT,
    GENERAL_EVENT_TYPES,
    SERVICE_ARCHIVE_ANIMAL,
    SERVICE_CREATE_ANIMAL,
    SERVICE_CREATE_EVENT,
    SERVICE_LIST_EVENTS,
    SERVICE_RECORD_MEDICATION,
    SERVICE_RECORD_SYMPTOM,
    SERVICE_RECORD_VACCINATION,
    SERVICE_RECORD_WEIGHT,
    SERVICE_RESTORE_ANIMAL,
    SERVICE_SET_ANIMAL_STATUS,
    SERVICE_UPDATE_ANIMAL,
    SYMPTOM_SEVERITIES,
    WEIGHT_UNITS,
)
from .models import Animal
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


def _positive_number(value: Any) -> float:
    number = vol.Coerce(float)(value)
    if number <= 0:
        raise vol.Invalid("value must be greater than zero")
    return number


def _optional_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(cv.string(value))
    except ValueError as err:
        raise vol.Invalid("date must use YYYY-MM-DD") from err


def _optional_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(cv.string(value))
    except ValueError as err:
        raise vol.Invalid("date and time must use ISO format") from err


def _event_datetime_utc(hass: HomeAssistant, value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC).replace(microsecond=0)
    if value.tzinfo is None:
        timezone = dt_util.get_time_zone(hass.config.time_zone)
        if timezone is None:
            timezone = UTC
        value = value.replace(tzinfo=timezone)
    return value.astimezone(UTC).replace(microsecond=0)


CREATE_ANIMAL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NAME): _required_text,
        vol.Required(ATTR_SPECIES): _required_text,
        vol.Optional(ATTR_BREED): _optional_text,
        vol.Optional(ATTR_COLOR): _optional_text,
        vol.Optional(ATTR_SEX): vol.In(ANIMAL_SEXES),
        vol.Optional(ATTR_BIRTH_DATE): _optional_date,
        vol.Optional(ATTR_ARRIVAL_DATE): _optional_date,
    }
)

UPDATE_ANIMAL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): _required_text,
        vol.Optional(ATTR_NAME): _required_text,
        vol.Optional(ATTR_SPECIES): _required_text,
        vol.Optional(ATTR_BREED): _optional_text,
        vol.Optional(ATTR_COLOR): _optional_text,
        vol.Optional(ATTR_SEX): vol.In(ANIMAL_SEXES),
        vol.Optional(ATTR_BIRTH_DATE): _optional_date,
        vol.Optional(ATTR_ARRIVAL_DATE): _optional_date,
    }
)

SET_ANIMAL_STATUS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): _required_text,
        vol.Required(ATTR_STATUS): vol.In(ANIMAL_STATUSES),
    }
)

ANIMAL_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): _required_text,
    }
)

CREATE_EVENT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): _required_text,
        vol.Required(ATTR_EVENT_TYPE): vol.In(GENERAL_EVENT_TYPES),
        vol.Optional(ATTR_OCCURRED_AT): _optional_datetime,
        vol.Required(ATTR_TITLE): _required_text,
        vol.Optional(ATTR_NOTES): _optional_text,
        vol.Optional(ATTR_CORRECTION_OF_EVENT_ID): _optional_text,
    }
)

RECORD_WEIGHT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): _required_text,
        vol.Optional(ATTR_OCCURRED_AT): _optional_datetime,
        vol.Required(ATTR_WEIGHT): _positive_number,
        vol.Optional(ATTR_WEIGHT_UNIT, default="kg"): vol.In(WEIGHT_UNITS),
        vol.Optional(ATTR_NOTES): _optional_text,
        vol.Optional(ATTR_CORRECTION_OF_EVENT_ID): _optional_text,
    }
)

RECORD_SYMPTOM_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): _required_text,
        vol.Optional(ATTR_OCCURRED_AT): _optional_datetime,
        vol.Required(ATTR_SYMPTOM): _required_text,
        vol.Optional(ATTR_SEVERITY, default="moderate"): vol.In(
            SYMPTOM_SEVERITIES
        ),
        vol.Optional(ATTR_NOTES): _optional_text,
        vol.Optional(ATTR_CORRECTION_OF_EVENT_ID): _optional_text,
    }
)

RECORD_MEDICATION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): _required_text,
        vol.Optional(ATTR_OCCURRED_AT): _optional_datetime,
        vol.Required(ATTR_MEDICATION_NAME): _required_text,
        vol.Required(ATTR_DOSE): _positive_number,
        vol.Optional(ATTR_DOSE_UNIT, default="mg"): vol.In(DOSE_UNITS),
        vol.Optional(ATTR_ROUTE): vol.In(ADMINISTRATION_ROUTES),
        vol.Optional(ATTR_NOTES): _optional_text,
        vol.Optional(ATTR_CORRECTION_OF_EVENT_ID): _optional_text,
    }
)

RECORD_VACCINATION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): _required_text,
        vol.Optional(ATTR_OCCURRED_AT): _optional_datetime,
        vol.Required(ATTR_VACCINE_NAME): _required_text,
        vol.Required(ATTR_DOSE): _positive_number,
        vol.Optional(ATTR_DOSE_UNIT, default="ml"): vol.In(DOSE_UNITS),
        vol.Optional(ATTR_ROUTE): vol.In(ADMINISTRATION_ROUTES),
        vol.Optional(ATTR_BATCH_NUMBER): _optional_text,
        vol.Optional(ATTR_NOTES): _optional_text,
        vol.Optional(ATTR_CORRECTION_OF_EVENT_ID): _optional_text,
    }
)

LIST_EVENTS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): _required_text,
        vol.Optional(ATTR_LIMIT, default=50): vol.All(
            vol.Coerce(int),
            vol.Range(min=1, max=200),
        ),
    }
)

EDITABLE_FIELDS = {
    ATTR_NAME,
    ATTR_SPECIES,
    ATTR_BREED,
    ATTR_COLOR,
    ATTR_SEX,
    ATTR_BIRTH_DATE,
    ATTR_ARRIVAL_DATE,
}


def _get_runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise ServiceValidationError("Animal Health is not loaded")


def _get_animal_id_from_device(hass: HomeAssistant, device_id: str) -> str:
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        raise ServiceValidationError("The selected animal device no longer exists")
    for identifier_domain, identifier in device.identifiers:
        if identifier_domain == DOMAIN:
            return identifier
    raise ServiceValidationError("The selected device is not an Animal Health animal")


def _update_device_metadata(
    hass: HomeAssistant,
    device_id: str,
    animal: Animal,
) -> None:
    dr.async_get(hass).async_update_device(
        device_id,
        name=animal.name,
        model=animal.species,
    )


def _canonical_animal_values(
    species_value: str,
    breed_value: str | None,
) -> tuple[str, str | None, str | None]:
    species, species_id = canonical_species_name(species_value)
    try:
        breed, _breed_id = canonical_breed_name(breed_value, species_id)
    except ValueError as err:
        raise ServiceValidationError(str(err)) from err
    return species, breed, species_id


async def _refresh_and_get_response(
    runtime_data: AnimalHealthRuntimeData,
    animal_id: str,
) -> tuple[Animal, ServiceResponse]:
    await runtime_data.coordinator.async_request_refresh()
    animal = runtime_data.coordinator.data.get(animal_id)
    if animal is None:
        raise ServiceValidationError("The selected animal no longer exists")
    return animal, animal.as_dict()


async def _optional_response(
    call: ServiceCall,
    runtime_data: AnimalHealthRuntimeData,
    animal_id: str,
) -> tuple[Animal, ServiceResponse]:
    animal, response = await _refresh_and_get_response(runtime_data, animal_id)
    return animal, response if call.return_response else None


async def _create_event_response(
    hass: HomeAssistant,
    call: ServiceCall,
    *,
    event_type: str,
    title: str,
    value: float | None = None,
    unit: str | None = None,
    data: dict[str, Any] | None = None,
) -> ServiceResponse:
    runtime_data = _get_runtime_data(hass)
    animal_id = _get_animal_id_from_device(hass, call.data[ATTR_DEVICE_ID])
    try:
        event = await runtime_data.database.create_event(
            animal_id=animal_id,
            event_type=event_type,
            occurred_at=_event_datetime_utc(
                hass,
                call.data.get(ATTR_OCCURRED_AT),
            ),
            title=title,
            notes=call.data.get(ATTR_NOTES),
            value=value,
            unit=unit,
            correction_of_event_id=call.data.get(ATTR_CORRECTION_OF_EVENT_ID),
            data=data,
        )
    except KeyError as err:
        raise ServiceValidationError(
            "The animal or referenced event no longer exists"
        ) from err
    except ValueError as err:
        raise ServiceValidationError(str(err)) from err
    return event.as_dict() if call.return_response else None


def async_setup_services(hass: HomeAssistant) -> None:
    async def handle_create_animal(call: ServiceCall) -> ServiceResponse:
        runtime_data = _get_runtime_data(hass)
        species, breed, _species_id = _canonical_animal_values(
            call.data[ATTR_SPECIES],
            call.data.get(ATTR_BREED),
        )
        animal = await runtime_data.database.create_animal(
            name=call.data[ATTR_NAME],
            species=species,
            breed=breed,
            color=call.data.get(ATTR_COLOR),
            sex=call.data.get(ATTR_SEX),
            birth_date=call.data.get(ATTR_BIRTH_DATE),
            arrival_date=call.data.get(ATTR_ARRIVAL_DATE),
        )
        _, response = await _optional_response(call, runtime_data, animal.id)
        return response

    async def handle_update_animal(call: ServiceCall) -> ServiceResponse:
        runtime_data = _get_runtime_data(hass)
        device_id = call.data[ATTR_DEVICE_ID]
        animal_id = _get_animal_id_from_device(hass, device_id)
        current = runtime_data.coordinator.data.get(animal_id)
        if current is None:
            raise ServiceValidationError("The selected animal no longer exists")

        changes = {
            field: call.data[field]
            for field in EDITABLE_FIELDS
            if field in call.data
        }
        if not changes:
            raise ServiceValidationError("No animal fields were supplied")

        if ATTR_SPECIES in call.data or ATTR_BREED in call.data:
            species_input = call.data.get(ATTR_SPECIES, current.species)
            species_name, species_id = canonical_species_name(species_input)
            changes[ATTR_SPECIES] = species_name

            if ATTR_BREED in call.data:
                try:
                    breed_name, _breed_id = canonical_breed_name(
                        call.data.get(ATTR_BREED),
                        species_id,
                    )
                except ValueError as err:
                    raise ServiceValidationError(str(err)) from err
                changes[ATTR_BREED] = breed_name
            elif (
                ATTR_SPECIES in call.data
                and current.breed
                and species_name != current.species
            ):
                changes[ATTR_BREED] = None

        try:
            await runtime_data.database.update_animal(animal_id, changes)
        except KeyError as err:
            raise ServiceValidationError("The selected animal no longer exists") from err
        animal, response = await _optional_response(call, runtime_data, animal_id)
        _update_device_metadata(hass, device_id, animal)
        return response

    async def handle_set_animal_status(call: ServiceCall) -> ServiceResponse:
        runtime_data = _get_runtime_data(hass)
        animal_id = _get_animal_id_from_device(hass, call.data[ATTR_DEVICE_ID])
        try:
            await runtime_data.database.set_animal_status(
                animal_id,
                call.data[ATTR_STATUS],
            )
        except KeyError as err:
            raise ServiceValidationError("The selected animal no longer exists") from err
        _, response = await _optional_response(call, runtime_data, animal_id)
        return response

    async def handle_archive_animal(call: ServiceCall) -> ServiceResponse:
        runtime_data = _get_runtime_data(hass)
        animal_id = _get_animal_id_from_device(hass, call.data[ATTR_DEVICE_ID])
        try:
            await runtime_data.database.set_animal_archived(animal_id, True)
        except KeyError as err:
            raise ServiceValidationError("The selected animal no longer exists") from err
        _, response = await _optional_response(call, runtime_data, animal_id)
        return response

    async def handle_restore_animal(call: ServiceCall) -> ServiceResponse:
        runtime_data = _get_runtime_data(hass)
        animal_id = _get_animal_id_from_device(hass, call.data[ATTR_DEVICE_ID])
        try:
            await runtime_data.database.set_animal_archived(animal_id, False)
        except KeyError as err:
            raise ServiceValidationError("The selected animal no longer exists") from err
        _, response = await _optional_response(call, runtime_data, animal_id)
        return response

    async def handle_create_event(call: ServiceCall) -> ServiceResponse:
        return await _create_event_response(
            hass,
            call,
            event_type=call.data[ATTR_EVENT_TYPE],
            title=call.data[ATTR_TITLE],
        )

    async def handle_record_weight(call: ServiceCall) -> ServiceResponse:
        return await _create_event_response(
            hass,
            call,
            event_type=EVENT_TYPE_WEIGHT,
            title="weight_measurement",
            value=call.data[ATTR_WEIGHT],
            unit=call.data[ATTR_WEIGHT_UNIT],
            data={"measurement": "weight"},
        )

    async def handle_record_symptom(call: ServiceCall) -> ServiceResponse:
        known_symptoms = {
            "reduced_appetite",
            "lethargy",
            "diarrhea",
            "coughing",
            "sneezing",
            "lameness",
            "weight_loss",
        }
        symptom = call.data[ATTR_SYMPTOM]
        return await _create_event_response(
            hass,
            call,
            event_type=EVENT_TYPE_SYMPTOM,
            title=symptom,
            data={
                "symptom": symptom,
                "severity": call.data[ATTR_SEVERITY],
                "catalog_source": (
                    "builtin" if symptom in known_symptoms else "custom"
                ),
            },
        )

    async def handle_record_medication(call: ServiceCall) -> ServiceResponse:
        medication_name, catalog_data = product_event_metadata(
            call.data[ATTR_MEDICATION_NAME]
        )
        route = call.data.get(ATTR_ROUTE)
        data = {
            "medication_name": medication_name,
            **catalog_data,
        }
        if route is not None:
            data["route"] = route
        return await _create_event_response(
            hass,
            call,
            event_type=EVENT_TYPE_MEDICATION,
            title=medication_name,
            value=call.data[ATTR_DOSE],
            unit=call.data[ATTR_DOSE_UNIT],
            data=data,
        )

    async def handle_record_vaccination(call: ServiceCall) -> ServiceResponse:
        vaccine_name, catalog_data = product_event_metadata(
            call.data[ATTR_VACCINE_NAME],
            vaccine=True,
        )
        data = {
            "vaccine_name": vaccine_name,
            **catalog_data,
        }
        if route := call.data.get(ATTR_ROUTE):
            data["route"] = route
        if batch_number := call.data.get(ATTR_BATCH_NUMBER):
            data["batch_number"] = batch_number
        return await _create_event_response(
            hass,
            call,
            event_type=EVENT_TYPE_VACCINATION,
            title=vaccine_name,
            value=call.data[ATTR_DOSE],
            unit=call.data[ATTR_DOSE_UNIT],
            data=data,
        )

    async def handle_list_events(call: ServiceCall) -> ServiceResponse:
        runtime_data = _get_runtime_data(hass)
        animal_id = _get_animal_id_from_device(hass, call.data[ATTR_DEVICE_ID])
        events = await runtime_data.database.get_events(
            animal_id,
            call.data[ATTR_LIMIT],
        )
        return {"events": [event.as_dict() for event in events]}

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
        SERVICE_SET_ANIMAL_STATUS,
        handle_set_animal_status,
        schema=SET_ANIMAL_STATUS_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ARCHIVE_ANIMAL,
        handle_archive_animal,
        schema=ANIMAL_DEVICE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESTORE_ANIMAL,
        handle_restore_animal,
        schema=ANIMAL_DEVICE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_EVENT,
        handle_create_event,
        schema=CREATE_EVENT_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RECORD_WEIGHT,
        handle_record_weight,
        schema=RECORD_WEIGHT_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RECORD_SYMPTOM,
        handle_record_symptom,
        schema=RECORD_SYMPTOM_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RECORD_MEDICATION,
        handle_record_medication,
        schema=RECORD_MEDICATION_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RECORD_VACCINATION,
        handle_record_vaccination,
        schema=RECORD_VACCINATION_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LIST_EVENTS,
        handle_list_events,
        schema=LIST_EVENTS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
