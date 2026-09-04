import { normalizeAttachment } from "./animals.js";
import {
  asRecord,
  camelizeObject,
  dateTime,
  firstDefined,
  numberValue,
  optionalText,
  requiredText,
} from "./common.js";
import { normalizeTarget } from "./tasks.js";

function attachmentsFor(index, eventId) {
  if (index instanceof Map) return index.get(eventId) || [];
  if (index && typeof index === "object") return index[eventId] || [];
  return [];
}

export function normalizeHealthEvent(
  rawValue,
  { attachmentsByEventId = {} } = {},
) {
  const raw = asRecord(rawValue, "event");
  const id = requiredText(
    firstDefined(raw, ["id", "event_id", "eventId"]),
    "event.id",
  );
  const animalId = requiredText(
    firstDefined(raw, ["animal_id", "animalId"]),
    "event.animalId",
  );
  const taskId = optionalText(firstDefined(raw, ["task_id", "taskId"]));
  const occurrenceId = optionalText(
    firstDefined(
      raw,
      [
        "task_occurrence_id",
        "taskOccurrenceId",
        "occurrence_id",
        "occurrenceId",
      ],
    ),
  );
  const rawPayload = firstDefined(raw, ["data", "payload"], {});
  const payload = camelizeObject(
    rawPayload && typeof rawPayload === "object" && !Array.isArray(rawPayload)
      ? rawPayload
      : {},
  );
  const target = normalizeTarget(payload, {
    scope: "animal",
    animalId,
    animalIds: [animalId],
    groupId: null,
    memberSnapshot: [],
  });
  const sourceKind = optionalText(
    firstDefined(payload, ["source", "sourceKind"]),
  );
  const hasSource = taskId || occurrenceId || sourceKind;
  return {
    id,
    animalId,
    animalName: optionalText(
      firstDefined(raw, ["animal_name", "animalName"]),
    ),
    type: requiredText(
      firstDefined(raw, ["event_type", "eventType", "type"]),
      "event.type",
    ),
    occurredAt: dateTime(
      firstDefined(raw, ["occurred_at", "occurredAt"]),
      "event.occurredAt",
    ),
    title: requiredText(
      firstDefined(raw, ["title"], "event"),
      "event.title",
    ),
    notes: optionalText(raw.notes),
    value: numberValue(raw.value, null, "event.value"),
    unit: optionalText(raw.unit),
    correctionOfEventId: optionalText(
      firstDefined(raw, ["correction_of_event_id", "correctionOfEventId"]),
    ),
    createdAt: dateTime(
      firstDefined(raw, ["created_at", "createdAt"]),
      "event.createdAt",
    ),
    target,
    source: hasSource
      ? {
          kind: taskId || occurrenceId ? "task" : sourceKind,
          taskId,
          occurrenceId,
          groupId: target.groupId,
          treatmentPlanId: optionalText(
            firstDefined(payload, ["treatmentPlanId"]),
          ),
        }
      : null,
    payload,
    attachments: attachmentsFor(attachmentsByEventId, id).map((item) =>
      normalizeAttachment(item),
    ),
  };
}
