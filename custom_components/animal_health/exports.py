from __future__ import annotations

import io
import json
import sqlite3
import tempfile
import textwrap
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def database_export(database_path: Path) -> dict[str, Any]:
    """Return every application table as portable JSON-compatible rows."""
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        tables = [
            str(row[0])
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        ]
        content = {
            table: [
                dict(row)
                for row in connection.execute(
                    f'SELECT * FROM "{table_name}"'
                ).fetchall()
            ]
            for table in tables
            for table_name in [table.replace('"', '""')]
        }
        schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    return {
        "format": "animal-health-portable-export",
        "format_version": 1,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "database_schema_version": schema_version,
        "tables": content,
    }


def json_export_bytes(database_path: Path) -> bytes:
    return json.dumps(
        database_export(database_path),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ).encode("utf-8")


def backup_zip_bytes(database_path: Path, attachment_root: Path) -> bytes:
    """Create a consistent SQLite backup plus portable JSON and attachments."""
    output = io.BytesIO()
    with tempfile.TemporaryDirectory(prefix="animal-health-") as temporary_dir:
        backup_path = Path(temporary_dir) / "animal_health.db"
        with sqlite3.connect(database_path) as source:
            with sqlite3.connect(backup_path) as target:
                source.backup(target)
        portable = json_export_bytes(backup_path)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(backup_path, "database/animal_health.db")
            archive.writestr("animal_health.json", portable)
            archive.writestr(
                "README.txt",
                (
                    "Animal Health backup\n"
                    "====================\n\n"
                    "database/animal_health.db: konsistente SQLite-Sicherung\n"
                    "animal_health.json: menschen- und maschinenlesbarer Datenexport\n"
                    "attachments/: lokal gespeicherte Originaldokumente\n"
                ).encode("utf-8"),
            )
            if attachment_root.is_dir():
                for path in sorted(attachment_root.iterdir()):
                    if path.is_file() and not path.name.endswith(".tmp"):
                        archive.write(path, f"attachments/{path.name}")
    return output.getvalue()


def _fetch_animal_report_data(
    database_path: Path,
    animal_id: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        animal = connection.execute(
            """
            SELECT
                a.*,
                g.id AS group_id,
                g.name AS group_name
            FROM animals AS a
            LEFT JOIN animal_group_memberships AS m ON m.animal_id = a.id
            LEFT JOIN animal_groups AS g ON g.id = m.group_id
            WHERE a.id = ?
            """,
            (animal_id,),
        ).fetchone()
        if animal is None:
            raise KeyError(animal_id)
        events = [
            dict(row)
            for row in connection.execute(
                """
                SELECT *
                FROM events
                WHERE animal_id = ?
                ORDER BY occurred_at, created_at, id
                """,
                (animal_id,),
            ).fetchall()
        ]
        attachments = [
            dict(row)
            for row in connection.execute(
                """
                SELECT id, animal_id, event_id, filename, media_type,
                       size_bytes, title, created_at
                FROM attachments
                WHERE animal_id = ?
                ORDER BY created_at, id
                """,
                (animal_id,),
            ).fetchall()
        ]
    return dict(animal), events, attachments


def _display(value: Any) -> str:
    if value is None or value == "":
        return "–"
    return str(value)


def _localized_value(field: str, value: Any) -> str:
    if value is None or value == "":
        return "–"
    mappings = {
        "sex": {"male": "Männlich", "female": "Weiblich", "other": "Andere"},
        "status": {
            "active": "Aktiv",
            "missing": "Vermisst",
            "sold": "Verkauft",
            "rehomed": "Weitervermittelt",
            "deceased": "Verstorben",
            "other_departure": "Anderer Abgang",
        },
        "severity": {
            "mild": "Leicht",
            "moderate": "Mittel",
            "severe": "Schwer",
            "critical": "Kritisch",
        },
    }
    return mappings.get(field, {}).get(str(value), str(value))


def _event_title(value: Any) -> str:
    title = _display(value)
    return {
        "weight_measurement": "Gewichtsmessung",
        "vaccination": "Impfung",
    }.get(title, title)


def _event_label(event_type: str) -> str:
    return {
        "observation": "Beobachtung",
        "symptom": "Symptom",
        "weight": "Gewicht",
        "diagnosis": "Diagnose",
        "treatment": "Behandlung",
        "medication": "Medikation",
        "vaccination": "Impfung",
        "veterinary_visit": "Tierarztbesuch",
        "care": "Pflege",
        "status_change": "Statusänderung",
        "other": "Sonstiger Eintrag",
    }.get(event_type, event_type.replace("_", " ").title())


def _format_timestamp(value: str | None) -> str:
    if not value:
        return "–"
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return value


def _report_lines(
    animal: dict[str, Any],
    events: list[dict[str, Any]],
    attachments: list[dict[str, Any]],
) -> list[tuple[str, int, str]]:
    lines: list[tuple[str, int, str]] = [
        ("bold", 20, "Animal Health – Gesundheitschronik"),
        ("regular", 10, f"Erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')}"),
        ("space", 8, ""),
        ("bold", 16, _display(animal.get("name"))),
        ("regular", 11, f"Tierart: {_display(animal.get('species'))}"),
        ("regular", 11, f"Rasse: {_display(animal.get('breed'))}"),
        ("regular", 11, f"Farbe: {_display(animal.get('color'))}"),
        ("regular", 11, f"Geschlecht: {_localized_value('sex', animal.get('sex'))}"),
        ("regular", 11, f"Geburtsdatum: {_display(animal.get('birth_date'))}"),
        ("regular", 11, f"Eintrittsdatum: {_display(animal.get('arrival_date'))}"),
        ("regular", 11, f"Tiergruppe: {_display(animal.get('group_name'))}"),
        ("regular", 11, f"Status: {_localized_value('status', animal.get('status'))}"),
        ("space", 12, ""),
        ("bold", 15, "Gesundheitliche Chronik"),
    ]
    attachments_by_event: dict[str | None, list[dict[str, Any]]] = {}
    for attachment in attachments:
        attachments_by_event.setdefault(attachment.get("event_id"), []).append(attachment)

    general_attachments = attachments_by_event.get(None, [])
    if general_attachments:
        lines.append(("bold", 12, "Allgemeine Dokumente"))
        for attachment in general_attachments:
            title = attachment.get("title") or attachment.get("filename")
            lines.append(
                (
                    "regular",
                    10,
                    f"• {title} ({attachment.get('filename')}, {attachment.get('id')})",
                )
            )
        lines.append(("space", 8, ""))

    if not events:
        lines.append(("regular", 11, "Keine gesundheitlichen Einträge vorhanden."))
        return lines

    for event in events:
        occurred = _format_timestamp(event.get("occurred_at"))
        label = _event_label(str(event.get("event_type", "other")))
        title = _event_title(event.get("title"))
        lines.append(("bold", 12, f"{occurred} – {label}: {title}"))
        value = event.get("value")
        unit = event.get("unit")
        if value is not None and unit:
            lines.append(("regular", 10, f"Messwert: {value} {unit}"))
        if event.get("notes"):
            lines.append(("regular", 10, f"Notizen: {event['notes']}"))
        try:
            event_data = json.loads(event.get("data_json") or "{}")
        except (TypeError, json.JSONDecodeError):
            event_data = {}
        hidden_data = {
            "catalog_source",
            "catalog_scope",
            "catalog_id",
            "task_execution",
            "measurement",
        }
        labels = {
            "symptom": "Symptom",
            "severity": "Schweregrad",
            "medication_name": "Medikament",
            "route": "Applikationsweg",
            "vaccination_targets": "Impfziele",
            "custom_vaccination_target": "Eigenes Impfziel",
            "vaccine_name": "Impfstoff",
            "antigen": "Antigen",
            "batch_number": "Charge",
            "diagnosis": "Diagnose",
            "provider": "Tierarzt / Praxis",
            "visit_reason": "Besuchsgrund",
            "care_action": "Pflegemassnahme",
            "outcome": "Ergebnis",
        }
        for key, data_value in event_data.items():
            if key in hidden_data or data_value in (None, "", [], {}):
                continue
            if isinstance(data_value, list):
                display_value = ", ".join(str(item) for item in data_value)
            elif isinstance(data_value, dict):
                display_value = json.dumps(data_value, ensure_ascii=False, sort_keys=True)
            else:
                display_value = _localized_value(key, data_value)
            label = labels.get(key, key.replace("_", " ").title())
            lines.append(("regular", 10, f"{label}: {display_value}"))
        for attachment in attachments_by_event.get(event.get("id"), []):
            attachment_title = attachment.get("title") or attachment.get("filename")
            lines.append(
                (
                    "regular",
                    9,
                    f"Dokument: {attachment_title} ({attachment.get('filename')}, {attachment.get('id')})",
                )
            )
        lines.append(("space", 7, ""))
    return lines


def _pdf_text(value: str) -> bytes:
    encoded = value.encode("cp1252", errors="replace")
    return encoded.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def _wrap_line(text: str, font_size: int) -> list[str]:
    width = max(42, int(101 * 10 / max(font_size, 8)))
    paragraphs = text.splitlines() or [""]
    result: list[str] = []
    for paragraph in paragraphs:
        result.extend(
            textwrap.wrap(
                paragraph,
                width=width,
                replace_whitespace=False,
                drop_whitespace=True,
                break_long_words=True,
                break_on_hyphens=False,
            )
            or [""]
        )
    return result


def _build_pdf(lines: list[tuple[str, int, str]], title: str) -> bytes:
    page_width = 595
    page_height = 842
    margin_x = 50
    top_y = 790
    bottom_y = 52
    pages: list[list[tuple[str, int, str]]] = [[]]
    y = top_y
    for style, size, text in lines:
        if style == "space":
            y -= size
            if y < bottom_y:
                pages.append([])
                y = top_y
            continue
        wrapped = _wrap_line(text, size)
        for line in wrapped:
            line_height = size + 4
            if y - line_height < bottom_y:
                pages.append([])
                y = top_y
            pages[-1].append((style, size, line))
            y -= line_height

    objects: list[bytes] = []

    def add_object(payload: bytes) -> int:
        objects.append(payload)
        return len(objects)

    catalog_id = add_object(b"")
    pages_id = add_object(b"")
    regular_font_id = add_object(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    )
    bold_font_id = add_object(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
    )
    page_ids: list[int] = []
    for page_number, page in enumerate(pages, start=1):
        commands = [b"BT", b"1 0 0 1 50 790 Tm"]
        current_y = top_y
        for style, size, text in page:
            font = b"F2" if style == "bold" else b"F1"
            commands.append(b"/%s %d Tf" % (font, size))
            commands.append(b"1 0 0 1 %d %d Tm" % (margin_x, current_y))
            commands.append(b"(" + _pdf_text(text) + b") Tj")
            current_y -= size + 4
        commands.extend(
            [
                b"/F1 8 Tf",
                b"1 0 0 1 50 28 Tm",
                b"(" + _pdf_text(f"Seite {page_number} von {len(pages)}") + b") Tj",
                b"ET",
            ]
        )
        stream = b"\n".join(commands)
        content_id = add_object(
            b"<< /Length %d >>\nstream\n" % len(stream)
            + stream
            + b"\nendstream"
        )
        page_id = add_object(
            (
                f"<< /Type /Page /Parent {pages_id} 0 R "
                f"/MediaBox [0 0 {page_width} {page_height}] "
                f"/Resources << /Font << /F1 {regular_font_id} 0 R /F2 {bold_font_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        page_ids.append(page_id)

    objects[catalog_id - 1] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode(
        "ascii"
    )
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"
    ).encode("ascii")
    info_id = add_object(
        b"<< /Title ("
        + _pdf_text(title)
        + b") /Creator (Animal Health 0.7.1) >>"
    )

    output = io.BytesIO()
    output.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, payload in enumerate(objects, start=1):
        offsets.append(output.tell())
        output.write(f"{index} 0 obj\n".encode("ascii"))
        output.write(payload)
        output.write(b"\nendobj\n")
    xref = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.write(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.write(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R "
            f"/Info {info_id} 0 R >>\nstartxref\n{xref}\n%%EOF"
        ).encode("ascii")
    )
    return output.getvalue()


def animal_health_pdf_bytes(database_path: Path, animal_id: str) -> tuple[str, bytes]:
    animal, events, attachments = _fetch_animal_report_data(database_path, animal_id)
    lines = _report_lines(animal, events, attachments)
    name = str(animal.get("name") or animal_id)
    filename = f"Gesundheitschronik_{name}.pdf"
    return filename, _build_pdf(lines, f"Gesundheitschronik {name}")
