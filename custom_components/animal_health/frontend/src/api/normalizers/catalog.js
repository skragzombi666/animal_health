import { asArray, asRecord, camelizeObject, firstDefined, stringList } from "./common.js";

function objectList(value, path) {
  return asArray(value, path).map((item, index) =>
    camelizeObject(asRecord(item, `${path}[${index}]`)),
  );
}

export function normalizeCatalog(rawValue) {
  const raw = asRecord(rawValue, "catalog");
  return {
    animalStatuses: stringList(firstDefined(raw, ["animal_statuses", "animalStatuses"], [])),
    animalSexes: stringList(firstDefined(raw, ["animal_sexes", "animalSexes"], [])),
    eventTypes: stringList(firstDefined(raw, ["event_types", "eventTypes"], [])),
    weightUnits: stringList(firstDefined(raw, ["weight_units", "weightUnits"], [])),
    doseUnits: stringList(firstDefined(raw, ["dose_units", "doseUnits"], [])),
    administrationRoutes: stringList(
      firstDefined(raw, ["administration_routes", "administrationRoutes"], []),
    ),
    symptoms: stringList(firstDefined(raw, ["symptoms"], [])),
    symptomSeverities: stringList(
      firstDefined(raw, ["symptom_severities", "symptomSeverities"], []),
    ),
    vaccinationTargets: stringList(
      firstDefined(raw, ["vaccination_targets", "vaccinationTargets"], []),
    ),
    taskKinds: stringList(firstDefined(raw, ["task_kinds", "taskKinds"], [])),
    healthCheckResults: stringList(
      firstDefined(raw, ["health_check_results", "healthCheckResults"], []),
    ),
    medicineNames: stringList(
      firstDefined(raw, ["medicine_names", "medicineNames"], []),
    ),
    vaccineNames: stringList(
      firstDefined(raw, ["vaccine_names", "vaccineNames"], []),
    ),
    species: objectList(firstDefined(raw, ["species"], []), "catalog.species"),
    breeds: objectList(firstDefined(raw, ["breeds"], []), "catalog.breeds"),
  };
}
