from __future__ import annotations

from typing import Any


def _select(options: list[tuple[str, str]], *, multiple: bool = False) -> dict[str, Any]:
    selector: dict[str, Any] = {
        "options": [{"label": label, "value": value} for value, label in options],
        "mode": "dropdown",
    }
    if multiple:
        selector["multiple"] = True
    return {"select": selector}


def _device_selector() -> dict[str, Any]:
    return {"device": {"filter": [{"integration": "animal_health"}]}}


def _text_selector(*, multiline: bool = False) -> dict[str, Any]:
    return {"text": {"multiline": True} if multiline else {}}


def _number_selector(*, minimum: int, maximum: int, step: int = 1) -> dict[str, Any]:
    return {
        "number": {
            "min": minimum,
            "max": maximum,
            "step": step,
            "mode": "box",
        }
    }


def _common_options(language: str) -> dict[str, list[tuple[str, str]]]:
    if language.startswith("de"):
        return {
            "scope_create": [("animal", "Tierbezogen"), ("general", "Allgemein")],
            "scope_filter": [
                ("all", "Alle"),
                ("animal", "Tierbezogen"),
                ("general", "Allgemein"),
            ],
            "recurrence": [
                ("once", "Einmalig"),
                ("daily", "Täglich"),
                ("weekly", "Wöchentlich"),
                ("monthly", "Monatlich"),
            ],
            "active": [
                ("all", "Alle"),
                ("active", "Aktiv"),
                ("inactive", "Inaktiv"),
            ],
            "status": [
                ("all", "Alle"),
                ("pending", "Offen"),
                ("completed", "Erledigt"),
                ("skipped", "Übersprungen"),
                ("cancelled", "Abgebrochen"),
            ],
        }
    return {
        "scope_create": [("animal", "Animal-specific"), ("general", "General")],
        "scope_filter": [
            ("all", "All"),
            ("animal", "Animal-specific"),
            ("general", "General"),
        ],
        "recurrence": [
            ("once", "Once"),
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
        "active": [
            ("all", "All"),
            ("active", "Active"),
            ("inactive", "Inactive"),
        ],
        "status": [
            ("all", "All"),
            ("pending", "Pending"),
            ("completed", "Completed"),
            ("skipped", "Skipped"),
            ("cancelled", "Cancelled"),
        ],
    }


def task_service_descriptions(language: str) -> dict[str, dict[str, Any]]:
    options = _common_options(language)
    if language.startswith("de"):
        return _german_descriptions(options)
    return _english_descriptions(options)


def _german_descriptions(options: dict[str, list[tuple[str, str]]]) -> dict[str, dict[str, Any]]:
    return {
        "create_task": {
            "name": "Aufgabe anlegen",
            "description": "Legt eine einmalige oder wiederkehrende Aufgabe für ein Tier oder den gesamten Bestand an.",
            "fields": {
                "task_scope": {
                    "name": "Aufgabenbereich",
                    "description": "Tierbezogene oder allgemeine Aufgabe.",
                    "default": "animal",
                    "selector": _select(options["scope_create"]),
                },
                "device_id": {
                    "name": "Tier",
                    "description": "Bei tierbezogenen Aufgaben das Tier auswählen. Bei allgemeinen Aufgaben leer lassen.",
                    "selector": _device_selector(),
                },
                "title": {
                    "name": "Titel",
                    "description": "Kurze Bezeichnung der Aufgabe.",
                    "required": True,
                    "selector": _text_selector(),
                },
                "description": {
                    "name": "Beschreibung",
                    "description": "Optionale nähere Angaben zur Aufgabe.",
                    "selector": _text_selector(multiline=True),
                },
                "recurrence_type": {
                    "name": "Wiederholung",
                    "description": "Einmalig, täglich, wöchentlich oder monatlich.",
                    "required": True,
                    "selector": _select(options["recurrence"]),
                },
                "recurrence_interval": {
                    "name": "Intervall",
                    "description": "Zum Beispiel 2 für alle zwei Tage oder alle zwei Wochen.",
                    "default": 1,
                    "selector": _number_selector(minimum=1, maximum=365),
                },
                "start_date": {
                    "name": "Startdatum",
                    "description": "Datum der ersten Fälligkeit.",
                    "required": True,
                    "selector": {"date": {}},
                },
                "end_date": {
                    "name": "Enddatum",
                    "description": "Optionales letztes Datum der Wiederholung.",
                    "selector": {"date": {}},
                },
                "due_time": {
                    "name": "Uhrzeit",
                    "description": "Optionale lokale Fälligkeitszeit. Ohne Uhrzeit gilt die Aufgabe für den ganzen Tag.",
                    "selector": {"time": {}},
                },
            },
        },
        "list_tasks": {
            "name": "Aufgaben auflisten",
            "description": "Gibt Aufgaben mit Status, nächster Fälligkeit und offenen Fälligkeiten zurück.",
            "fields": {
                "task_scope": {
                    "name": "Aufgabenbereich",
                    "default": "all",
                    "selector": _select(options["scope_filter"]),
                },
                "device_id": {
                    "name": "Tier",
                    "description": "Optional auf ein bestimmtes Tier filtern.",
                    "selector": _device_selector(),
                },
                "active_state": {
                    "name": "Aktivitätsstatus",
                    "default": "all",
                    "selector": _select(options["active"]),
                },
                "limit": {
                    "name": "Maximale Anzahl",
                    "default": 200,
                    "selector": _number_selector(minimum=1, maximum=500),
                },
            },
        },
        "list_due_tasks": {
            "name": "Fällige Aufgaben auflisten",
            "description": "Gibt alle offenen Fälligkeiten bis zum gewählten Datum zurück; überfällige Aufgaben sind eingeschlossen.",
            "fields": {
                "through_date": {
                    "name": "Bis Datum",
                    "description": "Ohne Angabe wird bis heute gesucht.",
                    "selector": {"date": {}},
                },
                "device_id": {
                    "name": "Tier",
                    "description": "Optional auf ein bestimmtes Tier filtern.",
                    "selector": _device_selector(),
                },
                "include_general": {
                    "name": "Allgemeine Aufgaben einschliessen",
                    "default": True,
                    "selector": {"boolean": {}},
                },
                "limit": {
                    "name": "Maximale Anzahl",
                    "default": 200,
                    "selector": _number_selector(minimum=1, maximum=500),
                },
            },
        },
        "list_task_occurrences": {
            "name": "Aufgabenfälligkeiten auflisten",
            "description": "Gibt geplante und bearbeitete Fälligkeiten innerhalb eines Zeitraums zurück.",
            "fields": {
                "task_id": {
                    "name": "Aufgaben-ID",
                    "description": "Optional auf eine bestimmte Aufgabe filtern.",
                    "selector": _text_selector(),
                },
                "task_scope": {
                    "name": "Aufgabenbereich",
                    "default": "all",
                    "selector": _select(options["scope_filter"]),
                },
                "device_id": {
                    "name": "Tier",
                    "description": "Optional auf ein bestimmtes Tier filtern.",
                    "selector": _device_selector(),
                },
                "include_general": {
                    "name": "Allgemeine Aufgaben einschliessen",
                    "default": True,
                    "selector": {"boolean": {}},
                },
                "status": {
                    "name": "Fälligkeitsstatus",
                    "default": "all",
                    "selector": _select(options["status"]),
                },
                "from_date": {
                    "name": "Von Datum",
                    "description": "Standardmässig 30 Tage vor heute.",
                    "selector": {"date": {}},
                },
                "to_date": {
                    "name": "Bis Datum",
                    "description": "Standardmässig 90 Tage nach heute.",
                    "selector": {"date": {}},
                },
                "limit": {
                    "name": "Maximale Anzahl",
                    "default": 200,
                    "selector": _number_selector(minimum=1, maximum=500),
                },
            },
        },
        "update_task": {
            "name": "Aufgabe bearbeiten",
            "description": "Ändert eine bestehende Aufgabe. Bereits erledigte, übersprungene oder abgebrochene Fälligkeiten bleiben erhalten.",
            "fields": {
                "task_id": {
                    "name": "Aufgaben-ID",
                    "required": True,
                    "selector": _text_selector(),
                },
                "task_scope": {
                    "name": "Aufgabenbereich",
                    "description": "Optional zwischen tierbezogen und allgemein wechseln.",
                    "selector": _select(options["scope_create"]),
                },
                "device_id": {
                    "name": "Tier",
                    "description": "Neues oder bisheriges Tier für eine tierbezogene Aufgabe.",
                    "selector": _device_selector(),
                },
                "title": {"name": "Titel", "selector": _text_selector()},
                "description": {
                    "name": "Beschreibung",
                    "description": "Leer übermitteln, um die Beschreibung zu entfernen.",
                    "selector": _text_selector(multiline=True),
                },
                "recurrence_type": {
                    "name": "Wiederholung",
                    "selector": _select(options["recurrence"]),
                },
                "recurrence_interval": {
                    "name": "Intervall",
                    "selector": _number_selector(minimum=1, maximum=365),
                },
                "start_date": {"name": "Startdatum", "selector": {"date": {}}},
                "end_date": {"name": "Enddatum", "selector": {"date": {}}},
                "clear_end_date": {
                    "name": "Enddatum entfernen",
                    "default": False,
                    "selector": {"boolean": {}},
                },
                "due_time": {"name": "Uhrzeit", "selector": {"time": {}}},
                "clear_due_time": {
                    "name": "Uhrzeit entfernen",
                    "default": False,
                    "selector": {"boolean": {}},
                },
            },
        },
        "set_task_active": {
            "name": "Aufgabe aktivieren oder deaktivieren",
            "description": "Pausiert oder reaktiviert eine Aufgabe, ohne bestehende Fälligkeiten oder den Verlauf zu löschen.",
            "fields": {
                "task_id": {
                    "name": "Aufgaben-ID",
                    "required": True,
                    "selector": _text_selector(),
                },
                "is_active": {
                    "name": "Aktiv",
                    "required": True,
                    "selector": {"boolean": {}},
                },
            },
        },
        "complete_task_occurrence": _occurrence_action_de(
            "Fälligkeit erledigen",
            "Markiert eine offene Aufgabenfälligkeit als erledigt.",
        ),
        "skip_task_occurrence": _occurrence_action_de(
            "Fälligkeit überspringen",
            "Markiert eine offene Aufgabenfälligkeit bewusst als übersprungen.",
        ),
        "cancel_task_occurrence": _occurrence_action_de(
            "Fälligkeit abbrechen",
            "Markiert eine offene Aufgabenfälligkeit als abgebrochen.",
        ),
    }


def _occurrence_action_de(name: str, description: str) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "fields": {
            "task_entity_ids": {
                "name": "Offene Aufgaben / Fälligkeiten",
                "description": (
                    "Eine oder mehrere offene Aufgaben auswählen. Pro Auswahl wird die früheste offene Fälligkeit verwendet."
                ),
                "required": False,
                "selector": {
                    "entity": {
                        "filter": [{"integration": "animal_health", "domain": "switch"}],
                        "multiple": True,
                    }
                },
            },
            "scheduled_date": {
                "name": "Fälligkeitsdatum",
                "description": "Optional auf ein bestimmtes Fälligkeitsdatum einschränken.",
                "selector": {"date": {}},
            },
            "occurrence_id": {
                "name": "Fälligkeits-ID (Automation)",
                "description": "Technische Alternative für bestehende Automationen.",
                "selector": _text_selector(),
            },
            "notes": {
                "name": "Notiz",
                "description": "Eine gemeinsame Notiz für alle ausgewählten Fälligkeiten.",
                "selector": _text_selector(multiline=True),
            },
        },
    }


def _english_descriptions(options: dict[str, list[tuple[str, str]]]) -> dict[str, dict[str, Any]]:
    return {
        "create_task": {
            "name": "Create task",
            "description": "Creates a one-off or recurring task for an animal or for the whole group.",
            "fields": {
                "task_scope": {
                    "name": "Task scope",
                    "description": "Animal-specific or general task.",
                    "default": "animal",
                    "selector": _select(options["scope_create"]),
                },
                "device_id": {
                    "name": "Animal",
                    "description": "Select an animal for animal-specific tasks. Leave empty for general tasks.",
                    "selector": _device_selector(),
                },
                "title": {
                    "name": "Title",
                    "required": True,
                    "selector": _text_selector(),
                },
                "description": {
                    "name": "Description",
                    "selector": _text_selector(multiline=True),
                },
                "recurrence_type": {
                    "name": "Recurrence",
                    "required": True,
                    "selector": _select(options["recurrence"]),
                },
                "recurrence_interval": {
                    "name": "Interval",
                    "description": "For example 2 for every two days or every two weeks.",
                    "default": 1,
                    "selector": _number_selector(minimum=1, maximum=365),
                },
                "start_date": {
                    "name": "Start date",
                    "description": "Date of the first occurrence.",
                    "required": True,
                    "selector": {"date": {}},
                },
                "end_date": {
                    "name": "End date",
                    "description": "Optional last recurrence date.",
                    "selector": {"date": {}},
                },
                "due_time": {
                    "name": "Due time",
                    "description": "Optional local due time. Without a time, the task is treated as an all-day task.",
                    "selector": {"time": {}},
                },
            },
        },
        "list_tasks": {
            "name": "List tasks",
            "description": "Returns tasks with their state, next occurrence and pending counts.",
            "fields": {
                "task_scope": {
                    "name": "Task scope",
                    "default": "all",
                    "selector": _select(options["scope_filter"]),
                },
                "device_id": {
                    "name": "Animal",
                    "description": "Optionally filter by animal.",
                    "selector": _device_selector(),
                },
                "active_state": {
                    "name": "Active state",
                    "default": "all",
                    "selector": _select(options["active"]),
                },
                "limit": {
                    "name": "Maximum results",
                    "default": 200,
                    "selector": _number_selector(minimum=1, maximum=500),
                },
            },
        },
        "list_due_tasks": {
            "name": "List due tasks",
            "description": "Returns pending occurrences through the selected date, including overdue tasks.",
            "fields": {
                "through_date": {
                    "name": "Through date",
                    "description": "Defaults to today.",
                    "selector": {"date": {}},
                },
                "device_id": {
                    "name": "Animal",
                    "description": "Optionally filter by animal.",
                    "selector": _device_selector(),
                },
                "include_general": {
                    "name": "Include general tasks",
                    "default": True,
                    "selector": {"boolean": {}},
                },
                "limit": {
                    "name": "Maximum results",
                    "default": 200,
                    "selector": _number_selector(minimum=1, maximum=500),
                },
            },
        },
        "list_task_occurrences": {
            "name": "List task occurrences",
            "description": "Returns planned and processed task occurrences within a date range.",
            "fields": {
                "task_id": {
                    "name": "Task ID",
                    "description": "Optionally filter by task.",
                    "selector": _text_selector(),
                },
                "task_scope": {
                    "name": "Task scope",
                    "default": "all",
                    "selector": _select(options["scope_filter"]),
                },
                "device_id": {
                    "name": "Animal",
                    "description": "Optionally filter by animal.",
                    "selector": _device_selector(),
                },
                "include_general": {
                    "name": "Include general tasks",
                    "default": True,
                    "selector": {"boolean": {}},
                },
                "status": {
                    "name": "Occurrence status",
                    "default": "all",
                    "selector": _select(options["status"]),
                },
                "from_date": {
                    "name": "From date",
                    "description": "Defaults to 30 days before today.",
                    "selector": {"date": {}},
                },
                "to_date": {
                    "name": "To date",
                    "description": "Defaults to 90 days after today.",
                    "selector": {"date": {}},
                },
                "limit": {
                    "name": "Maximum results",
                    "default": 200,
                    "selector": _number_selector(minimum=1, maximum=500),
                },
            },
        },
        "update_task": {
            "name": "Update task",
            "description": "Updates a task. Completed, skipped and cancelled occurrences remain unchanged.",
            "fields": {
                "task_id": {
                    "name": "Task ID",
                    "required": True,
                    "selector": _text_selector(),
                },
                "task_scope": {
                    "name": "Task scope",
                    "selector": _select(options["scope_create"]),
                },
                "device_id": {
                    "name": "Animal",
                    "selector": _device_selector(),
                },
                "title": {"name": "Title", "selector": _text_selector()},
                "description": {
                    "name": "Description",
                    "description": "Submit an empty value to clear it.",
                    "selector": _text_selector(multiline=True),
                },
                "recurrence_type": {
                    "name": "Recurrence",
                    "selector": _select(options["recurrence"]),
                },
                "recurrence_interval": {
                    "name": "Interval",
                    "selector": _number_selector(minimum=1, maximum=365),
                },
                "start_date": {"name": "Start date", "selector": {"date": {}}},
                "end_date": {"name": "End date", "selector": {"date": {}}},
                "clear_end_date": {
                    "name": "Clear end date",
                    "default": False,
                    "selector": {"boolean": {}},
                },
                "due_time": {"name": "Due time", "selector": {"time": {}}},
                "clear_due_time": {
                    "name": "Clear due time",
                    "default": False,
                    "selector": {"boolean": {}},
                },
            },
        },
        "set_task_active": {
            "name": "Activate or deactivate task",
            "description": "Pauses or reactivates a task without deleting its occurrences or history.",
            "fields": {
                "task_id": {
                    "name": "Task ID",
                    "required": True,
                    "selector": _text_selector(),
                },
                "is_active": {
                    "name": "Active",
                    "required": True,
                    "selector": {"boolean": {}},
                },
            },
        },
        "complete_task_occurrence": _occurrence_action_en(
            "Complete occurrence",
            "Marks a pending task occurrence as completed.",
        ),
        "skip_task_occurrence": _occurrence_action_en(
            "Skip occurrence",
            "Marks a pending task occurrence as intentionally skipped.",
        ),
        "cancel_task_occurrence": _occurrence_action_en(
            "Cancel occurrence",
            "Marks a pending task occurrence as cancelled.",
        ),
    }


def _occurrence_action_en(name: str, description: str) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "fields": {
            "task_entity_ids": {
                "name": "Open tasks / occurrences",
                "description": "Select one or more open tasks; the earliest open occurrence is used for each.",
                "selector": {
                    "entity": {
                        "filter": [{"integration": "animal_health", "domain": "switch"}],
                        "multiple": True,
                    }
                },
            },
            "scheduled_date": {
                "name": "Scheduled date",
                "description": "Optionally restrict selection to a date.",
                "selector": {"date": {}},
            },
            "occurrence_id": {
                "name": "Occurrence ID (automation)",
                "description": "Technical alternative for existing automations.",
                "selector": _text_selector(),
            },
            "notes": {
                "name": "Notes",
                "description": "One shared note for all selected occurrences.",
                "selector": _text_selector(multiline=True),
            },
        },
    }
