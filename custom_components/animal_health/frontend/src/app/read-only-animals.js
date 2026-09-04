import { AnimalHealthClient } from "../api/client.js";
import { normalizeError, validationError } from "../api/errors.js";
import { createController } from "./controller.js";
import { createRouter } from "./router.js";
import { createStore } from "./store.js";
import { createHomeAssistantTransport } from "../platform/home-assistant-adapter.js";
import { isPlainObject, requireName } from "../platform/transport.js";
import { createTranslator } from "../ui/read-only/i18n.js";
import { renderAnimalDetail } from "../ui/views/animal-detail.js";
import { renderAnimals } from "../ui/views/animals.js";
import { renderOverview } from "../ui/views/overview.js";

export const MIGRATED_READ_ROUTES = Object.freeze([
  "overview",
  "animals",
  "animal-detail",
]);

const MODERN_ACTIONS = new Set([
  "refresh",
  "read.refresh",
  "detail-refresh",
  "animal-detail",
  "home-group-toggle",
  "home-group-select",
  "home-tag-toggle",
  "home-tag-select",
  "home-search-toggle",
  "home-search",
  "home-filter-reset",
  "animals-filter",
  "animals-toggle-archived",
]);

function migrated(routeName) {
  return MIGRATED_READ_ROUTES.includes(String(routeName ?? ""));
}

function languageFromPanel(panel) {
  return String(panel?.h?.language || "en").toLocaleLowerCase().startsWith("de")
    ? { code: "de", locale: "de-CH" }
    : { code: "en", locale: "en-GB" };
}

function targetFromEvent(event) {
  if (!event || typeof event !== "object") return null;
  const path = typeof event.composedPath === "function"
    ? event.composedPath()
    : [event.target];
  return Array.isArray(path)
    ? path.find((candidate) => candidate?.dataset && (candidate.dataset.action || candidate.dataset.view)) || null
    : null;
}

function requiredPanel(panel) {
  if (!panel || typeof panel !== "object") {
    throw validationError("panel must be an object", "panel");
  }
  if (!panel.shadowRoot || typeof panel.shadowRoot !== "object") {
    throw validationError("panel.shadowRoot must be available", "panel.shadowRoot");
  }
  return panel;
}

function requiredLegacy(legacy) {
  if (!legacy || typeof legacy !== "object") {
    throw validationError("legacy methods must be an object", "legacy");
  }
  for (const method of ["load", "render", "loadDetail", "handleClick", "handleInput"]) {
    if (typeof legacy[method] !== "function") {
      throw validationError(`legacy.${method} must be a function`, `legacy.${method}`);
    }
  }
  return legacy;
}

function initialState(panel) {
  const language = languageFromPanel(panel);
  const routeName = migrated(panel.view) ? panel.view : "overview";
  const animalId = routeName === "animal-detail"
    ? panel.detail?.animal?.id || null
    : null;
  return {
    platform: {
      kind: panel.h?.standalone ? "android" : "home-assistant",
      available: Boolean(panel.h),
      metadata: {},
    },
    language,
    navigation: {
      current: {
        name: routeName,
        params: animalId ? { animalId: String(animalId) } : {},
      },
      stack: [],
      revision: 0,
    },
    animals: {
      status: "idle",
      items: [],
      groups: [],
      tags: [],
      catalog: {},
      directoryMeta: {
        version: null,
        generatedAt: null,
        timeZone: null,
        today: null,
        summary: {},
        exports: {},
      },
      filters: {
        query: "",
        groupId: "all",
        tagId: "all",
        includeArchived: true,
        openPanel: null,
        searchOpen: false,
      },
      detail: {
        status: "idle",
        animalId,
        data: null,
        error: null,
      },
      error: null,
    },
    tasks: {
      status: "idle",
      definitions: [],
      occurrences: [],
      error: null,
    },
    timeline: {
      status: "idle",
      items: [],
      error: null,
    },
  };
}

function applyDirectory(state, directory) {
  return {
    ...state,
    animals: {
      ...state.animals,
      status: "ready",
      items: [...directory.animals],
      groups: [...directory.groups],
      tags: [...directory.tags],
      catalog: { ...directory.catalog },
      directoryMeta: {
        version: directory.version,
        generatedAt: directory.generatedAt,
        timeZone: directory.timeZone,
        today: directory.today,
        summary: { ...directory.summary },
        exports: { ...(directory.exports || {}) },
      },
      error: null,
    },
    tasks: {
      ...state.tasks,
      status: "ready",
      definitions: [...directory.tasks],
      occurrences: [...directory.occurrences],
      error: null,
    },
    timeline: {
      ...state.timeline,
      status: "ready",
      items: [...directory.events],
      error: null,
    },
  };
}

function mergeDirectoryIdentity(state, detail) {
  const id = String(detail?.animal?.id ?? "");
  const directoryAnimal = state.animals.items.find((animal) => String(animal.id) === id);
  if (!directoryAnimal) return detail;
  return {
    ...detail,
    animal: {
      ...directoryAnimal,
      ...detail.animal,
      groupId: detail.animal.groupId ?? directoryAnimal.groupId,
      tagIds: detail.animal.tagIds?.length ? detail.animal.tagIds : directoryAnimal.tagIds,
      profileAttachmentId: detail.animal.profileAttachmentId ?? directoryAnimal.profileAttachmentId,
    },
  };
}

function routeContext(state, context = {}) {
  const language = context.language || state?.language?.code || "en";
  const locale = context.locale || state?.language?.locale || (language === "de" ? "de-CH" : "en-GB");
  return {
    ...context,
    language,
    locale,
    translate: context.translate || createTranslator(language),
    routeName: state?.navigation?.current?.name || "overview",
    timeZone: context.timeZone || state?.animals?.directoryMeta?.timeZone || null,
  };
}

export function renderReadOnlyAnimalsRoute(state, context = {}) {
  const routeName = state?.navigation?.current?.name;
  const active = routeContext(state, context);
  if (routeName === "overview") return renderOverview(state, active);
  if (routeName === "animals") return renderAnimals(state, active);
  if (routeName === "animal-detail") return renderAnimalDetail(state, active);
  throw validationError(`Route is not migrated: ${routeName}`, "route.name", {
    routeName,
  });
}

export function createReadOnlyAnimalsRuntime({
  panel: panelValue,
  legacy: legacyValue,
  client: clientValue = null,
  integrationVersion = "unknown",
} = {}) {
  const panel = requiredPanel(panelValue);
  const legacy = requiredLegacy(legacyValue);
  const client = clientValue || new AnimalHealthClient(
    createHomeAssistantTransport({ getHass: () => panel.h }),
  );
  for (const method of ["getAnimalDirectory", "getAnimalDetail"]) {
    if (typeof client[method] !== "function") {
      throw validationError(`client.${method} must be a function`, `client.${method}`);
    }
  }

  const store = createStore(initialState(panel));
  const router = createRouter(store);
  let legacyLoad = null;
  let destroyed = false;

  function requestRender() {
    if (!destroyed && migrated(panel.view) && !panel.modal && typeof panel.render === "function") {
      panel.render();
    }
  }

  const unsubscribe = store.subscribe(requestRender);

  function updateFilters(patch) {
    if (!isPlainObject(patch)) {
      throw validationError("filter update must be a plain object", "filters");
    }
    store.update((state) => ({
      ...state,
      animals: {
        ...state.animals,
        filters: {
          ...state.animals.filters,
          ...patch,
        },
      },
    }));
  }

  async function load({ force = false } = {}) {
    const current = store.getState();
    if (!force && current.animals.status === "ready") return current;
    store.update((state) => ({
      ...state,
      animals: { ...state.animals, status: "loading", error: null },
      tasks: { ...state.tasks, status: "loading", error: null },
      timeline: { ...state.timeline, status: "loading", error: null },
    }));
    try {
      const outcome = await controller.runLatest(
        "animal-directory",
        () => client.getAnimalDirectory(),
        applyDirectory,
      );
      if (outcome.applied) return store.getState();
      return outcome;
    } catch (error) {
      const normalized = normalizeError(error, { operation: "loadAnimalDirectory" });
      store.update((state) => ({
        ...state,
        animals: { ...state.animals, status: "error", error: normalized },
        tasks: { ...state.tasks, status: "error", error: normalized },
        timeline: { ...state.timeline, status: "error", error: normalized },
      }));
      throw normalized;
    }
  }

  async function loadDetail(animalId, { force = false } = {}) {
    const id = requireName(animalId, "animalId");
    if (store.getState().animals.status !== "ready") await load();
    const current = store.getState().animals.detail;
    if (!force && current.status === "ready" && current.animalId === id) {
      return current.data;
    }
    store.update((state) => ({
      ...state,
      animals: {
        ...state.animals,
        detail: {
          status: "loading",
          animalId: id,
          data: current.animalId === id ? current.data : null,
          error: null,
        },
      },
    }));
    try {
      const outcome = await controller.runLatest(
        "animal-detail",
        () => client.getAnimalDetail(id, {
          today: store.getState().animals.directoryMeta.today,
        }),
        (state, detail) => ({
          ...state,
          animals: {
            ...state.animals,
            detail: {
              status: "ready",
              animalId: id,
              data: mergeDirectoryIdentity(state, detail),
              error: null,
            },
          },
        }),
      );
      return outcome.applied ? store.getState().animals.detail.data : outcome;
    } catch (error) {
      const normalized = normalizeError(error, { operation: "loadAnimalDetail" });
      const active = store.getState();
      if (
        active.navigation.current.name === "animal-detail" &&
        active.navigation.current.params.animalId === id
      ) {
        store.update((state) => ({
          ...state,
          animals: {
            ...state.animals,
            detail: {
              status: "error",
              animalId: id,
              data: state.animals.detail.animalId === id
                ? state.animals.detail.data
                : null,
              error: normalized,
            },
          },
        }));
      }
      throw normalized;
    }
  }

  async function openAnimal(animalId) {
    const id = requireName(animalId, "animalId");
    if (store.getState().animals.status !== "ready") await load();
    panel.view = "animal-detail";
    router.navigate({ name: "animal-detail", params: { animalId: id } });
    return loadDetail(id);
  }

  async function ensureLegacyReady() {
    if (panel.d) return panel.d;
    if (!legacyLoad) {
      legacyLoad = Promise.resolve(legacy.load.call(panel)).finally(() => {
        legacyLoad = null;
      });
    }
    await legacyLoad;
    return panel.d;
  }

  async function navigate(routeName) {
    const name = requireName(routeName, "route.name");
    if (migrated(name)) {
      panel.view = name;
      router.navigate({ name, params: {} });
      if (store.getState().animals.status === "idle") await load();
      return { mode: "new", route: router.current() };
    }
    panel.view = name;
    panel.detail = null;
    await ensureLegacyReady();
    legacy.render.call(panel);
    return { mode: "legacy", route: name };
  }

  const controller = createController({
    store,
    router,
    client,
    actions: {
      "read.refresh": () => load({ force: true }),
      refresh: () =>
        router.current().name === "animal-detail"
          ? loadDetail(router.current().params.animalId, { force: true })
          : load({ force: true }),
      "detail-refresh": () =>
        loadDetail(router.current().params.animalId, { force: true }),
      "animal-detail": ({ id }) => openAnimal(id),
      "home-group-toggle": () => {
        const filters = store.getState().animals.filters;
        updateFilters({ openPanel: filters.openPanel === "group" ? null : "group" });
      },
      "home-group-select": ({ id }) => updateFilters({ groupId: id || "all", openPanel: null }),
      "home-tag-toggle": () => {
        const filters = store.getState().animals.filters;
        updateFilters({ openPanel: filters.openPanel === "tag" ? null : "tag" });
      },
      "home-tag-select": ({ id }) => updateFilters({ tagId: id || "all", openPanel: null }),
      "home-search-toggle": () => {
        const filters = store.getState().animals.filters;
        updateFilters({ searchOpen: !filters.searchOpen });
      },
      "home-search": ({ value }) => updateFilters({ query: String(value ?? "") }),
      "home-filter-reset": () => updateFilters({
        query: "",
        groupId: "all",
        tagId: "all",
        includeArchived: true,
        openPanel: null,
        searchOpen: false,
      }),
      "animals-filter": ({ value }) => updateFilters({ query: String(value ?? "") }),
      "animals-toggle-archived": () => {
        const filters = store.getState().animals.filters;
        updateFilters({ includeArchived: !filters.includeArchived });
      },
    },
  });

  function handlesEvent(event) {
    const target = targetFromEvent(event);
    if (!target) return false;
    if (target.dataset.view) return true;
    return MODERN_ACTIONS.has(String(target.dataset.action || ""));
  }

  async function handleEvent(event) {
    const target = targetFromEvent(event);
    if (!target) return false;
    if (target.dataset.view) return navigate(target.dataset.view);
    const action = String(target.dataset.action || "");
    if (!MODERN_ACTIONS.has(action)) return false;
    return controller.dispatch(action, {
      event,
      target,
      id: target.dataset.id || null,
      value: target.value,
    });
  }

  function render() {
    const language = languageFromPanel(panel);
    const state = store.getState();
    const html = renderReadOnlyAnimalsRoute(state, {
      language: language.code,
      locale: language.locale,
      translate: createTranslator(language.code),
      routeName: state.navigation.current.name,
      integrationVersion,
      narrow: typeof panel.hasAttribute === "function" && panel.hasAttribute("narrow"),
      timeZone: state.animals.directoryMeta.timeZone,
    });
    panel.shadowRoot.innerHTML = html;
    return html;
  }

  function destroy() {
    if (destroyed) return;
    destroyed = true;
    unsubscribe();
  }

  return Object.freeze({
    store,
    router,
    controller,
    client,
    load,
    loadDetail,
    openAnimal,
    navigate,
    ensureLegacyReady,
    handlesEvent,
    handleEvent,
    render,
    destroy,
  });
}
