import { normalizeError, validationError } from "../api/errors.js";
import { isPlainObject, requireName } from "../platform/transport.js";
import { createInitialState } from "./state.js";

function applyUpdate(current, updateOrPatch, path = "state update") {
  if (typeof updateOrPatch === "function") {
    const next = updateOrPatch(current);
    if (!isPlainObject(next)) {
      throw validationError(`${path} must return a plain object`, path);
    }
    return next;
  }
  if (!isPlainObject(updateOrPatch)) {
    throw validationError(`${path} must be a function or plain object`, path);
  }
  const entries = Object.entries(updateOrPatch);
  if (entries.every(([key, value]) => Object.is(current[key], value))) {
    return current;
  }
  return { ...current, ...updateOrPatch };
}

function errorRecord(error) {
  const normalized = normalizeError(error);
  return {
    code: normalized.code,
    message: normalized.message,
    operation: normalized.operation,
    details: { ...normalized.details },
  };
}

export function createStore(initialState = {}) {
  let state = createInitialState(initialState);
  const listeners = new Set();
  let requestSequence = 0;

  function replaceState(next) {
    if (next === state) return state;
    if (!isPlainObject(next)) {
      throw validationError("application state must be a plain object", "state");
    }
    const previous = state;
    state = next;
    for (const listener of [...listeners]) listener(state, previous);
    return state;
  }

  function getState() {
    return state;
  }

  function update(updateOrPatch) {
    return replaceState(applyUpdate(state, updateOrPatch));
  }

  function subscribe(listener) {
    if (typeof listener !== "function") {
      throw validationError("store listener must be a function", "listener");
    }
    listeners.add(listener);
    let active = true;
    return () => {
      if (!active) return;
      active = false;
      listeners.delete(listener);
    };
  }

  function beginRequest(key) {
    const requestKey = requireName(key, "request.key");
    const token = Object.freeze({
      key: requestKey,
      id: ++requestSequence,
      navigationRevision: state.navigation.revision,
    });
    update((current) => ({
      ...current,
      requests: {
        ...current.requests,
        [requestKey]: {
          ...token,
          status: "pending",
          error: null,
        },
      },
    }));
    return token;
  }

  function isCurrentRequest(token) {
    if (!token || typeof token !== "object") return false;
    const active = state.requests[token.key];
    return Boolean(
      active &&
        active.id === token.id &&
        active.navigationRevision === token.navigationRevision &&
        state.navigation.revision === token.navigationRevision,
    );
  }

  function commitRequest(token, updateOrPatch = {}) {
    if (!isCurrentRequest(token)) return false;
    const active = state.requests[token.key];
    const updated = applyUpdate(state, updateOrPatch, "request result update");
    const updatedRequests = isPlainObject(updated.requests)
      ? updated.requests
      : state.requests;
    replaceState({
      ...updated,
      requests: {
        ...updatedRequests,
        [token.key]: {
          ...active,
          status: "success",
          error: null,
        },
      },
    });
    return true;
  }

  function failRequest(token, error) {
    if (!isCurrentRequest(token)) return false;
    const active = state.requests[token.key];
    update((current) => ({
      ...current,
      requests: {
        ...current.requests,
        [token.key]: {
          ...active,
          status: "error",
          error: errorRecord(error),
        },
      },
    }));
    return true;
  }

  return Object.freeze({
    getState,
    update,
    subscribe,
    beginRequest,
    commitRequest,
    failRequest,
    isCurrentRequest,
  });
}
