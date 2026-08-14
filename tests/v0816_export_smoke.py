from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sqlite3
import struct
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
EXPORT_PATH = ROOT / "custom_components" / "animal_health" / "v0816_exports.py"
SPEC = importlib.util.spec_from_file_location("animal_health_v0816_exports", EXPORT_PATH)
assert SPEC and SPEC.loader
EXPORTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORTS)


def tiny_png() -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0)
    raw = b"\x00\xff\x80\x20\x20\x80\xff\x00\x20\x20\x80\xff\x80\x20\x20\xff\x80\x20"
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary_dir:
        root = Path(temporary_dir)
        database = root / "animal_health.db"
        attachment_root = root / ".storage" / "animal_health" / "attachments"
        attachment_root.mkdir(parents=True)
        profile_bytes = tiny_png()
        (attachment_root / "AT-PROFILE.png").write_bytes(profile_bytes)

        with sqlite3.connect(database) as connection:
            connection.executescript(
                """
                CREATE TABLE animals (
                    id TEXT PRIMARY KEY, name TEXT, species TEXT, breed TEXT,
                    color TEXT, sex TEXT, birth_date TEXT, arrival_date TEXT,
                    status TEXT, status_changed_at TEXT, is_archived INTEGER,
                    archived_at TEXT, created_at TEXT, updated_at TEXT
                );
                CREATE TABLE animal_groups (
                    id TEXT PRIMARY KEY, name TEXT, species TEXT,
                    description TEXT, created_at TEXT, updated_at TEXT
                );
                CREATE TABLE animal_group_memberships (
                    animal_id TEXT PRIMARY KEY, group_id TEXT, updated_at TEXT
                );
                CREATE TABLE attachments (
                    id TEXT PRIMARY KEY, animal_id TEXT, event_id TEXT,
                    filename TEXT, media_type TEXT, size_bytes INTEGER,
                    storage_name TEXT, title TEXT, created_at TEXT
                );
                CREATE TABLE animal_profiles (
                    animal_id TEXT PRIMARY KEY, image_attachment_id TEXT, updated_at TEXT
                );
                CREATE TABLE tasks (
                    id TEXT PRIMARY KEY, animal_id TEXT, title TEXT, description TEXT,
                    recurrence_type TEXT, recurrence_interval INTEGER, start_date TEXT,
                    end_date TEXT, due_time TEXT, is_active INTEGER,
                    created_at TEXT, updated_at TEXT
                );
                CREATE TABLE task_record_configs (
                    task_id TEXT PRIMARY KEY, task_kind TEXT, template_json TEXT,
                    created_at TEXT, updated_at TEXT
                );
                CREATE TABLE events (
                    id TEXT PRIMARY KEY, animal_id TEXT, event_type TEXT,
                    occurred_at TEXT, title TEXT, notes TEXT, value REAL,
                    unit TEXT, correction_of_event_id TEXT, data_json TEXT,
                    task_id TEXT, task_occurrence_id TEXT, created_at TEXT
                );
                """
            )
            connection.execute(
                "INSERT INTO animals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "AH-1", "Chlümmli", "Huhn", "Legehybride", "Hellbraun", "female",
                    None, None, "active", "2026-08-01T10:00:00+00:00", 0, None,
                    "2026-01-01T10:00:00+00:00", "2026-08-01T10:00:00+00:00",
                ),
            )
            connection.execute(
                "INSERT INTO animal_groups VALUES (?,?,?,?,?,?)",
                ("GR-1", "Tschiggies", "Huhn", "Legehennen", "2026-01-01", "2026-08-01"),
            )
            connection.execute(
                "INSERT INTO animal_group_memberships VALUES (?,?,?)",
                ("AH-1", "GR-1", "2026-08-01"),
            )
            connection.execute(
                "INSERT INTO attachments VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    "AT-PROFILE", "AH-1", None, "tierbild.png", "image/png",
                    len(profile_bytes), "AT-PROFILE.png", "Tierbild", "2026-08-01T10:00:00+00:00",
                ),
            )
            connection.execute(
                "INSERT INTO animal_profiles VALUES (?,?,?)",
                ("AH-1", "AT-PROFILE", "2026-08-01T10:00:00+00:00"),
            )
            connection.execute(
                "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "TK-1", "AH-1", "Doxycyclin", "Nach tierärztlicher Verordnung",
                    "daily", 1, "2026-08-10", None, "20:00", 1,
                    "2026-08-10T10:00:00+00:00", "2026-08-10T10:00:00+00:00",
                ),
            )
            connection.execute(
                "INSERT INTO task_record_configs VALUES (?,?,?,?,?)",
                (
                    "TK-1", "medication",
                    json.dumps({
                        "medication_name": "Doxycyclin 100 mg, Tabletten",
                        "dose": 1.0,
                        "dose_unit": "tablet",
                        "route": "oral",
                        "catalog_source": "custom",
                        "catalog_scope": "custom",
                    }),
                    "2026-08-10T10:00:00+00:00", "2026-08-10T10:00:00+00:00",
                ),
            )
            connection.execute(
                "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "EV-OLD", "AH-1", "weight", "2026-08-12T10:00:00+00:00",
                    "weight_measurement", "Alter falscher Wert", 1.20, "kg", None,
                    json.dumps({"measurement": "weight", "task_execution": {"technical": True}}),
                    None, None, "2026-08-12T10:00:00+00:00",
                ),
            )
            connection.execute(
                "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "EV-CORRECTED", "AH-1", "weight", "2026-08-13T10:00:00+00:00",
                    "weight_measurement", "Korrigierter Wert", 1.24, "kg", "EV-OLD",
                    json.dumps({"measurement": "weight", "timing_status": "early", "timing_deviation_minutes": -1440}),
                    None, None, "2026-08-13T10:00:00+00:00",
                ),
            )
            connection.execute(
                "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "EV-MED", "AH-1", "medication", "2026-08-14T08:00:00+00:00",
                    "Doxycyclin 100 mg, Tabletten", "Gut aufgenommen", 1.0, "tablet", None,
                    json.dumps({
                        "actual": {"medication_name": "Doxycyclin 100 mg, Tabletten", "dose": 1.0, "dose_unit": "tablet", "route": "oral"},
                        "planned": {"catalog_id": "technical-id"},
                        "task_execution": {"timing_status": "early", "timing_deviation_minutes": -1440},
                        "catalog_source": "custom",
                    }),
                    "TK-1", "OC-1", "2026-08-14T08:00:00+00:00",
                ),
            )
            connection.execute(
                "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "EV-STATUS", "AH-1", "status_change", "2026-08-14T09:00:00+00:00",
                    "status_changed", "Administrative Statusänderung", None, None, None,
                    json.dumps({"old_status": "active", "new_status": "active"}),
                    None, None, "2026-08-14T09:00:00+00:00",
                ),
            )

        data = EXPORTS._fetch_report_data(database, "AH-1")
        lines = EXPORTS._report_lines(data)
        text = "\n".join(item[2] for item in lines if item[0] not in {"space", "profile"})

        assert "Tierdaten" in text
        assert "Stammdaten" in text
        assert "Gruppendaten" in text
        assert "Aktuell laufende Therapien / Serien" in text
        assert "Gesundheitschronik" in text
        assert "Doxycyclin 100 mg, Tabletten" in text
        assert "Tschiggies" in text
        assert "Alter falscher Wert" not in text
        assert "Administrative Statusänderung" not in text
        assert "Timing Status" not in text
        assert "timing_status" not in text
        assert "timing_deviation_minutes" not in text
        assert "task_execution" not in text
        assert "catalog_source" not in text
        assert "catalog_scope" not in text
        assert "catalog_id" not in text
        assert "AT-PROFILE" not in text
        assert text.index("14.08.2026 08:00") < text.index("13.08.2026 10:00")

        image = EXPORTS._profile_image(database, data["profile"])
        assert image is not None
        assert image["width"] == 2 and image["height"] == 2

        filename, pdf = EXPORTS.animal_health_pdf_bytes(database, "AH-1")
        assert filename == "Gesundheitschronik_Chlümmli.pdf"
        assert pdf.startswith(b"%PDF-1.4") and pdf.endswith(b"%%EOF")
        assert b"/Subtype /Image" in pdf
        assert b"task_execution" not in pdf
        assert b"timing_status" not in pdf
        assert b"catalog_source" not in pdf

    print("Animal Health 0.8.16 health PDF validation passed")


if __name__ == "__main__":
    main()
