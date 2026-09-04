import { validationError } from "../api/errors.js";

const EVENT_TYPES = Object.freeze(["click", "change", "input", "submit"]);

function escapeAttribute(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("'", "&#039;");
}

function requestStatus(requests) {
  const values = Object.values(
    requests && typeof requests === "object" ? requests : {},
  );
  if (values.some((request) => request?.status === "pending")) return "loading";
  if (values.some((request) => request?.status === "error")) return "error";
  if (values.length && values.every((request) => request?.status === "success")) {
    return "success";
  }
  return "idle";
}

function assertMethod(value, owner, method) {
  if (value === null || typeof value !== "object") {
    throw validationError(`${owner} must be an object`, owner);
  }
  if (typeof value[method] !== "function") {
    throw validationError(
      `${owner}.${method} must be a function`,
      `${owner}.${method}`,
    );
  }
  return value;
}

export function renderApplicationShell(state) {
  if (state === null || typeof state !== "object") {
    throw validationError("state must be an object", "state");
  }
  const route = state.navigation?.current?.name || "overview";
  const dialog = state.dialog?.open ? state.dialog.type || "" : "";
  return `<section data-animal-health-shell="phase-3" data-route="${escapeAttribute(route)}" data-dialog="${escapeAttribute(dialog)}" data-request-status="${requestStatus(state.requests)}"></section>`;
}

export function createAnimalHealthPanelClass({
  store,
  controller,
  render = renderApplicationShell,
  HTMLElementBase,
} = {}) {
  const actualStore = assertMethod(store, "store", "getState");
  assertMethod(actualStore, "store", "subscribe");
  const actualController = assertMethod(
    controller,
    "controller",
    "handleEvent",
  );
  if (typeof render !== "function") {
    throw validationError("render must be a function", "render");
  }
  if (typeof HTMLElementBase !== "function") {
    throw validationError(
      "HTMLElementBase must be a constructor",
      "HTMLElementBase",
    );
  }

  return class AnimalHealthApplicationPanel extends HTMLElementBase {
    constructor(...args) {
      super(...args);
      if (typeof this.attachShadow !== "function") {
        throw validationError(
          "HTMLElementBase instances must support attachShadow",
          "HTMLElementBase.attachShadow",
        );
      }
      this._applicationRoot = this.attachShadow({ mode: "open" });
      this._eventsBound = false;
      this._unsubscribeStore = null;
      this._delegateEvent = (event) => {
        const result = actualController.handleEvent(event);
        if (result && typeof result.catch === "function") {
          result.catch(() => undefined);
        }
      };
    }

    _bindEvents() {
      if (this._eventsBound) return;
      for (const type of EVENT_TYPES) {
        this._applicationRoot.addEventListener(type, this._delegateEvent);
      }
      this._eventsBound = true;
    }

    connectedCallback() {
      this._bindEvents();
      if (!this._unsubscribeStore) {
        this._unsubscribeStore = actualStore.subscribe(() => this.render());
      }
      this.render();
    }

    disconnectedCallback() {
      if (!this._unsubscribeStore) return;
      this._unsubscribeStore();
      this._unsubscribeStore = null;
    }

    render() {
      const markup = render(actualStore.getState());
      if (typeof markup !== "string") {
        throw validationError("render must return a string", "render");
      }
      this._applicationRoot.innerHTML = markup;
      return markup;
    }
  };
}
