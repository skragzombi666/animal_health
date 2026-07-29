from __future__ import annotations

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

_TASK_KIND_LABELS = {
    "de": {
        TASK_KIND_REMINDER: "Erinnerung",
        TASK_KIND_WEIGHT: "Gewicht",
        TASK_KIND_MEDICATION: "Medikament",
        TASK_KIND_VACCINATION: "Impfung",
        TASK_KIND_HEALTH_CHECK: "Gesundheitskontrolle",
        TASK_KIND_CARE: "Pflege",
        TASK_KIND_VETERINARY_VISIT: "Tierarztbesuch",
    },
    "en": {
        TASK_KIND_REMINDER: "Reminder",
        TASK_KIND_WEIGHT: "Weight",
        TASK_KIND_MEDICATION: "Medication",
        TASK_KIND_VACCINATION: "Vaccination",
        TASK_KIND_HEALTH_CHECK: "Health check",
        TASK_KIND_CARE: "Care",
        TASK_KIND_VETERINARY_VISIT: "Veterinary visit",
    },
}

TASK_KIND_ICONS = {
    TASK_KIND_REMINDER: "mdi:calendar-clock",
    TASK_KIND_WEIGHT: "mdi:scale",
    TASK_KIND_MEDICATION: "mdi:pill",
    TASK_KIND_VACCINATION: "mdi:needle",
    TASK_KIND_HEALTH_CHECK: "mdi:stethoscope",
    TASK_KIND_CARE: "mdi:hand-heart",
    TASK_KIND_VETERINARY_VISIT: "mdi:hospital-box-outline",
}

_GERMAN_COUNTRIES = {"AT", "CH", "DE", "LI"}


def task_language(language: str | None, country: str | None = None) -> str:
    """Return the task UI language for the Home Assistant installation."""
    configured_language = (language or "").casefold()
    if configured_language:
        return "de" if configured_language.startswith("de") else "en"
    return "de" if (country or "").upper() in _GERMAN_COUNTRIES else "en"


def task_kind_label(task_kind: str, language: str = "en") -> str:
    """Return a human-readable task kind label."""
    labels = _TASK_KIND_LABELS["de" if language.startswith("de") else "en"]
    return labels.get(task_kind, task_kind.replace("_", " ").title())


def task_display_name(
    title: str,
    task_kind: str,
    task_id: str,
    language: str = "en",
) -> str:
    """Build an unambiguous task entity name for Home Assistant selectors."""
    return f"{title} · {task_kind_label(task_kind, language)} · {task_id}"
