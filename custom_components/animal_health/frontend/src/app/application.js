import { AnimalHealthClient } from "../api/client.js";
import {
  AnimalHealthError,
  ERROR_CODES,
  validationError,
} from "../api/errors.js";
import { createCompatibilityBridge } from "../legacy/compatibility-bridge.js";
import { isPlainObject, requireName } from "../platform/transport.js";
import {
  createAnimalHealthPanelClass,
  renderApplicationShell,
} from "./animal-health-panel.js";
import { createController } from "./controller.js";
import { createRouter } from "./router.js";
import { createStore } from "./store.js";

function assertRegistry(registry) {
  if (registry === null || typeof registry !== "object") {
    throw validationError("element registry must be an object", "registry");
  }
  for (const method of ["get", "define"]) {
    if (typeof registry[method] !== "function") {
      throw validationError(
        `registry.${method} must be a function`,
        `registry.${method}`,
      );
    }
  }
  return registry;
}

export function createAnimalHealthApplication(options = {}) {
  if (!isPlainObject(options)) {
    throw validationError("application options must be a plain object", "options");
  }

  const client = new AnimalHealthClient(options.transport);
  const store = createStore(options.initialState);
  const router = createRouter(store);
  const controller = createController({
    store,
    router,
    client,
    actions: options.actions,
  });
  const bridge = createCompatibilityBridge(options.legacy);
  const PanelClass = createAnimalHealthPanelClass({
    store,
    controller,
    render: options.render ?? renderApplicationShell,
    HTMLElementBase: options.HTMLElementBase,
  });

  function define(registryValue, tagName = "animal-health-phase-3") {
    const registry = assertRegistry(registryValue);
    const name = requireName(tagName, "tagName");
    const existing = registry.get(name);
    if (existing === PanelClass) return PanelClass;
    if (existing) {
      throw new AnimalHealthError(
        `Custom element tag is already occupied: ${name}`,
        {
          code: ERROR_CODES.CONFLICT,
          operation: "defineApplicationElement",
          details: { tagName: name },
        },
      );
    }
    registry.define(name, PanelClass);
    return PanelClass;
  }

  return Object.freeze({
    client,
    store,
    router,
    controller,
    bridge,
    PanelClass,
    define,
  });
}
