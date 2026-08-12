from __future__ import annotations

import json
from typing import Any

import voluptuous as vol

from homeassistant.components import ai_task, websocket_api
from homeassistant.core import HomeAssistant

from .ai_assist import get_ai_upload
from .const import DOMAIN
from .v083_features import _animal_context
from .v086_features import (
    _AI_BATCH_STRUCTURE,
    _optional_context,
    _parse_entries,
    _required_text,
    _instructions as _instructions_v086,
)

_AI_ANALYZE_COMMAND = f"{DOMAIN}/v088/ai/analyze"


def _instructions(hass: HomeAssistant, mode: str, context: str) -> str:
    instructions = _instructions_v086(hass, mode, context)
    if mode != "weight":
        return instructions
    return instructions + (
        "\n\nWEIGHT-LIST COMPLETENESS RULES: First inspect the entire attachment before returning any "
        "result. Scan every visible row from the top edge to the bottom edge and, where relevant, "
        "from left to right. A handwritten list with twelve visible animal/weight rows must produce "
        "twelve draft entries, not a partial subset. Treat every visible line or row that plausibly "
        "contains an animal name and/or weight as its own draft. Never omit a row merely because the "
        "handwriting, animal name or number is uncertain: keep the row, leave uncertain fields empty, "
        "and describe the uncertainty. The known animal names are identification vocabulary only; do "
        "not invent rows for animals that are not actually visible in the attachment. Before returning, "
        "perform a final top-to-bottom coverage check and make sure every visible measurement row is "
        "represented exactly once."
    )


def _coverage_instructions(
    hass: HomeAssistant,
    first_entries: list[dict[str, Any]],
    context: str,
) -> str:
    names, _ = _animal_context(hass)
    summary = [
        {
            "animal_name": str(entry.get("animal_name") or ""),
            "weight": str(entry.get("weight") or ""),
            "weight_unit": str(entry.get("weight_unit") or ""),
            "document_date": str(entry.get("document_date") or ""),
            "occurred_at": str(entry.get("occurred_at") or ""),
        }
        for entry in first_entries
    ]
    instructions = (
        "This is a second, completeness-only verification pass for a multi-row WEIGHT document. "
        "Do not diagnose, recommend, calculate, or invent information. Re-scan the COMPLETE supplied "
        "attachment from top to bottom and left to right. Return entries_json containing ONLY genuinely "
        "additional visible weight rows that are not already represented by the first-pass entries below. "
        "Do not repeat an existing row. Do not create rows just because an animal exists in the known-name "
        "list. If an additional visible row is uncertain, still return that row with uncertain fields empty "
        "and explain the uncertainty. If no visible rows were missed, return an empty JSON array string. "
        f"Known animal names for identification are: {', '.join(names) if names else '(none)'}.\n\n"
        "First-pass entries already represented:\n"
        + json.dumps(summary, ensure_ascii=False)
    )
    if context:
        instructions += (
            "\n\nUser-provided supplemental text is factual extraction input only:\n---\n"
            + context
            + "\n---"
        )
    return instructions


def _merge_weight_entries(
    primary: list[dict[str, Any]],
    additions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result = [dict(entry) for entry in primary]

    def name_key(entry: dict[str, Any]) -> str:
        return str(entry.get("animal_name") or "").strip().casefold()

    def unnamed_signature(entry: dict[str, Any]) -> tuple[str, ...]:
        return (
            str(entry.get("weight") or "").strip(),
            str(entry.get("weight_unit") or "").strip().casefold(),
            str(entry.get("occurred_at") or "").strip(),
            str(entry.get("document_date") or "").strip(),
            str(entry.get("due_time") or "").strip(),
            str(entry.get("notes") or "").strip().casefold(),
        )

    for addition in additions:
        candidate = dict(addition)
        candidate_name = name_key(candidate)
        if candidate_name:
            matching = [entry for entry in result if name_key(entry) == candidate_name]
            if matching:
                existing = matching[0]
                for field in (
                    "weight",
                    "weight_unit",
                    "occurred_at",
                    "document_date",
                    "due_time",
                    "notes",
                    "confidence",
                    "uncertainties",
                ):
                    if not str(existing.get(field) or "").strip() and str(candidate.get(field) or "").strip():
                        existing[field] = candidate[field]
                continue
        elif any(
            not name_key(entry) and unnamed_signature(entry) == unnamed_signature(candidate)
            for entry in result
        ):
            continue
        result.append(candidate)
    return result


def async_setup_v088_features(hass: HomeAssistant) -> None:
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
                "v088_ai_input_required",
                "Photo/file, text or dictation required",
            )
            return

        records: list[tuple[str, dict[str, Any]]] = []
        for upload_id in upload_ids:
            record = get_ai_upload(hass, upload_id)
            if record is None:
                connection.send_error(
                    msg["id"],
                    "v088_ai_upload_missing",
                    "AI upload expired or missing",
                )
                return
            records.append((upload_id, record))

        entities = sorted(hass.states.async_entity_ids("ai_task"))
        entity_id = msg.get("entity_id")
        if entity_id is None and len(entities) == 1:
            entity_id = entities[0]
        mode = str(msg.get("mode") or "general")
        attachments = [
            {
                "media_content_id": f"media-source://{DOMAIN}/{upload_id}",
                "media_content_type": str(record["media_type"]),
            }
            for upload_id, record in records
        ]

        try:
            result = await ai_task.async_generate_data(
                hass,
                task_name=f"animal_health_v088_{mode}_batch_extraction",
                entity_id=entity_id,
                instructions=_instructions(hass, mode, context),
                structure=_AI_BATCH_STRUCTURE,
                attachments=attachments,
            )
            entries = _parse_entries(hass, result.data, mode)
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v088_ai_analyze_failed", str(err))
            return

        coverage_checked = False
        coverage_added_count = 0
        if mode == "weight" and attachments and len(entries) > 1:
            try:
                verification = await ai_task.async_generate_data(
                    hass,
                    task_name="animal_health_v088_weight_coverage_check",
                    entity_id=entity_id,
                    instructions=_coverage_instructions(hass, entries, context),
                    structure=_AI_BATCH_STRUCTURE,
                    attachments=attachments,
                )
                additions = _parse_entries(hass, verification.data, "weight")
                before = len(entries)
                entries = _merge_weight_entries(entries, additions)
                coverage_added_count = len(entries) - before
                coverage_checked = True
            except Exception:  # noqa: BLE001
                coverage_checked = False

        filenames = [str(record["filename"]) for _, record in records]
        for entry in entries:
            entry["source_filenames"] = filenames
            entry["capture_mode"] = mode

        connection.send_result(
            msg["id"],
            {
                "entries": entries,
                "count": len(entries),
                "source_filenames": filenames,
                "coverage_checked": coverage_checked,
                "coverage_added_count": coverage_added_count,
            },
        )

    websocket_api.async_register_command(hass, websocket_ai_analyze)
