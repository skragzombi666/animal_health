from __future__ import annotations

from typing import Any

from .catalog import medicine_catalog_names, vaccine_catalog_names
from .const import DOMAIN
from .task_record_creation import SERVICE_CREATE_RECORD_TASK
from .task_records import (
    SERVICE_RECORD_TASK_CARE,
    SERVICE_RECORD_TASK_HEALTH_CHECK,
    SERVICE_RECORD_TASK_MEDICATION,
    SERVICE_RECORD_TASK_REMINDER,
    SERVICE_RECORD_TASK_VACCINATION,
    SERVICE_RECORD_TASK_VETERINARY_VISIT,
    SERVICE_RECORD_TASK_WEIGHT,
)


def _select(options: list[tuple[str, str]], *, multiple: bool = False) -> dict[str, Any]:
    selector: dict[str, Any] = {
        "options": [{"value": value, "label": label} for value, label in options],
        "mode": "dropdown",
    }
    if multiple:
        selector["multiple"] = True
    return {"select": selector}


def _task_selector() -> dict[str, Any]:
    return {
        "entity": {
            "filter": [{"integration": DOMAIN, "domain": "switch"}],
        }
    }


def _animal_selector() -> dict[str, Any]:
    return {
        "device": {
            "filter": [{"integration": DOMAIN}],
            "entity": [{"integration": DOMAIN, "domain": "sensor"}],
            "multiple": True,
        }
    }


def _text(*, multiline: bool = False) -> dict[str, Any]:
    return {"text": {"multiline": True} if multiline else {}}


def _number() -> dict[str, Any]:
    return {"number": {"min": 0.001, "step": "any", "mode": "box"}}


def _catalog_selector(values: list[str]) -> dict[str, Any]:
    return {
        "select": {
            "options": values,
            "custom_value": True,
            "mode": "dropdown",
            "sort": True,
        }
    }


def _common_record_fields(german: bool) -> dict[str, Any]:
    return {
        "task_entity_id": {
            "name": "Aufgabe" if german else "Task",
            "description": (
                "Aufgabe anhand von Titel, Aufgabenart und ID auswählen. "
                "Es werden nur Fälligkeiten der passenden Aufgabenart akzeptiert; "
                "standardmässig wird die früheste offene Fälligkeit verwendet."
                if german
                else "Select the task by title, kind and ID. Only occurrences of "
                "the matching task kind are accepted; the earliest open occurrence "
                "is used by default."
            ),
            "selector": _task_selector(),
        },
        "scheduled_date": {
            "name": "Fälligkeitsdatum" if german else "Scheduled date",
            "description": (
                "Optional, wenn gezielt eine bestimmte offene Fälligkeit dieser Aufgabe ausgeführt werden soll."
                if german
                else "Optional when a specific open occurrence of the task should be recorded."
            ),
            "selector": {"date": {}},
        },
        "occurrence_id": {
            "name": "Fälligkeits-ID" if german else "Occurrence ID",
            "description": (
                "Technische Alternative zur Aufgabenauswahl, beispielsweise für bestehende Automationen."
                if german
                else "Technical alternative to task selection, for example for existing automations."
            ),
            "selector": _text(),
        },
        "performed_at": {
            "name": "Tatsächlich ausgeführt am" if german else "Actually performed at",
            "description": (
                "Ohne Angabe wird der aktuelle Zeitpunkt verwendet."
                if german
                else "The current time is used when omitted."
            ),
            "selector": {"datetime": {}},
        },
        "deviation_reason": {
            "name": "Begründung der Abweichung" if german else "Reason for deviation",
            "description": (
                "Optionaler Grund für eine frühere, spätere oder inhaltlich abweichende Ausführung."
                if german
                else "Optional reason for early, late or otherwise changed execution."
            ),
            "selector": _text(multiline=True),
        },
        "notes": {
            "name": "Notiz" if german else "Notes",
            "selector": _text(multiline=True),
        },
    }


def _create_description(german: bool) -> dict[str, Any]:
    task_kinds = [
        ("reminder", "Erinnerung" if german else "Reminder"),
        ("weight", "Gewicht erfassen" if german else "Record weight"),
        ("medication", "Medikament geben" if german else "Administer medication"),
        ("vaccination", "Impfung durchführen" if german else "Record vaccination"),
        ("health_check", "Gesundheitskontrolle" if german else "Health check"),
        ("care", "Pflege durchführen" if german else "Care action"),
        ("veterinary_visit", "Tierarztbesuch" if german else "Veterinary visit"),
    ]
    recurrence = [
        ("once", "Einmalig" if german else "Once"),
        ("daily", "Täglich" if german else "Daily"),
        ("weekly", "Wöchentlich" if german else "Weekly"),
        ("monthly", "Monatlich" if german else "Monthly"),
    ]
    dose_units = [
        ("mcg", "µg – Mikrogramm" if german else "µg – Microgram"),
        ("mg", "mg – Milligramm" if german else "mg – Milligram"),
        ("g", "g – Gramm" if german else "g – Gram"),
        ("ul", "µL – Mikroliter" if german else "µL – Microlitre"),
        ("ml", "mL – Milliliter" if german else "mL – Millilitre"),
        ("drop", "Tropfen" if german else "Drop"),
        ("tablet", "Tablette" if german else "Tablet"),
        ("dose", "Dosis" if german else "Dose"),
    ]
    routes = [
        ("oral", "Oral"),
        ("topical", "Topisch" if german else "Topical"),
        ("subcutaneous", "Subkutan" if german else "Subcutaneous"),
        ("intramuscular", "Intramuskulär" if german else "Intramuscular"),
        ("intravenous", "Intravenös" if german else "Intravenous"),
        ("eye", "Auge" if german else "Eye"),
        ("ear", "Ohr" if german else "Ear"),
        ("spray", "Spray"),
        ("other", "Andere" if german else "Other"),
    ]
    vaccination_targets = [
        ("rabies", "Tollwut" if german else "Rabies"),
        ("distemper", "Staupe" if german else "Distemper"),
        ("canine_adenovirus", "Hepatitis / Adenovirus" if german else "Canine adenovirus / hepatitis"),
        ("canine_parvovirus", "Parvovirose" if german else "Canine parvovirus"),
        ("leptospirosis", "Leptospirose" if german else "Leptospirosis"),
        ("parainfluenza", "Parainfluenza"),
        ("kennel_cough", "Zwingerhusten" if german else "Kennel cough"),
        ("feline_panleukopenia", "Katzenseuche" if german else "Feline panleukopenia"),
        ("feline_herpesvirus", "Felines Herpesvirus" if german else "Feline herpesvirus"),
        ("feline_calicivirus", "Felines Calicivirus" if german else "Feline calicivirus"),
        ("feline_leukemia", "Feline Leukämie (FeLV)" if german else "Feline leukaemia (FeLV)"),
        ("marek", "Marek-Krankheit" if german else "Marek's disease"),
        ("newcastle", "Newcastle-Krankheit" if german else "Newcastle disease"),
        ("infectious_bronchitis", "Infektiöse Bronchitis" if german else "Infectious bronchitis"),
        ("gumboro", "Gumboro"),
        ("avian_pox", "Geflügelpocken" if german else "Avian pox"),
        ("paramyxovirus", "Paramyxovirus"),
        ("myxomatosis", "Myxomatose" if german else "Myxomatosis"),
        ("rabbit_hemorrhagic_disease", "RHD / Chinaseuche" if german else "Rabbit haemorrhagic disease"),
        ("tetanus", "Tetanus"),
        ("equine_influenza", "Pferdeinfluenza" if german else "Equine influenza"),
        ("strangles", "Druse" if german else "Strangles"),
        ("bluetongue", "Blauzungenkrankheit" if german else "Bluetongue"),
        ("other", "Andere Impfung" if german else "Other vaccination target"),
    ]
    fields: dict[str, Any] = {
        "task_scope": {
            "name": "Aufgabenbereich" if german else "Task scope",
            "default": "animal",
            "selector": _select([
                ("animal", "Tierbezogen" if german else "Animal-specific"),
                ("general", "Allgemein" if german else "General"),
            ]),
        },
        "device_ids": {
            "name": "Tiere" if german else "Animals",
            "description": (
                "Ein oder mehrere Tiere auswählen. Nur reine Erinnerungen dürfen allgemein sein."
                if german
                else "Select one or more animals. Only reminders may be general tasks."
            ),
            "selector": _animal_selector(),
        },
        "task_kind": {
            "name": "Aufgabenart" if german else "Task kind",
            "required": True,
            "selector": _select(task_kinds),
        },
        "title": {
            "name": "Titel" if german else "Title",
            "required": True,
            "selector": _text(),
        },
        "description": {
            "name": "Beschreibung" if german else "Description",
            "selector": _text(multiline=True),
        },
        "recurrence_type": {
            "name": "Wiederholung" if german else "Recurrence",
            "required": True,
            "selector": _select(recurrence),
        },
        "recurrence_interval": {
            "name": "Intervall" if german else "Interval",
            "default": 1,
            "selector": {"number": {"min": 1, "max": 365, "step": 1, "mode": "box"}},
        },
        "start_date": {
            "name": "Startdatum" if german else "Start date",
            "required": True,
            "selector": {"date": {}},
        },
        "end_date": {
            "name": "Enddatum" if german else "End date",
            "selector": {"date": {}},
        },
        "due_time": {
            "name": "Uhrzeit" if german else "Due time",
            "description": (
                "Ohne Uhrzeit gilt die Aufgabe für den gesamten Fälligkeitstag."
                if german
                else "Without a time, the task is due throughout the whole date."
            ),
            "selector": {"time": {}},
        },
        "planned_medication_name": {
            "name": "Geplantes Medikament" if german else "Planned medication",
            "description": (
                "Für Aufgabenart Medikament zwingend. Katalogauswahl oder eigener Präparatname."
                if german
                else "Required for medication tasks. Choose a catalogue product or enter a custom name."
            ),
            "selector": _catalog_selector(medicine_catalog_names()),
        },
        "planned_dose": {
            "name": "Geplante Dosis" if german else "Planned dose",
            "selector": _number(),
        },
        "planned_dose_unit": {
            "name": "Geplante Dosiseinheit" if german else "Planned dose unit",
            "selector": _select(dose_units),
        },
        "planned_route": {
            "name": "Geplanter Applikationsweg" if german else "Planned route",
            "selector": _select(routes),
        },
        "planned_vaccination_targets": {
            "name": "Geplante Impfung gegen" if german else "Planned vaccination against",
            "description": (
                "Für Aufgabenart Impfung mindestens ein Impfziel auswählen."
                if german
                else "Select at least one target for vaccination tasks."
            ),
            "selector": _select(vaccination_targets, multiple=True),
        },
        "planned_custom_vaccination_target": {
            "name": "Anderes geplantes Impfziel" if german else "Other planned vaccination target",
            "selector": _text(),
        },
        "planned_vaccine_name": {
            "name": "Geplanter Impfstoff" if german else "Planned vaccine",
            "description": (
                "Optional aus dem Katalog auswählen oder eigenen Impfstoff eingeben."
                if german
                else "Optionally choose a catalogue vaccine or enter a custom product."
            ),
            "selector": _catalog_selector(vaccine_catalog_names()),
        },
        "planned_antigen": {
            "name": "Geplantes Antigen / Impfstamm" if german else "Planned antigen / strain",
            "selector": _text(),
        },
        "planned_vaccination_dose": {
            "name": "Geplante Impfdosis" if german else "Planned vaccination dose",
            "selector": _number(),
        },
        "planned_vaccination_dose_unit": {
            "name": "Einheit der geplanten Impfdosis" if german else "Planned vaccination dose unit",
            "selector": _select(dose_units),
        },
        "planned_vaccination_route": {
            "name": "Geplanter Impfweg" if german else "Planned vaccination route",
            "selector": _select(routes),
        },
        "planned_check_focus": {
            "name": "Schwerpunkt der Gesundheitskontrolle" if german else "Health-check focus",
            "selector": _text(multiline=True),
        },
        "planned_care_action": {
            "name": "Geplante Pflegemassnahme" if german else "Planned care action",
            "selector": _text(),
        },
        "planned_visit_reason": {
            "name": "Geplanter Grund des Tierarztbesuchs" if german else "Planned visit reason",
            "selector": _text(),
        },
        "planned_provider": {
            "name": "Geplante Praxis / behandelnde Person" if german else "Planned provider",
            "selector": _text(),
        },
    }
    return {
        "name": "Strukturierte Aufgabe anlegen" if german else "Create structured task",
        "description": (
            "Legt eine Aufgabe mit fachlicher Aufgabenart und geplanten Angaben an. Beim Ausführen werden Planung, tatsächliche Durchführung und zeitliche Abweichung gemeinsam dokumentiert."
            if german
            else "Creates a task with a record type and planned values. Execution records the plan, actual work and timing deviation together."
        ),
        "fields": fields,
    }


def _record_description(
    german: bool,
    *,
    name_de: str,
    name_en: str,
    description_de: str,
    description_en: str,
    extra_fields: dict[str, Any],
) -> dict[str, Any]:
    fields = _common_record_fields(german)
    ordered = {
        "task_entity_id": fields.pop("task_entity_id"),
        "scheduled_date": fields.pop("scheduled_date"),
        "occurrence_id": fields.pop("occurrence_id"),
        "performed_at": fields.pop("performed_at"),
        **extra_fields,
        "deviation_reason": fields.pop("deviation_reason"),
        "notes": fields.pop("notes"),
    }
    return {
        "name": name_de if german else name_en,
        "description": description_de if german else description_en,
        "fields": ordered,
    }


def task_record_descriptions(language: str) -> dict[str, dict[str, Any]]:
    german = language.startswith("de")
    dose_units = [
        ("mcg", "µg – Mikrogramm" if german else "µg – Microgram"),
        ("mg", "mg – Milligramm" if german else "mg – Milligram"),
        ("g", "g – Gramm" if german else "g – Gram"),
        ("ul", "µL – Mikroliter" if german else "µL – Microlitre"),
        ("ml", "mL – Milliliter" if german else "mL – Millilitre"),
        ("drop", "Tropfen" if german else "Drop"),
        ("tablet", "Tablette" if german else "Tablet"),
        ("dose", "Dosis" if german else "Dose"),
    ]
    routes = [
        ("oral", "Oral"),
        ("topical", "Topisch" if german else "Topical"),
        ("subcutaneous", "Subkutan" if german else "Subcutaneous"),
        ("intramuscular", "Intramuskulär" if german else "Intramuscular"),
        ("intravenous", "Intravenös" if german else "Intravenous"),
        ("eye", "Auge" if german else "Eye"),
        ("ear", "Ohr" if german else "Ear"),
        ("spray", "Spray"),
        ("other", "Andere" if german else "Other"),
    ]
    vaccination_targets = _create_description(german)["fields"][
        "planned_vaccination_targets"
    ]["selector"]

    descriptions = {SERVICE_CREATE_RECORD_TASK: _create_description(german)}
    descriptions[SERVICE_RECORD_TASK_REMINDER] = _record_description(
        german,
        name_de="Erinnerungsaufgabe dokumentieren",
        name_en="Record reminder task",
        description_de="Dokumentiert die Ausführung einer reinen Erinnerung im Aufgabenverlauf. Es entsteht kein medizinischer Chronikeintrag.",
        description_en="Records completion of a reminder in task history without creating a medical logbook event.",
        extra_fields={},
    )
    descriptions[SERVICE_RECORD_TASK_WEIGHT] = _record_description(
        german,
        name_de="Gewichtsaufgabe ausführen",
        name_en="Record weight task",
        description_de="Erfasst das tatsächliche Gewicht, erstellt den Gewichtseintrag und erledigt die Fälligkeit atomar.",
        description_en="Records actual weight, creates the weight event and completes the occurrence atomically.",
        extra_fields={
            "weight": {
                "name": "Tatsächliches Gewicht" if german else "Actual weight",
                "required": True,
                "selector": _number(),
            },
            "weight_unit": {
                "name": "Gewichtseinheit" if german else "Weight unit",
                "default": "kg",
                "selector": _select([
                    ("mg", "Milligramm" if german else "Milligram"),
                    ("g", "Gramm" if german else "Gram"),
                    ("kg", "Kilogramm" if german else "Kilogram"),
                ]),
            },
        },
    )
    descriptions[SERVICE_RECORD_TASK_MEDICATION] = _record_description(
        german,
        name_de="Medikamentenaufgabe ausführen",
        name_en="Record medication task",
        description_de="Übernimmt geplante Medikamentenangaben als Vorbelegung. Tatsächliche Angaben können korrigiert werden und werden getrennt von der Planung gespeichert.",
        description_en="Uses the medication plan as defaults. Actual values may be changed and are stored separately from the plan.",
        extra_fields={
            "medication_name": {
                "name": "Tatsächliches Medikament" if german else "Actual medication",
                "description": (
                    "Geplantes Präparat beibehalten, aus dem vollständigen Katalog wählen oder einen eigenen Produktnamen eingeben."
                    if german
                    else "Keep the planned product, choose from the complete catalogue or enter a custom product name."
                ),
                "selector": _catalog_selector(medicine_catalog_names()),
            },
            "dose": {"name": "Tatsächliche Dosis" if german else "Actual dose", "selector": _number()},
            "dose_unit": {"name": "Tatsächliche Dosiseinheit" if german else "Actual dose unit", "selector": _select(dose_units)},
            "route": {"name": "Tatsächlicher Applikationsweg" if german else "Actual route", "selector": _select(routes)},
        },
    )
    descriptions[SERVICE_RECORD_TASK_VACCINATION] = _record_description(
        german,
        name_de="Impfaufgabe ausführen",
        name_en="Record vaccination task",
        description_de="Übernimmt das geplante Impfziel und ergänzt die tatsächlich verwendeten Impf-, Dosis-, Chargen- und Applikationsdaten.",
        description_en="Uses the planned vaccination target and records the actual vaccine, dose, batch and route.",
        extra_fields={
            "vaccination_targets": {"name": "Tatsächlich geimpft gegen" if german else "Actually vaccinated against", "selector": vaccination_targets},
            "custom_vaccination_target": {"name": "Anderes tatsächliches Impfziel" if german else "Other actual target", "selector": _text()},
            "vaccine_name": {
                "name": "Tatsächlicher Impfstoff" if german else "Actual vaccine",
                "description": (
                    "Geplanten Impfstoff beibehalten, aus dem vollständigen Katalog wählen oder einen eigenen Produktnamen eingeben."
                    if german
                    else "Keep the planned vaccine, choose from the complete catalogue or enter a custom product name."
                ),
                "selector": _catalog_selector(vaccine_catalog_names()),
            },
            "antigen": {"name": "Antigen / Impfstamm" if german else "Antigen / strain", "selector": _text()},
            "dose": {"name": "Tatsächliche Impfdosis" if german else "Actual vaccination dose", "selector": _number()},
            "dose_unit": {"name": "Einheit" if german else "Unit", "selector": _select(dose_units)},
            "route": {"name": "Applikationsweg" if german else "Route", "selector": _select(routes)},
            "batch_number": {"name": "Charge / Losnummer" if german else "Batch / lot number", "selector": _text()},
        },
    )
    descriptions[SERVICE_RECORD_TASK_HEALTH_CHECK] = _record_description(
        german,
        name_de="Gesundheitskontrolle ausführen",
        name_en="Record health-check task",
        description_de="Dokumentiert eine unauffällige Kontrolle, eine Auffälligkeit oder ein festgestelltes Symptom und erledigt die Fälligkeit.",
        description_en="Records a normal check, concern or observed symptom and completes the occurrence.",
        extra_fields={
            "check_result": {
                "name": "Ergebnis" if german else "Result",
                "required": True,
                "selector": _select([
                    ("normal", "Unauffällig" if german else "Normal"),
                    ("concern", "Auffälligkeit ohne definiertes Symptom" if german else "Concern without defined symptom"),
                    ("symptom", "Symptom festgestellt" if german else "Symptom observed"),
                ]),
            },
            "symptom": {
                "name": "Symptom" if german else "Symptom",
                "selector": _select([
                    ("reduced_appetite", "Verminderter Appetit" if german else "Reduced appetite"),
                    ("lethargy", "Teilnahmslosigkeit" if german else "Lethargy"),
                    ("diarrhea", "Durchfall" if german else "Diarrhea"),
                    ("coughing", "Husten" if german else "Coughing"),
                    ("sneezing", "Niesen" if german else "Sneezing"),
                    ("lameness", "Lahmheit" if german else "Lameness"),
                    ("weight_loss", "Gewichtsverlust" if german else "Weight loss"),
                    ("other", "Anderes Symptom" if german else "Other symptom"),
                ]),
            },
            "custom_symptom": {"name": "Anderes Symptom" if german else "Custom symptom", "selector": _text()},
            "severity": {
                "name": "Schweregrad" if german else "Severity",
                "selector": _select([
                    ("mild", "Leicht" if german else "Mild"),
                    ("moderate", "Mittel" if german else "Moderate"),
                    ("severe", "Schwer" if german else "Severe"),
                    ("critical", "Kritisch" if german else "Critical"),
                ]),
            },
        },
    )
    descriptions[SERVICE_RECORD_TASK_CARE] = _record_description(
        german,
        name_de="Pflegeaufgabe ausführen",
        name_en="Record care task",
        description_de="Dokumentiert die geplante und tatsächlich durchgeführte Pflegemassnahme mit Ergebnis.",
        description_en="Records the planned and actual care action with its outcome.",
        extra_fields={
            "care_action": {"name": "Tatsächliche Pflegemassnahme" if german else "Actual care action", "selector": _text()},
            "outcome": {"name": "Ergebnis" if german else "Outcome", "selector": _text(multiline=True)},
        },
    )
    descriptions[SERVICE_RECORD_TASK_VETERINARY_VISIT] = _record_description(
        german,
        name_de="Tierarztaufgabe ausführen",
        name_en="Record veterinary-visit task",
        description_de="Dokumentiert den geplanten und tatsächlichen Tierarztbesuch, die behandelnde Stelle und eine allfällige Diagnose.",
        description_en="Records the planned and actual veterinary visit, provider and any diagnosis.",
        extra_fields={
            "visit_reason": {"name": "Tatsächlicher Besuchsgrund" if german else "Actual visit reason", "selector": _text()},
            "provider": {"name": "Praxis / behandelnde Person" if german else "Provider", "selector": _text()},
            "diagnosis": {"name": "Diagnose / Ergebnis" if german else "Diagnosis / result", "selector": _text(multiline=True)},
        },
    )
    return descriptions
