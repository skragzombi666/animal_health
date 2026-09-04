import {
  escapeAttribute,
  escapeHtml,
  formatDateOnly,
  formatDateTime,
  formatEnum,
  formatNumber,
  formatWeight,
  speciesLabel,
} from "./format.js";
import { READ_ONLY_STYLES } from "./styles.js";

const ICONS = Object.freeze({
  reminder: "mdi:bell-outline",
  weight: "mdi:scale-bathroom",
  medication: "mdi:pill",
  vaccination: "mdi:needle",
  health_check: "mdi:stethoscope",
  care: "mdi:hand-heart",
  veterinary_visit: "mdi:hospital-box-outline",
  observation: "mdi:eye-outline",
  symptom: "mdi:alert-circle-outline",
  diagnosis: "mdi:clipboard-pulse-outline",
  treatment: "mdi:medical-bag",
  status_change: "mdi:swap-horizontal",
  other: "mdi:dots-horizontal-circle-outline",
});

function iconFor(value) {
  return ICONS[value] || ICONS.other;
}

function translator(context) {
  return typeof context?.translate === "function"
    ? context.translate
    : (key) => String(key);
}

function routeIsActive(context, route) {
  const current = context?.routeName === "animal-detail"
    ? "animals"
    : context?.routeName;
  return current === route;
}

function buttonView(route, icon, context) {
  const t = translator(context);
  return `<button data-view="${escapeAttribute(route)}" class="${routeIsActive(context, route) ? "on" : ""}" aria-label="${escapeAttribute(t(route))}"><ha-icon icon="${icon}"></ha-icon><span>${escapeHtml(t(route))}</span></button>`;
}

export function renderHeader(context = {}) {
  const t = translator(context);
  return `<header><div class="brand"><ha-icon icon="mdi:paw"></ha-icon><span>Animal Health</span></div><nav>${buttonView("overview", "mdi:view-dashboard", context)}${buttonView("animals", "mdi:paw", context)}${buttonView("tasks", "mdi:clipboard-check-outline", context)}${buttonView("calendar", "mdi:calendar-month", context)}${buttonView("timeline", "mdi:timeline-clock", context)}</nav><button class="icon" data-action="refresh" aria-label="${escapeAttribute(t("refresh"))}" title="${escapeAttribute(t("refresh"))}"><ha-icon icon="mdi:refresh"></ha-icon></button></header>`;
}

export function renderHeading(title, actions = "") {
  return `<div class="heading"><h1>${escapeHtml(title)}</h1><div class="actions">${actions}</div></div>`;
}

function actionButton(action, icon, label, id = null, primary = false) {
  const idAttribute = id == null ? "" : ` data-id="${escapeAttribute(id)}"`;
  return `<button${primary ? ' class="primary"' : ""} data-action="${escapeAttribute(action)}"${idAttribute}><ha-icon icon="${icon}"></ha-icon>${escapeHtml(label)}</button>`;
}

export function renderQuickActions(animalId = "", translate = (key) => key) {
  const id = String(animalId ?? "");
  return `<div class="quick" aria-label="${escapeAttribute(translate("quickActions"))}">${actionButton("create-animal", "mdi:plus-circle-outline", translate("createAnimal"))}${actionButton("create-task", "mdi:clipboard-plus", translate("createTask"))}${actionButton("record-weight", "mdi:scale", translate("recordWeight"), id)}${actionButton("record-symptom", "mdi:alert-plus", translate("recordSymptom"), id)}</div>`;
}

export function renderStats(items = []) {
  return `<section class="stats">${items.map((item) => {
    const bad = item?.bad ? " bad" : "";
    return `<div class="stat${bad}"><ha-icon icon="${escapeAttribute(item?.icon || "mdi:information-outline")}"></ha-icon><div><strong>${escapeHtml(item?.value ?? "–")}</strong><span>${escapeHtml(item?.label ?? "")}</span></div></div>`;
  }).join("")}</section>`;
}

function animalSecondary(animal, context) {
  const t = translator(context);
  const species = speciesLabel(animal, context?.state, t, context?.language);
  return [species, animal?.breed].filter(Boolean).join(" · ");
}

function canonicalTags(animal, context) {
  const tagIds = Array.isArray(animal?.tagIds) ? animal.tagIds.map(String) : [];
  const tags = Array.isArray(context?.state?.animals?.tags)
    ? context.state.animals.tags
    : [];
  return tags.filter((tag) => tagIds.includes(String(tag?.id))).map((tag) => tag?.name).filter(Boolean);
}

function canonicalGroup(animal, context) {
  const groups = Array.isArray(context?.state?.animals?.groups)
    ? context.state.animals.groups
    : [];
  return groups.find((group) => String(group?.id) === String(animal?.groupId ?? "")) || null;
}

export function renderAnimalTile(animal, context = {}) {
  return `<button class="animalTile" data-action="animal-detail" data-id="${escapeAttribute(animal?.id)}" title="${escapeAttribute(animal?.name)}"><ha-icon icon="mdi:paw"></ha-icon><span>${escapeHtml(animal?.name)}</span></button>`;
}

export function renderAnimalCard(animal, context = {}) {
  const t = translator(context);
  const group = canonicalGroup(animal, context);
  const tags = canonicalTags(animal, context);
  const next = context?.nextOccurrence || null;
  const status = animal?.isArchived ? t("archived") : formatEnum(animal?.status, t);
  const groupAndTags = [group?.name, ...tags.map((tag) => `#${tag}`)].filter(Boolean).join(" · ");
  return `<article class="animal${animal?.isArchived ? " muted" : ""}"><button class="animalHead" data-action="animal-detail" data-id="${escapeAttribute(animal?.id)}"><ha-icon icon="mdi:paw"></ha-icon><div><h3>${escapeHtml(animal?.name)}</h3><span>${escapeHtml(animalSecondary(animal, context))}${groupAndTags ? ` · ${escapeHtml(groupAndTags)}` : ""}</span></div><b>${escapeHtml(status)}</b></button><div class="animalMeta"><span>${escapeHtml(t("currentWeight"))}<b>${escapeHtml(formatWeight(animal?.latestWeight, context?.locale))}</b></span><span>${escapeHtml(t("upcoming"))}<b>${escapeHtml(next?.title || "–")}</b></span></div></article>`;
}

function occurrenceWhen(occurrence, context) {
  const t = translator(context);
  const timing = formatEnum(occurrence?.timing, t);
  const date = occurrence?.dueDate
    ? formatDateOnly(occurrence.dueDate, context?.locale)
    : formatDateTime(occurrence?.scheduledLocal || occurrence?.scheduledAt, context?.locale, context?.timeZone);
  return [timing, date].filter((value) => value && value !== "–").join(" · ");
}

export function renderOccurrenceRow(occurrence, context = {}) {
  const t = translator(context);
  const kind = occurrence?.planned?.taskKind || occurrence?.kind || "reminder";
  const secondary = [
    occurrence?.animalName || (occurrence?.target?.scope === "general" ? t("general") : null),
    occurrenceWhen(occurrence, context),
    formatEnum(occurrence?.status, t),
  ].filter(Boolean).join(" · ");
  const overdueClass = occurrence?.timing === "overdue" ? " over" : "";
  const execute = occurrence?.status === "pending" && context?.showTaskActions
    ? `<div class="rowAside"><button class="primary" data-action="execute" data-id="${escapeAttribute(occurrence?.id)}">${escapeHtml(t("edit"))}</button></div>`
    : "";
  return `<div class="row${overdueClass}"><ha-icon icon="${iconFor(kind)}"></ha-icon><div><b>${escapeHtml(occurrence?.title)}</b><span>${escapeHtml(secondary)}</span>${occurrence?.timing === "overdue" ? `<small class="badge bad">${escapeHtml(t("overdue"))}</small>` : ""}</div>${execute}</div>`;
}

export function renderEventRow(event, context = {}) {
  const t = translator(context);
  const sourceBadges = [];
  if (event?.source?.kind === "task") sourceBadges.push(t("fromTask"));
  if (event?.target?.scope === "group") sourceBadges.push(t("groupAction"));
  const secondary = [
    event?.animalName,
    formatEnum(event?.type, t),
    formatDateTime(event?.occurredAt, context?.locale, context?.timeZone),
  ].filter(Boolean).join(" · ");
  const badges = sourceBadges.map((label) => `<small class="badge">${escapeHtml(label)}</small>`).join("");
  const value = event?.value != null
    ? `<strong>${escapeHtml(`${formatNumber(event.value, context?.locale)}${event?.unit ? ` ${event.unit}` : ""}`)}</strong>`
    : "";
  return `<div class="row"><ha-icon icon="${iconFor(event?.type)}"></ha-icon><div><b>${escapeHtml(event?.title)}</b><span>${escapeHtml(secondary)}</span>${badges}${event?.notes ? `<small>${escapeHtml(event.notes)}</small>` : ""}</div>${value}</div>`;
}

export function renderEmpty(message) {
  return `<div class="empty">${escapeHtml(message)}</div>`;
}

export function renderLoading(message) {
  return `<div class="loading"><ha-icon icon="mdi:paw"></ha-icon><p>${escapeHtml(message)}</p></div>`;
}

export function renderError(error, retryAction, context = {}) {
  const t = translator(context);
  const message = error?.message || t("loadError");
  return `<div class="errorState"><ha-icon icon="mdi:alert-circle-outline"></ha-icon><p>${escapeHtml(message)}</p><button data-action="${escapeAttribute(retryAction)}">${escapeHtml(t("retry"))}</button></div>`;
}

export function renderShell(content, context = {}) {
  const route = context?.routeName || "overview";
  return `<style>${READ_ONLY_STYLES}</style><div data-modern-route="${escapeAttribute(route)}">${renderHeader(context)}<main>${content}<div class="version">${escapeHtml(context?.integrationVersion || "")}</div></main></div>`;
}
