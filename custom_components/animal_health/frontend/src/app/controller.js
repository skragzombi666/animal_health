import {
  AnimalHealthError,
  ERROR_CODES,
  normalizeError,
  validationError,
} from "../api/errors.js";
import { isPlainObject, requireName } from "../platform/transport.js";

function assertDependency(value, name, methods) {
  if (value === null || typeof value !== "object") {
    throw validationError(`${name} must be an object`, name);
  }
  for (const method of methods) {
    if (typeof value[method] !== "function") {
      throw validationError(`${name}.${method} must be a function`, `${name}.${method}`);
    }
  }
  return value;
}

function operationError(error, operation) {
  const normalized = normalizeError(error, { operation });
  if (normalized.operation === operation) return normalized;
  return new AnimalHealthError(normalized.message, {
    code: normalized.code,
    operation,
    details: normalized.details,
    cause: normalized,
  });
}

function errorRecord(error) {
  return {
    code: error.code,
    message: error.message,
    operation: error.operation,
    details: { ...error.details },
  };
}

function parseDatasetRecord(value, path) {
  if (value === undefined || value === null || value === "") return {};
  let parsed;
  try {
    parsed = JSON.parse(String(value));
  } catch (error) {
    throw validationError(`${path} must contain valid JSON`, path, {
      cause: error instanceof Error ? error.message : String(error),
    });
  }
  if (!isPlainObject(parsed)) {
    throw validationError(`${path} must contain a JSON object`, path);
  }
  return parsed;
}

function actionTarget(event) {
  if (event === null || typeof event !== "object") return null;
  const path =
    typeof event.composedPath === "function"
      ? event.composedPath()
      : [event.target];
  if (!Array.isArray(path)) return null;
  return (
    path.find(
      (candidate) =>
        candidate &&
        candidate.dataset &&
        typeof candidate.dataset.action === "string" &&
        candidate.dataset.action.trim(),
    ) || null
  );
}

function eventContext(event, target) {
  const dataset = { ...target.dataset };
  const context = {
    event,
    target,
    dataset,
  };
  if (dataset.route) {
    context.route = {
      name: dataset.route,
      params: parseDatasetRecord(
        dataset.routeParams,
        "data-route-params",
      ),
    };
  }
  if (dataset.dialogType) {
    context.dialogType = dataset.dialogType;
    context.data = parseDatasetRecord(
      dataset.dialogData,
      "data-dialog-data",
    );
  }
  return context;
}

export function createController({ store, router, client, actions = {} } = {}) {
  const actualStore = assertDependency(store, "store", [
    "getState",
    "update",
    "beginRequest",
    "commitRequest",
    "failRequest",
  ]);
  const actualRouter = assertDependency(router, "router", [
    "navigate",
    "back",
    "openDialog",
    "closeDialog",
  ]);
  if (!isPlainObject(actions)) {
    throw validationError("actions must be a plain object", "actions");
  }

  const registry = new Map();
  let actionSequence = 0;

  function register(name, handler) {
    const actionName = requireName(name, "action.name");
    if (typeof handler !== "function") {
      throw validationError("action handler must be a function", "action.handler");
    }
    if (registry.has(actionName)) {
      throw new AnimalHealthError(`Action already registered: ${actionName}`, {
        code: ERROR_CODES.CONFLICT,
        operation: "registerAction",
        details: { action: actionName },
      });
    }
    registry.set(actionName, handler);
    return handler;
  }

  function unregister(name) {
    return registry.delete(requireName(name, "action.name"));
  }

  function recordActionFailure(name, error) {
    const key = `action:${name}`;
    const normalized = operationError(error, key);
    actualStore.update((state) => ({
      ...state,
      requests: {
        ...state.requests,
        [key]: {
          key,
          id: ++actionSequence,
          navigationRevision: state.navigation.revision,
          status: "error",
          error: errorRecord(normalized),
        },
      },
    }));
    return normalized;
  }

  async function dispatch(name, context = {}) {
    const actionName = requireName(name, "action.name");
    if (!isPlainObject(context)) {
      throw validationError("action context must be a plain object", "action.context");
    }
    const handler = registry.get(actionName);
    if (!handler) return false;
    try {
      return await handler(context);
    } catch (error) {
      throw recordActionFailure(actionName, error);
    }
  }

  async function handleEvent(event) {
    const target = actionTarget(event);
    if (!target) return false;
    const name = requireName(target.dataset.action, "action.name");
    if (event.type === "submit") event.preventDefault?.();
    let context;
    try {
      context = eventContext(event, target);
    } catch (error) {
      throw recordActionFailure(name, error);
    }
    return dispatch(name, context);
  }

  async function runLatest(key, operation, applyResult) {
    const requestKey = requireName(key, "request.key");
    if (typeof operation !== "function") {
      throw validationError("request operation must be a function", "operation");
    }
    if (typeof applyResult !== "function") {
      throw validationError("result applicator must be a function", "applyResult");
    }
    const token = actualStore.beginRequest(requestKey);
    try {
      const result = await operation({
        client,
        store: actualStore,
        router: actualRouter,
        token,
      });
      const applied = actualStore.commitRequest(token, (state) => {
        const next = applyResult(state, result);
        if (!isPlainObject(next)) {
          throw validationError(
            "result applicator must return a plain object",
            "applyResult",
          );
        }
        return next;
      });
      return { applied, result };
    } catch (error) {
      const normalized = operationError(error, `request:${requestKey}`);
      actualStore.failRequest(token, normalized);
      throw normalized;
    }
  }

  register("app.navigate", ({ route }) => actualRouter.navigate(route));
  register("app.back", () => actualRouter.back());
  register("dialog.open", ({ dialogType, data = {} }) =>
    actualRouter.openDialog(dialogType, data),
  );
  register("dialog.close", () => actualRouter.closeDialog());
  for (const [name, handler] of Object.entries(actions)) register(name, handler);

  return Object.freeze({
    register,
    unregister,
    dispatch,
    handleEvent,
    runLatest,
  });
}
