import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { ERROR_CODES } from "../../custom_components/animal_health/frontend/src/api/errors.js";
import {
  dateOnly,
  normalizeAnimalDetail,
  normalizeAnimalDirectory,
  normalizeHealthEvent,
  normalizeProduct,
  normalizeProductState,
  normalizeSettingsState,
  normalizeTaskDefinition,
  normalizeTaskOccurrence,
} from "../../custom_components/animal_health/frontend/src/api/normalizers/index.js";

const fixture = JSON.parse(
  await readFile(
    new URL("./fixtures/phase2-snapshots-0.9.41.json", import.meta.url),
    "utf8",
  ),
);

test("date-only normalization preserves calendar text without timezone conversion", () => {
  assert.equal(dateOnly("2026-09-04", "animal.birthDate"), "2026-09-04");
  assert.equal(dateOnly(null, "animal.birthDate"), null);
  assert.throws(
    () => dateOnly("04.09.2026", "animal.birthDate"),
    (error) =>
      error.code === ERROR_CODES.VALIDATION &&
      error.details.path === "animal.birthDate",
  );
});

test("animal directory merges groups tags profiles and keeps canonical camelCase", () => {
  const result = normalizeAnimalDirectory({
    dashboard: fixture.dashboard,
    catalog: fixture.catalog,
    features: fixture.features,
    tagState: fixture.tagState,
  });

  assert.equal(result.version, "0.9.41");
  assert.equal(result.timeZone, "Europe/Zurich");
  assert.equal(result.today, "2026-09-04");
  assert.deepEqual(result.summary, {
    activeAnimals: 1,
    archivedAnimals: 0,
    pendingTasks: 2,
    overdueTasks: 1,
    todayTasks: 1,
    upcomingTasks: 0,
  });
  assert.equal(result.animals.length, 1);
  assert.deepEqual(result.animals[0], {
    id: "AH-CHICKEN-1",
    name: "Tartar",
    species: "chicken",
    breed: "Hybrid",
    color: "Braun",
    sex: "female",
    birthDate: "2024-03-18",
    arrivalDate: "2026-07-24",
    status: "active",
    statusChangedAt: "2026-07-24T08:30:00+00:00",
    isArchived: false,
    archivedAt: null,
    createdAt: "2026-07-24T08:30:00+00:00",
    updatedAt: "2026-09-04T10:00:00+00:00",
    deviceId: "device-tartar",
    latestWeight: {
      eventId: "EV-WEIGHT-1",
      valueKg: 1.25,
      originalValue: 1250,
      originalUnit: "g",
      occurredAt: "2026-09-03T07:15:00+00:00",
    },
    groupId: "GR-FLOCK",
    tagIds: ["TG-RESCUE"],
    profileAttachmentId: "ATT-PROFILE",
  });
  assert.equal(result.groups[0].animalCount, 1);
  assert.equal(result.tags[0].name, "Ehemalige Legehenne");
  assert.equal(result.catalog.species[0].nameDe, "Huhn");
  assert.equal(result.exports.animalPdf.includes("{animal_id}"), true);
  assert.equal(fixture.dashboard.animals[0].groupId, undefined);
});

test("task definitions and concrete occurrences remain separate", () => {
  const task = normalizeTaskDefinition(fixture.dashboard.tasks[0]);
  const taskById = { [task.id]: task };
  const overdue = normalizeTaskOccurrence(fixture.dashboard.occurrences[0], {
    taskById,
    today: "2026-09-04",
  });
  const today = normalizeTaskOccurrence(fixture.dashboard.occurrences[1], {
    taskById,
    today: "2026-09-04",
  });
  const upcomingRaw = {
    ...fixture.dashboard.occurrences[1],
    id: "OCC-20260905",
    scheduled_date: "2026-09-05",
    scheduled_for: "2026-09-05T06:00:00+00:00",
    scheduled_local: "2026-09-05T08:00:00+02:00",
  };
  delete upcomingRaw.is_overdue;
  delete upcomingRaw.is_today;
  delete upcomingRaw.is_upcoming;
  const upcoming = normalizeTaskOccurrence(upcomingRaw, {
    taskById,
    today: "2026-09-04",
  });
  const closed = normalizeTaskOccurrence(
    { ...upcomingRaw, id: "OCC-CLOSED", status: "completed" },
    { taskById, today: "2026-09-04" },
  );

  assert.equal(task.id, "TASK-MED-1");
  assert.equal(task.seriesId, "TASK-MED-1");
  assert.equal(task.kind, "medication");
  assert.equal(task.planned.medicationName, "Meloxidyl");
  assert.equal(overdue.id, "OCC-20260903");
  assert.equal(overdue.definitionId, "TASK-MED-1");
  assert.equal(overdue.seriesId, "TASK-MED-1");
  assert.equal(overdue.timing, "overdue");
  assert.equal(today.timing, "today");
  assert.equal(upcoming.timing, "upcoming");
  assert.equal(closed.timing, "closed");
  assert.equal(overdue.planned.doseUnit, "ml");
  assert.notEqual(overdue.id, today.id);
});

test("one-time task definitions do not invent a series identifier", () => {
  const task = normalizeTaskDefinition({
    ...fixture.dashboard.tasks[0],
    id: "TASK-ONCE",
    recurrence_type: "once",
    series_id: undefined,
  });
  assert.equal(task.seriesId, null);
});

test("health events preserve payload and expose task origin metadata", () => {
  const event = normalizeHealthEvent(fixture.dashboard.events[0], {
    attachmentsByEventId: {
      "EV-MED-1": fixture.animalDetail.attachments,
    },
  });

  assert.equal(event.type, "medication");
  assert.equal(event.source.kind, "task");
  assert.equal(event.source.taskId, "TASK-MED-1");
  assert.equal(event.source.occurrenceId, "OCC-20260903");
  assert.equal(event.payload.medicationName, "Meloxidyl");
  assert.equal(event.payload.doseUnit, "ml");
  assert.equal(event.attachments[0].mediaType, "image/jpeg");
});

test("animal detail associates attachments with events", () => {
  const detail = normalizeAnimalDetail(fixture.animalDetail, {
    today: "2026-09-04",
  });
  assert.equal(detail.animal.id, "AH-CHICKEN-1");
  assert.equal(detail.events[0].attachments[0].id, "ATT-EVENT-1");
  assert.equal(detail.occurrences[0].timing, "overdue");
});

test("product normalization keeps source and a non-recursive original snapshot", () => {
  const state = normalizeProductState(fixture.productState);
  const official = state.products[0];

  assert.equal(state.databases[0].sourceName, "Swissmedic");
  assert.equal(state.databases[0].dataAsOf, "2026-09-01");
  assert.equal(official.databaseId, "swissmedic_ch");
  assert.equal(official.isModified, true);
  assert.equal(official.original.name, "Meloxidyl");
  assert.equal(official.original.original, undefined);
  assert.deepEqual(state.views, {
    dewormingDatabaseId: "swissmedic_dewormers",
    swissmedicDatabaseId: "swissmedic_ch",
  });
});

test("catalog originals inherit source identity omitted by the current backend snapshot", () => {
  const product = normalizeProduct({
    id: "swissmedic_ch:56764",
    database_id: "swissmedic_ch",
    kind: "medication",
    name: "Meloxidyl angepasst",
    original: {
      id: "56764",
      source_id: "swissmedic_ch",
      name: "Meloxidyl",
      target_species: ["chicken"],
    },
  });

  assert.equal(product.original.databaseId, "swissmedic_ch");
  assert.equal(product.original.kind, "medication");
  assert.equal(product.original.name, "Meloxidyl");
  assert.equal(product.original.original, undefined);
});

test("settings normalization combines treatment and master-data state", () => {
  const settings = normalizeSettingsState(
    fixture.treatmentState,
    fixture.masterDataState,
  );

  assert.equal(settings.offLabelMode, "show_marked");
  assert.equal(settings.treatmentPlans[0].components[0].dose, 0.2);
  assert.equal(settings.treatmentPlans[0].components[1].type, "action");
  assert.equal(settings.statusChanges[0].targetStatus, "deceased");
  assert.equal(settings.entryTypes[0].isModified, true);
  assert.equal(settings.symptoms[0].storageValue, "diarrhea");
});

test("required canonical identifiers report their field path", () => {
  assert.throws(
    () => normalizeTaskDefinition({ title: "Ungültig" }),
    (error) =>
      error.code === ERROR_CODES.VALIDATION &&
      error.details.path === "task.id",
  );
});
