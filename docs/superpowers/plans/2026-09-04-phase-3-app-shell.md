# Phase 3 Application Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the inactive, host-neutral application shell for the modular Animal Health frontend without changing the delivered Home Assistant or Android interface.

**Architecture:** Add a canonical state factory, observable store with request fencing, internal router, explicit action controller, injectable panel class, application composition factory, and route-level legacy bridge. All modules remain outside the productive bundle and are consumed only through side-effect-free ES-module exports.

**Tech Stack:** JavaScript ES modules, JSDoc contracts, Node built-in test runner, Python architecture tests, existing deterministic legacy bundle build.

**Spec:** `docs/superpowers/specs/2026-09-04-phase-3-app-shell-design.md`

## Global Constraints

- No visible UI change.
- No change to backend commands, services, database schema, stored IDs, or user data.
- No modification of the 99 frozen legacy fragments or their manifest.
- No external JavaScript dependency.
- No app-module access to `hass`, Android bridge objects, `window.history`, or implicit host globals.
- No `shadowRoot.innerHTML +=`, prototype patch chain, or import-time custom-element registration.
- `frontend/src/entry.js` remains side-effect free.
- The productive dist bundle remains byte-identical to the Phase-2 legacy reference.

---

### Task 1: Canonical state and observable store

**Files:**
- Create: `tests/frontend/app-state-store.test.mjs`
- Create: `custom_components/animal_health/frontend/src/app/state.js`
- Create: `custom_components/animal_health/frontend/src/app/store.js`

**Interfaces:**
- Produces: `createRoute(value) -> RouteDto`
- Produces: `createInitialState(overrides) -> ApplicationState`
- Produces: `createStore(initialState) -> {getState, update, subscribe, beginRequest, commitRequest, failRequest, isCurrentRequest}`

- [ ] **Step 1: Write failing state and store tests**

```javascript
import { createInitialState, createRoute } from "../../custom_components/animal_health/frontend/src/app/state.js";
import { createStore } from "../../custom_components/animal_health/frontend/src/app/store.js";

test("initial state copies overrides and exposes every canonical slice", () => {
  const overrides = { language: { code: "en", locale: "en-GB" } };
  const state = createInitialState(overrides);
  assert.equal(state.language.code, "en");
  assert.notEqual(state.language, overrides.language);
  assert.deepEqual(Object.keys(state).sort(), [
    "animals", "dialog", "drafts", "language", "navigation",
    "notifications", "platform", "products", "requests", "settings",
    "tasks", "timeline", "treatments",
  ].sort());
});

test("newer requests and navigation invalidate older tokens", () => {
  const store = createStore();
  const first = store.beginRequest("animals");
  const second = store.beginRequest("animals");
  assert.equal(store.commitRequest(first, { animals: { status: "ready" } }), false);
  assert.equal(store.commitRequest(second, { animals: { status: "ready" } }), true);
  const routed = store.beginRequest("detail");
  store.update((state) => ({
    ...state,
    navigation: { ...state.navigation, revision: state.navigation.revision + 1 },
  }));
  assert.equal(store.commitRequest(routed, {}), false);
});
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `node --test tests/frontend/app-state-store.test.mjs`

Expected: module-not-found failure for `app/state.js` or `app/store.js`.

- [ ] **Step 3: Implement canonical state**

```javascript
export function createRoute(value = { name: "overview", params: {} }) {
  const route = typeof value === "string" ? { name: value, params: {} } : value;
  return { name: requireName(route.name, "route.name"), params: cloneRecord(route.params) };
}

export function createInitialState(overrides = {}) {
  return mergeCanonicalState(BASE_STATE, overrides);
}
```

Use recursive copying only for arrays and plain records. Reject non-record overrides with the existing Phase-2 validation error helper.

- [ ] **Step 4: Implement store and request fencing**

```javascript
export function createStore(initialState = {}) {
  let state = createInitialState(initialState);
  const listeners = new Set();
  let requestSequence = 0;

  function beginRequest(key) {
    const token = Object.freeze({
      key: requireName(key, "request.key"),
      id: ++requestSequence,
      navigationRevision: state.navigation.revision,
    });
    update((current) => ({
      ...current,
      requests: {
        ...current.requests,
        [token.key]: { ...token, status: "pending", error: null },
      },
    }));
    return token;
  }

  function isCurrentRequest(token) {
    const active = state.requests[token?.key];
    return Boolean(
      active && active.id === token.id &&
      state.navigation.revision === token.navigationRevision
    );
  }
}
```

`commitRequest` and `failRequest` must return `false` without mutation when the token is stale.

- [ ] **Step 5: Run focused and complete frontend tests**

Run:

```bash
node --test tests/frontend/app-state-store.test.mjs
npm run test:frontend
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add tests/frontend/app-state-store.test.mjs custom_components/animal_health/frontend/src/app/state.js custom_components/animal_health/frontend/src/app/store.js
git commit -m "feat: add canonical application state and store"
```

---

### Task 2: Internal router and dialog state

**Files:**
- Create: `tests/frontend/app-router.test.mjs`
- Create: `custom_components/animal_health/frontend/src/app/router.js`

**Interfaces:**
- Consumes: `createRoute`, `createStore`
- Produces: `createRouter(store) -> {current, navigate, replace, back, openDialog, closeDialog}`

- [ ] **Step 1: Write failing router tests**

```javascript
test("router owns its stack and closes dialogs on navigation", () => {
  const store = createStore();
  const router = createRouter(store);
  router.openDialog("create-animal", { source: "overview" });
  router.navigate({ name: "animals", params: { filter: "active" } });
  assert.equal(router.current().name, "animals");
  assert.equal(store.getState().navigation.stack.length, 1);
  assert.equal(store.getState().dialog.open, false);
  router.replace({ name: "animal-detail", params: { animalId: "AH-1" } });
  assert.equal(store.getState().navigation.stack.length, 1);
  router.back();
  assert.equal(router.current().name, "overview");
});
```

- [ ] **Step 2: Verify RED**

Run: `node --test tests/frontend/app-router.test.mjs`

Expected: module-not-found failure for `app/router.js`.

- [ ] **Step 3: Implement the router**

```javascript
export function createRouter(store) {
  function navigate(route, { replace = false } = {}) {
    const next = createRoute(route);
    store.update((state) => ({
      ...state,
      navigation: {
        current: next,
        stack: replace ? state.navigation.stack : [...state.navigation.stack, state.navigation.current],
        revision: state.navigation.revision + 1,
      },
      dialog: CLOSED_DIALOG,
    }));
    return next;
  }
}
```

Add route equality so navigation to the identical route is a no-op. `back()` at the root must not increment the revision.

- [ ] **Step 4: Run tests**

Run:

```bash
node --test tests/frontend/app-router.test.mjs
npm run test:frontend
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/frontend/app-router.test.mjs custom_components/animal_health/frontend/src/app/router.js
git commit -m "feat: add internal application router"
```

---

### Task 3: Explicit controller and latest-request orchestration

**Files:**
- Create: `tests/frontend/app-controller.test.mjs`
- Create: `custom_components/animal_health/frontend/src/app/controller.js`

**Interfaces:**
- Consumes: `store`, `router`, `AnimalHealthClient`, Phase-2 error normalization
- Produces: `createController({store, router, client, actions})`

- [ ] **Step 1: Write failing controller tests**

```javascript
test("controller dispatches structural actions through one registry", async () => {
  const controller = createController({ store, router, client: {} });
  await controller.dispatch("app.navigate", { route: { name: "tasks" } });
  assert.equal(router.current().name, "tasks");
  assert.equal(await controller.dispatch("missing.action", {}), false);
  assert.throws(() => controller.register("app.back", () => {}));
});

test("runLatest discards an older async result", async () => {
  const first = deferred();
  const second = deferred();
  const firstRun = controller.runLatest("dashboard", () => first.promise, applyDashboard);
  const secondRun = controller.runLatest("dashboard", () => second.promise, applyDashboard);
  second.resolve("new");
  first.resolve("old");
  assert.equal((await secondRun).applied, true);
  assert.equal((await firstRun).applied, false);
  assert.equal(store.getState().settings.data, "new");
});
```

- [ ] **Step 2: Verify RED**

Run: `node --test tests/frontend/app-controller.test.mjs`

Expected: module-not-found failure for `app/controller.js`.

- [ ] **Step 3: Implement registry and event extraction**

```javascript
export function createController({ store, router, client, actions = {} }) {
  const registry = new Map();
  register("app.navigate", ({ route }) => router.navigate(route));
  register("app.back", () => router.back());
  register("dialog.open", ({ dialogType, data }) => router.openDialog(dialogType, data));
  register("dialog.close", () => router.closeDialog());

  async function handleEvent(event) {
    const target = findActionTarget(event);
    if (!target) return false;
    if (event.type === "submit") event.preventDefault?.();
    return dispatch(target.dataset.action, contextFromEvent(event, target));
  }
}
```

Parse optional route and dialog JSON only from `data-route-params` and `data-dialog-data`; invalid JSON becomes a validation error.

- [ ] **Step 4: Implement `runLatest`**

```javascript
async function runLatest(key, operation, applyResult) {
  const token = store.beginRequest(key);
  try {
    const result = await operation({ client, store, router, token });
    const applied = store.commitRequest(token, (state) => applyResult(state, result));
    return { applied, result };
  } catch (error) {
    const normalized = normalizeError(error, { operation: `request:${key}` });
    store.failRequest(token, normalized);
    throw normalized;
  }
}
```

- [ ] **Step 5: Run tests**

Run:

```bash
node --test tests/frontend/app-controller.test.mjs
npm run test:frontend
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add tests/frontend/app-controller.test.mjs custom_components/animal_health/frontend/src/app/controller.js
git commit -m "feat: add explicit application action controller"
```

---

### Task 4: Panel lifecycle and controlled renderer

**Files:**
- Create: `tests/frontend/app-panel.test.mjs`
- Create: `custom_components/animal_health/frontend/src/app/animal-health-panel.js`

**Interfaces:**
- Consumes: `store`, `controller`
- Produces: `renderApplicationShell(state) -> string`
- Produces: `createAnimalHealthPanelClass({store, controller, render, HTMLElementBase}) -> class`

- [ ] **Step 1: Write failing panel tests with a fake element base**

```javascript
test("panel binds delegated events once and renders through one path", () => {
  const Panel = createAnimalHealthPanelClass({
    store,
    controller,
    HTMLElementBase: FakeElement,
  });
  const panel = new Panel();
  panel.connectedCallback();
  panel.connectedCallback();
  assert.deepEqual(panel.shadowRoot.listenerCounts(), {
    click: 1, change: 1, input: 1, submit: 1,
  });
  const before = panel.shadowRoot.writes;
  store.update({ language: { code: "en", locale: "en-GB" } });
  assert.equal(panel.shadowRoot.writes, before + 1);
  panel.disconnectedCallback();
});
```

- [ ] **Step 2: Verify RED**

Run: `node --test tests/frontend/app-panel.test.mjs`

Expected: module-not-found failure for `app/animal-health-panel.js`.

- [ ] **Step 3: Implement renderer and panel factory**

```javascript
export function renderApplicationShell(state) {
  return `<section data-animal-health-shell="phase-3" data-route="${escapeAttribute(state.navigation.current.name)}" data-dialog="${escapeAttribute(state.dialog.type || "")}" data-request-status="${requestStatus(state.requests)}"></section>`;
}

export function createAnimalHealthPanelClass({
  store,
  controller,
  render = renderApplicationShell,
  HTMLElementBase,
}) {
  return class AnimalHealthApplicationPanel extends HTMLElementBase {
    connectedCallback() {
      if (!this._eventsBound) this._bindEvents();
      if (!this._unsubscribe) this._unsubscribe = store.subscribe(() => this.render());
      this.render();
    }
  };
}
```

The constructor must attach exactly one open shadow root. Event listeners remain delegated on that root and are never duplicated after reconnects.

- [ ] **Step 4: Run tests**

Run:

```bash
node --test tests/frontend/app-panel.test.mjs
npm run test:frontend
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/frontend/app-panel.test.mjs custom_components/animal_health/frontend/src/app/animal-health-panel.js
git commit -m "feat: add controlled application panel shell"
```

---

### Task 5: Legacy bridge and application composition

**Files:**
- Create: `tests/frontend/app-application.test.mjs`
- Create: `custom_components/animal_health/frontend/src/legacy/compatibility-bridge.js`
- Create: `custom_components/animal_health/frontend/src/app/application.js`
- Modify: `custom_components/animal_health/frontend/src/entry.js`

**Interfaces:**
- Produces: `createCompatibilityBridge(options)`
- Produces: `createAnimalHealthApplication(options)`
- Produces: explicit idempotent `application.define(registry, tagName)`

- [ ] **Step 1: Write failing bridge and composition tests**

```javascript
test("legacy bridge defaults every route to legacy", async () => {
  const calls = [];
  const bridge = createCompatibilityBridge({
    legacyDelegate: (route) => calls.push(["legacy", route]),
    newDelegate: (route) => calls.push(["new", route]),
  });
  assert.equal(bridge.modeFor("overview"), "legacy");
  await bridge.delegate("overview", {});
  bridge.markMigrated("overview");
  await bridge.delegate("overview", {});
  assert.deepEqual(calls, [["legacy", "overview"], ["new", "overview"]]);
});

test("application composition has no global side effects and registration is explicit", () => {
  const application = createAnimalHealthApplication({
    transport: recordingTransport(),
    HTMLElementBase: FakeElement,
  });
  const registry = fakeRegistry();
  assert.equal(registry.names.length, 0);
  application.define(registry, "animal-health-phase-3");
  application.define(registry, "animal-health-phase-3");
  assert.deepEqual(registry.names, ["animal-health-phase-3"]);
});
```

- [ ] **Step 2: Verify RED**

Run: `node --test tests/frontend/app-application.test.mjs`

Expected: module-not-found failure for the bridge or application factory.

- [ ] **Step 3: Implement the route-level bridge**

```javascript
export function createCompatibilityBridge({
  migratedRoutes = [],
  legacyDelegate = () => undefined,
  newDelegate = () => undefined,
} = {}) {
  const migrated = new Set(migratedRoutes.map((route) => requireName(route, "routeName")));
  return {
    modeFor(routeName) {
      return migrated.has(requireName(routeName, "routeName")) ? "new" : "legacy";
    },
    markMigrated(routeName) { migrated.add(requireName(routeName, "routeName")); },
    markLegacy(routeName) { migrated.delete(requireName(routeName, "routeName")); },
    delegate(routeName, context = {}) {
      const name = requireName(routeName, "routeName");
      return (migrated.has(name) ? newDelegate : legacyDelegate)(name, context);
    },
  };
}
```

- [ ] **Step 4: Implement application composition**

```javascript
export function createAnimalHealthApplication(options = {}) {
  const client = new AnimalHealthClient(options.transport);
  const store = createStore(options.initialState);
  const router = createRouter(store);
  const controller = createController({ store, router, client, actions: options.actions });
  const bridge = createCompatibilityBridge(options.legacy);
  const PanelClass = createAnimalHealthPanelClass({
    store,
    controller,
    render: options.render,
    HTMLElementBase: options.HTMLElementBase,
  });
  return { client, store, router, controller, bridge, PanelClass, define };
}
```

`define` receives a registry object with `get` and `define`. It returns the existing identical class without redefining it and throws a conflict error if the tag is occupied by another class.

- [ ] **Step 5: Export the Phase-3 boundary from `entry.js`**

```javascript
export { createAnimalHealthApplication } from "./app/application.js";
export { createAnimalHealthPanelClass, renderApplicationShell } from "./app/animal-health-panel.js";
export { createController } from "./app/controller.js";
export { createRouter } from "./app/router.js";
export { createInitialState, createRoute } from "./app/state.js";
export { createStore } from "./app/store.js";
export { createCompatibilityBridge } from "./legacy/compatibility-bridge.js";
```

- [ ] **Step 6: Run tests**

Run:

```bash
node --test tests/frontend/app-application.test.mjs
npm run check:frontend
npm run test:frontend
```

Expected: all tests pass and importing `entry.js` registers nothing.

- [ ] **Step 7: Commit**

```bash
git add tests/frontend/app-application.test.mjs custom_components/animal_health/frontend/src/legacy/compatibility-bridge.js custom_components/animal_health/frontend/src/app/application.js custom_components/animal_health/frontend/src/entry.js
git commit -m "feat: compose inactive application shell"
```

---

### Task 6: Architecture guardrails, documentation, and full verification

**Files:**
- Create: `tests/test_frontend_phase3.py`
- Modify: `scripts/check_frontend_modules.mjs`
- Modify: `custom_components/animal_health/frontend/src/README.md`

**Interfaces:**
- Consumes: all Phase-3 source modules and entry exports
- Produces: permanent CI enforcement for the Phase-3 shell

- [ ] **Step 1: Write failing Phase-3 architecture tests**

```python
EXPECTED_APP_FILES = {
    "app/application.js",
    "app/animal-health-panel.js",
    "app/controller.js",
    "app/router.js",
    "app/state.js",
    "app/store.js",
    "legacy/compatibility-bridge.js",
}

def test_phase3_application_shell_files_exist():
    assert EXPECTED_APP_FILES <= _sources().keys()

def test_phase3_app_modules_are_host_neutral():
    for path, source in _sources().items():
        if path.startswith("app/") or path == "legacy/compatibility-bridge.js":
            assert "hass." not in source
            assert "bridge." not in source
            assert "window.history" not in source
            assert "customElements.define" not in source
```

Also assert that the legacy manifest still lists 99 files and the dist bundle still equals their exact concatenation.

- [ ] **Step 2: Verify RED before guardrail updates**

Run: `python -m pytest -q tests/test_frontend_phase3.py`

Expected: failure because the permanent Phase-3 export/checker expectations are not yet updated.

- [ ] **Step 3: Extend the module checker**

Add these required exports:

```javascript
"createAnimalHealthApplication",
"createAnimalHealthPanelClass",
"createCompatibilityBridge",
"createController",
"createInitialState",
"createRouter",
"createStore",
"renderApplicationShell",
```

Rename diagnostic text from “Phase 2 entry” to “modular frontend entry” so the checker remains phase-neutral.

- [ ] **Step 4: Update source documentation**

Document that Phase 3 provides an inactive application shell, no route is migrated, registration is explicit, and the productive bundle remains the exact legacy reference.

- [ ] **Step 5: Run the full verification matrix**

Run:

```bash
python -m compileall custom_components tests scripts
python scripts/architecture_inventory.py --root . --check
node scripts/build_frontend.mjs --check
node --check custom_components/animal_health/frontend/dist/animal-health-panel.js
npm run check:frontend
npm run test:frontend
python -m pytest -q
python tests/dashboard_frontend_smoke.py
python tests/ai_assist_smoke.py
python tests/v081_workflow_smoke.py
python tests/v084_features_smoke.py
python tests/feature_export_smoke.py
python tests/v080_feature_smoke.py
python tests/breed_catalog_smoke.py
python tests/download_stabilization_smoke.py
python tests/task_record_schema_smoke.py
python tests/task_overdue_smoke.py
python tests/task_resolution_smoke.py
python tests/catalog_selector_smoke.py
python tests/task_action_resolution_smoke.py
python tests/task_batch_atomicity_smoke.py
python tests/test_task_service_translations.py
```

Expected: all commands exit with status 0; no test failures; dist bundle remains unchanged.

- [ ] **Step 6: Commit**

```bash
git add tests/test_frontend_phase3.py scripts/check_frontend_modules.mjs custom_components/animal_health/frontend/src/README.md
git commit -m "test: enforce Phase 3 application boundaries"
```

- [ ] **Step 7: Open a stacked draft pull request**

Base: `consolidation/phase-2-platform-api`  
Head: `consolidation/phase-3-app-shell`

The PR must explicitly state that no route is activated and that Phase 2 must merge first.
