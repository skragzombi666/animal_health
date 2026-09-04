import {
  selectAnimalById,
  selectOpenOccurrencesForAnimal,
} from "../../domain/animals/selectors.js";
import {
  escapeAttribute,
  escapeHtml,
  formatDateOnly,
  formatEnum,
  formatWeight,
  speciesLabel,
} from "../read-only/format.js";
import {
  renderEmpty,
  renderError,
  renderEventRow,
  renderHeading,
  renderLoading,
  renderOccurrenceRow,
  renderQuickActions,
  renderShell,
  renderStats,
} from "../read-only/components.js";

function viewContext(state, context) {
  return {
    ...context,
    state,
    routeName: "animal-detail",
    timeZone: context?.timeZone || state?.animals?.directoryMeta?.timeZone,
  };
}

function groupFor(state, animal) {
  const groups = Array.isArray(state?.animals?.groups) ? state.animals.groups : [];
  return groups.find((group) => String(group?.id) === String(animal?.groupId ?? "")) || null;
}

function tagsFor(state, animal) {
  const ids = Array.isArray(animal?.tagIds) ? animal.tagIds.map(String) : [];
  const tags = Array.isArray(state?.animals?.tags) ? state.animals.tags : [];
  return tags.filter((tag) => ids.includes(String(tag?.id)));
}

function definitionList(items, context) {
  const t = context.translate;
  return `<dl>${items.map(([key, value]) => `<div><dt>${escapeHtml(t(key))}</dt><dd>${escapeHtml(value ?? "–")}</dd></div>`).join("")}</dl>`;
}

function hero(animal, state, context) {
  const t = context.translate;
  const group = groupFor(state, animal);
  const tags = tagsFor(state, animal);
  const metadata = [
    speciesLabel(animal, state, t, context.language),
    animal?.breed,
    formatEnum(animal?.status, t),
    group?.name,
    ...tags.map((tag) => `#${tag.name}`),
  ].filter(Boolean).join(" · ");
  const archiveAction = animal?.isArchived ? "restore" : "archive";
  const archiveLabel = animal?.isArchived ? t("restore") : t("archive");
  return `<section class="hero"><ha-icon icon="mdi:paw"></ha-icon><div><h1>${escapeHtml(animal?.name)}</h1><p>${escapeHtml(metadata)}</p></div><div class="actions"><button data-action="edit-animal" data-id="${escapeAttribute(animal?.id)}">${escapeHtml(t("edit"))}</button><button data-action="animal-status" data-id="${escapeAttribute(animal?.id)}">${escapeHtml(t("changeStatus"))}</button><button data-action="${archiveAction}" data-id="${escapeAttribute(animal?.id)}">${escapeHtml(archiveLabel)}</button></div></section>`;
}

export function renderAnimalDetail(state, context = {}) {
  const active = viewContext(state, context);
  const t = active.translate;
  const animalId = state?.navigation?.current?.params?.animalId;
  const directoryAnimal = selectAnimalById(state, animalId);
  const detailState = state?.animals?.detail || {};
  const detail = detailState.status === "ready" ? detailState.data : null;
  const animal = detail?.animal || directoryAnimal;
  const back = `<button data-view="animals" aria-label="${escapeAttribute(t("back"))}"><ha-icon icon="mdi:arrow-left"></ha-icon>${escapeHtml(t("back"))}</button>`;

  if (!animal) {
    const content = `${renderHeading(t("animalDetail"), back)}${detailState.status === "error" ? renderError(detailState.error, "detail-refresh", active) : renderLoading(t("loading"))}`;
    return renderShell(content, active);
  }

  const top = `${renderHeading(t("animals"), back)}${hero(animal, state, active)}`;
  if (detailState.status !== "ready" || !detail) {
    const status = detailState.status === "error"
      ? renderError(detailState.error, "detail-refresh", active)
      : renderLoading(t("loading"));
    return renderShell(`${top}${status}`, active);
  }

  const group = groupFor(state, animal);
  const tags = tagsFor(state, animal);
  const occurrenceState = {
    ...state,
    tasks: {
      ...state.tasks,
      occurrences: Array.isArray(detail.occurrences) ? detail.occurrences : [],
    },
  };
  const openOccurrences = selectOpenOccurrencesForAnimal(occurrenceState, animal.id);
  const occurrenceRows = openOccurrences.map((occurrence) => renderOccurrenceRow(occurrence, active)).join("") || renderEmpty(t("noTasks"));
  const events = Array.isArray(detail.events) ? detail.events : [];
  const eventRows = events.map((event) => renderEventRow(event, active)).join("") || renderEmpty(t("noEvents"));
  const groupAndTags = [group?.name, ...tags.map((tag) => `#${tag.name}`)].filter(Boolean).join(" · ") || t("noGroup");
  const masterData = definitionList([
    ["species", speciesLabel(animal, state, t, active.language)],
    ["breed", animal.breed || "–"],
    ["color", animal.color || "–"],
    ["sex", formatEnum(animal.sex, t)],
    ["birthDate", formatDateOnly(animal.birthDate, active.locale)],
    ["arrivalDate", formatDateOnly(animal.arrivalDate, active.locale)],
    ["status", animal.isArchived ? t("archived") : formatEnum(animal.status, t)],
    ["group", groupAndTags],
  ], active);
  const content = [
    top,
    renderQuickActions(animal.id, t),
    renderStats([
      { icon: "mdi:scale", value: formatWeight(animal.latestWeight, active.locale), label: t("currentWeight") },
      { icon: "mdi:clipboard", value: openOccurrences.length, label: t("openTasks") },
      { icon: "mdi:calendar", value: formatDateOnly(animal.birthDate, active.locale), label: t("birthDate") },
      { icon: "mdi:identifier", value: animal.id, label: t("technicalId") },
    ]),
    `<section class="cols"><article class="card"><h2>${escapeHtml(t("masterData"))}</h2>${masterData}</article><article class="card"><h2>${escapeHtml(t("tasksForAnimal"))}</h2>${occurrenceRows}</article></section>`,
    `<section class="card"><h2>${escapeHtml(t("recentRecords"))}</h2>${eventRows}</section>`,
  ].join("");
  return renderShell(content, active);
}
