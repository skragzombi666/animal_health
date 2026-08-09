from __future__ import annotations

import mimetypes
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import voluptuous as vol
from aiohttp import web

from homeassistant.components import ai_task, stt, websocket_api
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers.http import KEY_HASS

from .const import DOMAIN
from .runtime import AnimalHealthRuntimeData

AI_STATE_KEY = f"{DOMAIN}_ai_assist"
_AI_UPLOAD_COMMAND = f"{DOMAIN}/ai/upload"
_AI_ANALYZE_COMMAND = f"{DOMAIN}/ai/analyze"
_AI_TRANSCRIBE_COMMAND = f"{DOMAIN}/ai/transcribe"
_AI_STATUS_COMMAND = f"{DOMAIN}/ai/status"
_MAX_AI_FILE_SIZE = 15 * 1024 * 1024
_MAX_AI_DOCUMENTS = 10
_MAX_AI_CONTEXT_LENGTH = 4000
_AI_UPLOAD_TTL = timedelta(minutes=15)
_DOCUMENT_MEDIA_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}
_AUDIO_MEDIA_TYPES = {"audio/wav", "audio/x-wav"}
_ALLOWED_MEDIA_TYPES = _DOCUMENT_MEDIA_TYPES | _AUDIO_MEDIA_TYPES
_AI_RESULT_FIELDS = (
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
)
_AI_STRUCTURE = vol.Schema(
    {
        vol.Optional(field, description="Return an empty string when absent or uncertain"): str
        for field in _AI_RESULT_FIELDS
    },
    extra=vol.PREVENT_EXTRA,
)


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state.value == "loaded":
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _required_text(value: Any) -> str:
    text = str(value).strip()
    if not text:
        raise vol.Invalid("value must not be empty")
    return text


def _optional_context(value: Any) -> str:
    text = str(value or "").strip()
    if len(text) > _MAX_AI_CONTEXT_LENGTH:
        raise vol.Invalid(f"context must not exceed {_MAX_AI_CONTEXT_LENGTH} characters")
    return text


def _state(hass: HomeAssistant) -> dict[str, Any]:
    return hass.data.setdefault(AI_STATE_KEY, {})


def _cleanup_uploads(hass: HomeAssistant) -> None:
    now = datetime.now(UTC)
    uploads = _state(hass).setdefault("uploads", {})
    for upload_id, record in list(uploads.items()):
        if record["expires_at"] > now:
            continue
        Path(record["path"]).unlink(missing_ok=True)
        uploads.pop(upload_id, None)


def _discard_upload(hass: HomeAssistant, upload_id: str) -> None:
    record = _state(hass).setdefault("uploads", {}).pop(upload_id, None)
    if record is not None:
        Path(record["path"]).unlink(missing_ok=True)


def get_ai_upload(hass: HomeAssistant, upload_id: str) -> dict[str, Any] | None:
    _cleanup_uploads(hass)
    record = _state(hass).setdefault("uploads", {}).get(upload_id)
    if record is None:
        return None
    if not Path(record["path"]).is_file():
        _state(hass)["uploads"].pop(upload_id, None)
        return None
    return record


def _consume_upload_token(request: web.Request) -> None:
    hass: HomeAssistant = request.app[KEY_HASS]
    token = request.query.get("token", "")
    _cleanup_uploads(hass)
    tokens = _state(hass).setdefault("upload_tokens", {})
    record = tokens.pop(token, None)
    if record is None or record["expires_at"] < datetime.now(UTC):
        raise web.HTTPUnauthorized()


def _suffix_for(filename: str, media_type: str) -> str:
    if media_type in _AUDIO_MEDIA_TYPES:
        return ".wav"
    suffix = mimetypes.guess_extension(media_type, strict=False)
    if suffix:
        return suffix
    candidate = Path(filename).suffix.lower()
    return candidate if candidate in {".jpg", ".jpeg", ".png", ".webp", ".pdf", ".wav"} else ""


def _animal_context(hass: HomeAssistant) -> tuple[list[str], dict[str, str]]:
    runtime = _runtime_data(hass)
    names: list[str] = []
    by_name: dict[str, str] = {}
    for animal in runtime.coordinator.data.values():
        name = str(animal.name).strip()
        if not name:
            continue
        names.append(name)
        by_name[name.casefold()] = str(animal.id)
    return sorted(names, key=str.casefold), by_name


def _instructions(hass: HomeAssistant, context: str = "") -> str:
    names, _ = _animal_context(hass)
    vaccination_targets = (
        "rabies, distemper, canine_adenovirus, canine_parvovirus, leptospirosis, "
        "parainfluenza, kennel_cough, feline_panleukopenia, feline_herpesvirus, "
        "feline_calicivirus, feline_leukemia, marek, newcastle, infectious_bronchitis, "
        "gumboro, avian_pox, paramyxovirus, myxomatosis, rabbit_hemorrhagic_disease, "
        "tetanus, equine_influenza, strangles, bluetongue, other"
    )
    instructions = (
        "Extract factual information from all attached animal-health documents, medicine labels "
        "and images as one coherent data-entry case. Multiple attachments may show different sides "
        "or pages of the same item. This is data entry assistance only. Never diagnose, prescribe, "
        "recommend, calculate, change a dose, infer a treatment, or fill information that is not "
        "explicitly visible in an attachment or explicitly stated in the user-provided supplemental "
        "context. When a field is absent, ambiguous, partially hidden, contradictory or uncertain, "
        "return an empty string for that field and describe the uncertainty in uncertainties. "
        "suggested_record_type must be one of medication, vaccination, veterinary_visit, treatment, "
        "health_check, weight, reminder, other. It only classifies the supplied material; it is not "
        "a medical recommendation. suggested_title should be a short neutral title based only on "
        "supplied information. For dates use YYYY-MM-DD only when clearly supplied. For due_time use "
        "HH:MM only when a future/scheduled time is explicitly supplied. scheduled_date is only for "
        "an explicitly stated future appointment or administration date; do not reuse an invoice, "
        "issue or document date as a schedule. dose must contain the supplied numeric dose only and "
        "dose_unit its supplied unit. route is only an explicitly supplied administration route. "
        f"Known animal names are: {', '.join(names) if names else '(none)'}. "
        "Set animal_name only when the attachments or supplemental context clearly identify exactly "
        "one of these animals; otherwise leave it empty. For vaccination_target use an exact identifier "
        f"only when clearly supplied and mapping to one of: {vaccination_targets}. Otherwise leave it "
        "empty. confidence should be high, medium or low for the extraction as a whole."
    )
    if context:
        instructions += (
            "\n\nUser-provided supplemental context follows. Treat it as factual user input, not as a medical "
            "instruction to invent missing information:\n---\n"
            + context
            + "\n---"
        )
    return instructions


def _normalize_result(hass: HomeAssistant, data: Any) -> dict[str, Any]:
    raw = data if isinstance(data, dict) else {}
    result = {field: str(raw.get(field) or "").strip() for field in _AI_RESULT_FIELDS}
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
    if result["suggested_record_type"] not in allowed_types:
        result["suggested_record_type"] = "other"
    if result["confidence"] not in {"high", "medium", "low"}:
        result["confidence"] = "low" if result["confidence"] else ""
    _, by_name = _animal_context(hass)
    result["matched_animal_id"] = by_name.get(result["animal_name"].casefold(), "")
    return result


def _stt_entity(hass: HomeAssistant, requested: str | None):
    entities = sorted(hass.states.async_entity_ids("stt"))
    entity_id = requested
    if entity_id and entity_id not in entities:
        raise ValueError("Selected speech-to-text entity is not available")
    if not entity_id:
        default_engine = stt.async_default_engine(hass)
        if default_engine in entities:
            entity_id = default_engine
        elif len(entities) == 1:
            entity_id = entities[0]
        elif entities:
            entity_id = entities[0]
    if not entity_id:
        raise ValueError("No Home Assistant speech-to-text entity is available")
    entity = stt.async_get_speech_to_text_entity(hass, entity_id)
    if entity is None:
        raise ValueError("Speech-to-text entity is unavailable")
    return entity_id, entity


def _stt_language(hass: HomeAssistant, entity: Any) -> str:
    supported = list(entity.supported_languages or [])
    if not supported:
        raise ValueError("Speech-to-text entity exposes no supported language")
    configured = str(hass.config.language or "en").replace("_", "-")
    base = configured.split("-", 1)[0].lower()
    country = str(hass.config.country or "").upper()
    candidates = [configured]
    if country:
        candidates.insert(0, f"{base}-{country}")
    lowered = {item.lower(): item for item in supported}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    for item in supported:
        if item.lower().split("-", 1)[0] == base:
            return item
    return supported[0]


class AnimalHealthAIUploadView(HomeAssistantView):
    url = f"/api/{DOMAIN}/ai/upload"
    name = f"api:{DOMAIN}:ai_upload"
    requires_auth = False

    async def post(self, request: web.Request) -> web.Response:
        _consume_upload_token(request)
        hass: HomeAssistant = request.app[KEY_HASS]
        reader = await request.multipart()
        filename = "document"
        media_type = "application/octet-stream"
        content = bytearray()
        while part := await reader.next():
            if part.name != "file":
                continue
            filename = part.filename or "document"
            media_type = part.headers.get("Content-Type", media_type).split(";", 1)[0]
            while chunk := await part.read_chunk(size=64 * 1024):
                content.extend(chunk)
                if len(content) > _MAX_AI_FILE_SIZE:
                    raise web.HTTPRequestEntityTooLarge(
                        max_size=_MAX_AI_FILE_SIZE,
                        actual_size=len(content),
                    )
        if not content:
            raise web.HTTPBadRequest(text="A non-empty file is required")
        if media_type not in _ALLOWED_MEDIA_TYPES:
            raise web.HTTPUnsupportedMediaType(
                text="Supported AI inputs are JPEG, PNG, WebP, PDF and WAV"
            )
        upload_id = secrets.token_urlsafe(18)
        root = Path(hass.config.path(".storage", DOMAIN, "ai_uploads"))
        await hass.async_add_executor_job(root.mkdir, 0o700, True, True)
        path = root / f"{upload_id}{_suffix_for(filename, media_type)}"
        await hass.async_add_executor_job(path.write_bytes, bytes(content))
        _state(hass).setdefault("uploads", {})[upload_id] = {
            "path": str(path),
            "filename": filename,
            "media_type": media_type,
            "expires_at": datetime.now(UTC) + _AI_UPLOAD_TTL,
        }
        return web.json_response(
            {"upload_id": upload_id, "filename": filename, "media_type": media_type},
            headers={"Cache-Control": "no-store"},
        )


def async_setup_ai_assist(hass: HomeAssistant) -> None:
    state = _state(hass)
    if not state.get("view_registered"):
        hass.http.register_view(AnimalHealthAIUploadView())
        state["view_registered"] = True

    @websocket_api.websocket_command({vol.Required("type"): _AI_UPLOAD_COMMAND})
    @websocket_api.async_response
    async def websocket_ai_upload(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        _cleanup_uploads(hass)
        token = secrets.token_urlsafe(32)
        _state(hass).setdefault("upload_tokens", {})[token] = {
            "expires_at": datetime.now(UTC) + timedelta(minutes=2)
        }
        connection.send_result(
            msg["id"],
            {
                "url": f"/api/{DOMAIN}/ai/upload?token={token}",
                "max_size_bytes": _MAX_AI_FILE_SIZE,
                "max_documents": _MAX_AI_DOCUMENTS,
                "accepted_media_types": sorted(_ALLOWED_MEDIA_TYPES),
            },
        )

    @websocket_api.websocket_command({vol.Required("type"): _AI_STATUS_COMMAND})
    @websocket_api.async_response
    async def websocket_ai_status(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        entities = sorted(hass.states.async_entity_ids("ai_task"))
        stt_entities = sorted(hass.states.async_entity_ids("stt"))
        connection.send_result(
            msg["id"],
            {
                "available": bool(entities),
                "entities": entities,
                "stt_available": bool(stt_entities),
                "stt_entities": stt_entities,
            },
        )

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _AI_ANALYZE_COMMAND,
            vol.Optional("upload_id"): _required_text,
            vol.Optional("upload_ids"): vol.All(
                [_required_text], vol.Length(min=1, max=_MAX_AI_DOCUMENTS)
            ),
            vol.Optional("entity_id"): _required_text,
            vol.Optional("context", default=""): _optional_context,
        }
    )
    @websocket_api.async_response
    async def websocket_ai_analyze(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        upload_ids = list(msg.get("upload_ids") or [])
        if not upload_ids and msg.get("upload_id"):
            upload_ids = [msg["upload_id"]]
        if not upload_ids:
            connection.send_error(msg["id"], "ai_upload_missing", "No AI document was supplied")
            return
        records: list[tuple[str, dict[str, Any]]] = []
        for upload_id in upload_ids:
            record = get_ai_upload(hass, upload_id)
            if record is None:
                connection.send_error(
                    msg["id"], "ai_upload_missing", "AI upload expired or missing"
                )
                return
            if record["media_type"] not in _DOCUMENT_MEDIA_TYPES:
                connection.send_error(
                    msg["id"], "ai_unsupported_document", "Only image and PDF uploads can be analyzed as documents"
                )
                return
            records.append((upload_id, record))
        entities = sorted(hass.states.async_entity_ids("ai_task"))
        entity_id = msg.get("entity_id")
        if entity_id is None and len(entities) == 1:
            entity_id = entities[0]
        try:
            result = await ai_task.async_generate_data(
                hass,
                task_name="animal_health_document_extraction",
                entity_id=entity_id,
                instructions=_instructions(hass, msg.get("context", "")),
                structure=_AI_STRUCTURE,
                attachments=[
                    {
                        "media_content_id": f"media-source://{DOMAIN}/{upload_id}",
                        "media_content_type": str(record["media_type"]),
                    }
                    for upload_id, record in records
                ],
            )
            normalized = _normalize_result(hass, result.data)
            normalized["source_filenames"] = [str(record["filename"]) for _, record in records]
            normalized["source_filename"] = normalized["source_filenames"][0]
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "ai_analysis_failed", str(err))
            return
        connection.send_result(msg["id"], normalized)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _AI_TRANSCRIBE_COMMAND,
            vol.Required("upload_id"): _required_text,
            vol.Optional("entity_id"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_ai_transcribe(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        upload_id = msg["upload_id"]
        record = get_ai_upload(hass, upload_id)
        if record is None:
            connection.send_error(msg["id"], "ai_audio_missing", "Dictation upload expired or missing")
            return
        if record["media_type"] not in _AUDIO_MEDIA_TYPES:
            connection.send_error(msg["id"], "ai_audio_invalid", "Dictation must be WAV audio")
            return
        try:
            entity_id, entity = _stt_entity(hass, msg.get("entity_id"))
            language = _stt_language(hass, entity)
            metadata = stt.SpeechMetadata(
                language=language,
                format=stt.AudioFormats.WAV,
                codec=stt.AudioCodecs.PCM,
                bit_rate=stt.AudioBitRates.BITRATE_16,
                sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
                channel=stt.AudioChannels.CHANNEL_MONO,
            )
            if not entity.check_metadata(metadata):
                raise ValueError("Selected speech-to-text entity does not support 16 kHz mono WAV")
            audio = await hass.async_add_executor_job(Path(record["path"]).read_bytes)

            async def audio_stream():
                yield audio

            result = await entity.internal_async_process_audio_stream(metadata, audio_stream())
            if result.result != stt.SpeechResultState.SUCCESS or not result.text:
                raise ValueError("Speech-to-text did not return a transcript")
            transcript = str(result.text).strip()
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "ai_transcription_failed", str(err))
            return
        finally:
            _discard_upload(hass, upload_id)
        connection.send_result(
            msg["id"],
            {"text": transcript, "entity_id": entity_id, "language": language},
        )

    websocket_api.async_register_command(hass, websocket_ai_upload)
    websocket_api.async_register_command(hass, websocket_ai_status)
    websocket_api.async_register_command(hass, websocket_ai_analyze)
    websocket_api.async_register_command(hass, websocket_ai_transcribe)
