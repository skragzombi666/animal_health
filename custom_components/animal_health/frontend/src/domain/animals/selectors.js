import { validationError } from "../../api/errors.js";

const TIMING_ORDER = Object.freeze({
  overdue: 0,
  today: 1,
  upcoming: 2,
  closed: 3,
});

function stateSlice(state, name) {
  if (state === null || typeof state !== "object") {
    throw validationError("state must be an object", "state");
  }
  const slice = state[name];
  return slice && typeof slice === "object" ? slice : {};
}

function values(value) {
  return Array.isArray(value) ? value : [];
}

function text(value) {
  return String(value ?? "").trim();
}

function folded(value) {
  return text(value).toLocaleLowerCase();
}

function compareText(left, right) {
  return text(left).localeCompare(text(right), undefined, {
    sensitivity: "base",
    numeric: true,
  });
}

function compareAnimal(left, right) {
  const archived = Number(Boolean(left?.isArchived)) - Number(Boolean(right?.isArchived));
  if (archived) return archived;
  return compareText(left?.name, right?.name) || compareText(left?.id, right?.id);
}

function occurrenceSortKey(occurrence) {
  return [
    TIMING_ORDER[occurrence?.timing] ?? 9,
    text(occurrence?.dueDate) || "9999-12-31",
    text(occurrence?.scheduledAt) || "9999-12-31T23:59:59Z",
    text(occurrence?.id),
  ];
}

function compareOccurrence(left, right) {
  const a = occurrenceSortKey(left);
  const b = occurrenceSortKey(right);
  for (let index = 0; index < a.length; index += 1) {
    if (typeof a[index] === "number") {
      const difference = a[index] - b[index];
      if (difference) return difference;
    } else {
      const difference = compareText(a[index], b[index]);
      if (difference) return difference;
    }
  }
  return 0;
}

function targetsAnimal(occurrence, animalId) {
  const id = text(animalId);
  if (!id) return false;
  const target = occurrence?.target || {};
  return (
    text(target.animalId) === id ||
    values(target.animalIds).map(text).includes(id) ||
    values(target.memberSnapshot).map(text).includes(id)
  );
}

function filterState(state) {
  const filters = stateSlice(state, "animals").filters || {};
  return {
    query: folded(filters.query),
    groupId: text(filters.groupId) || "all",
    tagId: text(filters.tagId) || "all",
    includeArchived: filters.includeArchived !== false,
  };
}

function animalSearchHaystack(state, animal) {
  const group = selectGroupById(state, animal?.groupId);
  const tags = values(stateSlice(state, "animals").tags)
    .filter((tag) => values(animal?.tagIds).map(text).includes(text(tag?.id)))
    .map((tag) => tag?.name);
  return [
    animal?.id,
    animal?.name,
    animal?.species,
    animal?.breed,
    animal?.color,
    animal?.status,
    group?.name,
    ...tags,
  ]
    .map(folded)
    .filter(Boolean)
    .join(" ");
}

export function selectAnimalById(state, animalId) {
  const id = text(animalId);
  if (!id) return null;
  return values(stateSlice(state, "animals").items).find(
    (animal) => text(animal?.id) === id,
  ) || null;
}

export function selectGroupById(state, groupId) {
  const id = text(groupId);
  if (!id) return null;
  return values(stateSlice(state, "animals").groups).find(
    (group) => text(group?.id) === id,
  ) || null;
}

export function selectVisibleAnimals(state) {
  const filters = filterState(state);
  const queryTokens = filters.query.split(/\s+/).filter(Boolean);
  return values(stateSlice(state, "animals").items)
    .filter((animal) => {
      if (!filters.includeArchived && animal?.isArchived) return false;
      if (filters.groupId === "ungrouped" && text(animal?.groupId)) return false;
      if (
        filters.groupId !== "all" &&
        filters.groupId !== "ungrouped" &&
        text(animal?.groupId) !== filters.groupId
      ) {
        return false;
      }
      if (
        filters.tagId !== "all" &&
        !values(animal?.tagIds).map(text).includes(filters.tagId)
      ) {
        return false;
      }
      if (queryTokens.length) {
        const haystack = animalSearchHaystack(state, animal);
        if (!queryTokens.every((token) => haystack.includes(token))) return false;
      }
      return true;
    })
    .slice()
    .sort(compareAnimal);
}

export function selectGroupedAnimals(state) {
  const animals = selectVisibleAnimals(state);
  const result = [];
  const groups = values(stateSlice(state, "animals").groups)
    .slice()
    .sort((left, right) =>
      compareText(left?.name, right?.name) || compareText(left?.id, right?.id),
    );
  for (const group of groups) {
    const members = animals.filter(
      (animal) => text(animal?.groupId) === text(group?.id),
    );
    if (members.length) {
      result.push({
        id: text(group.id),
        name: text(group.name) || null,
        group,
        animals: members,
      });
    }
  }
  const ungrouped = animals.filter((animal) => !text(animal?.groupId));
  if (ungrouped.length) {
    result.push({
      id: "ungrouped",
      name: null,
      group: null,
      animals: ungrouped,
    });
  }
  return result;
}

export function selectOpenOccurrencesForAnimal(state, animalId) {
  return values(stateSlice(state, "tasks").occurrences)
    .filter(
      (occurrence) =>
        occurrence?.status === "pending" && targetsAnimal(occurrence, animalId),
    )
    .slice()
    .sort(compareOccurrence);
}

export function selectNextOccurrenceForAnimal(state, animalId) {
  return selectOpenOccurrencesForAnimal(state, animalId)[0] || null;
}

export function selectUrgentOccurrences(state) {
  return values(stateSlice(state, "tasks").occurrences)
    .filter(
      (occurrence) =>
        occurrence?.status === "pending" &&
        (occurrence?.timing === "overdue" || occurrence?.timing === "today"),
    )
    .slice()
    .sort(compareOccurrence);
}

export function selectRecentEvents(state, limit = 10) {
  const count = Number(limit);
  if (!Number.isFinite(count) || count <= 0) return [];
  return values(stateSlice(state, "timeline").items)
    .slice()
    .sort((left, right) => {
      const leftDate = text(left?.occurredAt);
      const rightDate = text(right?.occurredAt);
      if (leftDate && !rightDate) return -1;
      if (!leftDate && rightDate) return 1;
      return compareText(rightDate, leftDate) || compareText(left?.id, right?.id);
    })
    .slice(0, Math.floor(count));
}
