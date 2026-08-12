from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .runtime import AnimalHealthRuntimeData

_HISTORY_COMMAND = f"{DOMAIN}/v084/history_suggestions"
_DIAGNOSTICS_COMMAND = f"{DOMAIN}/v084/diagnostics"

_HISTORY_FIELDS = (
    "medication_name",
    "vaccine_name",
    "provider",
    "care_action",
    "visit_reason",
    "check_focus",
    "antigen",
)

_EXPECTED_TABLES = {
    "animals",
    "events",
    "tasks",
    "task_occurrences",
    "task_record_configs",
    "task_occurrence_plans",
    "animal_groups",
    "animal_group_memberships",
    "attachments",
    "animal_tags",
    "animal_tag_memberships",
    "animal_profiles",
    "animal_group_lifecycle",
    "v081_settings",
    "group_events",
    "task_group_targets",
    "group_task_configs",
    "animal_v083_metadata",
    "animal_group_v083_metadata",
    "animal_custom_values",
}

_EXPECTED_INDEXES = {
    "idx_animals_name",
    "idx_animals_status",
    "idx_animals_archived",
    "idx_tasks_animal_active",
    "idx_tasks_start_end",
    "idx_task_occurrences_due_status",
    "idx_events_animal_occurred",
    "idx_events_type",
    "idx_events_correction",
    "idx_attachments_animal",
    "idx_attachments_event",
    "idx_animal_group_memberships_group",
    "idx_animal_tag_memberships_tag",
    "idx_task_record_configs_kind",
    "idx_task_occurrence_plans_resolved",
    "idx_group_events_group_occurred",
    "idx_task_group_targets_group",
    "idx_group_task_configs_kind",
    "idx_animal_custom_values_kind",
}


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _walk_history_values(value: Any) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in _HISTORY_FIELDS and isinstance(item, (str, int, float)):
                text = str(item).strip()
                if text:
                    found.append((key, text))
            if isinstance(item, (dict, list)):
                found.extend(_walk_history_values(item))
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                found.extend(_walk_history_values(item))
    return found


def _history_sync(path: Path) -> dict[str, list[dict[str, Any]]]:
    aggregated: dict[str, dict[tuple[str, str], dict[str, Any]]] = defaultdict(dict)

    def add_payload(payload: str | None, species: str | None, used_at: str | None) -> None:
        if not payload:
            return
        try:
            decoded = json.loads(payload)
        except (TypeError, json.JSONDecodeError):
            return
        species_text = str(species or "").strip()
        timestamp = str(used_at or "")
        for kind, value in _walk_history_values(decoded):
            key = (species_text.casefold(), " ".join(value.split()).casefold())
            current = aggregated[kind].get(key)
            if current is None:
                aggregated[kind][key] = {
                    "value": " ".join(value.split()),
                    "species_id": species_text,
                    "count": 1,
                    "last_used": timestamp,
                }
            else:
                current["count"] = int(current["count"]) + 1
                if timestamp > str(current.get("last_used") or ""):
                    current["last_used"] = timestamp
                    current["value"] = " ".join(value.split())

    with _connect(path) as connection:
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if {"events", "animals"} <= tables:
            for row in connection.execute(
                """
                SELECT event.data_json, event.occurred_at, animal.species
                FROM events AS event
                LEFT JOIN animals AS animal ON animal.id = event.animal_id
                ORDER BY event.occurred_at DESC
                """
            ).fetchall():
                add_payload(row["data_json"], row["species"], row["occurred_at"])
        if {"task_record_configs", "tasks", "animals"} <= tables:
            for row in connection.execute(
                """
                SELECT config.template_json, task.updated_at, animal.species
                FROM task_record_configs AS config
                JOIN tasks AS task ON task.id = config.task_id
                LEFT JOIN animals AS animal ON animal.id = task.animal_id
                ORDER BY task.updated_at DESC
                """
            ).fetchall():
                add_payload(row["template_json"], row["species"], row["updated_at"])
        if {"group_events", "animal_groups"} <= tables:
            for row in connection.execute(
                """
                SELECT event.data_json, event.occurred_at, grp.species
                FROM group_events AS event
                LEFT JOIN animal_groups AS grp ON grp.id = event.group_id
                ORDER BY event.occurred_at DESC
                """
            ).fetchall():
                add_payload(row["data_json"], row["species"], row["occurred_at"])
        if {
            "group_task_configs",
            "task_group_targets",
            "animal_groups",
            "tasks",
        } <= tables:
            for row in connection.execute(
                """
                SELECT config.template_json, task.updated_at, grp.species
                FROM group_task_configs AS config
                JOIN tasks AS task ON task.id = config.task_id
                LEFT JOIN task_group_targets AS target ON target.task_id = task.id
                LEFT JOIN animal_groups AS grp ON grp.id = target.group_id
                ORDER BY task.updated_at DESC
                """
            ).fetchall():
                add_payload(row["template_json"], row["species"], row["updated_at"])

    return {
        kind: sorted(
            values.values(),
            key=lambda item: (
                -int(item.get("count") or 0),
                str(item.get("last_used") or ""),
                str(item.get("value") or "").casefold(),
            ),
            reverse=False,
        )[:100]
        for kind, values in aggregated.items()
    }


def _diagnostics_sync(database_path: Path, attachment_root: Path) -> dict[str, Any]:
    with _connect(database_path) as connection:
        integrity = [
            str(row[0]) for row in connection.execute("PRAGMA integrity_check").fetchall()
        ]
        foreign_keys = [
            {
                "table": str(row[0]),
                "rowid": row[1],
                "parent": str(row[2]),
                "fkid": row[3],
            }
            for row in connection.execute("PRAGMA foreign_key_check").fetchall()
        ]
        user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        indexes = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        missing_files: list[dict[str, str]] = []
        referenced_files: set[str] = set()
        if "attachments" in tables:
            for row in connection.execute(
                "SELECT id, filename, storage_name FROM attachments ORDER BY created_at, id"
            ).fetchall():
                storage_name = str(row["storage_name"])
                referenced_files.add(storage_name)
                if not (attachment_root / storage_name).is_file():
                    missing_files.append(
                        {
                            "attachment_id": str(row["id"]),
                            "filename": str(row["filename"]),
                            "storage_name": storage_name,
                        }
                    )

    orphaned_files = sorted(
        path.name
        for path in attachment_root.iterdir()
        if path.is_file() and path.name not in referenced_files
    ) if attachment_root.is_dir() else []
    missing_tables = sorted(_EXPECTED_TABLES - tables)
    missing_indexes = sorted(_EXPECTED_INDEXES - indexes)
    ok = (
        integrity == ["ok"]
        and not foreign_keys
        and not missing_tables
        and not missing_indexes
        and not missing_files
    )
    return {
        "ok": ok,
        "integrity_check": integrity,
        "foreign_key_violations": foreign_keys,
        "user_version": user_version,
        "table_count": len(tables),
        "index_count": len(indexes),
        "missing_tables": missing_tables,
        "missing_indexes": missing_indexes,
        "missing_attachment_files": missing_files,
        "orphaned_attachment_files": orphaned_files,
    }


def async_setup_v084_features(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command({vol.Required("type"): _HISTORY_COMMAND})
    @websocket_api.async_response
    async def websocket_history(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            runtime = _runtime_data(hass)
            result = await hass.async_add_executor_job(
                _history_sync,
                runtime.feature_store.database_path,
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v084_history_failed", str(err))
            return
        connection.send_result(msg["id"], {"suggestions": result})

    @websocket_api.websocket_command({vol.Required("type"): _DIAGNOSTICS_COMMAND})
    @websocket_api.async_response
    async def websocket_diagnostics(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        connection.require_admin()
        try:
            runtime = _runtime_data(hass)
            result = await hass.async_add_executor_job(
                _diagnostics_sync,
                runtime.feature_store.database_path,
                runtime.feature_store.attachment_root,
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v084_diagnostics_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    websocket_api.async_register_command(hass, websocket_history)
    websocket_api.async_register_command(hass, websocket_diagnostics)
