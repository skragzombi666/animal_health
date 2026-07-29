from __future__ import annotations

import json
from pathlib import Path


INTEGRATION_DIR = (
    Path(__file__).parents[1] / "custom_components" / "animal_health"
)

TASK_SERVICE_FIELDS = {
    "create_task": {
        "task_scope",
        "device_ids",
        "title",
        "description",
        "recurrence_type",
        "recurrence_interval",
        "start_date",
        "end_date",
        "due_time",
    },
    "list_tasks": {"task_scope", "device_id", "active_state", "limit"},
    "list_due_tasks": {
        "through_date",
        "device_ids",
        "include_general",
        "limit",
    },
    "list_task_occurrences": {
        "task_id",
        "task_scope",
        "device_id",
        "include_general",
        "status",
        "from_date",
        "to_date",
        "limit",
    },
    "update_task": {
        "task_id",
        "task_scope",
        "device_id",
        "title",
        "description",
        "recurrence_type",
        "recurrence_interval",
        "start_date",
        "end_date",
        "clear_end_date",
        "due_time",
        "clear_due_time",
    },
    "set_task_active": {"entity_ids", "is_active"},
    "complete_task_occurrence": {
        "task_entity_ids",
        "scheduled_date",
        "occurrence_id",
        "notes",
    },
    "skip_task_occurrence": {
        "task_entity_ids",
        "scheduled_date",
        "occurrence_id",
        "notes",
    },
    "cancel_task_occurrence": {
        "task_entity_ids",
        "scheduled_date",
        "occurrence_id",
        "notes",
    },
    "create_record_task": {
        "task_scope",
        "device_ids",
        "task_kind",
        "title",
        "description",
        "recurrence_type",
        "recurrence_interval",
        "start_date",
        "end_date",
        "due_time",
        "planned_medication_name",
        "planned_dose",
        "planned_dose_unit",
        "planned_route",
        "planned_vaccination_targets",
        "planned_custom_vaccination_target",
        "planned_vaccine_name",
        "planned_antigen",
        "planned_vaccination_dose",
        "planned_vaccination_dose_unit",
        "planned_vaccination_route",
        "planned_check_focus",
        "planned_care_action",
        "planned_visit_reason",
        "planned_provider",
    },
    "record_task_reminder": {
        "task_entity_id",
        "scheduled_date",
        "occurrence_id",
        "performed_at",
        "deviation_reason",
        "notes",
    },
    "record_task_weight": {
        "task_entity_id",
        "scheduled_date",
        "occurrence_id",
        "performed_at",
        "weight",
        "weight_unit",
        "deviation_reason",
        "notes",
    },
    "record_task_medication": {
        "task_entity_id",
        "scheduled_date",
        "occurrence_id",
        "performed_at",
        "medication_name",
        "dose",
        "dose_unit",
        "route",
        "deviation_reason",
        "notes",
    },
    "record_task_vaccination": {
        "task_entity_id",
        "scheduled_date",
        "occurrence_id",
        "performed_at",
        "vaccination_targets",
        "custom_vaccination_target",
        "vaccine_name",
        "antigen",
        "dose",
        "dose_unit",
        "route",
        "batch_number",
        "deviation_reason",
        "notes",
    },
    "record_task_health_check": {
        "task_entity_id",
        "scheduled_date",
        "occurrence_id",
        "performed_at",
        "check_result",
        "symptom",
        "custom_symptom",
        "severity",
        "deviation_reason",
        "notes",
    },
    "record_task_care": {
        "task_entity_id",
        "scheduled_date",
        "occurrence_id",
        "performed_at",
        "care_action",
        "outcome",
        "deviation_reason",
        "notes",
    },
    "record_task_veterinary_visit": {
        "task_entity_id",
        "scheduled_date",
        "occurrence_id",
        "performed_at",
        "visit_reason",
        "provider",
        "diagnosis",
        "deviation_reason",
        "notes",
    },
}


def _load(relative_path: str) -> dict:
    with (INTEGRATION_DIR / relative_path).open(encoding="utf-8") as file:
        return json.load(file)


def test_all_task_services_and_fields_are_fully_translated() -> None:
    for relative_path in (
        "strings.json",
        "translations/de.json",
        "translations/en.json",
    ):
        services = _load(relative_path)["services"]
        for service_name, expected_fields in TASK_SERVICE_FIELDS.items():
            assert service_name in services, (
                f"{relative_path}: missing task service {service_name}"
            )
            service = services[service_name]
            assert service.get("name")
            assert service.get("description")
            assert set(service.get("fields", {})) == expected_fields
            for field_name, field in service["fields"].items():
                assert field.get("name"), (
                    f"{relative_path}: {service_name}.{field_name} has no name"
                )
                assert field.get("description"), (
                    f"{relative_path}: {service_name}.{field_name} "
                    "has no description"
                )


def test_custom_component_english_translation_matches_strings_source() -> None:
    assert _load("translations/en.json")["services"] == _load("strings.json")[
        "services"
    ]


def test_german_task_service_names_are_not_english_fallbacks() -> None:
    german = _load("translations/de.json")["services"]
    assert german["create_record_task"]["name"] == "Strukturierte Aufgabe anlegen"
    assert german["record_task_weight"]["name"] == "Gewichtsaufgabe ausführen"
    assert german["record_task_medication"]["fields"]["medication_name"][
        "name"
    ] == "Tatsächliches Medikament"
    assert german["record_task_vaccination"]["fields"]["vaccine_name"][
        "name"
    ] == "Tatsächlicher Impfstoff"


def test_task_exceptions_are_complete_and_translatable() -> None:
    english = _load("strings.json")["exceptions"]
    translated_english = _load("translations/en.json")["exceptions"]
    german = _load("translations/de.json")["exceptions"]

    assert english == translated_english
    assert set(english) == set(german)
    assert english["general_task_requires_reminder"]["message"]
    assert german["general_task_requires_reminder"]["message"] == (
        "Als allgemeine Aufgabe kann nur eine Erinnerung angelegt werden."
    )
    for task_kind in (
        "reminder",
        "weight",
        "medication",
        "vaccination",
        "health_check",
        "care",
        "veterinary_visit",
    ):
        key = f"wrong_task_kind_{task_kind}"
        assert english[key]["message"]
        assert german[key]["message"]


def main() -> None:
    test_all_task_services_and_fields_are_fully_translated()
    test_custom_component_english_translation_matches_strings_source()
    test_german_task_service_names_are_not_english_fallbacks()
    test_task_exceptions_are_complete_and_translatable()
    print("Task service translations validated")


if __name__ == "__main__":
    main()
