import assert from "node:assert/strict";
import test from "node:test";

import {
  createAnimalHealthPanelClass,
  renderApplicationShell,
} from "../../custom_components/animal_health/frontend/src/app/animal-health-panel.js";
import { createStore } from "../../custom_components/animal_health/frontend/src/app/store.js";

class FakeShadowRoot {
  constructor() {
    this.listeners = new Map();
    this.writes = 0;
    this._innerHTML = "";
  }

  addEventListener(type, handler) {
    const handlers = this.listeners.get(type) || [];
    handlers.push(handler);
    this.listeners.set(type, handlers);
  }

  listenerCounts() {
    return Object.fromEntries(
      [...this.listeners.entries()].map(([type, handlers]) => [
        type,
        handlers.length,
      ]),
    );
  }

  emit(type, event = {}) {
    for (const handler of this.listeners.get(type) || []) {
      handler({ type, ...event });
    }
  }

  set innerHTML(value) {
    this.writes += 1;
    this._innerHTML = String(value);
  }

  get innerHTML() {
    return this._innerHTML;
  }
}

class FakeElement {
  constructor() {
    this.shadowRoot = null;
    this.attachCalls = 0;
    this.shadowOptions = null;
  }

  attachShadow(options) {
    if (this.shadowRoot) throw new Error("shadow root already attached");
    this.attachCalls += 1;
    this.shadowOptions = options;
    this.shadowRoot = new FakeShadowRoot();
    return this.shadowRoot;
  }
}

function controllerRecorder() {
  const events = [];
  return {
    events,
    handleEvent(event) {
      events.push(event);
      return Promise.resolve(true);
    },
  };
}

test("application shell renderer exposes only neutral structural state", () => {
  const store = createStore({
    navigation: {
      current: { name: 'animal-"detail', params: {} },
    },
    dialog: {
      open: true,
      type: "execute&task",
      data: {},
    },
    requests: {
      detail: { status: "pending" },
    },
  });

  const markup = renderApplicationShell(store.getState());

  assert.equal(
    markup,
    '<section data-animal-health-shell="phase-3" data-route="animal-&quot;detail" data-dialog="execute&amp;task" data-request-status="loading"></section>',
  );
  assert.equal(markup.includes("Tiere"), false);
  assert.equal(markup.includes("Tasks"), false);
});

test("panel binds delegated events once and subscribes once while connected", () => {
  const store = createStore();
  const controller = controllerRecorder();
  const Panel = createAnimalHealthPanelClass({
    store,
    controller,
    HTMLElementBase: FakeElement,
  });
  const panel = new Panel();

  assert.equal(panel.attachCalls, 1);
  assert.deepEqual(panel.shadowOptions, { mode: "open" });
  panel.connectedCallback();
  panel.connectedCallback();
  assert.deepEqual(panel.shadowRoot.listenerCounts(), {
    click: 1,
    change: 1,
    input: 1,
    submit: 1,
  });

  const beforeUpdate = panel.shadowRoot.writes;
  store.update({ language: { code: "en", locale: "en-GB" } });
  assert.equal(panel.shadowRoot.writes, beforeUpdate + 1);

  panel.disconnectedCallback();
  const afterDisconnect = panel.shadowRoot.writes;
  store.update({ notifications: [{ id: "N-1" }] });
  assert.equal(panel.shadowRoot.writes, afterDisconnect);

  panel.connectedCallback();
  assert.deepEqual(panel.shadowRoot.listenerCounts(), {
    click: 1,
    change: 1,
    input: 1,
    submit: 1,
  });
  const afterReconnect = panel.shadowRoot.writes;
  store.update({ notifications: [{ id: "N-2" }] });
  assert.equal(panel.shadowRoot.writes, afterReconnect + 1);
});

test("panel delegates every supported event type to the controller", () => {
  const store = createStore();
  const controller = controllerRecorder();
  const Panel = createAnimalHealthPanelClass({
    store,
    controller,
    HTMLElementBase: FakeElement,
  });
  const panel = new Panel();
  panel.connectedCallback();

  for (const type of ["click", "change", "input", "submit"]) {
    panel.shadowRoot.emit(type, { marker: type });
  }

  assert.deepEqual(
    controller.events.map(({ type, marker }) => ({ type, marker })),
    [
      { type: "click", marker: "click" },
      { type: "change", marker: "change" },
      { type: "input", marker: "input" },
      { type: "submit", marker: "submit" },
    ],
  );
});

test("panel uses the injected renderer as its only markup writer", () => {
  const store = createStore();
  const controller = controllerRecorder();
  const snapshots = [];
  const Panel = createAnimalHealthPanelClass({
    store,
    controller,
    HTMLElementBase: FakeElement,
    render(state) {
      snapshots.push(state.navigation.revision);
      return `<main data-revision="${state.navigation.revision}"></main>`;
    },
  });
  const panel = new Panel();

  panel.connectedCallback();
  assert.equal(panel.shadowRoot.innerHTML, '<main data-revision="0"></main>');
  assert.deepEqual(snapshots, [0]);
  assert.equal(panel.render(), '<main data-revision="0"></main>');
  assert.deepEqual(snapshots, [0, 0]);
});

test("panel factory rejects missing lifecycle dependencies", () => {
  const store = createStore();
  const controller = controllerRecorder();

  assert.throws(
    () => createAnimalHealthPanelClass({ store, controller }),
    (error) =>
      error.code === "validation" && error.details.path === "HTMLElementBase",
  );
  assert.throws(
    () =>
      createAnimalHealthPanelClass({
        store,
        controller: {},
        HTMLElementBase: FakeElement,
      }),
    (error) =>
      error.code === "validation" &&
      error.details.path === "controller.handleEvent",
  );
});
