import assert from "node:assert/strict";
import test from "node:test";

import { createRouter } from "../../custom_components/animal_health/frontend/src/app/router.js";
import { createStore } from "../../custom_components/animal_health/frontend/src/app/store.js";

test("router owns its stack and closes dialogs on navigation", () => {
  const store = createStore();
  const router = createRouter(store);

  router.openDialog("create-animal", { source: "overview" });
  assert.deepEqual(store.getState().dialog, {
    open: true,
    type: "create-animal",
    data: { source: "overview" },
  });

  router.navigate({ name: "animals", params: { filter: "active" } });
  assert.deepEqual(router.current(), {
    name: "animals",
    params: { filter: "active" },
  });
  assert.deepEqual(store.getState().navigation.stack, [
    { name: "overview", params: {} },
  ]);
  assert.equal(store.getState().navigation.revision, 1);
  assert.deepEqual(store.getState().dialog, {
    open: false,
    type: null,
    data: {},
  });

  router.replace({ name: "animal-detail", params: { animalId: "AH-1" } });
  assert.deepEqual(router.current(), {
    name: "animal-detail",
    params: { animalId: "AH-1" },
  });
  assert.equal(store.getState().navigation.stack.length, 1);
  assert.equal(store.getState().navigation.revision, 2);

  router.back();
  assert.deepEqual(router.current(), { name: "overview", params: {} });
  assert.deepEqual(store.getState().navigation.stack, []);
  assert.equal(store.getState().navigation.revision, 3);
});

test("identical navigation and root back are no-ops", () => {
  const store = createStore();
  const router = createRouter(store);
  const initial = store.getState();

  const same = router.navigate({ name: "overview", params: {} });
  assert.equal(same, initial.navigation.current);
  assert.equal(store.getState(), initial);

  const root = router.back();
  assert.equal(root, initial.navigation.current);
  assert.equal(store.getState(), initial);
});

test("route comparison is independent of parameter key order", () => {
  const store = createStore({
    navigation: {
      current: {
        name: "animals",
        params: { filter: "active", groupId: "GR-1" },
      },
    },
  });
  const router = createRouter(store);
  const before = store.getState();

  router.navigate({
    name: "animals",
    params: { groupId: "GR-1", filter: "active" },
  });

  assert.equal(store.getState(), before);
});

test("dialog operations copy their data and close idempotently", () => {
  const store = createStore();
  const router = createRouter(store);
  const data = { occurrenceId: "OCC-1", fields: ["dose"] };

  router.openDialog("execute-task", data);
  data.fields.push("route");
  assert.deepEqual(store.getState().dialog.data, {
    occurrenceId: "OCC-1",
    fields: ["dose"],
  });

  router.closeDialog();
  const closed = store.getState();
  router.closeDialog();
  assert.equal(store.getState(), closed);
  assert.throws(() => router.openDialog("", {}), (error) =>
    error.code === "validation" && error.details.path === "dialog.type"
  );
});
