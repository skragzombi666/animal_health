import {
  asRecord,
  booleanValue,
  camelizeObject,
  collectPrefixedFields,
  dateOnly,
  dateTime,
  firstDefined,
  integerValue,
  optionalText,
  requiredText,
  stringList,
} from "./common.js";

const CLOSED_STATUSES = new Set(["completed", "skipped", "cancelled"]);

function embeddedPlannedRecord(raw) {
  const embedded = firstDefined(raw, ["planned"], {});
  return embedded !== null &&
    typeof embedded === "object" &&
    !Array.isArray(embedded)
    ? embedded
    : {};
}

function targetScope(raw, fallback, animalId, animalIds, groupId) {
  const value = optionalText(
    firstDefined(
      raw,
      ["target_scope", "targetScope"],
      firstDefined(fallback, ["scope"], firstDefined(raw, ["scope"])),
    ),
  );
  if (value === "general" || value === "group" || value === "animals") {
    return value;
  }
  if (value === "animal") return "animal";
  if (groupId) return "group";
  if (animalIds.length > 1) return "animals";
  if (animalId || animalIds.length === 1) return "animal";
  return "general";
}

export function normalizeTarget(rawValue = {}, fallbackValue = {}) {
  const raw = asRecord(rawValue, "target");
  const fallback = asRecord(fallbackValue || {}, "targetFallback");
  const explicitAnimalId = optionalText(
    firstDefined(
      raw,
      ["animal_id", "animalId"],
      firstDefined(fallback, ["animal_id", "animalId"]),
    ),
  );
  const animalIds = stringList(
    firstDefined(
      raw,
      ["target_animal_ids", "targetAnimalIds", "animal_ids", "animalIds"],
      firstDefined(fallback, ["animal_ids", "animalIds"], []),
    ),
    "target.animalIds",
  );
  const animalId =
    explicitAnimalId || (animalIds.length === 1 ? animalIds[0] : null);
  const groupId = optionalText(
    firstDefined(
      raw,
      ["target_group_id", "targetGroupId", "group_id", "groupId"],
      firstDefined(fallback, ["group_id", "groupId"]),
    ),
  );
  const scope = targetScope(raw, fallback, animalId, animalIds, groupId);
  const memberSnapshot = stringList(
    firstDefined(
      raw,
      [
        "member_snapshot",
        "memberSnapshot",
        "target_member_snapshot",
        "targetMemberSnapshot",
        "target_animal_ids",
        "targetAnimalIds",
      ],
      firstDefined(
        fallback,
        ["member_snapshot", "memberSnapshot"],
        [],
      ),
    ),
    "target.memberSnapshot",
  );
  return {
    scope,
    animalId: scope === "animal" ? animalId : null,
    animalIds:
      scope === "animals"
        ? animalIds
        : scope === "animal" && animalId
          ? [animalId]
          : [],
    groupId: scope === "group" ? groupId : null,
    memberSnapshot,
  };
}

function normalizePlanned(raw, inherited = {}) {
  return {
    ...camelizeObject(inherited || {}),
    ...camelizeObject(embeddedPlannedRecord(raw)),
    ...collectPrefixedFields(raw, "planned_"),
  };
}

export function normalizeTaskDefinition(rawValue) {
  const raw = asRecord(rawValue, "task");
  const id = requiredText(
    firstDefined(raw, ["id", "task_id", "taskId"]),
    "task.id",
  );
  const recurrenceType = requiredText(
    firstDefined(raw, ["recurrence_type", "recurrenceType"], "once"),
    "task.recurrenceType",
  );
  const explicitSeriesId = optionalText(
    firstDefined(raw, ["series_id", "seriesId"]),
  );
  return {
    id,
    seriesId: explicitSeriesId || (recurrenceType === "once" ? null : id),
    target: normalizeTarget({ ...raw, ...embeddedPlannedRecord(raw) }),
    animalName: optionalText(
      firstDefined(raw, ["animal_name", "animalName"]),
    ),
    title: requiredText(
      firstDefined(raw, ["title", "task_title", "taskTitle"]),
      "task.title",
    ),
    description: optionalText(raw.description),
    kind: requiredText(
      firstDefined(raw, ["task_kind", "taskKind", "kind"], "reminder"),
      "task.kind",
    ),
    recurrenceType,
    recurrenceInterval: integerValue(
      firstDefined(raw, ["recurrence_interval", "recurrenceInterval"]),
      1,
      "task.recurrenceInterval",
    ),
    startDate: dateOnly(
      firstDefined(raw, ["start_date", "startDate"]),
      "task.startDate",
    ),
    endDate: dateOnly(
      firstDefined(raw, ["end_date", "endDate"]),
      "task.endDate",
    ),
    dueTime: optionalText(firstDefined(raw, ["due_time", "dueTime"])),
    isActive: booleanValue(
      firstDefined(raw, ["is_active", "isActive"]),
      true,
    ),
    nextPendingAt: dateTime(
      firstDefined(raw, ["next_pending_at", "nextPendingAt"]),
      "task.nextPendingAt",
    ),
    nextPendingLocal: dateTime(
      firstDefined(raw, ["next_pending_local", "nextPendingLocal"]),
      "task.nextPendingLocal",
    ),
    pendingCount: integerValue(
      firstDefined(raw, ["pending_count", "pendingCount"]),
      0,
      "task.pendingCount",
    ),
    overdueCount: integerValue(
      firstDefined(raw, ["overdue_count", "overdueCount"]),
      0,
      "task.overdueCount",
    ),
    planned: normalizePlanned(raw),
    entityId: optionalText(firstDefined(raw, ["entity_id", "entityId"])),
    createdAt: dateTime(
      firstDefined(raw, ["created_at", "createdAt"]),
      "task.createdAt",
    ),
    updatedAt: dateTime(
      firstDefined(raw, ["updated_at", "updatedAt"]),
      "task.updatedAt",
    ),
  };
}

function getTask(taskById, definitionId) {
  if (taskById instanceof Map) return taskById.get(definitionId) || null;
  if (taskById && typeof taskById === "object") {
    return taskById[definitionId] || null;
  }
  return null;
}

function occurrenceTiming(raw, status, scheduledDate, today) {
  if (CLOSED_STATUSES.has(status) || status !== "pending") return "closed";
  if (
    booleanValue(firstDefined(raw, ["is_overdue", "isOverdue"]), false)
  ) {
    return "overdue";
  }
  if (booleanValue(firstDefined(raw, ["is_today", "isToday"]), false)) {
    return "today";
  }
  if (
    booleanValue(firstDefined(raw, ["is_upcoming", "isUpcoming"]), false)
  ) {
    return "upcoming";
  }
  if (scheduledDate && today) {
    if (scheduledDate < today) return "overdue";
    if (scheduledDate === today) return "today";
    return "upcoming";
  }
  return "upcoming";
}

export function normalizeTaskOccurrence(
  rawValue,
  { taskById = {}, today = null } = {},
) {
  const raw = asRecord(rawValue, "occurrence");
  const id = requiredText(
    firstDefined(raw, ["id", "occurrence_id", "occurrenceId"]),
    "occurrence.id",
  );
  const definitionId = requiredText(
    firstDefined(
      raw,
      ["task_id", "taskId", "definition_id", "definitionId"],
    ),
    "occurrence.definitionId",
  );
  const task = getTask(taskById, definitionId);
  const status = requiredText(
    firstDefined(raw, ["status"], "pending"),
    "occurrence.status",
  );
  const scheduledDate = dateOnly(
    firstDefined(
      raw,
      ["scheduled_date", "scheduledDate", "due_date", "dueDate"],
    ),
    "occurrence.dueDate",
  );
  const localToday = dateOnly(today, "today");
  const explicitSeriesId = optionalText(
    firstDefined(raw, ["series_id", "seriesId"]),
  );
  return {
    id,
    seriesId: explicitSeriesId || task?.seriesId || null,
    definitionId,
    target: normalizeTarget(
      { ...raw, ...embeddedPlannedRecord(raw) },
      task?.target || {},
    ),
    animalName: optionalText(
      firstDefined(raw, ["animal_name", "animalName"], task?.animalName),
    ),
    title: requiredText(
      firstDefined(raw, ["task_title", "taskTitle", "title"], task?.title),
      "occurrence.title",
    ),
    scheduledAt: dateTime(
      firstDefined(raw, ["scheduled_for", "scheduledAt"]),
      "occurrence.scheduledAt",
    ),
    scheduledLocal: dateTime(
      firstDefined(raw, ["scheduled_local", "scheduledLocal"]),
      "occurrence.scheduledLocal",
    ),
    dueDate: scheduledDate,
    status,
    timing: occurrenceTiming(raw, status, scheduledDate, localToday),
    completedAt: dateTime(
      firstDefined(raw, ["completed_at", "completedAt"]),
      "occurrence.completedAt",
    ),
    notes: optionalText(raw.notes),
    taskIsActive: booleanValue(
      firstDefined(raw, ["task_is_active", "taskIsActive"], task?.isActive),
      true,
    ),
    planned: normalizePlanned(raw, task?.planned),
    completion:
      status === "pending"
        ? null
        : {
            status,
            completedAt: dateTime(
              firstDefined(raw, ["completed_at", "completedAt"]),
              "occurrence.completedAt",
            ),
            notes: optionalText(raw.notes),
          },
    createdAt: dateTime(
      firstDefined(raw, ["created_at", "createdAt"]),
      "occurrence.createdAt",
    ),
    updatedAt: dateTime(
      firstDefined(raw, ["updated_at", "updatedAt"]),
      "occurrence.updatedAt",
    ),
  };
}
