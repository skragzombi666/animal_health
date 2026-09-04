import assert from "node:assert/strict";
import test from "node:test";

import {
  createInitialState,
  createRoute,
} from "../../custom_components/animal_health/frontend/src/app/state.js";
import { createStore } from "../../custom_components/animal_health/frontend/src/app/store.js";

test("initial state copies overrides and exposes every canonical slice", () => {
  const overrides = {
    platform: { kind: "home-assistant", available: true },
    language: { code: "en", locale: "en-GB" },
    animals: { items: [{ id: "AH-1" }] },
  };

  const state = createInitialState(overrides);

  assert.deepEqual(Object.keys(state).sort(), [
    "animals",
    "dialog",
    "drafts",
    "language",
    "navigation",
    "notifications",
    "platform",
    "products",
    "requests",
    "settings",
    "tasks",
    "timeline",
    "treatments",
  ].sort());
  assert.deepEqual(state.navigation, {
    current: { name: "overview", params: {} },
    stack: [],
    revision: 0,
  });
  assert.equal(state.platform.kind, "home-assistant");
  assert.equal(state.language.code, "en");
  assert.deepEqual(state.animals.items, [{ id: "AH-1" }]);
  assert.notEqual(state.platform, overrides.platform);
  assert.notEqual(state.language, overrides.language);
  assert.notEqual(state.animals, overrides.animals);
  assert.notEqual(state.animals.items, overrides.animals.items);

  state.animals.items[0].id = "changed";
  assert.equal(overrides.animals.items[0].id, "AH-1");
});

test("route creation accepts names or records without retaining input objects", () => {
  const params = { animalId: "AH-1", filters: ["active"] };
  const route = createRoute({ name: "animal-detail", params });

  assert.deepEqual(route, {
    name: "animal-detail",
    params: { animalId: "AH-1", filters: ["active"] },
  });
  assert.notEqual(route.params, params);
  assert.notEqual(route.params.filters, params.filters);
  assert.deepEqual(createRoute("tasks"), { name: "tasks", params: {} });
  assert.throws(() => createRoute({ name: "", params: {} }), (error) =>
    error.code === "validation" && error.details.path === "route.name"
  );
});

test("store updates notify subscribers only for actual state changes", () => {
  const store = createStore();
  const snapshots = [];
  const unsubscribe = store.subscribe((state, previous) => {
    snapshots.push({ state, previous });
  });

  const initial = store.getState();
  store.update({ language: initial.language });
  assert.equal(snapshots.length, 0);

  store.update((state) => ({
    ...state,
    language: { code: "en", locale: "en-GB" },
  }));
  assert.equal(snapshots.length, 1);
  assert.equal(snapshots[0].previous, initial);
  assert.equal(snapshots[0].state.language.code, "en");

  unsubscribe();
  unsubscribe();
  store.update({ notifications: [{ id: "N-1" }] });
  assert.equal(snapshots.length, 1);
});

test("newer requests and navigation invalidate older request tokens", () => {
  const store = createStore();
  const first = store.beginRequest("animals");
  const second = store.beginRequest("animals");

  assert.equal(store.isCurrentRequest(first), false);
  assert.equal(store.isCurrentRequest(second), true);
  assert.equal(
    store.commitRequest(first, {
      animals: { status: "ready", items: [{ id: "old" }], error: null },
    }),
    false,
  );
  assert.equal(
    store.commitRequest(second, {
      animals: { status: "ready", items: [{ id: "new" }], error: null },
    }),
    true,
  );
  assert.equal(store.getState().animals.items[0].id, "new");
  assert.equal(store.getState().requests.animals.status, "success");

  const detail = store.beginRequest("animal-detail");
  store.update((state) => ({
    ...state,
    navigation: {
      ...state.navigation,
      revision: state.navigation.revision + 1,
    },
  }));
  assert.equal(store.isCurrentRequest(detail), false);
  assert.equal(store.commitRequest(detail, {}), false);
  assert.equal(
    store.failRequest(detail, Object.assign(new Error("late"), { code: "transport" })),
    false,
  );
});

test("current request failures are normalized into the request slice", () => {
  const store = createStore();
  const token = store.beginRequest("dashboard");

  assert.equal(
    store.failRequest(token, Object.assign(new Error("offline"), { code: "transport" })),
    true,
  );
  assert.deepEqual(store.getState().requests.dashboard.error, {
    code: "transport",
    message: "offline",
    operation: null,
    details: {},
  });
  assert.equal(store.getState().requests.dashboard.status, "error");
});
