import {
  asArray,
  asRecord,
  dateTime,
  firstDefined,
  numberValue,
  optionalText,
  requiredText,
} from "./common.js";

export function normalizeTreatmentComponent(rawValue) {
  const raw = asRecord(rawValue, "treatmentComponent");
  return {
    type: requiredText(raw.type, "treatmentComponent.type"),
    name: requiredText(raw.name, "treatmentComponent.name"),
    dose: numberValue(raw.dose, null, "treatmentComponent.dose"),
    unit: optionalText(raw.unit),
    route: optionalText(raw.route),
    instructions: optionalText(raw.instructions),
  };
}

export function normalizeTreatmentPlan(rawValue) {
  const raw = asRecord(rawValue, "treatmentPlan");
  return {
    id: requiredText(firstDefined(raw, ["id", "plan_id", "planId"]), "treatmentPlan.id"),
    name: requiredText(firstDefined(raw, ["name", "title"]), "treatmentPlan.name"),
    speciesId: optionalText(firstDefined(raw, ["species_id", "speciesId"])),
    listAs: optionalText(firstDefined(raw, ["list_as", "listAs"])),
    description: optionalText(raw.description),
    defaultUnit: optionalText(firstDefined(raw, ["default_unit", "defaultUnit"])),
    defaultRoute: optionalText(firstDefined(raw, ["default_route", "defaultRoute"])),
    components: asArray(raw.components, "treatmentPlan.components").map(
      normalizeTreatmentComponent,
    ),
  };
}

export function normalizeStatusChange(rawValue) {
  const raw = asRecord(rawValue, "statusChange");
  return {
    id: requiredText(firstDefined(raw, ["id", "status_change_id", "statusChangeId"]), "statusChange.id"),
    animalId: requiredText(firstDefined(raw, ["animal_id", "animalId"]), "statusChange.animalId"),
    animalName: optionalText(firstDefined(raw, ["animal_name", "animalName"])),
    targetStatus: requiredText(
      firstDefined(raw, ["target_status", "targetStatus"]),
      "statusChange.targetStatus",
    ),
    plannedFor: dateTime(
      firstDefined(raw, ["planned_for", "plannedFor"]),
      "statusChange.plannedFor",
    ),
    state: requiredText(firstDefined(raw, ["state"], "scheduled"), "statusChange.state"),
    notes: optionalText(raw.notes),
    createdAt: dateTime(firstDefined(raw, ["created_at", "createdAt"]), "statusChange.createdAt"),
    updatedAt: dateTime(firstDefined(raw, ["updated_at", "updatedAt"]), "statusChange.updatedAt"),
    resolvedAt: dateTime(firstDefined(raw, ["resolved_at", "resolvedAt"]), "statusChange.resolvedAt"),
  };
}

export function normalizeTreatmentState(rawValue) {
  const raw = asRecord(rawValue, "treatmentState");
  return {
    offLabelMode: optionalText(
      firstDefined(raw, ["off_label_mode", "offLabelMode"]),
    ),
    treatmentPlans: asArray(
      firstDefined(raw, ["treatment_plans", "treatmentPlans"], []),
      "treatmentState.treatmentPlans",
    ).map(normalizeTreatmentPlan),
    statusChanges: asArray(
      firstDefined(raw, ["status_changes", "statusChanges"], []),
      "treatmentState.statusChanges",
    ).map(normalizeStatusChange),
  };
}
