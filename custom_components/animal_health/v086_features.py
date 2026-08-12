from __future__ import annotations

import json
from typing import Any

import voluptuous as vol

from homeassistant.components import ai_task, websocket_api
from homeassistant.core import HomeAssistant

from .ai_assist import get_ai_upload
from .const import DOMAIN
from .v083_features import _animal_context

_AI_ANALYZE_COMMAND = f"{DOMAIN}/v086/ai/analyze"
_MAX_CONTEXT_LENGTH = 6000
_MAX_AI_ENTRIES = 50
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
    "symptom",
    "severity",
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


def _required_text(value: Any) -> str:
    text = str(value).strip()
    if not text:
        raise vol.Invalid("value must not be empty")
    return text


def _optional_context(value: Any) -> str:
    text = str(value or "").strip()
    if len(text) > _MAX_CONTEXT_LENGTH:
        raise vol.Invalid(f"context must not exceed {_MAX_CONTEXT_LENGTH} characters")
    return text


def _instructions(hass: HomeAssistant, mode: str, context: str) -> str:
    names, _ = _animal_context(hass)
    fields = ", ".join(_AI_FIELDS)
    common = (
        "This is data-entry assistance only. Extract only facts explicitly visible in supplied "
        "images/documents or explicitly stated by the user. Never diagnose, prescribe, recommend, "
        "calculate a dose, or invent missing medical facts. Create one draft for every distinct "
        "measurement, administration, symptom, vaccination, visit, treatment, check, or reminder. "
        "If one explicit date/time clearly applies to an entire list, copy it to every affected draft. "
        "Do not silently discard uncertain rows; retain them and explain uncertainty. Known animal "
        f"names are: {', '.join(names) if names else '(none)'}. Set animal_name only when exactly one "
        "known animal is clearly identified. Preserve count-based doses exactly: '1 tablet' means "
        "dose='1' and dose_unit='tablet', never mg. Do not infer a dose unit from product strength. "
        "confidence must be high, medium or low. severity may only be mild, moderate, severe or "
        "critical and only when explicitly supported. recurrence_type may only be once, daily, weekly "
        "or monthly and only when cadence is explicit. Canonical dose_unit values are mcg, mg, g, ul, "
        "ml, drop, tablet, dose. Canonical weight_unit values are mg, g, kg. suggested_record_type may "
        "be medication, vaccination, veterinary_visit, treatment, health_check, symptom, weight, "
        "reminder or other. Return entries_json as a JSON ARRAY STRING. Each item must be a JSON object "
        f"and may only contain these keys: {fields}. Use empty strings for absent values."
    )
    if mode == "weight":
        common += (
            " The current capture context is WEIGHT. Prefer weight drafts and focus on animal_name, "
            "weight, weight_unit, occurred_at/document_date, due_time and notes."
        )
    elif mode == "medication":
        common += (
            " The current capture context is a MEDICATION ADMINISTRATION FORM. Prefer medication "
            "drafts and focus on animal_name, medication_name, dose, dose_unit, route, occurred_at/"
            "document_date, due_time and notes. Do not create a recurrence unless the user explicitly "
            "states one."
        )
    elif mode == "symptom":
        common += (
            " The current capture context is a SYMPTOM FORM. Prefer symptom drafts and focus on "
            "animal_name, symptom, severity, occurred_at/document_date, due_time and notes. Do not "
            "interpret the symptom as a diagnosis."
        )
    if context:
        common += (
            "\n\nUser-provided supplemental text follows. It is factual extraction input only:\n---\n"
            + context
            + "\n---"
        )
    return common


def _normalize_entry(hass: HomeAssistant, raw: Any, mode: str) -> dict[str, Any]:
    source = raw if isinstance(raw, dict) else {}
    result = {field: str(source.get(field) or "").strip() for field in _AI_FIELDS}
    allowed_types = {
        "medication",
        "vaccination",
        "veterinary_visit",
        "treatment",
        "health_check",
        "symptom",
        "weight",
        "reminder",
        "other",
    }
    if mode == "weight" and result["weight"]:
        result["suggested_record_type"] = "weight"
    elif mode == "medication" and result["medication_name"]:
        result["suggested_record_type"] = "medication"
    elif mode == "symptom" and result["symptom"]:
        result["suggested_record_type"] = "symptom"
    elif result["suggested_record_type"] not in allowed_types:
        result["suggested_record_type"] = "other"
    if result["confidence"] not in {"high", "medium", "low"}:
        result["confidence"] = "low" if result["confidence"] else ""
    if result["severity"] not in {"mild", "moderate", "severe", "critical"}:
        result["severity"] = ""
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
    raw_text = str(payload.get("entries_json") or "").strip() if isinstance(payload, dict) else ""
    try:
        decoded = json.loads(raw_text) if raw_text else []
    except json.JSONDecodeError as err:
        raise ValueError("AI returned invalid batch JSON") from err
    if not isinstance(decoded, list):
        raise ValueError("AI batch output must be a JSON array")
    return [_normalize_entry(hass, item, mode) for item in decoded[:_MAX_AI_ENTRIES]]


def async_setup_v086_features(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command(
        {
            vol.Required("type"): _AI_ANALYZE_COMMAND,
            vol.Optional("upload_ids", default=[]): vol.All(
                [_required_text], vol.Length(max=10)
            ),
            vol.Optional("entity_id"): _required_text,
            vol.Optional("context", default=""): _optional_context,
            vol.Optional("mode", default="general"): vol.In(
                ("general", "weight", "medication", "symptom")
            ),
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
                msg["id"],
                "v086_ai_input_required",
                "Photo/file, text or dictation required",
            )
            return
        try:
            records = [(upload_id, get_ai_upload(hass, upload_id)) for upload_id in upload_ids]
        except KeyError as err:
            connection.send_error(msg["id"], "v086_ai_upload_missing", str(err))
            return
        entities = sorted(hass.states.async_entity_ids("ai_task"))
        entity_id = msg.get("entity_id")
        if entity_id is None and len(entities) == 1:
            entity_id = entities[0]
        mode = str(msg.get("mode") or "general")
        try:
            result = await ai_task.async_generate_data(
                hass,
                task_name=f"animal_health_v086_{mode}_batch_extraction",
                entity_id=entity_id,
                instructions=_instructions(hass, mode, context),
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
                entry["capture_mode"] = mode
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v086_ai_analyze_failed", str(err))
            return
        connection.send_result(
            msg["id"],
            {
                "entries": entries,
                "count": len(entries),
                "source_filenames": [str(record["filename"]) for _, record in records],
            },
        )

    websocket_api.async_register_command(hass, websocket_ai_analyze)
