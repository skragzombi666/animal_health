import assert from "node:assert/strict";
import test from "node:test";

import * as entry from "../../custom_components/animal_health/frontend/src/entry.js";
import { createAnimalHealthApplication } from "../../custom_components/animal_health/frontend/src/app/application.js";
import { createCompatibilityBridge } from "../../custom_components/animal_health/frontend/src/legacy/compatibility-bridge.js";

class FakeShadowRoot {
  constructor() {
    this.listeners = new Map();
    this.innerHTML = "";
  }

  addEventListener(type, handler) {
    this.listeners.set(type, handler);
  }
}

class FakeElement {
  attachShadow() {
    this.shadowRoot = new FakeShadowRoot();
    return this.shadowRoot;
  }
}

function recordingTransport() {
  return {
    requests: [],
    services: [],
    downloads: [],
    notifications: [],
    async request(command, payload = {}) {
      this.requests.push({ command, payload });
      return {};
    },
    async callService(service, payload = {}, options = {}) {
      this.services.push({ service, payload, options });
      return {};
    },
    async download(resource) {
      this.downloads.push(resource);
    },
    notify(message, options = {}) {
      this.notifications.push({ message, options });
    },
  };
}

function fakeRegistry(initial = {}) {
  const definitions = new Map(Object.entries(initial));
  const names = [];
  return {
    names,
    get(name) {
      return definitions.get(name);
    },
    define(name, constructor) {
      if (definitions.has(name)) throw new Error(`duplicate ${name}`);
      definitions.set(name, constructor);
      names.push(name);
    },
  };
}

test("legacy bridge defaults every route to legacy and switches only explicitly", async () => {
  const calls = [];
  const context = { state: { untouched: true } };
  const bridge = createCompatibilityBridge({
    legacyDelegate(routeName, received) {
      calls.push(["legacy", routeName, received]);
      return "legacy-result";
    },
    newDelegate(routeName, received) {
      calls.push(["new", routeName, received]);
      return "new-result";
    },
  });

  assert.equal(bridge.modeFor("overview"), "legacy");
  assert.equal(await bridge.delegate("overview", context), "legacy-result");
  assert.equal(bridge.markMigrated("overview"), true);
  assert.equal(bridge.markMigrated("overview"), false);
  assert.equal(bridge.modeFor("overview"), "new");
  assert.equal(await bridge.delegate("overview", context), "new-result");
  assert.equal(bridge.markLegacy("overview"), true);
  assert.equal(bridge.markLegacy("overview"), false);
  assert.equal(bridge.modeFor("overview"), "legacy");
  assert.deepEqual(calls, [
    ["legacy", "overview", context],
    ["new", "overview", context],
  ]);
  assert.deepEqual(context, { state: { untouched: true } });
});

test("legacy bridge accepts an explicit initial migrated route set", () => {
  const bridge = createCompatibilityBridge({
    migratedRoutes: ["animals", "animal-detail", "animals"],
  });

  assert.equal(bridge.modeFor("animals"), "new");
  assert.equal(bridge.modeFor("tasks"), "legacy");
  assert.throws(() => bridge.modeFor(""), (error) =>
    error.code === "validation" && error.details.path === "routeName"
  );
});

test("application composition is inactive and registration is explicit", () => {
  const transport = recordingTransport();
  const application = createAnimalHealthApplication({
    transport,
    HTMLElementBase: FakeElement,
    initialState: {
      platform: { kind: "android", available: true },
      language: { code: "en", locale: "en-GB" },
    },
  });
  const registry = fakeRegistry();

  assert.equal(application.store.getState().platform.kind, "android");
  assert.equal(application.store.getState().language.code, "en");
  assert.equal(application.router.current().name, "overview");
  assert.equal(application.bridge.modeFor("overview"), "legacy");
  assert.equal(registry.names.length, 0);

  const first = application.define(registry, "animal-health-phase-3");
  const second = application.define(registry, "animal-health-phase-3");
  assert.equal(first, application.PanelClass);
  assert.equal(second, application.PanelClass);
  assert.deepEqual(registry.names, ["animal-health-phase-3"]);

  const panel = new application.PanelClass();
  panel.connectedCallback();
  assert.equal(
    panel.shadowRoot.innerHTML,
    '<section data-animal-health-shell="phase-3" data-route="overview" data-dialog="" data-request-status="idle"></section>',
  );
  assert.deepEqual(transport.requests, []);
});

test("application registration refuses a tag occupied by another class", () => {
  class ExistingElement {}
  const application = createAnimalHealthApplication({
    transport: recordingTransport(),
    HTMLElementBase: FakeElement,
  });
  const registry = fakeRegistry({ "animal-health-phase-3": ExistingElement });

  assert.throws(
    () => application.define(registry, "animal-health-phase-3"),
    (error) =>
      error.code === "conflict" &&
      error.operation === "defineApplicationElement" &&
      error.details.tagName === "animal-health-phase-3",
  );
  assert.deepEqual(registry.names, []);
});

test("Phase 3 application boundary is exported without registering anything", () => {
  for (const name of [
    "createAnimalHealthApplication",
    "createAnimalHealthPanelClass",
    "createCompatibilityBridge",
    "createController",
    "createInitialState",
    "createRoute",
    "createRouter",
    "createStore",
    "renderApplicationShell",
  ]) {
    assert.equal(typeof entry[name], "function", name);
  }
});
