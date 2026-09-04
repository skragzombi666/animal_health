import assert from "node:assert/strict";
import test from "node:test";

import {
  normalizeHealthEvent,
  normalizeTarget,
  normalizeTaskDefinition,
  normalizeTaskOccurrence,
} from "../../custom_components/animal_health/frontend/src/api/normalizers/index.js";

const groupMetadata = {
  target_scope: "group",
  target_group_id: "GR-FLOCK",
  target_group_name: "Legehennen",
  target_animal_ids: ["AH-1", "AH-2"],
  target_batch_id: "TG-BATCH",
};

const expectedGroupTarget = {
  scope: "group",
  animalId: null,
  animalIds: [],
  groupId: "GR-FLOCK",
  memberSnapshot: ["AH-1", "AH-2"],
};

test("target normalizer preserves the current group metadata aliases", () => {
  assert.deepEqual(normalizeTarget(groupMetadata), expectedGroupTarget);
});

test("task definitions and occurrences preserve a group target stored in planned data", () => {
  const task = normalizeTaskDefinition({
    id: "TASK-GROUP",
    scope: "animal",
    animal_id: "AH-1",
    title: "Gruppe entwurmen",
    task_kind: "deworming",
    recurrence_type: "once",
    start_date: "2026-09-04",
    is_active: true,
    planned: groupMetadata,
  });
  const occurrence = normalizeTaskOccurrence(
    {
      id: "OCC-GROUP",
      task_id: task.id,
      scope: "animal",
      animal_id: "AH-1",
      task_title: task.title,
      scheduled_for: "2026-09-04T06:00:00+00:00",
      scheduled_local: "2026-09-04T08:00:00+02:00",
      scheduled_date: "2026-09-04",
      status: "pending",
      task_is_active: true,
    },
    {
      taskById: { [task.id]: task },
      today: "2026-09-04",
    },
  );

  assert.deepEqual(task.target, expectedGroupTarget);
  assert.deepEqual(occurrence.target, expectedGroupTarget);
});

test("health events expose group target and member snapshot independently of source metadata", () => {
  const event = normalizeHealthEvent({
    id: "EV-GROUP",
    animal_id: "AH-1",
    event_type: "medication",
    occurred_at: "2026-09-04T08:05:00+00:00",
    title: "Entwurmung",
    task_id: "TASK-GROUP",
    task_occurrence_id: "OCC-GROUP",
    data: {
      source: "task",
      ...groupMetadata,
      medication_name: "Flubenol",
    },
  });

  assert.deepEqual(event.target, expectedGroupTarget);
  assert.equal(event.source.groupId, "GR-FLOCK");
  assert.equal(event.source.taskId, "TASK-GROUP");
  assert.equal(event.payload.targetGroupName, "Legehennen");
});
