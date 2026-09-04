import { validationError } from "../api/errors.js";
import { isPlainObject, requireName } from "../platform/transport.js";

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
