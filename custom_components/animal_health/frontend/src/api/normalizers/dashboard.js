import { normalizeAnimal, normalizeAttachment } from "./animals.js";
import { normalizeCatalog } from "./catalog.js";
import {
  asArray,
  asRecord,
  dateOnly,
  dateTime,
  firstDefined,
  integerValue,
  optionalText,
  requiredText,
} from "./common.js";
import { normalizeFeatureState } from "./features.js";
import { normalizeTaskDefinition, normalizeTaskOccurrence } from "./tasks.js";
import { normalizeHealthEvent } from "./timeline.js";

function animalMetadata(featureState, animalId) {
  if (!featureState) return {};
  return {
    groupId: featureState.memberships?.[animalId] || null,
    tagIds: featureState.tagMemberships?.[animalId] || [],
    profileAttachmentId: featureState.profiles?.[animalId] || null,
  };
}

function normalizeSummary(value) {
  const raw = value == null ? {} : asRecord(value, "dashboard.summary");
  return {
    activeAnimals: integerValue(firstDefined(raw, ["active_animals", "activeAnimals"]), 0),
    archivedAnimals: integerValue(firstDefined(raw, ["archived_animals", "archivedAnimals"]), 0),
    pendingTasks: integerValue(firstDefined(raw, ["pending_tasks", "pendingTasks"]), 0),
    overdueTasks: integerValue(firstDefined(raw, ["overdue_tasks", "overdueTasks"]), 0),
    todayTasks: integerValue(firstDefined(raw, ["today_tasks", "todayTasks"]), 0),
    upcomingTasks: integerValue(firstDefined(raw, ["upcoming_tasks", "upcomingTasks"]), 0),
  };
}

function taskIndex(tasks) {
  return Object.fromEntries(tasks.map((task) => [task.id, task]));
}

function attachmentIndex(attachments) {
  const result = {};
  for (const attachment of attachments) {
    if (!attachment.eventId) continue;
    (result[attachment.eventId] ||= []).push(attachment);
  }
  return result;
}

export function normalizeDashboard(
  rawValue,
  { featureState = null, today = null } = {},
) {
  const raw = asRecord(rawValue, "dashboard");
  const localToday = dateOnly(firstDefined(raw, ["today"], today), "dashboard.today");
  const tasks = asArray(raw.tasks, "dashboard.tasks").map(normalizeTaskDefinition);
  const byId = taskIndex(tasks);
  return {
    version: requiredText(raw.version, "dashboard.version"),
    generatedAt: dateTime(
      firstDefined(raw, ["generated_at", "generatedAt"]),
      "dashboard.generatedAt",
    ),
    timeZone: optionalText(firstDefined(raw, ["time_zone", "timeZone"])),
    today: localToday,
    summary: normalizeSummary(raw.summary),
    animals: asArray(raw.animals, "dashboard.animals").map((animal) => {
      const id = requiredText(firstDefined(animal, ["id", "animal_id", "animalId"]), "animal.id");
      return normalizeAnimal(animal, animalMetadata(featureState, id));
    }),
    tasks,
    occurrences: asArray(raw.occurrences, "dashboard.occurrences").map((occurrence) =>
      normalizeTaskOccurrence(occurrence, { taskById: byId, today: localToday }),
    ),
    events: asArray(raw.events, "dashboard.events").map((event) =>
      normalizeHealthEvent(event),
    ),
  };
}

export function normalizeAnimalDetail(
  rawValue,
  { featureState = null, today = null } = {},
) {
  const raw = asRecord(rawValue, "animalDetail");
  const attachments = asArray(raw.attachments, "animalDetail.attachments").map(
    normalizeAttachment,
  );
  const attachmentsByEventId = attachmentIndex(attachments);
  const tasks = asArray(raw.tasks, "animalDetail.tasks").map(normalizeTaskDefinition);
  const byId = taskIndex(tasks);
  const animalRaw = asRecord(raw.animal, "animalDetail.animal");
  const animalId = requiredText(
    firstDefined(animalRaw, ["id", "animal_id", "animalId"]),
    "animal.id",
  );
  return {
    version: requiredText(raw.version, "animalDetail.version"),
    animal: normalizeAnimal(animalRaw, animalMetadata(featureState, animalId)),
    tasks,
    occurrences: asArray(raw.occurrences, "animalDetail.occurrences").map((occurrence) =>
      normalizeTaskOccurrence(occurrence, { taskById: byId, today }),
    ),
    events: asArray(raw.events, "animalDetail.events").map((event) =>
      normalizeHealthEvent(event, { attachmentsByEventId }),
    ),
    attachments,
  };
}

export function normalizeAnimalDirectory({
  dashboard,
  catalog,
  features,
  tagState,
}) {
  const featureState = normalizeFeatureState(features, tagState);
  const normalizedDashboard = normalizeDashboard(dashboard, { featureState });
  return {
    ...normalizedDashboard,
    groups: featureState.groups,
    tags: featureState.tags,
    memberships: featureState.memberships,
    tagMemberships: featureState.tagMemberships,
    profiles: featureState.profiles,
    exports: featureState.exports,
    storage: featureState.storage,
    maxAttachmentSizeBytes: featureState.maxAttachmentSizeBytes,
    primaryGroupRequired: featureState.primaryGroupRequired,
    catalog: normalizeCatalog(catalog),
  };
}
