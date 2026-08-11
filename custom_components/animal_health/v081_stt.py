from __future__ import annotations

from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import stt, websocket_api
from homeassistant.core import HomeAssistant

from .ai_assist import AI_STATE_KEY, get_ai_upload
from .const import DOMAIN

_TRANSCRIBE_COMMAND = f"{DOMAIN}/v081/transcribe"


def _required_text(value: Any) -> str:
    text = str(value).strip()
    if not text:
        raise vol.Invalid("value must not be empty")
    return text


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


def _language_candidates(locale: str, country: str) -> list[str]:
    configured = locale.replace("_", "-").strip()
    base = configured.split("-", 1)[0].lower() if configured else ""
    candidates: list[str] = []

    def add(value: str | None) -> None:
        if value and value not in candidates:
            candidates.append(value)

    add(configured)
    if base == "de":
        add("de-CH")
        add("de-DE")
        add("de")
    elif base:
        if country:
            add(f"{base}-{country.upper()}")
        add(base)
    return candidates


def _stt_language(
    hass: HomeAssistant,
    entity: Any,
    requested_language: str | None,
) -> str:
    supported = [str(item) for item in (entity.supported_languages or [])]
    if not supported:
        raise ValueError("Speech-to-text entity exposes no supported language")
    lowered = {item.lower(): item for item in supported}
    country = str(hass.config.country or "").upper()
    configured = str(hass.config.language or "en")
    candidates: list[str] = []
    for locale in (requested_language or "", configured):
        for candidate in _language_candidates(locale, country):
            if candidate not in candidates:
                candidates.append(candidate)
    for candidate in candidates:
        exact = lowered.get(candidate.lower())
        if exact:
            return exact
    requested_base = (requested_language or configured).replace("_", "-").split("-", 1)[0].lower()
    if requested_base:
        for item in supported:
            if item.lower().split("-", 1)[0] == requested_base:
                return item
    return supported[0]


def _discard_upload(hass: HomeAssistant, upload_id: str) -> None:
    record = hass.data.setdefault(AI_STATE_KEY, {}).setdefault("uploads", {}).pop(
        upload_id, None
    )
    if record is not None:
        Path(record["path"]).unlink(missing_ok=True)


def async_setup_v081_stt(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command(
        {
            vol.Required("type"): _TRANSCRIBE_COMMAND,
            vol.Required("upload_id"): _required_text,
            vol.Optional("entity_id"): _required_text,
            vol.Optional("language"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_transcribe(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        upload_id = msg["upload_id"]
        record = get_ai_upload(hass, upload_id)
        if record is None:
            connection.send_error(
                msg["id"], "ai_audio_missing", "Dictation upload expired or missing"
            )
            return
        if record["media_type"] not in {"audio/wav", "audio/x-wav"}:
            connection.send_error(msg["id"], "ai_audio_invalid", "Dictation must be WAV audio")
            return
        try:
            entity_id, entity = _stt_entity(hass, msg.get("entity_id"))
            language = _stt_language(hass, entity, msg.get("language"))
            metadata = stt.SpeechMetadata(
                language=language,
                format=stt.AudioFormats.WAV,
                codec=stt.AudioCodecs.PCM,
                bit_rate=stt.AudioBitRates.BITRATE_16,
                sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
                channel=stt.AudioChannels.CHANNEL_MONO,
            )
            if not entity.check_metadata(metadata):
                raise ValueError(
                    f"Selected speech-to-text entity does not support 16 kHz mono WAV in {language}"
                )
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

    websocket_api.async_register_command(hass, websocket_transcribe)
