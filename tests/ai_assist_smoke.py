from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def read(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"{path} is empty"
    return text


def main() -> None:
    ai_source = read(INTEGRATION / "ai_assist.py")
    media_source = read(INTEGRATION / "media_source.py")
    frontend = "".join(
        read(FRONTEND / f"animal-health-panel.part{index:02d}.js")
        for index in (14, 15, 16)
    )
    init_source = read(INTEGRATION / "__init__.py")
    manifest = json.loads(read(INTEGRATION / "manifest.json"))
    docs = read(ROOT / "docs" / "version-0.8.0.md")

    ast.parse(ai_source)
    ast.parse(media_source)

    for dependency in ("ai_task", "media_source", "stt"):
        assert dependency in manifest["dependencies"]
    assert "async_setup_ai_assist(hass)" in init_source

    for marker in (
        "ai_task.async_generate_data",
        "media-source://{DOMAIN}",
        "_AI_STRUCTURE",
        "Never diagnose",
        "Never diagnose, prescribe,",
        "recommend, calculate",
        "return an empty string",
        "matched_animal_id",
        "AI upload expired or missing",
        "upload_ids",
        "_MAX_AI_DOCUMENTS = 10",
        "supplemental context",
        "_AI_TRANSCRIBE_COMMAND",
        "stt.async_get_speech_to_text_entity",
        "internal_async_process_audio_stream",
        "AudioFormats.WAV",
        "SAMPLERATE_16000",
    ):
        assert marker in ai_source, marker

    assert "path=Path(record[\"path\"])" in media_source
    assert "Temporary Animal Health AI uploads are not browsable" in media_source

    for marker in (
        "aiAssist",
        "aiProviderNotice",
        "aiSafety",
        'data-action=\"ai-use-task\"',
        'data-form=\"ai-upload\"',
        "aiTaskDraft",
        "/ai/status",
        "/ai/upload",
        "/ai/analyze",
        "/ai/transcribe",
        "image/jpeg,image/png,image/webp,application/pdf",
        "Aufgabe mit diesen Angaben vorbereiten",
        "multiple accept",
        "aiMoreInfo",
        "ai-start-dictation",
        "ai-stop-dictation",
        "audio/wav",
        "upload_ids",
        "aiFiles",
    ):
        assert marker in frontend, marker

    lowered = (ai_source + frontend).lower()
    assert "api.openai.com" not in lowered
    assert "api.anthropic.com" not in lowered
    assert "api_key" not in lowered

    assert "Home Assistants `AI Task`-Schnittstelle" in docs
    assert "keine automatische Speicherung" in docs
    assert "keine autonome medizinische Entscheidung" in docs
    assert "mehrere fotos" in docs.lower()
    assert "Speech-to-Text" in docs

    print("Animal Health 0.8.0 AI assistant validation passed")


if __name__ == "__main__":
    main()
