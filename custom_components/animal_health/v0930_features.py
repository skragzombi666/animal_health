from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from . import v0913_features, v0928_data, v0928_features

DATABASE_MEDICATION_STARTER = "animal_health_medications_ch"
DATABASE_HISTORY = "local_history_suggestions"
_BASE_INITIALIZE = v0928_data.initialize_product_databases_sync
_BASE_STATE = v0928_data.state_sync
_PATCHED = False
_KINDS = {"medication", "vaccination", "deworming", "supplement", "feed"}
_KIND_ALIASES = {
    "medicine": "medication",
    "product": "medication",
    "vaccine": "vaccination",
    "worming": "deworming",
    "dewormer": "deworming",
    "food": "feed",
}
_DATABASES = (
    (
        v0928_data.DATABASE_SWISSMEDIC,
        "Swissmedic – Tierarzneimittel",
        "Offizielle Schweizer Quelle zugelassener Tierarzneimittel. Die lokale Liste wird automatisch aktualisiert.",
        ["medication", "vaccination", "deworming"],
        "Swissmedic",
        "official",
        "laufend",
        "",
        100,
        "automatic",
        "Quelle und Fachinformationen: Swissmedic.",
        "https://www.swissmedic.ch/swissmedic/de/home/services/listen_neu.html",
        1,
        1,
        "",
    ),
    (
        v0928_data.DATABASE_DEWORMERS,
        "Swissmedic – Entwurmungsmittel",
        "Gefilterte Ansicht der Swissmedic-Tierarzneimittel mit als Entwurmungsmittel klassifizierten Produkten.",
        ["deworming"],
        "Swissmedic",
        "official_view",
        "laufend",
        "",
        100,
        "automatic",
        "Gefilterte lokale Ansicht; Quelldaten bleiben bei Swissmedic.",
        "https://www.swissmedic.ch/swissmedic/de/home/services/listen_neu.html",
        1,
        1,
        v0928_data.DATABASE_SWISSMEDIC,
    ),
    (
        DATABASE_MEDICATION_STARTER,
        "Animal Health – Medikamenten-Starterkatalog Schweiz",
        "Offline verfügbare Medikamenten-Grundliste. Sie ergänzt Swissmedic und bewahrt die bisherige Produktauswahl.",
        ["medication", "deworming"],
        "Animal Health / Swissmedic-Referenzen",
        "bundled",
        "2026.09",
        "2026-09-01",
        90,
        "bundled",
        "Dokumentationskatalog, keine Therapieempfehlung. Zulassung und Fachinformation prüfen.",
        "https://www.swissmedic.ch/swissmedic/de/home/services/listen_neu.html",
        1,
        1,
        "",
    ),
    (
        v0928_data.DATABASE_VACCINES,
        "Animal Health – Impfstoffe Schweiz",
        "Mitgelieferter Schweizer Impfstoff-Starterkatalog für Hunde, Katzen, Geflügel, Rinder, Schafe und weitere Tierarten.",
        ["vaccination"],
        "Animal Health / Swissmedic-Referenzen",
        "curated",
        "2026.09",
        "2026-09-01",
        85,
        "bundled",
        "Dokumentationskatalog. Verfügbarkeit, Zulassung und Fachinformation prüfen.",
        "https://www.swissmedic.ch/swissmedic/de/home/services/listen_neu.html",
        1,
        1,
        "",
    ),
    (
        v0928_data.DATABASE_SUPPLEMENTS,
        "Animal Health – Ergänzungspräparate & Mineralfutter",
        "Ergänzungspräparate, Darmflora-Produkte, Vitamin-/Mineralprodukte und Grit für Geflügel.",
        ["supplement"],
        "UFA AG / ufamed AG / Anima-Strath / Vetark",
        "curated",
        "2026.09",
        "2026-09-01",
        80,
        "bundled",
        "Herstellerangaben dienen der Dokumentation; aktuelle Deklaration prüfen.",
        "",
        1,
        1,
        "",
    ),
    (
        v0928_data.DATABASE_FEEDS,
        "UFA – Geflügelfuttermittel",
        "UFA-Geflügelfutter für Küken, Junghennen, Legehennen, Mastpoulets, Wassergeflügel, Wachteln und Truten.",
        ["feed"],
        "UFA AG",
        "manufacturer",
        "2026.09",
        "2026-09-01",
        80,
        "bundled",
        "Öffentliche Herstellerinformationen; aktuelle Produktetikette prüfen.",
        "https://www.ufa.ch",
        1,
        1,
        "",
    ),
    (
        DATABASE_HISTORY,
        "Lokale Produktwerte aus Verlauf & Aufgaben",
        "Produktnamen aus Chronik, Aufgaben, Gruppenaktionen und Behandlungsdaten. Damit sind produktbezogene Vorschläge im Datenbankmanagement sichtbar.",
        ["medication", "vaccination", "deworming", "supplement", "feed"],
        "Lokale Animal-Health-Daten",
        "local_history",
        "dynamisch",
        "",
        45,
        "automatic",
        "Nur lokal aus den eigenen Animal-Health-Daten abgeleitet.",
        "",
        1,
        1,
        "",
    ),
    (
        v0928_data.DATABASE_USER,
        "Meine Produktdatenbank",
        "Eigene Produkte und bearbeitbare Kopien aus anderen Datenbanken.",
        ["medication", "vaccination", "deworming", "supplement", "feed"],
        "Benutzerdefiniert",
        "user",
        "lokal",
        "",
        120,
        "manual",
        "Eigene lokale Daten.",
        "",
        0,
        0,
        "",
    ),
)


def _kind(value: Any, fallback: str | None = None) -> str | None:
    candidate = _KIND_ALIASES.get(v0928_data.norm(value), v0928_data.norm(value))
    if candidate in _KINDS:
        return candidate
    return fallback if fallback in _KINDS else None


def _upsert_databases(connection: sqlite3.Connection) -> None:
    stamp = v0928_data.now()
    for item in _DATABASES:
        connection.execute(
            """
            INSERT INTO v0928_product_databases(
                database_id,name,description,product_types_json,source_name,
                source_type,version,data_as_of,priority,update_mode,
                license_notice,source_url,enabled,is_system,
                supports_local_overrides,view_of,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,1,?,?,?,?,?)
            ON CONFLICT(database_id) DO UPDATE SET
                name=excluded.name,description=excluded.description,
                product_types_json=excluded.product_types_json,
                source_name=excluded.source_name,source_type=excluded.source_type,
                version=excluded.version,
                data_as_of=CASE WHEN excluded.data_as_of=''
                    THEN v0928_product_databases.data_as_of
                    ELSE excluded.data_as_of END,
                priority=excluded.priority,update_mode=excluded.update_mode,
                license_notice=excluded.license_notice,
                source_url=excluded.source_url,is_system=excluded.is_system,
                supports_local_overrides=excluded.supports_local_overrides,
                view_of=excluded.view_of,updated_at=excluded.updated_at
            """,
            (
                item[0],
                item[1],
                item[2],
                json.dumps(item[3], ensure_ascii=False),
                *item[4:12],
                item[12],
                item[13],
                item[14],
                stamp,
                stamp,
            ),
        )


def _insert_product(
    connection: sqlite3.Connection,
    *,
    product_id: str,
    kind: str,
    source: str,
    source_id: str,
    name: str,
    species: list[str],
    metadata: dict[str, Any],
    database_id: str,
    custom: bool,
    update_existing: bool,
) -> None:
    stamp = v0928_data.now()
    conflict = (
        """ON CONFLICT(id) DO UPDATE SET
            kind=excluded.kind,source=excluded.source,source_id=excluded.source_id,
            name=excluded.name,normalized_name=excluded.normalized_name,
            species_json=excluded.species_json,metadata_json=excluded.metadata_json,
            database_id=excluded.database_id,updated_at=excluded.updated_at"""
        if update_existing
        else "ON CONFLICT(id) DO NOTHING"
    )
    connection.execute(
        f"""
        INSERT INTO v0927_products(
            id,kind,source,source_id,name,normalized_name,species_json,
            metadata_json,override_json,is_hidden,is_custom,created_at,
            updated_at,database_id
        ) VALUES(?,?,?,?,?,?,?,?,?,0,?,?,?,?) {conflict}
        """,
        (
            product_id,
            kind,
            source,
            source_id,
            name,
            v0928_data.norm(name),
            json.dumps(species, ensure_ascii=False),
            json.dumps(metadata, ensure_ascii=False, sort_keys=True),
            "{}",
            int(custom),
            stamp,
            stamp,
            database_id,
        ),
    )


def _seed_medications(connection: sqlite3.Connection) -> None:
    if not v0928_data.table(connection, "v0927_products"):
        return
    try:
        products = v0913_features._catalog_products()  # noqa: SLF001
    except Exception:  # noqa: BLE001
        return
    for raw in products:
        source_id = v0928_data.text(raw.get("id"))
        name = v0928_data.text(raw.get("name"))
        if not source_id or not name:
            continue
        ingredients = [
            v0928_data.text(value)
            for value in raw.get("active_ingredients", [])
            if v0928_data.text(value)
        ]
        _insert_product(
            connection,
            product_id=f"{DATABASE_MEDICATION_STARTER}:{source_id}",
            kind="medication",
            source=DATABASE_MEDICATION_STARTER,
            source_id=source_id,
            name=name,
            species=list(raw.get("target_species") or []),
            metadata={
                "active_ingredient": v0928_data.text(raw.get("active_ingredient"))
                or ", ".join(ingredients),
                "active_ingredients": ingredients,
                "concentration": v0928_data.text(raw.get("concentration")),
                "dosage_form": v0928_data.text(raw.get("dosage_form")),
                "aliases": list(raw.get("aliases") or []),
                "manufacturer": v0928_data.text(raw.get("manufacturer")),
                "source_name": "Animal Health / Swissmedic-Referenzen",
                "source_as_of": "2026-09-01",
            },
            database_id=DATABASE_MEDICATION_STARTER,
            custom=False,
            update_existing=True,
        )


def _reconcile_legacy(connection: sqlite3.Connection) -> None:
    if not all(
        v0928_data.table(connection, name)
        for name in ("v0817_medications", "v0927_products")
    ):
        return
    columns = v0928_data.cols(connection, "v0817_medications")
    if not {"id", "name"} <= columns:
        return
    category_join = v0928_data.table(connection, "v0917_product_categories")
    rows = connection.execute(
        """
        SELECT medication.*,COALESCE(category.category,'medication') AS product_category
        FROM v0817_medications AS medication
        LEFT JOIN v0917_product_categories AS category
          ON category.medication_id=medication.id
        ORDER BY medication.id
        """
        if category_join
        else "SELECT medication.*,'medication' AS product_category FROM v0817_medications AS medication ORDER BY medication.id"
    ).fetchall()
    for row in rows:
        name = v0928_data.text(row["name"])
        if not name:
            continue
        species = (
            [v0928_data.text(row["species_id"])]
            if "species_id" in columns and v0928_data.text(row["species_id"])
            else []
        )
        _insert_product(
            connection,
            product_id=f"legacy-medication:{row['id']}",
            kind="medication",
            source="legacy_manual",
            source_id=f"legacy-medication:{row['id']}",
            name=name,
            species=species,
            metadata={
                "active_ingredient": v0928_data.text(row["active_ingredient"])
                if "active_ingredient" in columns
                else "",
                "concentration": v0928_data.text(row["concentration"])
                if "concentration" in columns
                else "",
                "dosage_form": v0928_data.text(row["dosage_form"])
                if "dosage_form" in columns
                else "",
                "default_unit": v0928_data.text(row["default_unit"])
                if "default_unit" in columns
                else "dose",
                "default_route": v0928_data.text(row["default_route"])
                if "default_route" in columns
                else "",
                "product_category": v0928_data.text(row["product_category"])
                or "medication",
                "source_name": "Benutzerdefiniert",
            },
            database_id=v0928_data.DATABASE_USER,
            custom=True,
            update_existing=False,
        )


def _walk_products(
    value: Any,
    fallback: str | None = None,
    snapshot: bool = False,
) -> list[tuple[str, str]]:
    if isinstance(value, list):
        return [
            pair
            for item in value
            for pair in _walk_products(item, fallback, snapshot)
        ]
    if not isinstance(value, dict):
        return []
    explicit = (
        _kind(value.get("gabe_type"))
        or _kind(value.get("product_type"))
        or _kind(value.get("component_type"))
        or _kind(value.get("task_kind"))
        or _kind(value.get("type"))
    )
    current = explicit or fallback
    found: list[tuple[str, str]] = []
    for field, field_kind in (
        ("vaccine_name", "vaccination"),
        ("planned_vaccine_name", "vaccination"),
        ("medication_name", current or "medication"),
        ("planned_medication_name", current or "medication"),
        ("product_name", current or "medication"),
        ("planned_product_name", current or "medication"),
    ):
        name = v0928_data.text(value.get(field))
        kind = _kind(field_kind)
        if name and kind:
            found.append((kind, name))
    if snapshot and current:
        name = v0928_data.text(
            value.get("name") or value.get("official_product_name")
        )
        if name:
            found.append((current, name))
    if explicit:
        name = v0928_data.text(value.get("name"))
        if name:
            found.append((explicit, name))
    for key, child in value.items():
        child_snapshot = key in {
            "medication_snapshot",
            "vaccine_snapshot",
            "product_snapshot",
            "gabe_snapshot",
            "catalog",
        }
        child_kind = "vaccination" if key == "vaccine_snapshot" else current
        if key == "medication_snapshot":
            child_kind = current or "medication"
        found.extend(_walk_products(child, child_kind, child_snapshot))
    return found


def _history_products(connection: sqlite3.Connection) -> dict[tuple[str, str, str], dict[str, Any]]:
    products: dict[tuple[str, str, str], dict[str, Any]] = {}

    def add(
        payload: Any,
        species: Any,
        used_at: Any,
        fallback: str | None,
        source: str,
    ) -> None:
        decoded = v0928_data.loads(payload, {})
        if not isinstance(decoded, (dict, list)):
            return
        species_text = v0928_data.text(species)
        stamp = v0928_data.text(used_at)
        unique = {
            (kind, v0928_data.norm(name), name)
            for kind, name in _walk_products(decoded, fallback)
            if kind in _KINDS and v0928_data.norm(name)
        }
        for kind, normalized, name in unique:
            key = (kind, species_text.casefold(), normalized)
            item = products.setdefault(
                key,
                {
                    "kind": kind,
                    "name": name,
                    "species": species_text,
                    "count": 0,
                    "last_used": "",
                    "sources": set(),
                },
            )
            item["count"] += 1
            item["sources"].add(source)
            if stamp > item["last_used"]:
                item["last_used"] = stamp
                item["name"] = name

    if v0928_data.table(connection, "events"):
        has_animals = v0928_data.table(connection, "animals")
        join = (
            "LEFT JOIN animals AS animal ON animal.id=event.animal_id"
            if has_animals
            else ""
        )
        species = "animal.species" if has_animals else "''"
        for row in connection.execute(
            f"SELECT event.data_json,event.occurred_at,event.event_type,{species} AS species FROM events AS event {join}"
        ):
            add(
                row["data_json"],
                row["species"],
                row["occurred_at"],
                _kind(row["event_type"]),
                "chronik",
            )
    if all(
        v0928_data.table(connection, name)
        for name in ("task_record_configs", "tasks")
    ):
        has_animals = v0928_data.table(connection, "animals")
        join = (
            "LEFT JOIN animals AS animal ON animal.id=task.animal_id"
            if has_animals
            else ""
        )
        species = "animal.species" if has_animals else "''"
        for row in connection.execute(
            f"SELECT config.template_json,config.task_kind,task.updated_at,{species} AS species FROM task_record_configs AS config JOIN tasks AS task ON task.id=config.task_id {join}"
        ):
            add(
                row["template_json"],
                row["species"],
                row["updated_at"],
                _kind(row["task_kind"]),
                "aufgabe",
            )
    if v0928_data.table(connection, "group_events"):
        has_groups = v0928_data.table(connection, "animal_groups")
        join = (
            "LEFT JOIN animal_groups AS animal_group ON animal_group.id=event.group_id"
            if has_groups
            else ""
        )
        species = "animal_group.species" if has_groups else "''"
        for row in connection.execute(
            f"SELECT event.data_json,event.occurred_at,event.event_type,{species} AS species FROM group_events AS event {join}"
        ):
            add(
                row["data_json"],
                row["species"],
                row["occurred_at"],
                _kind(row["event_type"]),
                "gruppenchronik",
            )
    if all(
        v0928_data.table(connection, name)
        for name in ("group_task_configs", "tasks", "task_group_targets")
    ):
        has_groups = v0928_data.table(connection, "animal_groups")
        join = (
            "LEFT JOIN animal_groups AS animal_group ON animal_group.id=target.group_id"
            if has_groups
            else ""
        )
        species = "animal_group.species" if has_groups else "''"
        for row in connection.execute(
            f"SELECT DISTINCT config.template_json,config.task_kind,task.updated_at,{species} AS species FROM group_task_configs AS config JOIN tasks AS task ON task.id=config.task_id JOIN task_group_targets AS target ON target.task_id=task.id {join}"
        ):
            add(
                row["template_json"],
                row["species"],
                row["updated_at"],
                _kind(row["task_kind"]),
                "gruppenaufgabe",
            )
    return products


def _seed_history(connection: sqlite3.Connection) -> None:
    if not v0928_data.table(connection, "v0927_products"):
        return
    stamp = v0928_data.now()
    for item in _history_products(connection).values():
        digest = hashlib.sha256(
            f"{item['kind']}|{v0928_data.norm(item['species'])}|{v0928_data.norm(item['name'])}".encode()
        ).hexdigest()[:20]
        product_id = f"history:{item['kind']}:{digest}"
        _insert_product(
            connection,
            product_id=product_id,
            kind=item["kind"],
            source=DATABASE_HISTORY,
            source_id=product_id,
            name=item["name"],
            species=[item["species"]] if item["species"] else [],
            metadata={
                "history_count": item["count"],
                "last_used": item["last_used"],
                "derived_from": sorted(item["sources"]),
                "source_name": "Lokale Animal-Health-Daten",
                "source_as_of": stamp[:10],
            },
            database_id=DATABASE_HISTORY,
            custom=False,
            update_existing=True,
        )


def _assign_unassigned(connection: sqlite3.Connection) -> None:
    if not v0928_data.table(connection, "v0927_products"):
        return
    connection.execute(
        """
        UPDATE v0927_products SET database_id=CASE
            WHEN source=? THEN ?
            WHEN source=? THEN ?
            WHEN source=? THEN ?
            WHEN kind='vaccination' THEN ?
            WHEN kind='supplement' AND is_custom=0 THEN ?
            WHEN kind='feed' AND is_custom=0 THEN ?
            ELSE ?
        END
        WHERE database_id IS NULL OR TRIM(database_id)=''
        """,
        (
            DATABASE_MEDICATION_STARTER,
            DATABASE_MEDICATION_STARTER,
            DATABASE_HISTORY,
            DATABASE_HISTORY,
            v0928_data.DATABASE_VACCINES,
            v0928_data.DATABASE_VACCINES,
            v0928_data.DATABASE_VACCINES,
            v0928_data.DATABASE_SUPPLEMENTS,
            v0928_data.DATABASE_FEEDS,
            v0928_data.DATABASE_USER,
        ),
    )


def _reconcile(path: Path) -> None:
    with v0928_data.connect(path) as connection:
        _upsert_databases(connection)
        _seed_medications(connection)
        _reconcile_legacy(connection)
        _seed_history(connection)
        _assign_unassigned(connection)
        connection.execute(
            """
            INSERT INTO v0928_meta(key,value,updated_at)
            VALUES('v0930_product_database_reconciled','1',?)
            ON CONFLICT(key) DO UPDATE SET
                value=excluded.value,updated_at=excluded.updated_at
            """,
            (v0928_data.now(),),
        )


def initialize_product_databases_v0930(path: Path) -> None:
    _BASE_INITIALIZE(path)
    _reconcile(path)


def state_sync_v0930(path: Path) -> dict[str, Any]:
    initialize_product_databases_v0930(path)
    return _BASE_STATE(path)


def apply_v0930_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True
    v0928_data.initialize_product_databases_sync = initialize_product_databases_v0930
    v0928_data.state_sync = state_sync_v0930
    v0928_features.initialize_product_databases_sync = initialize_product_databases_v0930
    v0928_features.state_sync = state_sync_v0930
