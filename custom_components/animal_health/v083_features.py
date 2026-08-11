from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import ai_task, websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .ai_assist import get_ai_upload
from .const import DOMAIN
from .runtime import AnimalHealthRuntimeData

_STATE_COMMAND = f"{DOMAIN}/v083/state"
_SET_ANIMAL_META_COMMAND = f"{DOMAIN}/v083/animal_metadata/set"
_SET_GROUP_META_COMMAND = f"{DOMAIN}/v083/group_metadata/set"
_REMEMBER_CUSTOM_COMMAND = f"{DOMAIN}/v083/custom_value/remember"
_AI_ANALYZE_COMMAND = f"{DOMAIN}/v083/ai/analyze"
_MAX_CONTEXT_LENGTH = 6000
_MAX_AI_ENTRIES = 50
_CUSTOM_KINDS = ("breed", "color", "medication")
_AI_FIELDS = (
    "document_type",
    "suggested_record_type",
    "suggested_title",
    "animal_name",
    "document_date",
    "scheduled_date",
    "due_time",
    "medication_name",
    "vaccine_name",
    "dose",
    "dose_unit",
    "route",
    "vaccination_target",
    "provider",
    "diagnosis",
    "treatment",
    "visit_reason",
    "notes",
    "confidence",
    "uncertainties",
    "weight",
    "weight_unit",
    "occurred_at",
    "recurrence_type",
    "recurrence_interval",
)
_AI_BATCH_STRUCTURE = vol.Schema(
    {
        vol.Required(
            "entries_json",
            description=(
                "A JSON array encoded as a string. Each array item is one extracted draft "
                "and may only contain the requested canonical fields."
            ),
        ): str
    },
    extra=vol.PREVENT_EXTRA,
)


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _required_text(value: Any) -> str:
    text = str(value).strip()
    if not text:
        raise vol.Invalid("value must not be empty")
    return text


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_context(value: Any) -> str:
    text = str(value or "").strip()
    if len(text) > _MAX_CONTEXT_LENGTH:
        raise vol.Invalid(f"context must not exceed {_MAX_CONTEXT_LENGTH} characters")
    return text


def _normalize_custom(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def _initialize_sync(store) -> None:
    with store._connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS animal_v083_metadata (
                animal_id TEXT PRIMARY KEY
                    REFERENCES animals(id) ON DELETE CASCADE,
                distinctive_features TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS animal_group_v083_metadata (
                group_id TEXT PRIMARY KEY
                    REFERENCES animal_groups(id) ON DELETE CASCADE,
                breed TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS animal_custom_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                species_id TEXT NOT NULL DEFAULT '',
                breed_context TEXT NOT NULL DEFAULT '',
                value TEXT NOT NULL,
                normalized_value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(kind, species_id, breed_context, normalized_value)
            );
            CREATE INDEX IF NOT EXISTS idx_animal_custom_values_kind
                ON animal_custom_values(kind, species_id, breed_context, normalized_value);
            """
        )


async def async_initialize_v083_features(store) -> None:
    await store._hass.async_add_executor_job(_initialize_sync, store)


def _load_medicine_catalog() -> list[dict[str, Any]]:
    path = Path(__file__).parent / "catalogs" / "medicines_ch.json"
    with path.open(encoding="utf-8") as file:
        document = json.load(file)
    result: list[dict[str, Any]] = []
    for raw in document.get("items", []):
        item = dict(raw)
        result.append(
            {
                "id": str(item.get("id") or ""),
                "name": str(
                    item.get("name")
                    or item.get("name_de")
                    or item.get("name_en")
                    or item.get("id")
                    or ""
                ),
                "active_ingredients": [
                    str(value) for value in (item.get("active_ingredients") or [])
                ],
                "target_species": [
                    str(value) for value in (item.get("target_species") or [])
                ],
                "aliases": [str(value) for value in (item.get("aliases") or [])],
                "authorisation_number": (
                    str(item["authorisation_number"])
                    if item.get("authorisation_number")
                    else None
                ),
                "catalog_source": "standard",
            }
        )
    return sorted(result, key=lambda item: item["name"].casefold())


def _state_sync(store) -> dict[str, Any]:
    with store._connect() as connection:
        animal_metadata = {
            str(row["animal_id"]): {
                "distinctive_features": str(row["distinctive_features"] or ""),
                "updated_at": str(row["updated_at"]),
            }
            for row in connection.execute(
                "SELECT animal_id, distinctive_features, updated_at FROM animal_v083_metadata"
            ).fetchall()
        }
        group_metadata = {
            str(row["group_id"]): {
                "breed": str(row["breed"] or ""),
                "updated_at": str(row["updated_at"]),
            }
            for row in connection.execute(
                "SELECT group_id, breed, updated_at FROM animal_group_v083_metadata"
            ).fetchall()
        }
        custom_values = [
            {
                "id": int(row["id"]),
                "kind": str(row["kind"]),
                "species_id": str(row["species_id"] or ""),
                "breed_context": str(row["breed_context"] or ""),
                "value": str(row["value"]),
                "catalog_source": "custom",
                "authorisation_status": (
                    "unknown" if str(row["kind"]) == "medication" else None
                ),
            }
            for row in connection.execute(
                """
                SELECT id, kind, species_id, breed_context, value
                FROM animal_custom_values
                ORDER BY kind, value COLLATE NOCASE, id
                """
            ).fetchall()
        ]
    return {
        "animal_metadata": animal_metadata,
        "group_metadata": group_metadata,
        "custom_values": custom_values,
        "medicines": _load_medicine_catalog(),
    }


def _set_animal_metadata_sync(
    store,
    animal_id: str,
    distinctive_features: str | None,
) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with store._connect() as connection:
        if connection.execute(
            "SELECT 1 FROM animals WHERE id = ?", (animal_id,)
        ).fetchone() is None:
            raise KeyError(animal_id)
        connection.execute(
            """
            INSERT INTO animal_v083_metadata (animal_id, distinctive_features, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(animal_id) DO UPDATE SET
                distinctive_features = excluded.distinctive_features,
                updated_at = excluded.updated_at
            """,
            (animal_id, distinctive_features, now),
        )
    return {
        "animal_id": animal_id,
        "distinctive_features": distinctive_features or "",
        "updated_at": now,
    }


def _set_group_metadata_sync(
    store,
    group_id: str,
    breed: str | None,
) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with store._connect() as connection:
        if connection.execute(
            "SELECT 1 FROM animal_groups WHERE id = ?", (group_id,)
        ).fetchone() is None:
            raise KeyError(group_id)
        connection.execute(
            """
            INSERT INTO animal_group_v083_metadata (group_id, breed, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(group_id) DO UPDATE SET
                breed = excluded.breed,
                updated_at = excluded.updated_at
            """,
            (group_id, breed, now),
        )
    return {"group_id": group_id, "breed": breed or "", "updated_at": now}


def _remember_custom_sync(
    store,
    kind: str,
    value: str,
    species_id: str | None,
    breed_context: str | None,
) -> dict[str, Any]:
    clean = re.sub(r"\s+", " ", value.strip())
    normalized = _normalize_custom(clean)
    species = str(species_id or "").strip().casefold()
    breed = re.sub(r"\s+", " ", str(breed_context or "").strip()).casefold()
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with store._connect() as connection:
        connection.execute(
            """
            INSERT INTO animal_custom_values (
                kind, species_id, breed_context, value, normalized_value, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(kind, species_id, breed_context, normalized_value) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (kind, species, breed, clean, normalized, now, now),
        )
        row = connection.execute(
            """
            SELECT id, kind, species_id, breed_context, value
            FROM animal_custom_values
            WHERE kind = ? AND species_id = ? AND breed_context = ? AND normalized_value = ?
            """,
            (kind, species, breed, normalized),
        ).fetchone()
    return {
        "id": int(row["id"]),
        "kind": str(row["kind"]),
        "species_id": str(row["species_id"]),
        "breed_context": str(row["breed_context"]),
        "value": str(row["value"]),
        "catalog_source": "custom",
        "authorisation_status": "unknown" if kind == "medication" else None,
    }


def _animal_context(hass: HomeAssistant) -> tuple[list[str], dict[str, str]]:
    names: list[str] = []
    by_name: dict[str, str] = {}
    for animal in _runtime_data(hass).coordinator.data.values():
        name = str(animal.name).strip()
        if not name:
            continue
        names.append(name)
        by_name[name.casefold()] = str(animal.id)
    return sorted(names, key=str.casefold), by_name


def _ai_instructions(hass: HomeAssistant, mode: str, context: str) -> str:
    names, _ = _animal_context(hass)
    fields = ", ".join(_AI_FIELDS)
    common = (
        "This is data-entry assistance only. Extract facts explicitly visible in the supplied "
        "images/documents or explicitly stated in the user's supplemental text. Never diagnose, "
        "prescribe, recommend, calculate a dose, or infer missing medical facts. Create one draft "
        "entry for every distinct measurement, medication administration/task, vaccination, visit, "
        "treatment, check, or reminder that is clearly present. A handwritten list with nine animal "
        "names and nine weights therefore produces nine entries. If one clearly written date applies "
        "to the entire list, copy that date to each affected entry. Do not silently discard uncertain "
        "rows: retain them as entries and explain uncertainty. Known animal names are: "
        f"{', '.join(names) if names else '(none)'}. Set animal_name only when exactly one known animal "
        "is clearly identified. Preserve count-based doses exactly: '1 tablet' means dose='1' and "
        "dose_unit='tablet', never mg. Do not infer a dose unit from a product strength such as "
        "'100 mg/tablet'. recurrence_type may only be once, daily, weekly or monthly and may only be "
        "set when the cadence is explicit. For 'once daily', use recurrence_type='daily' and "
        "recurrence_interval='1'. Canonical dose_unit values are mcg, mg, g, ul, ml, drop, tablet, dose. "
        "Canonical weight_unit values are mg, g, kg. suggested_record_type may be medication, vaccination, "
        "veterinary_visit, treatment, health_check, weight, reminder or other. confidence must be high, "
        "medium or low. Return entries_json as a JSON ARRAY STRING. Each item must be a JSON object and "
        f"may only contain these keys: {fields}. Use empty strings for absent values."
    )
    if mode == "weight":
        common += (
            " The current capture context is weight. Prefer weight entries and focus on animal_name, "
            "weight, weight_unit, occurred_at/document_date and notes. Do not convert unrelated text "
            "into medical advice."
        )
    if context:
        common += (
            "\n\nUser-provided supplemental text follows. It is factual extraction input only:\n---\n"
            + context
            + "\n---"
        )
    return common


def _normalize_ai_entry(
    hass: HomeAssistant,
    raw: Any,
    mode: str,
) -> dict[str, Any]:
    source = raw if isinstance(raw, dict) else {}
    result = {field: str(source.get(field) or "").strip() for field in _AI_FIELDS}
    allowed_types = {
        "medication",
        "vaccination",
        "veterinary_visit",
        "treatment",
        "health_check",
        "weight",
        "reminder",
        "other",
    }
    if mode == "weight" and result["weight"]:
        result["suggested_record_type"] = "weight"
    elif result["suggested_record_type"] not in allowed_types:
        result["suggested_record_type"] = "other"
    if result["confidence"] not in {"high", "medium", "low"}:
        result["confidence"] = "low" if result["confidence"] else ""
    if result["recurrence_type"] not in {"once", "daily", "weekly", "monthly"}:
        result["recurrence_type"] = ""
        result["recurrence_interval"] = ""
    if result["weight_unit"] not in {"mg", "g", "kg"}:
        result["weight_unit"] = ""
    if result["dose_unit"] not in {
        "mcg",
        "mg",
        "g",
        "ul",
        "ml",
        "drop",
        "tablet",
        "dose",
    }:
        result["dose_unit"] = ""
    _, by_name = _animal_context(hass)
    result["matched_animal_id"] = by_name.get(result["animal_name"].casefold(), "")
    return result


def _parse_entries(hass: HomeAssistant, payload: Any, mode: str) -> list[dict[str, Any]]:
    raw_text = ""
    if isinstance(payload, dict):
        raw_text = str(payload.get("entries_json") or "").strip()
    try:
        decoded = json.loads(raw_text) if raw_text else []
    except json.JSONDecodeError as err:
        raise ValueError("AI returned invalid batch JSON") from err
    if not isinstance(decoded, list):
        raise ValueError("AI batch output must be a JSON array")
    if len(decoded) > _MAX_AI_ENTRIES:
        decoded = decoded[:_MAX_AI_ENTRIES]
    return [_normalize_ai_entry(hass, item, mode) for item in decoded]


def async_setup_v083_features(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command({vol.Required("type"): _STATE_COMMAND})
    @websocket_api.async_response
    async def websocket_state(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            state = await hass.async_add_executor_job(
                _state_sync, _runtime_data(hass).feature_store
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v083_state_failed", str(err))
            return
        connection.send_result(msg["id"], state)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SET_ANIMAL_META_COMMAND,
            vol.Required("animal_id"): _required_text,
            vol.Optional("distinctive_features"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_set_animal_metadata(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _set_animal_metadata_sync,
                _runtime_data(hass).feature_store,
                msg["animal_id"],
                msg.get("distinctive_features"),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v083_animal_metadata_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SET_GROUP_META_COMMAND,
            vol.Required("group_id"): _required_text,
            vol.Optional("breed"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_set_group_metadata(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _set_group_metadata_sync,
                _runtime_data(hass).feature_store,
                msg["group_id"],
                msg.get("breed"),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v083_group_metadata_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _REMEMBER_CUSTOM_COMMAND,
            vol.Required("kind"): vol.In(_CUSTOM_KINDS),
            vol.Required("value"): _required_text,
            vol.Optional("species_id"): _optional_text,
            vol.Optional("breed_context"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_remember_custom(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _remember_custom_sync,
                _runtime_data(hass).feature_store,
                str(msg["kind"]),
                str(msg["value"]),
                msg.get("species_id"),
                msg.get("breed_context"),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v083_custom_value_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _AI_ANALYZE_COMMAND,
            vol.Optional("upload_ids", default=[]): vol.All(
                [_required_text], vol.Length(max=10)
            ),
            vol.Optional("entity_id"): _required_text,
            vol.Optional("context", default=""): _optional_context,
            vol.Optional("mode", default="general"): vol.In(("general", "weight")),
        }
    )
    @websocket_api.async_response
    async def websocket_ai_analyze(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        upload_ids = list(msg.get("upload_ids") or [])
        context = str(msg.get("context") or "").strip()
        if not upload_ids and not context:
            connection.send_error(
                msg["id"], "v083_ai_input_required", "Photo/file, text or dictation required"
            )
            return
        try:
            records = [(upload_id, get_ai_upload(hass, upload_id)) for upload_id in upload_ids]
        except KeyError as err:
            connection.send_error(msg["id"], "v083_ai_upload_missing", str(err))
            return
        entities = sorted(hass.states.async_entity_ids("ai_task"))
        entity_id = msg.get("entity_id")
        if entity_id is None and len(entities) == 1:
            entity_id = entities[0]
        mode = str(msg.get("mode") or "general")
        try:
            result = await ai_task.async_generate_data(
                hass,
                task_name=f"animal_health_v083_{mode}_batch_extraction",
                entity_id=entity_id,
                instructions=_ai_instructions(hass, mode, context),
                structure=_AI_BATCH_STRUCTURE,
                attachments=[
                    {
                        "media_content_id": f"media-source://{DOMAIN}/{upload_id}",
                        "media_content_type": str(record["media_type"]),
                    }
                    for upload_id, record in records
                ],
            )
            entries = _parse_entries(hass, result.data, mode)
            filenames = [str(record["filename"]) for _, record in records]
            for entry in entries:
                entry["source_filenames"] = filenames
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v083_ai_analyze_failed", str(err))
            return
        connection.send_result(
            msg["id"],
            {
                "entries": entries,
                "count": len(entries),
                "source_filenames": [str(record["filename"]) for _, record in records],
            },
        )

    websocket_api.async_register_command(hass, websocket_state)
    websocket_api.async_register_command(hass, websocket_set_animal_metadata)
    websocket_api.async_register_command(hass, websocket_set_group_metadata)
    websocket_api.async_register_command(hass, websocket_remember_custom)
    websocket_api.async_register_command(hass, websocket_ai_analyze)
