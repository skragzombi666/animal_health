from __future__ import annotations

import json
import secrets
import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.service import async_set_service_schema
from homeassistant.util import dt as dt_util

from .const import DATABASE_NAME, DOMAIN
from .task_store import (
    RECURRENCE_TYPES,
    TASK_SCOPE_ANIMAL,
    TASK_SCOPE_GENERAL,
    TaskStore,
)

TASK_KIND_REMINDER = "reminder"
TASK_KIND_WEIGHT = "weight"
TASK_KIND_MEDICATION = "medication"
TASK_KIND_VACCINATION = "vaccination"
TASK_KIND_HEALTH_CHECK = "health_check"
TASK_KIND_CARE = "care"
TASK_KIND_VETERINARY_VISIT = "veterinary_visit"
TASK_KINDS = (
    TASK_KIND_REMINDER,
    TASK_KIND_WEIGHT,
    TASK_KIND_MEDICATION,
    TASK_KIND_VACCINATION,
    TASK_KIND_HEALTH_CHECK,
    TASK_KIND_CARE,
    TASK_KIND_VETERINARY_VISIT,
)

SERVICE_CREATE_RECORD_TASK = "create_record_task"
SERVICE_RECORD_REMINDER_TASK = "record_reminder_task"
SERVICE_RECORD_WEIGHT_TASK = "record_weight_task"
SERVICE_RECORD_MEDICATION_TASK = "record_medication_task"
SERVICE_RECORD_VACCINATION_TASK = "record_vaccination_task"
SERVICE_RECORD_HEALTH_CHECK_TASK = "record_health_check_task"
SERVICE_RECORD_CARE_TASK = "record_care_task"
SERVICE_RECORD_VETERINARY_VISIT_TASK = "record_veterinary_visit_task"
SERVICE_LIST_TASK_RECORDS = "list_task_records"

_RECORD_ID_ALPHABET = "23456789ABCDEFGHJKMNPQRSTVWXYZ"
_RECORD_ID_LENGTH = 7


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


def _date_value(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(cv.string(value))


def _datetime_value(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(cv.string(value))


def _positive(value: Any) -> float:
    result = vol.Coerce(float)(value)
    if result <= 0:
        raise vol.Invalid("value must be greater than zero")
    return result


def _positive_integer(value: Any) -> int:
    result = vol.Coerce(int)(value)
    if result < 1:
        raise vol.Invalid("value must be at least 1")
    return result


def _string_list(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    return [_required_text(item) for item in values]


CREATE_RECORD_TASK_SCHEMA = vol.Schema(
    {
        vol.Optional("task_scope", default=TASK_SCOPE_ANIMAL): vol.In(
            (TASK_SCOPE_ANIMAL, TASK_SCOPE_GENERAL)
        ),
        vol.Optional("device_ids"): _string_list,
        vol.Required("task_kind"): vol.In(TASK_KINDS),
        vol.Required("title"): _required_text,
        vol.Optional("description"): _optional_text,
        vol.Required("recurrence_type"): vol.In(RECURRENCE_TYPES),
        vol.Optional("recurrence_interval", default=1): _positive_integer,
        vol.Required("start_date"): _date_value,
        vol.Optional("end_date"): _date_value,
        vol.Optional("due_time"): cv.time,
        vol.Optional("medication_name"): _optional_text,
        vol.Optional("dose"): _positive,
        vol.Optional("dose_unit"): vol.In(
            ("mcg", "mg", "g", "ul", "ml", "drop", "tablet", "dose")
        ),
        vol.Optional("route"): _optional_text,
        vol.Optional("vaccination_targets"): _string_list,
        vol.Optional("vaccine_name"): _optional_text,
        vol.Optional("antigen"): _optional_text,
        vol.Optional("check_focus"): _optional_text,
        vol.Optional("care_type"): _optional_text,
        vol.Optional("visit_reason"): _optional_text,
        vol.Optional("planned_notes"): _optional_text,
    }
)

BASE_RECORD_SCHEMA = {
    vol.Required("occurrence_id"): _required_text,
    vol.Optional("performed_at"): _datetime_value,
    vol.Optional("notes"): _optional_text,
    vol.Optional("deviation_reason"): _optional_text,
}

REMINDER_RECORD_SCHEMA = vol.Schema(BASE_RECORD_SCHEMA)
WEIGHT_RECORD_SCHEMA = vol.Schema(
    {
        **BASE_RECORD_SCHEMA,
        vol.Required("weight"): _positive,
        vol.Optional("weight_unit", default="kg"): vol.In(("mg", "g", "kg")),
    }
)
MEDICATION_RECORD_SCHEMA = vol.Schema(
    {
        **BASE_RECORD_SCHEMA,
        vol.Optional("medication_name"): _optional_text,
        vol.Optional("dose"): _positive,
        vol.Optional("dose_unit"): vol.In(
            ("mcg", "mg", "g", "ul", "ml", "drop", "tablet", "dose")
        ),
        vol.Optional("route"): _optional_text,
    }
)
VACCINATION_RECORD_SCHEMA = vol.Schema(
    {
        **BASE_RECORD_SCHEMA,
        vol.Optional("vaccination_targets"): _string_list,
        vol.Optional("vaccine_name"): _optional_text,
        vol.Optional("antigen"): _optional_text,
        vol.Optional("dose"): _positive,
        vol.Optional("dose_unit"): vol.In(
            ("mcg", "mg", "g", "ul", "ml", "drop", "tablet", "dose")
        ),
        vol.Optional("route"): _optional_text,
        vol.Optional("batch_number"): _optional_text,
    }
)
HEALTH_CHECK_RECORD_SCHEMA = vol.Schema(
    {
        **BASE_RECORD_SCHEMA,
        vol.Required("result"): vol.In(("normal", "symptom")),
        vol.Optional("symptom"): _optional_text,
        vol.Optional("severity"): vol.In(("mild", "moderate", "severe", "critical")),
    }
)
CARE_RECORD_SCHEMA = vol.Schema(
    {
        **BASE_RECORD_SCHEMA,
        vol.Optional("performed_care"): _optional_text,
    }
)
VETERINARY_VISIT_RECORD_SCHEMA = vol.Schema(
    {
        **BASE_RECORD_SCHEMA,
        vol.Optional("outcome"): _optional_text,
    }
)
LIST_TASK_RECORDS_SCHEMA = vol.Schema(
    {
        vol.Optional("occurrence_id"): _required_text,
        vol.Optional("task_id"): _required_text,
        vol.Optional("limit", default=100): vol.All(vol.Coerce(int), vol.Range(min=1, max=500)),
    }
)


def _connect(hass: HomeAssistant) -> sqlite3.Connection:
    connection = sqlite3.connect(Path(hass.config.path(DATABASE_NAME)))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _initialize_sync(hass: HomeAssistant) -> None:
    with _connect(hass) as connection:
        task_columns = {
            str(row[1]) for row in connection.execute("PRAGMA table_info(tasks)").fetchall()
        }
        if "task_kind" not in task_columns:
            connection.execute(
                "ALTER TABLE tasks ADD COLUMN task_kind TEXT NOT NULL DEFAULT 'reminder'"
            )
        if "planned_data_json" not in task_columns:
            connection.execute(
                "ALTER TABLE tasks ADD COLUMN planned_data_json TEXT NOT NULL DEFAULT '{}'"
            )

        occurrence_columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(task_occurrences)").fetchall()
        }
        if "planned_data_json" not in occurrence_columns:
            connection.execute(
                "ALTER TABLE task_occurrences ADD COLUMN planned_data_json TEXT NOT NULL DEFAULT '{}'"
            )
        if "resolved_at" not in occurrence_columns:
            connection.execute("ALTER TABLE task_occurrences ADD COLUMN resolved_at TEXT")

        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS task_records (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE RESTRICT,
                occurrence_id TEXT NOT NULL UNIQUE
                    REFERENCES task_occurrences(id) ON DELETE RESTRICT,
                animal_id TEXT REFERENCES animals(id) ON DELETE RESTRICT,
                task_kind TEXT NOT NULL,
                scheduled_for TEXT NOT NULL,
                performed_at TEXT NOT NULL,
                timing_status TEXT NOT NULL
                    CHECK (timing_status IN ('early', 'on_time', 'late')),
                timing_deviation_minutes INTEGER,
                timing_deviation_days INTEGER,
                planned_data_json TEXT NOT NULL,
                actual_data_json TEXT NOT NULL,
                deviation_reason TEXT,
                notes TEXT,
                event_id TEXT REFERENCES events(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_task_records_task
                ON task_records(task_id, performed_at DESC);
            CREATE INDEX IF NOT EXISTS idx_task_records_animal
                ON task_records(animal_id, performed_at DESC);
            """
        )

        connection.execute(
            """
            UPDATE task_occurrences
            SET planned_data_json = COALESCE(
                (SELECT tasks.planned_data_json FROM tasks WHERE tasks.id = task_occurrences.task_id),
                '{}'
            )
            WHERE planned_data_json = '{}'
            """
        )


async def async_initialize_task_records(hass: HomeAssistant) -> None:
    await hass.async_add_executor_job(_initialize_sync, hass)


def _animal_id_from_device(hass: HomeAssistant, device_id: str) -> str:
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        raise ServiceValidationError("Das ausgewählte Tiergerät existiert nicht mehr")
    for identifier_domain, identifier in device.identifiers:
        if identifier_domain == DOMAIN:
            return identifier
    raise ServiceValidationError("Das ausgewählte Gerät gehört nicht zu Animal Health")


def _planned_data(data: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "medication_name",
        "dose",
        "dose_unit",
        "route",
        "vaccination_targets",
        "vaccine_name",
        "antigen",
        "check_focus",
        "care_type",
        "visit_reason",
        "planned_notes",
    )
    return {field: data[field] for field in fields if data.get(field) is not None}


def _validate_planned(kind: str, planned: dict[str, Any]) -> None:
    if kind == TASK_KIND_MEDICATION:
        for field in ("medication_name", "dose", "dose_unit"):
            if field not in planned:
                raise ServiceValidationError(
                    "Bei einer Medikamentenaufgabe müssen Medikament, geplante Dosis und Einheit angegeben werden"
                )
    elif kind == TASK_KIND_VACCINATION and not planned.get("vaccination_targets"):
        raise ServiceValidationError(
            "Bei einer Impfaufgabe muss mindestens ein Impfziel angegeben werden"
        )


def _set_task_metadata_sync(
    hass: HomeAssistant,
    task_id: str,
    task_kind: str,
    planned: dict[str, Any],
) -> None:
    encoded = json.dumps(planned, ensure_ascii=False, sort_keys=True)
    with _connect(hass) as connection:
        connection.execute(
            "UPDATE tasks SET task_kind = ?, planned_data_json = ? WHERE id = ?",
            (task_kind, encoded, task_id),
        )
        connection.execute(
            "UPDATE task_occurrences SET planned_data_json = ? WHERE task_id = ? AND status = 'pending'",
            (encoded, task_id),
        )


def _generate_id(connection: sqlite3.Connection, table: str, prefix: str) -> str:
    existing = {
        str(row[0]) for row in connection.execute(f"SELECT id FROM {table}").fetchall()
    }
    while True:
        suffix = "".join(secrets.choice(_RECORD_ID_ALPHABET) for _ in range(_RECORD_ID_LENGTH))
        record_id = f"{prefix}-{suffix}"
        if record_id not in existing:
            return record_id


def _normalise_performed_at(hass: HomeAssistant, value: datetime | None) -> datetime:
    performed = value or datetime.now(UTC)
    if performed.tzinfo is None:
        timezone = dt_util.get_time_zone(hass.config.time_zone) or UTC
        performed = performed.replace(tzinfo=timezone)
    return performed.astimezone(UTC).replace(microsecond=0)


def _timing(
    hass: HomeAssistant,
    scheduled_for: datetime,
    performed_at: datetime,
    due_time: str | None,
) -> tuple[str, int | None, int | None]:
    timezone = dt_util.get_time_zone(hass.config.time_zone) or UTC
    scheduled_local = scheduled_for.astimezone(timezone)
    performed_local = performed_at.astimezone(timezone)
    if due_time is None:
        days = (performed_local.date() - scheduled_local.date()).days
        return ("early" if days < 0 else "late" if days > 0 else "on_time", None, days)
    minutes = round((performed_at - scheduled_for).total_seconds() / 60)
    return ("early" if minutes < 0 else "late" if minutes > 0 else "on_time", minutes, None)


def _event_payload(
    kind: str,
    task_title: str,
    planned: dict[str, Any],
    actual: dict[str, Any],
) -> tuple[str, str, float | None, str | None]:
    if kind == TASK_KIND_WEIGHT:
        return "weight", task_title, float(actual["weight"]), str(actual["weight_unit"])
    if kind == TASK_KIND_MEDICATION:
        return "medication", str(actual["medication_name"]), float(actual["dose"]), str(actual["dose_unit"])
    if kind == TASK_KIND_VACCINATION:
        targets = actual.get("vaccination_targets") or planned.get("vaccination_targets") or []
        return "vaccination", "Impfung gegen " + ", ".join(targets), (
            float(actual["dose"]) if actual.get("dose") is not None else None
        ), actual.get("dose_unit")
    if kind == TASK_KIND_HEALTH_CHECK:
        if actual.get("result") == "symptom":
            return "symptom", str(actual["symptom"]), None, None
        return "observation", "Gesundheitskontrolle unauffällig", None, None
    if kind == TASK_KIND_CARE:
        return "care", str(actual.get("performed_care") or planned.get("care_type") or task_title), None, None
    if kind == TASK_KIND_VETERINARY_VISIT:
        return "veterinary_visit", str(planned.get("visit_reason") or task_title), None, None
    return "other", task_title, None, None


def _execute_sync(
    hass: HomeAssistant,
    occurrence_id: str,
    expected_kind: str,
    performed_at: datetime,
    actual_input: dict[str, Any],
    deviation_reason: str | None,
    notes: str | None,
) -> dict[str, Any]:
    with _connect(hass) as connection:
        row = connection.execute(
            """
            SELECT occurrence.id, occurrence.task_id, occurrence.scheduled_for,
                   occurrence.status, occurrence.planned_data_json,
                   task.animal_id, task.title, task.due_time, task.task_kind,
                   task.planned_data_json AS task_planned_data_json
            FROM task_occurrences AS occurrence
            JOIN tasks AS task ON task.id = occurrence.task_id
            WHERE occurrence.id = ?
            """,
            (occurrence_id,),
        ).fetchone()
        if row is None:
            raise KeyError(occurrence_id)
        if str(row["status"]) != "pending":
            raise ValueError("Nur offene Fälligkeiten können dokumentiert werden")
        kind = str(row["task_kind"] or TASK_KIND_REMINDER)
        if kind != expected_kind:
            raise ValueError(
                f"Die Fälligkeit gehört zur Aufgabenart '{kind}' und nicht zu '{expected_kind}'"
            )

        planned_raw = str(row["planned_data_json"] or row["task_planned_data_json"] or "{}")
        planned = json.loads(planned_raw)
        actual = {key: value for key, value in actual_input.items() if value is not None}

        if kind == TASK_KIND_MEDICATION:
            for field in ("medication_name", "dose", "dose_unit", "route"):
                if field not in actual and planned.get(field) is not None:
                    actual[field] = planned[field]
            for field in ("medication_name", "dose", "dose_unit"):
                if actual.get(field) is None:
                    raise ValueError(f"Tatsächliche Angabe fehlt: {field}")
        elif kind == TASK_KIND_VACCINATION:
            for field in ("vaccination_targets", "vaccine_name", "antigen", "dose", "dose_unit", "route"):
                if field not in actual and planned.get(field) is not None:
                    actual[field] = planned[field]
            if not actual.get("vaccination_targets"):
                raise ValueError("Mindestens ein tatsächliches Impfziel ist erforderlich")
        elif kind == TASK_KIND_HEALTH_CHECK:
            if actual.get("result") == "symptom" and not actual.get("symptom"):
                raise ValueError("Bei auffälliger Kontrolle muss ein Symptom angegeben werden")

        scheduled_for = datetime.fromisoformat(str(row["scheduled_for"]))
        timing_status, deviation_minutes, deviation_days = _timing(
            hass,
            scheduled_for,
            performed_at,
            str(row["due_time"]) if row["due_time"] is not None else None,
        )
        now = datetime.now(UTC).replace(microsecond=0).isoformat()
        record_id = _generate_id(connection, "task_records", "TR")
        event_id: str | None = None
        animal_id = str(row["animal_id"]) if row["animal_id"] is not None else None

        if animal_id is not None:
            event_type, event_title, value, unit = _event_payload(
                kind,
                str(row["title"]),
                planned,
                actual,
            )
            event_id = _generate_id(connection, "events", "EV")
            event_data = {
                "source": "task_occurrence",
                "task_id": str(row["task_id"]),
                "task_occurrence_id": occurrence_id,
                "task_record_id": record_id,
                "task_kind": kind,
                "scheduled_for": scheduled_for.isoformat(),
                "performed_at": performed_at.isoformat(),
                "timing_status": timing_status,
                "timing_deviation_minutes": deviation_minutes,
                "timing_deviation_days": deviation_days,
                "planned": planned,
                "actual": actual,
                "deviation_reason": deviation_reason,
            }
            connection.execute(
                """
                INSERT INTO events (
                    id, animal_id, event_type, occurred_at, title, notes,
                    value, unit, correction_of_event_id, data_json,
                    task_id, task_occurrence_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    animal_id,
                    event_type,
                    performed_at.isoformat(),
                    event_title,
                    notes,
                    value,
                    unit,
                    json.dumps(event_data, ensure_ascii=False, sort_keys=True),
                    str(row["task_id"]),
                    occurrence_id,
                    now,
                ),
            )

        connection.execute(
            """
            INSERT INTO task_records (
                id, task_id, occurrence_id, animal_id, task_kind,
                scheduled_for, performed_at, timing_status,
                timing_deviation_minutes, timing_deviation_days,
                planned_data_json, actual_data_json, deviation_reason,
                notes, event_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                str(row["task_id"]),
                occurrence_id,
                animal_id,
                kind,
                scheduled_for.isoformat(),
                performed_at.isoformat(),
                timing_status,
                deviation_minutes,
                deviation_days,
                json.dumps(planned, ensure_ascii=False, sort_keys=True),
                json.dumps(actual, ensure_ascii=False, sort_keys=True),
                deviation_reason,
                notes,
                event_id,
                now,
            ),
        )
        connection.execute(
            """
            UPDATE task_occurrences
            SET status = 'completed', completed_at = ?, resolved_at = ?,
                notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (performed_at.isoformat(), performed_at.isoformat(), notes, now, occurrence_id),
        )

        return {
            "id": record_id,
            "task_id": str(row["task_id"]),
            "occurrence_id": occurrence_id,
            "animal_id": animal_id,
            "task_kind": kind,
            "scheduled_for": scheduled_for.isoformat(),
            "performed_at": performed_at.isoformat(),
            "timing_status": timing_status,
            "timing_deviation_minutes": deviation_minutes,
            "timing_deviation_days": deviation_days,
            "planned": planned,
            "actual": actual,
            "deviation_reason": deviation_reason,
            "notes": notes,
            "event_id": event_id,
        }


def _list_records_sync(
    hass: HomeAssistant,
    occurrence_id: str | None,
    task_id: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    values: list[Any] = []
    if occurrence_id:
        clauses.append("occurrence_id = ?")
        values.append(occurrence_id)
    if task_id:
        clauses.append("task_id = ?")
        values.append(task_id)
    sql = "SELECT * FROM task_records"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY performed_at DESC LIMIT ?"
    values.append(limit)
    with _connect(hass) as connection:
        rows = connection.execute(sql, values).fetchall()
    return [
        {
            "id": str(row["id"]),
            "task_id": str(row["task_id"]),
            "occurrence_id": str(row["occurrence_id"]),
            "animal_id": str(row["animal_id"]) if row["animal_id"] is not None else None,
            "task_kind": str(row["task_kind"]),
            "scheduled_for": str(row["scheduled_for"]),
            "performed_at": str(row["performed_at"]),
            "timing_status": str(row["timing_status"]),
            "timing_deviation_minutes": row["timing_deviation_minutes"],
            "timing_deviation_days": row["timing_deviation_days"],
            "planned": json.loads(str(row["planned_data_json"])),
            "actual": json.loads(str(row["actual_data_json"])),
            "deviation_reason": row["deviation_reason"],
            "notes": row["notes"],
            "event_id": row["event_id"],
        }
        for row in rows
    ]


def _device_selector_multiple() -> dict[str, Any]:
    return {"device": {"filter": [{"integration": DOMAIN}], "multiple": True}}


def _select(options: list[tuple[str, str]], *, multiple: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "options": [{"value": value, "label": label} for value, label in options],
        "mode": "dropdown",
    }
    if multiple:
        result["multiple"] = True
    return {"select": result}


def _register_descriptions(hass: HomeAssistant) -> None:
    task_kinds = [
        (TASK_KIND_REMINDER, "Erinnerung"),
        (TASK_KIND_WEIGHT, "Gewicht erfassen"),
        (TASK_KIND_MEDICATION, "Medikament geben"),
        (TASK_KIND_VACCINATION, "Impfung durchführen"),
        (TASK_KIND_HEALTH_CHECK, "Gesundheitskontrolle"),
        (TASK_KIND_CARE, "Pflege durchführen"),
        (TASK_KIND_VETERINARY_VISIT, "Tierarztbesuch"),
    ]
    recurrence = [("once", "Einmalig"), ("daily", "Täglich"), ("weekly", "Wöchentlich"), ("monthly", "Monatlich")]
    create_fields: dict[str, Any] = {
        "task_scope": {"name": "Aufgabenbereich", "default": "animal", "selector": _select([("animal", "Tierbezogen"), ("general", "Allgemein")])},
        "device_ids": {"name": "Tiere", "description": "Ein oder mehrere Tiere auswählen. Bei allgemeinen Erinnerungs- oder Pflegeaufgaben leer lassen.", "selector": _device_selector_multiple()},
        "task_kind": {"name": "Aufgabenart", "required": True, "selector": _select(task_kinds)},
        "title": {"name": "Titel", "required": True, "selector": {"text": {}}},
        "description": {"name": "Beschreibung", "selector": {"text": {"multiline": True}}},
        "recurrence_type": {"name": "Wiederholung", "required": True, "selector": _select(recurrence)},
        "recurrence_interval": {"name": "Intervall", "default": 1, "selector": {"number": {"min": 1, "max": 365, "step": 1, "mode": "box"}}},
        "start_date": {"name": "Startdatum", "required": True, "selector": {"date": {}}},
        "end_date": {"name": "Enddatum", "selector": {"date": {}}},
        "due_time": {"name": "Uhrzeit", "selector": {"time": {}}},
        "medication_name": {"name": "Geplantes Medikament", "selector": {"text": {}}},
        "dose": {"name": "Geplante Dosis", "selector": {"number": {"min": 0.001, "step": "any", "mode": "box"}}},
        "dose_unit": {"name": "Geplante Dosiseinheit", "selector": _select([("mcg", "µg – Mikrogramm"), ("mg", "mg – Milligramm"), ("g", "g – Gramm"), ("ul", "µL – Mikroliter"), ("ml", "mL – Milliliter"), ("drop", "Tropfen"), ("tablet", "Tablette"), ("dose", "Dosis")])},
        "route": {"name": "Geplanter Applikationsweg", "selector": {"text": {}}},
        "vaccination_targets": {"name": "Geplante Impfung gegen", "selector": {"text": {"multiple": True}}},
        "vaccine_name": {"name": "Geplanter Impfstoff", "selector": {"text": {}}},
        "antigen": {"name": "Geplantes Antigen / Impfstamm", "selector": {"text": {}}},
        "check_focus": {"name": "Schwerpunkt der Gesundheitskontrolle", "selector": {"text": {}}},
        "care_type": {"name": "Geplante Pflege", "selector": {"text": {}}},
        "visit_reason": {"name": "Grund des Tierarztbesuchs", "selector": {"text": {}}},
        "planned_notes": {"name": "Planungsnotiz", "selector": {"text": {"multiline": True}}},
    }
    async_set_service_schema(hass, DOMAIN, SERVICE_CREATE_RECORD_TASK, {"name": "Dokumentationsaufgabe anlegen", "description": "Legt eine Aufgabe an, deren geplante und tatsächliche Durchführung miteinander verknüpft dokumentiert werden.", "fields": create_fields})

    common = {
        "occurrence_id": {"name": "Fälligkeits-ID", "required": True, "selector": {"text": {}}},
        "performed_at": {"name": "Tatsächlich durchgeführt am", "selector": {"datetime": {}}},
        "deviation_reason": {"name": "Begründung der Abweichung", "description": "Grund für abweichende tatsächliche Angaben oder eine zu frühe beziehungsweise verspätete Durchführung.", "selector": {"text": {"multiline": True}}},
        "notes": {"name": "Notiz", "selector": {"text": {"multiline": True}}},
    }
    descriptions = {
        SERVICE_RECORD_REMINDER_TASK: ("Erinnerungsaufgabe dokumentieren", common),
        SERVICE_RECORD_WEIGHT_TASK: ("Gewichtsaufgabe dokumentieren", {**common, "weight": {"name": "Tatsächliches Gewicht", "required": True, "selector": {"number": {"min": 0.001, "step": "any", "mode": "box"}}}, "weight_unit": {"name": "Gewichtseinheit", "default": "kg", "selector": _select([("mg", "Milligramm"), ("g", "Gramm"), ("kg", "Kilogramm")])}}),
        SERVICE_RECORD_MEDICATION_TASK: ("Medikamentenaufgabe dokumentieren", {**common, "medication_name": {"name": "Tatsächlich gegebenes Medikament", "selector": {"text": {}}}, "dose": {"name": "Tatsächliche Dosis", "selector": {"number": {"min": 0.001, "step": "any", "mode": "box"}}}, "dose_unit": {"name": "Tatsächliche Dosiseinheit", "selector": _select([("mcg", "µg – Mikrogramm"), ("mg", "mg – Milligramm"), ("g", "g – Gramm"), ("ul", "µL – Mikroliter"), ("ml", "mL – Milliliter"), ("drop", "Tropfen"), ("tablet", "Tablette"), ("dose", "Dosis")])}, "route": {"name": "Tatsächlicher Applikationsweg", "selector": {"text": {}}}}),
        SERVICE_RECORD_VACCINATION_TASK: ("Impfaufgabe dokumentieren", {**common, "vaccination_targets": {"name": "Tatsächlich geimpft gegen", "selector": {"text": {"multiple": True}}}, "vaccine_name": {"name": "Tatsächlicher Impfstoff", "selector": {"text": {}}}, "antigen": {"name": "Antigen / Impfstamm", "selector": {"text": {}}}, "dose": {"name": "Tatsächliche Dosis", "selector": {"number": {"min": 0.001, "step": "any", "mode": "box"}}}, "dose_unit": {"name": "Dosiseinheit", "selector": {"text": {}}}, "route": {"name": "Applikationsweg", "selector": {"text": {}}}, "batch_number": {"name": "Charge", "selector": {"text": {}}}}),
        SERVICE_RECORD_HEALTH_CHECK_TASK: ("Gesundheitskontrolle dokumentieren", {**common, "result": {"name": "Ergebnis", "required": True, "selector": _select([("normal", "Unauffällig"), ("symptom", "Symptom festgestellt")])}, "symptom": {"name": "Festgestelltes Symptom", "selector": {"text": {}}}, "severity": {"name": "Schweregrad", "selector": _select([("mild", "Leicht"), ("moderate", "Mittel"), ("severe", "Schwer"), ("critical", "Kritisch")])}}),
        SERVICE_RECORD_CARE_TASK: ("Pflegeaufgabe dokumentieren", {**common, "performed_care": {"name": "Tatsächlich durchgeführte Pflege", "selector": {"text": {"multiline": True}}}}),
        SERVICE_RECORD_VETERINARY_VISIT_TASK: ("Tierarztaufgabe dokumentieren", {**common, "outcome": {"name": "Ergebnis des Tierarztbesuchs", "selector": {"text": {"multiline": True}}}}),
    }
    for service, (name, fields) in descriptions.items():
        async_set_service_schema(hass, DOMAIN, service, {"name": name, "description": "Dokumentiert Planung und tatsächliche Durchführung gemeinsam, erstellt den passenden Chronikeintrag und erledigt die Fälligkeit.", "fields": fields})
    async_set_service_schema(hass, DOMAIN, SERVICE_LIST_TASK_RECORDS, {"name": "Aufgabendokumentationen auflisten", "description": "Zeigt geplante und tatsächliche Durchführung inklusive zeitlicher Abweichung.", "fields": {"occurrence_id": {"name": "Fälligkeits-ID", "selector": {"text": {}}}, "task_id": {"name": "Aufgaben-ID", "selector": {"text": {}}}, "limit": {"name": "Maximale Anzahl", "default": 100, "selector": {"number": {"min": 1, "max": 500, "step": 1, "mode": "box"}}}}})


def async_setup_task_record_services(hass: HomeAssistant) -> None:
    store = TaskStore(hass)

    async def create_record_task(call: ServiceCall) -> ServiceResponse:
        scope = call.data["task_scope"]
        device_ids = call.data.get("device_ids", [])
        kind = call.data["task_kind"]
        planned = _planned_data(call.data)
        _validate_planned(kind, planned)
        if scope == TASK_SCOPE_ANIMAL and not device_ids:
            raise ServiceValidationError("Für eine tierbezogene Aufgabe muss mindestens ein Tier ausgewählt werden")
        if scope == TASK_SCOPE_GENERAL and device_ids:
            raise ServiceValidationError("Für eine allgemeine Aufgabe dürfen keine Tiere ausgewählt werden")
        if scope == TASK_SCOPE_GENERAL and kind not in (TASK_KIND_REMINDER, TASK_KIND_CARE):
            raise ServiceValidationError("Diese Aufgabenart benötigt ein Tier")

        animal_ids = [_animal_id_from_device(hass, item) for item in device_ids]
        targets = animal_ids if scope == TASK_SCOPE_ANIMAL else [None]
        tasks: list[dict[str, Any]] = []
        for animal_id in targets:
            task = await store.create_task(
                animal_id=animal_id,
                title=call.data["title"],
                description=call.data.get("description"),
                recurrence_type=call.data["recurrence_type"],
                recurrence_interval=call.data["recurrence_interval"],
                start_date=call.data["start_date"],
                end_date=call.data.get("end_date"),
                due_time=call.data.get("due_time"),
            )
            await hass.async_add_executor_job(
                _set_task_metadata_sync,
                hass,
                task.id,
                kind,
                planned,
            )
            result = task.as_dict(store.timezone)
            result["task_kind"] = kind
            result["planned"] = planned
            tasks.append(result)
        for entry in hass.config_entries.async_entries(DOMAIN):
            if getattr(entry, "runtime_data", None) is not None:
                await entry.runtime_data.coordinator.async_request_refresh()
        response = {"tasks": tasks}
        return response if call.return_response else None

    async def execute(call: ServiceCall, kind: str) -> ServiceResponse:
        performed_at = _normalise_performed_at(hass, call.data.get("performed_at"))
        excluded = {"occurrence_id", "performed_at", "notes", "deviation_reason"}
        actual = {key: value for key, value in call.data.items() if key not in excluded}
        try:
            record = await hass.async_add_executor_job(
                _execute_sync,
                hass,
                call.data["occurrence_id"],
                kind,
                performed_at,
                actual,
                call.data.get("deviation_reason"),
                call.data.get("notes"),
            )
        except (KeyError, ValueError) as err:
            raise ServiceValidationError(str(err)) from err
        for entry in hass.config_entries.async_entries(DOMAIN):
            if getattr(entry, "runtime_data", None) is not None:
                await entry.runtime_data.coordinator.async_request_refresh()
        response = {"task_record": record}
        return response if call.return_response else None

    async def list_records(call: ServiceCall) -> ServiceResponse:
        records = await hass.async_add_executor_job(
            _list_records_sync,
            hass,
            call.data.get("occurrence_id"),
            call.data.get("task_id"),
            call.data["limit"],
        )
        return {"task_records": records}

    hass.services.async_register(DOMAIN, SERVICE_CREATE_RECORD_TASK, create_record_task, schema=CREATE_RECORD_TASK_SCHEMA, supports_response=SupportsResponse.OPTIONAL)
    mappings = (
        (SERVICE_RECORD_REMINDER_TASK, TASK_KIND_REMINDER, REMINDER_RECORD_SCHEMA),
        (SERVICE_RECORD_WEIGHT_TASK, TASK_KIND_WEIGHT, WEIGHT_RECORD_SCHEMA),
        (SERVICE_RECORD_MEDICATION_TASK, TASK_KIND_MEDICATION, MEDICATION_RECORD_SCHEMA),
        (SERVICE_RECORD_VACCINATION_TASK, TASK_KIND_VACCINATION, VACCINATION_RECORD_SCHEMA),
        (SERVICE_RECORD_HEALTH_CHECK_TASK, TASK_KIND_HEALTH_CHECK, HEALTH_CHECK_RECORD_SCHEMA),
        (SERVICE_RECORD_CARE_TASK, TASK_KIND_CARE, CARE_RECORD_SCHEMA),
        (SERVICE_RECORD_VETERINARY_VISIT_TASK, TASK_KIND_VETERINARY_VISIT, VETERINARY_VISIT_RECORD_SCHEMA),
    )
    for service, kind, schema in mappings:
        async def handler(call: ServiceCall, task_kind: str = kind) -> ServiceResponse:
            return await execute(call, task_kind)
        hass.services.async_register(DOMAIN, service, handler, schema=schema, supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, SERVICE_LIST_TASK_RECORDS, list_records, schema=LIST_TASK_RECORDS_SCHEMA, supports_response=SupportsResponse.ONLY)
    _register_descriptions(hass)
