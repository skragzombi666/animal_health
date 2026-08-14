from __future__ import annotations

import io
import json
import sqlite3
import struct
import textwrap
import zlib
from datetime import datetime
from pathlib import Path
from typing import Any

_HEALTH_EVENT_TYPES = {
    "observation",
    "symptom",
    "weight",
    "diagnosis",
    "treatment",
    "medication",
    "vaccination",
    "veterinary_visit",
    "care",
    "other",
}

_EVENT_LABELS = {
    "observation": "Beobachtung",
    "symptom": "Symptom",
    "weight": "Gewicht",
    "diagnosis": "Diagnose",
    "treatment": "Behandlung",
    "medication": "Medikation",
    "vaccination": "Impfung",
    "veterinary_visit": "Tierarztbesuch",
    "care": "Pflege",
    "other": "Weiterer Eintrag",
}

_TASK_LABELS = {
    "weight": "Gewicht",
    "medication": "Medikation",
    "vaccination": "Impfung",
    "health_check": "Gesundheitskontrolle",
    "care": "Pflege",
    "veterinary_visit": "Tierarztbesuch",
    "reminder": "Erinnerung",
}

_CLINICAL_FIELD_ORDER = (
    "medication_name",
    "product_name",
    "product_type",
    "dose",
    "dose_unit",
    "route",
    "symptom",
    "severity",
    "diagnosis",
    "treatment",
    "visit_reason",
    "provider",
    "care_action",
    "outcome",
    "check_result",
    "vaccine_name",
    "vaccination_targets",
    "custom_vaccination_target",
    "antigen",
    "batch_number",
)

_FIELD_LABELS = {
    "medication_name": "Medikament",
    "product_name": "Produkt",
    "product_type": "Art",
    "dose": "Dosis",
    "dose_unit": "Einheit",
    "route": "Applikationsweg",
    "symptom": "Symptom",
    "severity": "Schweregrad",
    "diagnosis": "Diagnose",
    "treatment": "Behandlung",
    "visit_reason": "Besuchsgrund",
    "provider": "Tierarzt / Praxis",
    "care_action": "Pflegemassnahme",
    "outcome": "Ergebnis",
    "check_result": "Kontrollergebnis",
    "vaccine_name": "Impfstoff",
    "vaccination_targets": "Impfziele",
    "custom_vaccination_target": "Eigenes Impfziel",
    "antigen": "Antigen",
    "batch_number": "Charge",
}

_VALUE_MAPS = {
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
    "product_type": {"medication": "Medikament", "supplement": "Supplement"},
    "check_result": {"normal": "Unauffällig", "symptom": "Auffällig"},
}


def _table_exists(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _display(value: Any) -> str:
    return "–" if value is None or value == "" else str(value)


def _localized(field: str, value: Any) -> str:
    if value is None or value == "":
        return "–"
    return _VALUE_MAPS.get(field, {}).get(str(value), str(value))


def _format_date(value: Any) -> str:
    if not value:
        return "–"
    text = str(value)
    try:
        return datetime.fromisoformat(text).strftime("%d.%m.%Y")
    except ValueError:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
        except ValueError:
            return text


def _format_timestamp(value: Any) -> str:
    if not value:
        return "–"
    text = str(value)
    try:
        return datetime.fromisoformat(text).strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return text


def _event_title(value: Any) -> str:
    title = _display(value)
    return {
        "weight_measurement": "Gewichtsmessung",
        "vaccination": "Impfung",
        "series_medication_started": "Serienmedikation begonnen",
    }.get(title, title)


def _json_dict(value: Any) -> dict[str, Any]:
    try:
        parsed = json.loads(str(value or "{}"))
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _clinical_values(data: dict[str, Any]) -> list[tuple[str, str]]:
    actual = data.get("actual")
    merged = dict(data)
    if isinstance(actual, dict):
        for key, value in actual.items():
            if value not in (None, "", [], {}):
                merged[key] = value
    result: list[tuple[str, str]] = []
    for key in _CLINICAL_FIELD_ORDER:
        value = merged.get(key)
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            shown = ", ".join(_localized(key, item) for item in value)
        elif isinstance(value, dict):
            continue
        else:
            shown = _localized(key, value)
        result.append((_FIELD_LABELS[key], shown))
    return result


def _recurrence_label(kind: str, interval: int) -> str:
    interval = max(1, int(interval or 1))
    if kind == "daily":
        return "Täglich" if interval == 1 else f"Alle {interval} Tage"
    if kind == "weekly":
        return "Wöchentlich" if interval == 1 else f"Alle {interval} Wochen"
    if kind == "monthly":
        return "Monatlich" if interval == 1 else f"Alle {interval} Monate"
    return "Einmalig"


def _fetch_report_data(database_path: Path, animal_id: str) -> dict[str, Any]:
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        animal = connection.execute(
            """
            SELECT a.*, g.id AS group_id, g.name AS group_name,
                   g.species AS group_species, g.description AS group_description
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
                SELECT * FROM events
                WHERE animal_id = ?
                ORDER BY occurred_at DESC, created_at DESC, id DESC
                """,
                (animal_id,),
            ).fetchall()
        ]

        attachments = []
        if _table_exists(connection, "attachments"):
            attachments = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT id, animal_id, event_id, filename, media_type,
                           size_bytes, storage_name, title, created_at
                    FROM attachments
                    WHERE animal_id = ?
                    ORDER BY created_at DESC, id DESC
                    """,
                    (animal_id,),
                ).fetchall()
            ]

        profile = None
        if _table_exists(connection, "animal_profiles") and _table_exists(connection, "attachments"):
            row = connection.execute(
                """
                SELECT p.image_attachment_id, a.storage_name, a.media_type, a.filename
                FROM animal_profiles AS p
                LEFT JOIN attachments AS a ON a.id = p.image_attachment_id
                WHERE p.animal_id = ?
                """,
                (animal_id,),
            ).fetchone()
            if row is not None and row["storage_name"]:
                profile = dict(row)

        series: list[dict[str, Any]] = []
        if _table_exists(connection, "tasks") and _table_exists(connection, "task_record_configs"):
            today = datetime.now().date().isoformat()
            rows = connection.execute(
                """
                SELECT t.id, t.title, t.description, t.recurrence_type,
                       t.recurrence_interval, t.start_date, t.end_date, t.due_time,
                       t.is_active, c.task_kind, c.template_json
                FROM tasks AS t
                JOIN task_record_configs AS c ON c.task_id = t.id
                WHERE t.animal_id = ?
                  AND t.is_active = 1
                  AND t.recurrence_type <> 'once'
                  AND t.start_date <= ?
                  AND (t.end_date IS NULL OR t.end_date >= ?)
                ORDER BY c.task_kind, t.title COLLATE NOCASE, t.id
                """,
                (animal_id, today, today),
            ).fetchall()
            for row in rows:
                item = dict(row)
                item["planned"] = _json_dict(item.pop("template_json", "{}"))
                series.append(item)

    return {
        "animal": dict(animal),
        "events": events,
        "attachments": attachments,
        "profile": profile,
        "series": series,
    }


def _report_lines(data: dict[str, Any]) -> list[tuple[str, int, str]]:
    animal = data["animal"]
    events = data["events"]
    attachments = data["attachments"]
    series = data["series"]
    profile = data["profile"]

    lines: list[tuple[str, int, str]] = [
        ("bold", 20, "Animal Health – Gesundheitschronik"),
        ("regular", 9, f"Erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')}"),
        ("space", 10, ""),
        ("bold", 16, "Tierdaten"),
        ("bold", 13, "Stammdaten"),
    ]
    if profile:
        lines.append(("profile", 108, ""))
    lines.extend(
        [
            ("bold", 15, _display(animal.get("name"))),
            ("regular", 10, f"Tierart: {_display(animal.get('species'))}"),
            ("regular", 10, f"Rasse: {_display(animal.get('breed'))}"),
            ("regular", 10, f"Farbe: {_display(animal.get('color'))}"),
            ("regular", 10, f"Geschlecht: {_localized('sex', animal.get('sex'))}"),
            ("regular", 10, f"Geburtsdatum: {_format_date(animal.get('birth_date'))}"),
            ("regular", 10, f"Eintrittsdatum: {_format_date(animal.get('arrival_date'))}"),
            ("regular", 10, f"Status: {_localized('status', animal.get('status'))}"),
            ("space", 10, ""),
            ("bold", 13, "Gruppendaten"),
            ("regular", 10, f"Tiergruppe: {_display(animal.get('group_name'))}"),
        ]
    )
    if animal.get("group_species"):
        lines.append(("regular", 10, f"Tierart der Gruppe: {_display(animal.get('group_species'))}"))
    if animal.get("group_description"):
        lines.append(("regular", 10, f"Beschreibung: {_display(animal.get('group_description'))}"))

    lines.extend(
        [
            ("space", 10, ""),
            ("bold", 13, "Aktuell laufende Therapien / Serien"),
        ]
    )
    if not series:
        lines.append(("regular", 10, "Keine aktuell laufenden Serien erfasst."))
    else:
        for task in series:
            kind = str(task.get("task_kind") or "reminder")
            lines.append(("bold", 11, f"{_TASK_LABELS.get(kind, kind)}: {_display(task.get('title'))}"))
            period = f"Seit {_format_date(task.get('start_date'))} · {_recurrence_label(str(task.get('recurrence_type')), int(task.get('recurrence_interval') or 1))}"
            if task.get("end_date"):
                period += f" · bis {_format_date(task.get('end_date'))}"
            if task.get("due_time"):
                period += f" · {_display(task.get('due_time'))[:5]} Uhr"
            lines.append(("regular", 10, period))
            for label, value in _clinical_values(task.get("planned") or {}):
                lines.append(("regular", 10, f"{label}: {value}"))
            if task.get("description"):
                lines.append(("regular", 10, f"Hinweis: {_display(task.get('description'))}"))
            lines.append(("space", 5, ""))

    lines.extend(
        [
            ("space", 12, ""),
            ("bold", 15, "Gesundheitschronik"),
            ("regular", 9, "Neuester Eintrag zuerst"),
            ("space", 6, ""),
        ]
    )

    superseded = {
        str(event.get("correction_of_event_id"))
        for event in events
        if event.get("correction_of_event_id")
    }
    current_events = [
        event
        for event in events
        if str(event.get("event_type") or "") in _HEALTH_EVENT_TYPES
        and str(event.get("id") or "") not in superseded
    ]

    attachments_by_event: dict[str, list[dict[str, Any]]] = {}
    for attachment in attachments:
        event_id = attachment.get("event_id")
        if event_id:
            attachments_by_event.setdefault(str(event_id), []).append(attachment)

    if not current_events:
        lines.append(("regular", 10, "Keine gesundheitlich relevanten Einträge vorhanden."))
        return lines

    for event in current_events:
        event_type = str(event.get("event_type") or "other")
        title = _event_title(event.get("title"))
        label = _EVENT_LABELS.get(event_type, event_type.replace("_", " ").title())
        lines.append(("bold", 11, f"{_format_timestamp(event.get('occurred_at'))} – {label}: {title}"))

        event_data = _json_dict(event.get("data_json"))
        if event.get("title") == "series_medication_started" and isinstance(event_data.get("series"), dict):
            info = event_data["series"]
            planned = info.get("planned") if isinstance(info.get("planned"), dict) else {}
            for clinical_label, value in _clinical_values(planned):
                lines.append(("regular", 10, f"{clinical_label}: {value}"))
            start = info.get("start_date")
            if start:
                recurrence = _recurrence_label(str(info.get("recurrence_type") or "daily"), int(info.get("recurrence_interval") or 1))
                lines.append(("regular", 10, f"Serie: seit {_format_date(start)} · {recurrence}"))
            lines.append(("regular", 9, "Rückwirkend als Serie erfasst; frühere Einzelgaben wurden nicht automatisch als Einzeleinträge angelegt."))
        else:
            value = event.get("value")
            unit = event.get("unit")
            if value is not None:
                shown = f"{value:g}" if isinstance(value, (int, float)) else str(value)
                lines.append(("regular", 10, f"Messwert: {shown}{f' {unit}' if unit else ''}"))
            for clinical_label, clinical_value in _clinical_values(event_data):
                if clinical_label == "Dosis" and value is not None:
                    continue
                lines.append(("regular", 10, f"{clinical_label}: {clinical_value}"))

        if event.get("notes"):
            lines.append(("regular", 10, f"Notiz: {_display(event.get('notes'))}"))
        for attachment in attachments_by_event.get(str(event.get("id") or ""), []):
            title = attachment.get("title") or attachment.get("filename")
            lines.append(("regular", 9, f"Dokument: {_display(title)} ({_display(attachment.get('filename'))})"))
        lines.append(("space", 7, ""))

    return lines


def _jpeg_info(data: bytes) -> tuple[int, int, int] | None:
    if not data.startswith(b"\xff\xd8"):
        return None
    index = 2
    sof_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while index + 4 <= len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        while index < len(data) and data[index] == 0xFF:
            index += 1
        if index >= len(data):
            break
        marker = data[index]
        index += 1
        if marker in (0xD8, 0xD9):
            continue
        if marker == 0xDA:
            break
        if index + 2 > len(data):
            break
        length = struct.unpack(">H", data[index:index + 2])[0]
        if length < 2 or index + length > len(data):
            break
        if marker in sof_markers and length >= 8:
            height = struct.unpack(">H", data[index + 3:index + 5])[0]
            width = struct.unpack(">H", data[index + 5:index + 7])[0]
            components = data[index + 7]
            return width, height, components
        index += length
    return None


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _png_rgb(data: bytes) -> tuple[int, int, bytes, str] | None:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    index = 8
    width = height = bit_depth = color_type = interlace = None
    idat = bytearray()
    while index + 12 <= len(data):
        length = struct.unpack(">I", data[index:index + 4])[0]
        kind = data[index + 4:index + 8]
        payload = data[index + 8:index + 8 + length]
        if len(payload) != length:
            return None
        if kind == b"IHDR" and length >= 13:
            width, height, bit_depth, color_type, _compression, _filter, interlace = struct.unpack(">IIBBBBB", payload[:13])
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            break
        index += 12 + length
    if not width or not height or bit_depth != 8 or interlace != 0 or color_type not in {0, 2, 4, 6}:
        return None
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[int(color_type)]
    stride = int(width) * channels
    try:
        raw = zlib.decompress(bytes(idat))
    except zlib.error:
        return None
    expected = int(height) * (stride + 1)
    if len(raw) < expected:
        return None
    rows: list[bytearray] = []
    offset = 0
    previous = bytearray(stride)
    for _ in range(int(height)):
        filter_type = raw[offset]
        offset += 1
        scan = bytearray(raw[offset:offset + stride])
        offset += stride
        recon = bytearray(stride)
        for i, value in enumerate(scan):
            left = recon[i - channels] if i >= channels else 0
            up = previous[i]
            up_left = previous[i - channels] if i >= channels else 0
            if filter_type == 0:
                result = value
            elif filter_type == 1:
                result = (value + left) & 255
            elif filter_type == 2:
                result = (value + up) & 255
            elif filter_type == 3:
                result = (value + ((left + up) // 2)) & 255
            elif filter_type == 4:
                result = (value + _paeth(left, up, up_left)) & 255
            else:
                return None
            recon[i] = result
        rows.append(recon)
        previous = recon

    if color_type == 0:
        pixels = b"".join(bytes(row) for row in rows)
        return int(width), int(height), zlib.compress(pixels, 9), "/DeviceGray"

    rgb = bytearray()
    for row in rows:
        for i in range(0, len(row), channels):
            if color_type == 2:
                rgb.extend(row[i:i + 3])
            elif color_type == 6:
                r, g, b, alpha = row[i:i + 4]
                rgb.extend((
                    (r * alpha + 255 * (255 - alpha)) // 255,
                    (g * alpha + 255 * (255 - alpha)) // 255,
                    (b * alpha + 255 * (255 - alpha)) // 255,
                ))
            else:
                gray, alpha = row[i:i + 2]
                shown = (gray * alpha + 255 * (255 - alpha)) // 255
                rgb.extend((shown, shown, shown))
    return int(width), int(height), zlib.compress(bytes(rgb), 9), "/DeviceRGB"


def _profile_image(database_path: Path, profile: dict[str, Any] | None) -> dict[str, Any] | None:
    if not profile or not profile.get("storage_name"):
        return None
    path = database_path.parent / ".storage" / "animal_health" / "attachments" / str(profile["storage_name"])
    if not path.is_file():
        return None
    try:
        content = path.read_bytes()
    except OSError:
        return None
    jpeg = _jpeg_info(content)
    if jpeg:
        width, height, components = jpeg
        color_space = "/DeviceGray" if components == 1 else "/DeviceCMYK" if components == 4 else "/DeviceRGB"
        return {"width": width, "height": height, "data": content, "filter": "/DCTDecode", "color_space": color_space}
    png = _png_rgb(content)
    if png:
        width, height, compressed, color_space = png
        return {"width": width, "height": height, "data": compressed, "filter": "/FlateDecode", "color_space": color_space}
    return None


def _pdf_text(value: str) -> bytes:
    encoded = value.encode("cp1252", errors="replace")
    return encoded.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def _wrap_line(text: str, font_size: int) -> list[str]:
    width = max(42, int(101 * 10 / max(font_size, 8)))
    result: list[str] = []
    for paragraph in text.splitlines() or [""]:
        result.extend(textwrap.wrap(paragraph, width=width, replace_whitespace=False, drop_whitespace=True, break_long_words=True, break_on_hyphens=False) or [""])
    return result


def _build_pdf(lines: list[tuple[str, int, str]], title: str, image: dict[str, Any] | None) -> bytes:
    page_width, page_height = 595, 842
    margin_x, top_y, bottom_y = 50, 790, 52
    pages: list[list[tuple[str, int, str]]] = [[]]
    y = top_y
    for style, size, text in lines:
        if style == "space":
            y -= size
            if y < bottom_y:
                pages.append([])
                y = top_y
            continue
        if style == "profile":
            reserve = size + 8
            if y - reserve < bottom_y:
                pages.append([])
                y = top_y
            pages[-1].append((style, size, text))
            y -= reserve
            continue
        for wrapped in _wrap_line(text, size):
            line_height = size + 4
            if y - line_height < bottom_y:
                pages.append([])
                y = top_y
            pages[-1].append((style, size, wrapped))
            y -= line_height

    objects: list[bytes] = []

    def add_object(payload: bytes) -> int:
        objects.append(payload)
        return len(objects)

    catalog_id = add_object(b"")
    pages_id = add_object(b"")
    regular_font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    bold_font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")

    image_id: int | None = None
    if image:
        stream = image["data"]
        image_id = add_object(
            (
                f"<< /Type /XObject /Subtype /Image /Width {int(image['width'])} /Height {int(image['height'])} "
                f"/ColorSpace {image['color_space']} /BitsPerComponent 8 /Filter {image['filter']} /Length {len(stream)} >>\nstream\n"
            ).encode("ascii") + stream + b"\nendstream"
        )

    page_ids: list[int] = []
    for page_number, page in enumerate(pages, start=1):
        commands = [b"BT", b"1 0 0 1 50 790 Tm"]
        current_y = top_y
        for style, size, text in page:
            if style == "profile":
                if image_id and image:
                    iw, ih = float(image["width"]), float(image["height"])
                    scale = min(float(size) / iw, float(size) / ih, 1.0)
                    draw_w, draw_h = max(1.0, iw * scale), max(1.0, ih * scale)
                    x = page_width - margin_x - draw_w
                    y_image = current_y - draw_h
                    commands.extend([
                        b"ET",
                        f"q {draw_w:.2f} 0 0 {draw_h:.2f} {x:.2f} {y_image:.2f} cm /Im1 Do Q".encode("ascii"),
                        b"BT",
                    ])
                current_y -= size + 8
                continue
            font = b"F2" if style == "bold" else b"F1"
            commands.append(b"/%s %d Tf" % (font, size))
            commands.append(b"1 0 0 1 %d %d Tm" % (margin_x, current_y))
            commands.append(b"(" + _pdf_text(text) + b") Tj")
            current_y -= size + 4
        commands.extend([
            b"/F1 8 Tf",
            b"1 0 0 1 50 28 Tm",
            b"(" + _pdf_text(f"Seite {page_number} von {len(pages)}") + b") Tj",
            b"ET",
        ])
        content = b"\n".join(commands)
        content_id = add_object(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
        xobjects = f" /XObject << /Im1 {image_id} 0 R >>" if image_id else ""
        page_id = add_object(
            (
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {page_width} {page_height}] "
                f"/Resources << /Font << /F1 {regular_font_id} 0 R /F2 {bold_font_id} 0 R >>{xobjects} >> "
                f"/Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        page_ids.append(page_id)

    objects[catalog_id - 1] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("ascii")
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")
    info_id = add_object(b"<< /Title (" + _pdf_text(title) + b") /Creator (Animal Health 0.8.16) >>")

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
    output.write((f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R /Info {info_id} 0 R >>\nstartxref\n{xref}\n%%EOF").encode("ascii"))
    return output.getvalue()


def animal_health_pdf_bytes(database_path: Path, animal_id: str) -> tuple[str, bytes]:
    data = _fetch_report_data(database_path, animal_id)
    image = _profile_image(database_path, data.get("profile"))
    lines = _report_lines(data)
    name = str(data["animal"].get("name") or animal_id)
    filename = f"Gesundheitschronik_{name}.pdf"
    return filename, _build_pdf(lines, f"Gesundheitschronik {name}", image)
