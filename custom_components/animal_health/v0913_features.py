from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .const import (
    ADMINISTRATION_ROUTES,
    ANIMAL_STATUSES,
    DATABASE_NAME,
    DOMAIN,
    DOSE_UNITS,
)
from .runtime import AnimalHealthRuntimeData

_STATE_COMMAND = f"{DOMAIN}/v0913/state"
_DELETE_EVENT_COMMAND = f"{DOMAIN}/v0913/event/delete"
_SAVE_MEDICATION_COMMAND = f"{DOMAIN}/v0913/medication/save"
_ARCHIVE_MEDICATION_COMMAND = f"{DOMAIN}/v0913/medication/archive"

_CATALOG_ENRICHMENT: dict[str, dict[str, str]] = {
    "ch.flubenol_5": {
        "concentration": "50 mg/g",
        "dosage_form": "Pulver",
    },
    "ch.flubenol_kh": {
        "concentration": "44 mg/ml",
        "dosage_form": "Paste",
    },
}

_EXTRA_CATALOG_PRODUCTS: tuple[dict[str, Any], ...] = (
    {
        "id": "ch.baytril_10",
        "name": "Baytril 10% ad us. vet.",
        "active_ingredients": ["Enrofloxacin"],
        "target_species": [],
        "aliases": ["Baytril 10%", "Baytril"],
        "concentration": "100 mg/ml",
        "dosage_form": "Injektionslösung",
    },
)


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _database_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(DATABASE_NAME))


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _normalise(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def _required_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if not text:
        raise vol.Invalid("value must not be empty")
    return text


def _optional_text(value: Any) -> str | None:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    return text or None


def _initialise_sync(path: Path) -> None:
    with _connect(path) as connection:
        event_columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(events)").fetchall()
        }
        if "is_deleted" not in event_columns:
            connection.execute(
                "ALTER TABLE events ADD COLUMN is_deleted INTEGER NOT NULL "
                "DEFAULT 0 CHECK (is_deleted IN (0,1))"
            )
        if "deleted_at" not in event_columns:
            connection.execute("ALTER TABLE events ADD COLUMN deleted_at TEXT")
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_deleted_occurred "
            "ON events(is_deleted, occurred_at DESC, created_at DESC)"
        )

        medication_columns = {
            str(row[1])
            for row in connection.execute(
                "PRAGMA table_info(v0817_medications)"
            ).fetchall()
        }
        additions = {
            "active_ingredient": "TEXT",
            "concentration": "TEXT",
            "dosage_form": "TEXT",
            "is_archived": (
                "INTEGER NOT NULL DEFAULT 0 CHECK (is_archived IN (0,1))"
            ),
            "archived_at": "TEXT",
        }
        for name, definition in additions.items():
            if medication_columns and name not in medication_columns:
                connection.execute(
                    f"ALTER TABLE v0817_medications ADD COLUMN {name} {definition}"
                )
        if medication_columns:
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_v0913_medications_archived "
                "ON v0817_medications(is_archived, normalized_name, species_id)"
            )


def _infer_concentration(name: str) -> str:
    match = re.search(
        r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(mg|mcg|µg|g)\s*/\s*"
        r"(ml|g|tablette|tablet)",
        name,
        flags=re.IGNORECASE,
    )
    if not match:
        return ""
    value, numerator, denominator = match.groups()
    return f"{value.replace(',', '.')} {numerator}/{denominator}"


def _infer_dosage_form(name: str) -> str:
    candidates = (
        ("paste", "Paste"),
        ("injektionslösung", "Injektionslösung"),
        ("orale suspension", "Orale Suspension"),
        ("suspension", "Suspension"),
        ("augentropfen", "Augentropfen"),
        ("augensalbe", "Augensalbe"),
        ("spot-on", "Spot-on"),
        ("kautabletten", "Kautabletten"),
        ("tabletten", "Tabletten"),
    )
    lowered = name.casefold()
    for needle, label in candidates:
        if needle in lowered:
            return label
    return ""


def _catalog_products() -> list[dict[str, Any]]:
    catalog_path = Path(__file__).parent / "catalogs" / "medicines_ch.json"
    with catalog_path.open(encoding="utf-8") as file:
        document = json.load(file)

    raw_items = [dict(item) for item in document.get("items", [])]
    known = {str(item.get("id") or "") for item in raw_items}
    raw_items.extend(
        dict(item)
        for item in _EXTRA_CATALOG_PRODUCTS
        if str(item["id"]) not in known
    )

    products: list[dict[str, Any]] = []
    for raw in raw_items:
        product_id = str(raw.get("id") or "")
        enrichment = _CATALOG_ENRICHMENT.get(product_id, {})
        name = str(
            raw.get("name")
            or raw.get("name_de")
            or raw.get("id")
            or ""
        )
        ingredients = [
            str(value) for value in (raw.get("active_ingredients") or [])
        ]
        concentration = str(
            raw.get("concentration")
            or enrichment.get("concentration")
            or _infer_concentration(name)
            or ""
        )
        dosage_form = str(
            raw.get("dosage_form")
            or enrichment.get("dosage_form")
            or _infer_dosage_form(name)
            or ""
        )
        products.append(
            {
                "id": product_id,
                "name": name,
                "active_ingredient": ", ".join(ingredients),
                "active_ingredients": ingredients,
                "concentration": concentration,
                "dosage_form": dosage_form,
                "target_species": [
                    str(value) for value in (raw.get("target_species") or [])
                ],
                "aliases": [str(value) for value in (raw.get("aliases") or [])],
                "source": "catalog",
            }
        )
    return sorted(products, key=lambda item: item["name"].casefold())


def medication_snapshot_for_name(
    connection: sqlite3.Connection,
    product_name: str,
) -> dict[str, Any]:
    clean_name = re.sub(r"\s+", " ", str(product_name or "").strip())
    needle = _normalise(clean_name)
    columns = {
        str(row[1])
        for row in connection.execute(
            "PRAGMA table_info(v0817_medications)"
        ).fetchall()
    }
    if columns and {
        "active_ingredient",
        "concentration",
        "dosage_form",
    } <= columns:
        row = connection.execute(
            """
            SELECT id,name,active_ingredient,concentration,dosage_form
            FROM v0817_medications
            WHERE normalized_name=?
            ORDER BY CASE WHEN species_id='' THEN 0 ELSE 1 END,id
            LIMIT 1
            """,
            (needle,),
        ).fetchone()
        if row is not None:
            return {
                "source": "manual",
                "medication_id": int(row["id"]),
                "product_name": str(row["name"]),
                "active_ingredient": str(row["active_ingredient"] or ""),
                "concentration": str(row["concentration"] or ""),
                "dosage_form": str(row["dosage_form"] or ""),
            }

    for product in _catalog_products():
        candidates = [product["name"], *(product.get("aliases") or [])]
        if any(_normalise(value) == needle for value in candidates):
            return {
                "source": "catalog",
                "catalog_id": product["id"],
                "product_name": product["name"],
                "active_ingredient": product["active_ingredient"],
                "concentration": product["concentration"],
                "dosage_form": product["dosage_form"],
            }

    return {
        "source": "free_text",
        "product_name": clean_name,
        "active_ingredient": "",
        "concentration": "",
        "dosage_form": "",
    }


def _medications_sync(path: Path) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        columns = {
            str(row[1])
            for row in connection.execute(
                "PRAGMA table_info(v0817_medications)"
            ).fetchall()
        }
        if not columns:
            return []
        rows = connection.execute(
            """
            SELECT id,name,species_id,default_unit,default_route,
                   active_ingredient,concentration,dosage_form,
                   is_archived,archived_at
            FROM v0817_medications
            ORDER BY is_archived,name COLLATE NOCASE,species_id,id
            """
        ).fetchall()
    return [
        {
            "id": int(row["id"]),
            "name": str(row["name"]),
            "species_id": str(row["species_id"] or ""),
            "default_unit": str(row["default_unit"] or "dose"),
            "default_route": str(row["default_route"] or ""),
            "active_ingredient": str(row["active_ingredient"] or ""),
            "concentration": str(row["concentration"] or ""),
            "dosage_form": str(row["dosage_form"] or ""),
            "is_archived": bool(row["is_archived"]),
            "archived_at": str(row["archived_at"] or ""),
            "source": "manual",
        }
        for row in rows
    ]


def _deleted_events_sync(path: Path) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT e.id,e.animal_id,e.event_type,e.occurred_at,e.title,e.notes,
                   e.value,e.unit,e.correction_of_event_id,e.data_json,e.task_id,
                   e.task_occurrence_id,e.created_at,e.deleted_at,
                   a.name AS animal_name
            FROM events AS e
            LEFT JOIN animals AS a ON a.id=e.animal_id
            WHERE e.is_deleted=1
            ORDER BY e.occurred_at DESC,e.created_at DESC,e.id DESC
            LIMIT 1000
            """
        ).fetchall()

    result: list[dict[str, Any]] = []
    for row in rows:
        try:
            data = json.loads(str(row["data_json"] or "{}"))
        except json.JSONDecodeError:
            data = {}
        result.append(
            {
                "id": str(row["id"]),
                "animal_id": str(row["animal_id"]),
                "animal_name": str(row["animal_name"] or row["animal_id"]),
                "event_type": str(row["event_type"]),
                "occurred_at": str(row["occurred_at"]),
                "title": str(row["title"]),
                "notes": row["notes"],
                "value": row["value"],
                "unit": row["unit"],
                "correction_of_event_id": row["correction_of_event_id"],
                "data": data,
                "task_id": row["task_id"],
                "task_occurrence_id": row["task_occurrence_id"],
                "created_at": str(row["created_at"]),
                "is_deleted": True,
                "deleted_at": str(row["deleted_at"] or ""),
            }
        )
    return result


def _state_sync(path: Path) -> dict[str, Any]:
    return {
        "medications": _medications_sync(path),
        "catalog_products": _catalog_products(),
        "deleted_events": _deleted_events_sync(path),
    }


def _recompute_status_sync(
    connection: sqlite3.Connection,
    animal_id: str,
) -> None:
    rows = connection.execute(
        """
        SELECT occurred_at,created_at,data_json
        FROM events
        WHERE animal_id=?
          AND event_type='status_change'
          AND is_deleted=0
        ORDER BY occurred_at DESC,created_at DESC,id DESC
        """,
        (animal_id,),
    ).fetchall()

    status: str | None = None
    changed_at: str | None = None
    for row in rows:
        try:
            data = json.loads(str(row["data_json"] or "{}"))
        except json.JSONDecodeError:
            continue
        candidate = str(data.get("new_status") or "")
        if candidate in ANIMAL_STATUSES:
            status = candidate
            changed_at = str(row["occurred_at"])
            break

    if status is None:
        first = connection.execute(
            """
            SELECT data_json
            FROM events
            WHERE animal_id=? AND event_type='status_change'
            ORDER BY occurred_at ASC,created_at ASC,id ASC
            LIMIT 1
            """,
            (animal_id,),
        ).fetchone()
        if first is not None:
            try:
                candidate = str(
                    json.loads(str(first["data_json"] or "{}")).get(
                        "previous_status"
                    )
                    or ""
                )
                if candidate in ANIMAL_STATUSES:
                    status = candidate
            except json.JSONDecodeError:
                pass
        animal = connection.execute(
            "SELECT created_at FROM animals WHERE id=?",
            (animal_id,),
        ).fetchone()
        status = status or "active"
        changed_at = (
            str(animal["created_at"])
            if animal is not None
            else datetime.now(UTC).isoformat()
        )

    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    connection.execute(
        """
        UPDATE animals
        SET status=?,status_changed_at=?,updated_at=?
        WHERE id=?
        """,
        (status, changed_at, now, animal_id),
    )


def _delete_event_sync(path: Path, event_id: str) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT id,animal_id,event_type,is_deleted FROM events WHERE id=?",
            (event_id,),
        ).fetchone()
        if row is None:
            raise KeyError(event_id)
        if not bool(row["is_deleted"]):
            connection.execute(
                "UPDATE events SET is_deleted=1,deleted_at=? WHERE id=?",
                (now, event_id),
            )
            if str(row["event_type"]) == "status_change":
                _recompute_status_sync(connection, str(row["animal_id"]))
    return {"event_id": event_id, "deleted_at": now}


def _save_medication_sync(
    path: Path,
    medication_id: int | None,
    name: str,
    species_id: str | None,
    default_unit: str,
    default_route: str | None,
    active_ingredient: str | None,
    concentration: str | None,
    dosage_form: str | None,
) -> dict[str, Any]:
    clean_name = _required_text(name)
    species = _normalise(species_id or "")
    ingredient = _optional_text(active_ingredient)
    strength = _optional_text(concentration)
    form = _optional_text(dosage_form)
    route = _optional_text(default_route)
    now = datetime.now(UTC).replace(microsecond=0).isoformat()

    with _connect(path) as connection:
        if medication_id is not None:
            cursor = connection.execute(
                """
                UPDATE v0817_medications
                SET name=?,normalized_name=?,species_id=?,default_unit=?,
                    default_route=?,active_ingredient=?,concentration=?,
                    dosage_form=?,updated_at=?
                WHERE id=?
                """,
                (
                    clean_name,
                    _normalise(clean_name),
                    species,
                    default_unit,
                    route,
                    ingredient,
                    strength,
                    form,
                    now,
                    medication_id,
                ),
            )
            if cursor.rowcount == 0:
                raise KeyError(medication_id)
            target_id = medication_id
        else:
            connection.execute(
                """
                INSERT INTO v0817_medications(
                    name,normalized_name,species_id,default_unit,default_route,
                    active_ingredient,concentration,dosage_form,is_archived,
                    archived_at,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,0,NULL,?,?)
                ON CONFLICT(normalized_name,species_id) DO UPDATE SET
                    name=excluded.name,
                    default_unit=excluded.default_unit,
                    default_route=excluded.default_route,
                    active_ingredient=excluded.active_ingredient,
                    concentration=excluded.concentration,
                    dosage_form=excluded.dosage_form,
                    is_archived=0,
                    archived_at=NULL,
                    updated_at=excluded.updated_at
                """,
                (
                    clean_name,
                    _normalise(clean_name),
                    species,
                    default_unit,
                    route,
                    ingredient,
                    strength,
                    form,
                    now,
                    now,
                ),
            )
            row = connection.execute(
                """
                SELECT id
                FROM v0817_medications
                WHERE normalized_name=? AND species_id=?
                """,
                (_normalise(clean_name), species),
            ).fetchone()
            if row is None:
                raise RuntimeError("Saved medication could not be loaded")
            target_id = int(row["id"])

    return next(
        item for item in _medications_sync(path) if item["id"] == target_id
    )


def _archive_medication_sync(
    path: Path,
    medication_id: int,
    archived: bool,
) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with _connect(path) as connection:
        cursor = connection.execute(
            """
            UPDATE v0817_medications
            SET is_archived=?,archived_at=?,updated_at=?
            WHERE id=?
            """,
            (1 if archived else 0, now if archived else None, now, medication_id),
        )
        if cursor.rowcount == 0:
            raise KeyError(medication_id)
    return next(
        item for item in _medications_sync(path) if item["id"] == medication_id
    )


async def async_initialize_v0913_features(hass: HomeAssistant) -> None:
    await hass.async_add_executor_job(_initialise_sync, _database_path(hass))


def async_setup_v0913_features(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command({vol.Required("type"): _STATE_COMMAND})
    @websocket_api.async_response
    async def websocket_state(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _state_sync,
                _database_path(hass),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0913_state_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _DELETE_EVENT_COMMAND,
            vol.Required("event_id"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_delete_event(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        runtime = _runtime_data(hass)
        try:
            result = await hass.async_add_executor_job(
                _delete_event_sync,
                _database_path(hass),
                msg["event_id"],
            )
            await runtime.coordinator.async_request_refresh()
        except KeyError:
            connection.send_error(
                msg["id"],
                "event_not_found",
                "Event not found",
            )
            return
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v0913_delete_failed", str(err))
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SAVE_MEDICATION_COMMAND,
            vol.Optional("medication_id"): vol.Coerce(int),
            vol.Required("name"): _required_text,
            vol.Optional("species_id"): _optional_text,
            vol.Required("default_unit"): vol.In(DOSE_UNITS),
            vol.Optional("default_route"): vol.Any(
                None,
                "",
                vol.In(ADMINISTRATION_ROUTES),
            ),
            vol.Optional("active_ingredient"): _optional_text,
            vol.Optional("concentration"): _optional_text,
            vol.Optional("dosage_form"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_save_medication(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _save_medication_sync,
                _database_path(hass),
                msg.get("medication_id"),
                msg["name"],
                msg.get("species_id"),
                msg["default_unit"],
                msg.get("default_route") or None,
                msg.get("active_ingredient"),
                msg.get("concentration"),
                msg.get("dosage_form"),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(
                msg["id"],
                "v0913_medication_save_failed",
                str(err),
            )
            return
        connection.send_result(msg["id"], result)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _ARCHIVE_MEDICATION_COMMAND,
            vol.Required("medication_id"): vol.Coerce(int),
            vol.Required("archived"): bool,
        }
    )
    @websocket_api.async_response
    async def websocket_archive_medication(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            result = await hass.async_add_executor_job(
                _archive_medication_sync,
                _database_path(hass),
                int(msg["medication_id"]),
                bool(msg["archived"]),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(
                msg["id"],
                "v0913_medication_archive_failed",
                str(err),
            )
            return
        connection.send_result(msg["id"], result)

    websocket_api.async_register_command(hass, websocket_state)
    websocket_api.async_register_command(hass, websocket_delete_event)
    websocket_api.async_register_command(hass, websocket_save_medication)
    websocket_api.async_register_command(hass, websocket_archive_medication)
