import { validationError } from "../api/errors.js";
import { isPlainObject, requireName } from "../platform/transport.js";
import { cloneValue, createRoute } from "./state.js";

function closedDialog() {
  return {
    open: false,
    type: null,
    data: {},
  };
}

function equalValue(left, right) {
  if (Object.is(left, right)) return true;
  if (Array.isArray(left) || Array.isArray(right)) {
    if (!Array.isArray(left) || !Array.isArray(right)) return false;
    if (left.length !== right.length) return false;
    return left.every((item, index) => equalValue(item, right[index]));
  }
  if (isPlainObject(left) || isPlainObject(right)) {
    if (!isPlainObject(left) || !isPlainObject(right)) return false;
    const leftKeys = Object.keys(left).sort();
    const rightKeys = Object.keys(right).sort();
    if (!equalValue(leftKeys, rightKeys)) return false;
    return leftKeys.every((key) => equalValue(left[key], right[key]));
  }
  return false;
}

function assertStore(store) {
  if (store === null || typeof store !== "object") {
    throw validationError("store must be an object", "store");
  }
  for (const method of ["getState", "update"]) {
    if (typeof store[method] !== "function") {
      throw validationError(`store.${method} must be a function`, `store.${method}`);
    }
  }
  return store;
}

export function createRouter(storeValue) {
  const store = assertStore(storeValue);

  function current() {
    return store.getState().navigation.current;
  }

  function navigate(routeValue, options = {}) {
    if (!isPlainObject(options)) {
      throw validationError("navigation options must be a plain object", "options");
    }
    const next = createRoute(routeValue);
    const state = store.getState();
    if (equalValue(state.navigation.current, next)) {
      return state.navigation.current;
    }
    const replace = options.replace === true;
    store.update((active) => ({
      ...active,
      navigation: {
        current: next,
        stack: replace
          ? active.navigation.stack
          : [...active.navigation.stack, active.navigation.current],
        revision: active.navigation.revision + 1,
      },
      dialog: closedDialog(),
    }));
    return store.getState().navigation.current;
  }

  function replace(routeValue) {
    return navigate(routeValue, { replace: true });
  }

  function back() {
    const state = store.getState();
    const stack = state.navigation.stack;
    if (!stack.length) return state.navigation.current;
    const previous = createRoute(stack[stack.length - 1]);
    store.update((active) => ({
      ...active,
      navigation: {
        current: previous,
        stack: active.navigation.stack.slice(0, -1),
        revision: active.navigation.revision + 1,
      },
      dialog: closedDialog(),
    }));
    return store.getState().navigation.current;
  }

  function openDialog(type, data = {}) {
    const dialogType = requireName(type, "dialog.type");
    if (!isPlainObject(data)) {
      throw validationError("dialog.data must be a plain object", "dialog.data");
    }
    const next = {
      open: true,
      type: dialogType,
      data: cloneValue(data, "dialog.data"),
    };
    const state = store.getState();
    if (equalValue(state.dialog, next)) return state.dialog;
    store.update({ dialog: next });
    return store.getState().dialog;
  }

  function closeDialog() {
    const state = store.getState();
    if (!state.dialog.open && state.dialog.type === null) return state.dialog;
    store.update({ dialog: closedDialog() });
    return store.getState().dialog;
  }

  return Object.freeze({
    current,
    navigate,
    replace,
    back,
    openDialog,
    closeDialog,
  });
}
