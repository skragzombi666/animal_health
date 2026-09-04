import {
  selectGroupedAnimals,
  selectRecentEvents,
  selectUrgentOccurrences,
} from "../../domain/animals/selectors.js";
import {
  escapeAttribute,
  escapeHtml,
} from "../read-only/format.js";
import {
  renderAnimalTile,
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
    routeName: "overview",
    timeZone: context?.timeZone || state?.animals?.directoryMeta?.timeZone,
  };
}

function filterControls(state, context) {
  const t = context.translate;
  const filters = state.animals?.filters || {};
  const groups = Array.isArray(state.animals?.groups) ? state.animals.groups : [];
  const tags = Array.isArray(state.animals?.tags) ? state.animals.tags : [];
  const groupActive = filters.groupId && filters.groupId !== "all";
  const tagActive = filters.tagId && filters.tagId !== "all";
  const queryActive = Boolean(String(filters.query || "").trim());
  const filtered = groupActive || tagActive || queryActive || filters.includeArchived === false;
  const toolbar = `<div class="filterBar"><button class="icon${filters.openPanel === "group" || groupActive ? " on" : ""}" data-action="home-group-toggle" title="${escapeAttribute(t("filterGroups"))}"><ha-icon icon="mdi:account-group-outline"></ha-icon></button><button class="icon${filters.openPanel === "tag" || tagActive ? " on" : ""}" data-action="home-tag-toggle" title="${escapeAttribute(t("filterTags"))}"><ha-icon icon="mdi:tag-multiple-outline"></ha-icon></button><button class="icon${filters.searchOpen || queryActive ? " on" : ""}" data-action="home-search-toggle" title="${escapeAttribute(t("searchAnimals"))}"><ha-icon icon="mdi:magnify"></ha-icon></button>${filtered ? `<button class="icon" data-action="home-filter-reset" title="${escapeAttribute(t("resetFilters"))}"><ha-icon icon="mdi:close-circle-outline"></ha-icon></button>` : ""}</div>`;
  const groupOptions = filters.openPanel === "group"
    ? `<div class="filterOptions"><button class="${filters.groupId === "all" ? "on" : ""}" data-action="home-group-select" data-id="all"><span>${escapeHtml(t("allAnimals"))}</span></button><button class="${filters.groupId === "ungrouped" ? "on" : ""}" data-action="home-group-select" data-id="ungrouped"><span>${escapeHtml(t("ungrouped"))}</span></button>${groups.map((group) => `<button class="${String(filters.groupId) === String(group.id) ? "on" : ""}" data-action="home-group-select" data-id="${escapeAttribute(group.id)}"><span>${escapeHtml(group.name)}</span></button>`).join("")}</div>`
    : "";
  const tagOptions = filters.openPanel === "tag"
    ? `<div class="filterOptions"><button class="${filters.tagId === "all" ? "on" : ""}" data-action="home-tag-select" data-id="all"><span>${escapeHtml(t("allTags"))}</span></button>${tags.map((tag) => `<button class="${String(filters.tagId) === String(tag.id) ? "on" : ""}" data-action="home-tag-select" data-id="${escapeAttribute(tag.id)}"><span>#${escapeHtml(tag.name)}</span></button>`).join("")}</div>`
    : "";
  const search = filters.searchOpen
    ? `<label class="search"><ha-icon icon="mdi:magnify"></ha-icon><input data-action="home-search" value="${escapeAttribute(filters.query || "")}" placeholder="${escapeAttribute(t("searchAnimals"))}" autocomplete="off"></label>`
    : "";
  return { toolbar, groupOptions, tagOptions, search };
}

function animalOverview(state, context) {
  const t = context.translate;
  const groups = selectGroupedAnimals(state);
  const controls = filterControls(state, context);
  const body = groups.map((group) => {
    const name = group.id === "ungrouped" ? t("ungrouped") : group.name;
    return `<section class="animalGroup"><div class="animalGroupHead"><b>${escapeHtml(name)}</b><small>${group.animals.length}</small></div><div class="animalTiles">${group.animals.map((animal) => renderAnimalTile(animal, context)).join("")}</div></section>`;
  }).join("") || renderEmpty(t("noAnimals"));
  return `<section class="card"><div class="cardHead"><h2>${escapeHtml(t("animals"))}</h2>${controls.toolbar}</div>${controls.groupOptions}${controls.tagOptions}${controls.search}<div class="animalGroups">${body}</div></section>`;
}

export function renderOverview(state, context = {}) {
  const active = viewContext(state, context);
  const t = active.translate;
  const items = Array.isArray(state?.animals?.items) ? state.animals.items : [];
  if ((state?.animals?.status === "idle" || state?.animals?.status === "loading") && !items.length) {
    return renderShell(renderLoading(t("loading")), active);
  }
  if (state?.animals?.status === "error" && !items.length) {
    return renderShell(renderError(state.animals.error, "refresh", active), active);
  }

  const summary = state?.animals?.directoryMeta?.summary || {};
  const urgent = selectUrgentOccurrences(state).slice(0, 12);
  const events = selectRecentEvents(state, 10);
  const taskRows = urgent.map((item) => renderOccurrenceRow(item, active)).join("") || renderEmpty(t("noTasks"));
  const eventRows = events.map((item) => renderEventRow(item, active)).join("") || renderEmpty(t("noEvents"));
  const content = [
    renderHeading(t("overview")),
    renderQuickActions("", t),
    renderStats([
      { icon: "mdi:paw", value: summary.activeAnimals ?? items.filter((animal) => !animal.isArchived).length, label: t("activeAnimals") },
      { icon: "mdi:alert", value: summary.overdueTasks ?? urgent.filter((item) => item.timing === "overdue").length, label: t("overdue"), bad: true },
      { icon: "mdi:calendar-today", value: summary.todayTasks ?? urgent.filter((item) => item.timing === "today").length, label: t("dueToday") },
      { icon: "mdi:clipboard-clock", value: summary.pendingTasks ?? state?.tasks?.occurrences?.filter((item) => item.status === "pending").length ?? 0, label: t("openTasks") },
    ]),
    animalOverview(state, active),
    `<section class="cols"><article class="card"><h2>${escapeHtml(t("dueToday"))}</h2>${taskRows}</article><article class="card"><h2>${escapeHtml(t("recentRecords"))}</h2>${eventRows}</article></section>`,
  ].join("");
  return renderShell(content, active);
}
