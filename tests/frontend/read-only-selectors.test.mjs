import assert from "node:assert/strict";
import test from "node:test";

import {
  selectAnimalById,
  selectGroupById,
  selectGroupedAnimals,
  selectNextOccurrenceForAnimal,
  selectOpenOccurrencesForAnimal,
  selectRecentEvents,
  selectUrgentOccurrences,
  selectVisibleAnimals,
} from "../../custom_components/animal_health/frontend/src/domain/animals/selectors.js";

function state(overrides = {}) {
  return {
    animals: {
      items: [
        {
          id: "A-2",
          name: "Zora",
          species: "chicken",
          breed: "Hybrid",
          color: "Braun",
          status: "active",
          isArchived: false,
          groupId: "G-1",
          tagIds: ["T-1"],
        },
        {
          id: "A-1",
          name: "Alma",
          species: "chicken",
          breed: null,
          color: null,
          status: "active",
          isArchived: false,
          groupId: null,
          tagIds: [],
        },
        {
          id: "A-3",
          name: "Archiv",
          species: "cat",
          breed: "Europäisch Kurzhaar",
          color: "Schwarz",
          status: "rehomed",
          isArchived: true,
          groupId: null,
          tagIds: ["T-2"],
        },
      ],
      groups: [{ id: "G-1", name: "Legehennen" }],
      tags: [
        { id: "T-1", name: "Senior" },
        { id: "T-2", name: "Vermittelt" },
      ],
      filters: {
        query: "",
        groupId: "all",
        tagId: "all",
        includeArchived: true,
      },
      ...overrides.animals,
    },
    tasks: {
      occurrences: [
        {
          id: "O-3",
          target: {
            scope: "group",
            animalId: null,
            animalIds: [],
            groupId: "G-1",
            memberSnapshot: ["A-2"],
          },
          title: "Später",
          status: "pending",
          timing: "upcoming",
          dueDate: "2026-09-05",
          scheduledAt: "2026-09-05T08:00:00+02:00",
        },
        {
          id: "O-2",
          target: {
            scope: "animal",
            animalId: "A-2",
            animalIds: ["A-2"],
            groupId: null,
            memberSnapshot: [],
          },
          title: "Heute",
          status: "pending",
          timing: "today",
          dueDate: "2026-09-04",
          scheduledAt: "2026-09-04T08:00:00+02:00",
        },
        {
          id: "O-1",
          target: {
            scope: "animal",
            animalId: "A-2",
            animalIds: ["A-2"],
            groupId: null,
            memberSnapshot: [],
          },
          title: "Überfällig",
          status: "pending",
          timing: "overdue",
          dueDate: "2026-09-03",
          scheduledAt: "2026-09-03T08:00:00+02:00",
          is_overdue: false,
        },
        {
          id: "O-4",
          target: {
            scope: "animal",
            animalId: "A-2",
            animalIds: ["A-2"],
            groupId: null,
            memberSnapshot: [],
          },
          title: "Erledigt",
          status: "completed",
          timing: "closed",
          dueDate: "2026-09-02",
          scheduledAt: "2026-09-02T08:00:00+02:00",
        },
      ],
      ...overrides.tasks,
    },
    timeline: {
      items: [
        { id: "E-2", occurredAt: "2026-09-03T10:00:00+02:00" },
        { id: "E-3", occurredAt: null },
        { id: "E-1", occurredAt: "2026-09-04T10:00:00+02:00" },
      ],
      ...overrides.timeline,
    },
  };
}

test("animal and group selectors resolve canonical identifiers", () => {
  const value = state();
  assert.equal(selectAnimalById(value, "A-2")?.name, "Zora");
  assert.equal(selectAnimalById(value, "missing"), null);
  assert.equal(selectGroupById(value, "G-1")?.name, "Legehennen");
  assert.equal(selectGroupById(value, null), null);
});

test("visible animals combine group tag archive and search filters", () => {
  assert.deepEqual(
    selectVisibleAnimals(state()).map((animal) => animal.id),
    ["A-1", "A-2", "A-3"],
  );
  assert.deepEqual(
    selectVisibleAnimals(
      state({
        animals: {
          filters: {
            query: "senior",
            groupId: "G-1",
            tagId: "T-1",
            includeArchived: false,
          },
        },
      }),
    ).map((animal) => animal.id),
    ["A-2"],
  );
  assert.deepEqual(
    selectVisibleAnimals(
      state({
        animals: {
          filters: {
            query: "europäisch schwarz A-3",
            groupId: "ungrouped",
            tagId: "all",
            includeArchived: true,
          },
        },
      }),
    ).map((animal) => animal.id),
    ["A-3"],
  );
  assert.deepEqual(
    selectVisibleAnimals(
      state({
        animals: {
          filters: {
            query: "legehennen",
            groupId: "all",
            tagId: "all",
            includeArchived: true,
          },
        },
      }),
    ).map((animal) => animal.id),
    ["A-2"],
  );
});

test("grouped animals include ordered named and ungrouped buckets", () => {
  const groups = selectGroupedAnimals(state());
  assert.deepEqual(
    groups.map((group) => [group.id, group.name, group.animals.map((animal) => animal.id)]),
    [
      ["G-1", "Legehennen", ["A-2"]],
      ["ungrouped", null, ["A-1", "A-3"]],
    ],
  );
});

test("occurrence selectors use canonical target and timing only", () => {
  const value = state();
  assert.deepEqual(
    selectUrgentOccurrences(value).map((occurrence) => occurrence.id),
    ["O-1", "O-2"],
  );
  assert.deepEqual(
    selectOpenOccurrencesForAnimal(value, "A-2").map((occurrence) => occurrence.id),
    ["O-1", "O-2", "O-3"],
  );
  assert.equal(selectNextOccurrenceForAnimal(value, "A-2")?.id, "O-1");
  assert.equal(selectNextOccurrenceForAnimal(value, "A-1"), null);
});

test("recent events are sorted descending without mutating the source", () => {
  const value = state();
  const source = [...value.timeline.items];
  assert.deepEqual(
    selectRecentEvents(value, 2).map((event) => event.id),
    ["E-1", "E-2"],
  );
  assert.deepEqual(value.timeline.items, source);
  assert.deepEqual(selectRecentEvents(value, 0), []);
});
