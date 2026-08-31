from __future__ import annotations

TASK_KIND_REMINDER = "reminder"
TASK_KIND_WEIGHT = "weight"
TASK_KIND_MEDICATION = "medication"
TASK_KIND_VACCINATION = "vaccination"
TASK_KIND_DEWORMING = "deworming"
TASK_KIND_SUPPLEMENT = "supplement"
TASK_KIND_FEED = "feed"
TASK_KIND_TREATMENT = "treatment"
TASK_KIND_HEALTH_CHECK = "health_check"
TASK_KIND_CARE = "care"
TASK_KIND_VETERINARY_VISIT = "veterinary_visit"

TASK_KINDS = (
    TASK_KIND_REMINDER,
    TASK_KIND_WEIGHT,
    TASK_KIND_MEDICATION,
    TASK_KIND_VACCINATION,
    TASK_KIND_DEWORMING,
    TASK_KIND_SUPPLEMENT,
    TASK_KIND_FEED,
    TASK_KIND_TREATMENT,
    TASK_KIND_HEALTH_CHECK,
    TASK_KIND_CARE,
    TASK_KIND_VETERINARY_VISIT,
)

TASK_KIND_LABELS_DE = {
    TASK_KIND_REMINDER: "Erinnerung",
    TASK_KIND_WEIGHT: "Gewicht",
    TASK_KIND_MEDICATION: "Medikament",
    TASK_KIND_VACCINATION: "Impfung",
    TASK_KIND_DEWORMING: "Entwurmung",
    TASK_KIND_SUPPLEMENT: "Ergänzung",
    TASK_KIND_FEED: "Futter",
    TASK_KIND_TREATMENT: "Behandlung",
    TASK_KIND_HEALTH_CHECK: "Gesundheitskontrolle",
    TASK_KIND_CARE: "Pflege",
    TASK_KIND_VETERINARY_VISIT: "Tierarztbesuch",
}

TASK_KIND_LABELS_EN = {
    TASK_KIND_REMINDER: "Reminder",
    TASK_KIND_WEIGHT: "Weight",
    TASK_KIND_MEDICATION: "Medication",
    TASK_KIND_VACCINATION: "Vaccination",
    TASK_KIND_DEWORMING: "Deworming",
    TASK_KIND_SUPPLEMENT: "Supplement",
    TASK_KIND_FEED: "Feed",
    TASK_KIND_TREATMENT: "Treatment",
    TASK_KIND_HEALTH_CHECK: "Health check",
    TASK_KIND_CARE: "Care",
    TASK_KIND_VETERINARY_VISIT: "Veterinary visit",
}

TASK_KIND_ICONS = {
    TASK_KIND_REMINDER: "mdi:bell-outline",
    TASK_KIND_WEIGHT: "mdi:scale-bathroom",
    TASK_KIND_MEDICATION: "mdi:pill",
    TASK_KIND_VACCINATION: "mdi:needle",
    TASK_KIND_DEWORMING: "mdi:bug-outline",
    TASK_KIND_SUPPLEMENT: "mdi:leaf-circle-outline",
    TASK_KIND_FEED: "mdi:food-apple-outline",
    TASK_KIND_TREATMENT: "mdi:medical-bag",
    TASK_KIND_HEALTH_CHECK: "mdi:stethoscope",
    TASK_KIND_CARE: "mdi:hand-heart",
    TASK_KIND_VETERINARY_VISIT: "mdi:hospital-box-outline",
}
