from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXPORTS_PATH = ROOT / "custom_components" / "animal_health" / "exports.py"
SPEC = importlib.util.spec_from_file_location("animal_health_exports", EXPORTS_PATH)
assert SPEC and SPEC.loader
EXPORTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORTS)


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary_dir:
        root = Path(temporary_dir)
        database = root / "animal_health.db"
        attachments = root / "attachments"
        attachments.mkdir()
        with sqlite3.connect(database) as connection:
            connection.executescript(
                """
                CREATE TABLE animals (
                    id TEXT PRIMARY KEY, name TEXT, species TEXT, breed TEXT,
                    color TEXT, sex TEXT, birth_date TEXT, arrival_date TEXT,
                    status TEXT, status_changed_at TEXT, is_archived INTEGER,
                    archived_at TEXT, created_at TEXT, updated_at TEXT
                );
                CREATE TABLE events (
                    id TEXT PRIMARY KEY, animal_id TEXT, event_type TEXT,
                    occurred_at TEXT, title TEXT, notes TEXT, value REAL,
                    unit TEXT, correction_of_event_id TEXT, data_json TEXT,
                    task_id TEXT, task_occurrence_id TEXT, created_at TEXT
                );
                CREATE TABLE animal_groups (
                    id TEXT PRIMARY KEY, name TEXT, species TEXT,
                    description TEXT, created_at TEXT, updated_at TEXT
                );
                CREATE TABLE animal_group_memberships (
                    animal_id TEXT PRIMARY KEY, group_id TEXT, updated_at TEXT
                );
                CREATE TABLE animal_group_lifecycle (
                    group_id TEXT PRIMARY KEY, archived_at TEXT NOT NULL
                );
                CREATE TABLE attachments (
                    id TEXT PRIMARY KEY, animal_id TEXT, event_id TEXT,
                    filename TEXT, media_type TEXT, size_bytes INTEGER,
                    storage_name TEXT, title TEXT, created_at TEXT
                );
                """
            )
            connection.execute(
                "INSERT INTO animals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "AH-TEST001", "Tina", "Hund", "Mischling", "braun", "female",
                    "2020-01-01", "2024-01-01", "active", "2026-07-29T10:00:00+00:00",
                    0, None, "2026-07-29T10:00:00+00:00", "2026-07-29T10:00:00+00:00",
                ),
            )
            connection.execute(
                "INSERT INTO animal_groups VALUES (?,?,?,?,?,?)",
                ("GR-TEST001", "Hunde", "Hund", None, "2026-07-29", "2026-07-29"),
            )
            connection.execute(
                "INSERT INTO animal_group_memberships VALUES (?,?,?)",
                ("AH-TEST001", "GR-TEST001", "2026-07-29"),
            )
            connection.execute(
                "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "EV-TEST001", "AH-TEST001", "weight", "2026-07-29T12:00:00+00:00",
                    "weight_measurement", "Kontrollmessung", 25.4, "kg", None,
                    json.dumps({"measurement": "weight"}), None, None,
                    "2026-07-29T12:00:00+00:00",
                ),
            )
            attachment_content = b"test document"
            (attachments / "AT-TEST001.pdf").write_bytes(attachment_content)
            connection.execute(
                "INSERT INTO attachments VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    "AT-TEST001", "AH-TEST001", "EV-TEST001", "befund.pdf",
                    "application/pdf", len(attachment_content), "AT-TEST001.pdf",
                    "Tierarztbefund", "2026-07-29T12:05:00+00:00",
                ),
            )

        exported = json.loads(EXPORTS.json_export_bytes(database))
        assert exported["format"] == "animal-health-portable-export"
        assert exported["tables"]["animals"][0]["name"] == "Tina"
        assert "animal_group_lifecycle" in exported["tables"]

        filename, pdf = EXPORTS.animal_health_pdf_bytes(database, "AH-TEST001")
        assert filename.endswith(".pdf")
        assert pdf.startswith(b"%PDF-1.4") and pdf.endswith(b"%%EOF")
        assert len(pdf) > 1000

        backup = EXPORTS.backup_zip_bytes(database, attachments)
        backup_path = root / "backup.zip"
        backup_path.write_bytes(backup)
        with zipfile.ZipFile(backup_path) as archive:
            names = set(archive.namelist())
            assert "database/animal_health.db" in names
            assert "animal_health.json" in names
            assert "attachments/AT-TEST001.pdf" in names

    print("Animal Health 0.7.3 export validation passed")


if __name__ == "__main__":
    main()
