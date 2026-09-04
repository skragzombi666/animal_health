import {
  selectNextOccurrenceForAnimal,
  selectVisibleAnimals,
} from "../../domain/animals/selectors.js";
import {
  escapeAttribute,
  escapeHtml,
} from "../read-only/format.js";
import {
  renderAnimalCard,
  renderEmpty,
  renderError,
  renderHeading,
  renderLoading,
  renderShell,
} from "../read-only/components.js";

function viewContext(state, context) {
  return {
    ...context,
    state,
    routeName: "animals",
    timeZone: context?.timeZone || state?.animals?.directoryMeta?.timeZone,
  };
}

export function renderAnimals(state, context = {}) {
  const active = viewContext(state, context);
  const t = active.translate;
  const allAnimals = Array.isArray(state?.animals?.items) ? state.animals.items : [];
  if ((state?.animals?.status === "idle" || state?.animals?.status === "loading") && !allAnimals.length) {
    return renderShell(renderLoading(t("loading")), active);
  }
  if (state?.animals?.status === "error" && !allAnimals.length) {
    return renderShell(renderError(state.animals.error, "refresh", active), active);
  }

  const filters = state?.animals?.filters || {};
  const search = `<label class="search"><ha-icon icon="mdi:magnify"></ha-icon><input data-action="animals-filter" value="${escapeAttribute(filters.query || "")}" placeholder="${escapeAttribute(t("searchAnimals"))}" autocomplete="off"></label>`;
  const archivedLabel = filters.includeArchived === false
    ? t("showArchived")
    : t("hideArchived");
  const archived = `<button data-action="animals-toggle-archived"><ha-icon icon="mdi:archive-outline"></ha-icon>${escapeHtml(archivedLabel)}</button>`;
  const create = `<button class="primary" data-action="create-animal"><ha-icon icon="mdi:plus-circle-outline"></ha-icon>${escapeHtml(t("createAnimal"))}</button>`;
  const animals = selectVisibleAnimals(state);
  const cards = animals.map((animal) => renderAnimalCard(animal, {
    ...active,
    nextOccurrence: selectNextOccurrenceForAnimal(state, animal.id),
  })).join("") || renderEmpty(t("noAnimals"));
  const content = `${renderHeading(t("animals"), `${search}${archived}${create}`)}<section class="grid">${cards}</section>`;
  return renderShell(content, active);
}
