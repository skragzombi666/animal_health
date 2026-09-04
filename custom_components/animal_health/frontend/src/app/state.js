import { validationError } from "../api/errors.js";
import { isPlainObject, requireName } from "../platform/transport.js";

const RESOURCE_SLICE = Object.freeze({
  status: "idle",
  items: [],
  error: null,
});

const BASE_STATE = Object.freeze({
  platform: {
    kind: "unknown",
    available: false,
    metadata: {},
  },
  language: {
    code: "de",
    locale: "de-CH",
  },
  navigation: {
    current: { name: "overview", params: {} },
    stack: [],
    revision: 0,
  },
  dialog: {
    open: false,
    type: null,
    data: {},
  },
  animals: RESOURCE_SLICE,
  timeline: RESOURCE_SLICE,
  tasks: RESOURCE_SLICE,
  products: RESOURCE_SLICE,
  treatments: RESOURCE_SLICE,
  settings: {
    status: "idle",
    data: null,
    error: null,
  },
  drafts: {},
  requests: {},
  notifications: [],
});

const STATE_KEYS = new Set(Object.keys(BASE_STATE));

export function cloneValue(value, path = "value") {
  if (Array.isArray(value)) {
    return value.map((item, index) => cloneValue(item, `${path}[${index}]`));
  }
  if (isPlainObject(value)) {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [
        key,
        cloneValue(item, `${path}.${key}`),
      ]),
    );
  }
  if (
    value === null ||
    value === undefined ||
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return value;
  }
  throw validationError(`${path} must contain JSON-compatible values`, path);
}

function mergeValue(base, override, path) {
  if (override === undefined) return cloneValue(base, path);
  if (isPlainObject(base) && isPlainObject(override)) {
    const result = {};
    for (const key of new Set([
      ...Object.keys(base),
      ...Object.keys(override),
    ])) {
      result[key] = mergeValue(base[key], override[key], `${path}.${key}`);
    }
    return result;
  }
  return cloneValue(override, path);
}

function nonNegativeInteger(value, path) {
  const number = Number(value);
  if (!Number.isInteger(number) || number < 0) {
    throw validationError(`${path} must be a non-negative integer`, path);
  }
  return number;
}

export function createRoute(value = { name: "overview", params: {} }) {
  const route =
    typeof value === "string"
      ? { name: value, params: {} }
      : value;
  if (!isPlainObject(route)) {
    throw validationError("route must be a plain object or route name", "route");
  }
  const params = route.params === undefined ? {} : route.params;
  if (!isPlainObject(params)) {
    throw validationError("route.params must be a plain object", "route.params");
  }
  return {
    name: requireName(route.name, "route.name"),
    params: cloneValue(params, "route.params"),
  };
}

export function createInitialState(overrides = {}) {
  if (!isPlainObject(overrides)) {
    throw validationError("state overrides must be a plain object", "state");
  }
  for (const key of Object.keys(overrides)) {
    if (!STATE_KEYS.has(key)) {
      throw validationError(`Unknown application state slice: ${key}`, `state.${key}`);
    }
  }

  const state = mergeValue(BASE_STATE, overrides, "state");
  if (!isPlainObject(state.navigation)) {
    throw validationError("state.navigation must be a plain object", "state.navigation");
  }
  state.navigation.current = createRoute(state.navigation.current);
  if (!Array.isArray(state.navigation.stack)) {
    throw validationError(
      "state.navigation.stack must be an array",
      "state.navigation.stack",
    );
  }
  state.navigation.stack = state.navigation.stack.map((route) => createRoute(route));
  state.navigation.revision = nonNegativeInteger(
    state.navigation.revision,
    "state.navigation.revision",
  );

  if (!Array.isArray(state.notifications)) {
    throw validationError(
      "state.notifications must be an array",
      "state.notifications",
    );
  }
  if (!isPlainObject(state.requests)) {
    throw validationError("state.requests must be a plain object", "state.requests");
  }
  if (!isPlainObject(state.drafts)) {
    throw validationError("state.drafts must be a plain object", "state.drafts");
  }
  return state;
}
