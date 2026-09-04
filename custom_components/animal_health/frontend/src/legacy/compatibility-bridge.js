import {
  MIGRATED_READ_ROUTES,
  createReadOnlyAnimalsRuntime,
} from "../app/read-only-animals.js";
import { validationError } from "../api/errors.js";
import { isPlainObject, requireName } from "../platform/transport.js";

const INSTALLED_PANEL_CLASSES = new WeakSet();
const PANEL_STATES = new WeakMap();

function requireDelegate(value, path) {
  if (typeof value !== "function") {
    throw validationError(`${path} must be a function`, path);
  }
  return value;
}

export function createCompatibilityBridge(options = {}) {
  if (!isPlainObject(options)) {
    throw validationError("legacy bridge options must be a plain object", "legacy");
  }
  const routes = options.migratedRoutes ?? [];
  if (!Array.isArray(routes)) {
    throw validationError(
      "migratedRoutes must be an array",
      "legacy.migratedRoutes",
    );
  }
  const migrated = new Set(
    routes.map((routeName) => requireName(routeName, "routeName")),
  );
  const legacyDelegate = requireDelegate(
    options.legacyDelegate ?? (() => undefined),
    "legacy.legacyDelegate",
  );
  const newDelegate = requireDelegate(
    options.newDelegate ?? (() => undefined),
    "legacy.newDelegate",
  );

  function modeFor(routeName) {
    const name = requireName(routeName, "routeName");
    return migrated.has(name) ? "new" : "legacy";
  }

  function markMigrated(routeName) {
    const name = requireName(routeName, "routeName");
    const changed = !migrated.has(name);
    migrated.add(name);
    return changed;
  }

  function markLegacy(routeName) {
    return migrated.delete(requireName(routeName, "routeName"));
  }

  function delegate(routeName, context = {}) {
    const name = requireName(routeName, "routeName");
    if (!isPlainObject(context)) {
      throw validationError("legacy context must be a plain object", "context");
    }
    const handler = migrated.has(name) ? newDelegate : legacyDelegate;
    return handler(name, context);
  }

  return Object.freeze({
    modeFor,
    markMigrated,
    markLegacy,
    delegate,
  });
}

function isMigratedRoute(routeName) {
  return MIGRATED_READ_ROUTES.includes(String(routeName ?? ""));
}

function requirePanelClass(value) {
  if (typeof value !== "function" || !value.prototype) {
    throw validationError(
      "LegacyPanelClass must be a constructor",
      "LegacyPanelClass",
    );
  }
  return value;
}

function captureLegacyMethods(prototype) {
  const result = {};
  for (const method of [
    "render",
    "load",
    "loadDetail",
    "handleClick",
    "handleInput",
    "handleSubmit",
  ]) {
    result[method] = requireDelegate(
      prototype[method],
      `LegacyPanelClass.prototype.${method}`,
    );
  }
  return Object.freeze(result);
}

function panelState(panel) {
  let state = PANEL_STATES.get(panel);
  if (!state) {
    state = {
      runtime: null,
      legacyDepth: 0,
    };
    PANEL_STATES.set(panel, state);
  }
  return state;
}

function mustUseLegacy(panel, state) {
  return Boolean(
    state.legacyDepth > 0 ||
      panel.modal ||
      !isMigratedRoute(panel.view),
  );
}

async function withLegacyInteraction(
  panel,
  state,
  runtimeFor,
  callback,
  { ensureReady = false, refreshAfter = false } = {},
) {
  state.legacyDepth += 1;
  let succeeded = false;
  try {
    if (ensureReady) await runtimeFor(panel, state).ensureLegacyReady();
    const result = await callback();
    succeeded = true;
    return result;
  } finally {
    state.legacyDepth -= 1;
    if (
      succeeded &&
      refreshAfter &&
      state.legacyDepth === 0 &&
      !panel.modal &&
      isMigratedRoute(panel.view)
    ) {
      await Promise.resolve(
        runtimeFor(panel, state).refreshCurrentRoute(),
      ).catch(() => undefined);
    }
  }
}

export function installLegacyReadOnlyAnimalsSlice(
  LegacyPanelClassValue,
  options = {},
) {
  const LegacyPanelClass = requirePanelClass(LegacyPanelClassValue);
  if (!isPlainObject(options)) {
    throw validationError("bridge options must be a plain object", "options");
  }
  if (INSTALLED_PANEL_CLASSES.has(LegacyPanelClass)) return false;

  const prototype = LegacyPanelClass.prototype;
  const legacy = captureLegacyMethods(prototype);
  const runtimeFactory = requireDelegate(
    options.runtimeFactory ?? createReadOnlyAnimalsRuntime,
    "runtimeFactory",
  );
  const integrationVersion = String(options.integrationVersion ?? "unknown");

  function runtimeFor(panel, state = panelState(panel)) {
    if (!state.runtime) {
      state.runtime = runtimeFactory({
        panel,
        legacy,
        integrationVersion,
      });
    }
    return state.runtime;
  }

  prototype.render = function renderPhase4Route() {
    const state = panelState(this);
    if (mustUseLegacy(this, state)) return legacy.render.call(this);
    return runtimeFor(this, state).render();
  };

  prototype.load = function loadPhase4Route(optionsValue = {}) {
    const state = panelState(this);
    if (mustUseLegacy(this, state)) return legacy.load.call(this);
    const settings = isPlainObject(optionsValue) ? optionsValue : {};
    return runtimeFor(this, state).load(settings);
  };

  prototype.loadDetail = function loadPhase4Detail(animalId, ...args) {
    const state = panelState(this);
    if (mustUseLegacy(this, state)) {
      return legacy.loadDetail.call(this, animalId, ...args);
    }
    return runtimeFor(this, state).openAnimal(animalId);
  };

  prototype.handleClick = function handlePhase4Click(event) {
    const state = panelState(this);
    if (state.legacyDepth > 0) return legacy.handleClick.call(this, event);
    if (this.modal) {
      return withLegacyInteraction(
        this,
        state,
        runtimeFor,
        () => legacy.handleClick.call(this, event),
        { refreshAfter: true },
      );
    }
    const runtime = runtimeFor(this, state);
    if (runtime.handlesEvent(event)) return runtime.handleEvent(event);
    return withLegacyInteraction(
      this,
      state,
      runtimeFor,
      () => legacy.handleClick.call(this, event),
      { ensureReady: true, refreshAfter: true },
    );
  };

  prototype.handleInput = function handlePhase4Input(event) {
    const state = panelState(this);
    if (state.legacyDepth > 0 || this.modal) {
      return legacy.handleInput.call(this, event);
    }
    const runtime = runtimeFor(this, state);
    return runtime.handlesEvent(event)
      ? runtime.handleEvent(event)
      : legacy.handleInput.call(this, event);
  };

  prototype.handleSubmit = function handlePhase4Submit(event) {
    const state = panelState(this);
    return withLegacyInteraction(
      this,
      state,
      runtimeFor,
      () => legacy.handleSubmit.call(this, event),
      { refreshAfter: true },
    );
  };

  INSTALLED_PANEL_CLASSES.add(LegacyPanelClass);
  return true;
}
