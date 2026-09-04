import assert from "node:assert/strict";
import test from "node:test";

import { createController } from "../../custom_components/animal_health/frontend/src/app/controller.js";
import { createRouter } from "../../custom_components/animal_health/frontend/src/app/router.js";
import { createStore } from "../../custom_components/animal_health/frontend/src/app/store.js";

function setup() {
  const store = createStore();
  const router = createRouter(store);
  const client = { name: "client" };
  const controller = createController({ store, router, client });
  return { store, router, client, controller };
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolveValue, rejectValue) => {
    resolve = resolveValue;
    reject = rejectValue;
  });
  return { promise, resolve, reject };
}

test("controller dispatches structural actions through one registry", async () => {
  const { store, router, controller } = setup();

  await controller.dispatch("app.navigate", {
    route: { name: "tasks", params: { timing: "overdue" } },
  });
  assert.deepEqual(router.current(), {
    name: "tasks",
    params: { timing: "overdue" },
  });

  await controller.dispatch("dialog.open", {
    dialogType: "create-task",
    data: { source: "tasks" },
  });
  assert.equal(store.getState().dialog.type, "create-task");
  await controller.dispatch("dialog.close", {});
  assert.equal(store.getState().dialog.open, false);

  await controller.dispatch("app.back", {});
  assert.equal(router.current().name, "overview");
  assert.equal(await controller.dispatch("missing.action", {}), false);
});

test("controller rejects duplicate action names and supports explicit unregister", async () => {
  const { controller } = setup();
  const calls = [];

  controller.register("test.action", (context) => calls.push(context.value));
  assert.throws(
    () => controller.register("test.action", () => undefined),
    (error) => error.code === "conflict" && error.operation === "registerAction",
  );
  assert.equal(await controller.dispatch("test.action", { value: 7 }), 1);
  assert.deepEqual(calls, [7]);
  assert.equal(controller.unregister("test.action"), true);
  assert.equal(controller.unregister("test.action"), false);
  assert.equal(await controller.dispatch("test.action", {}), false);
});

test("handleEvent extracts stable action data and prevents form submission", async () => {
  const { router, controller } = setup();
  let prevented = 0;
  const target = {
    dataset: {
      action: "app.navigate",
      route: "animals",
      routeParams: JSON.stringify({ groupId: "GR-1" }),
    },
  };
  const event = {
    type: "submit",
    preventDefault() {
      prevented += 1;
    },
    composedPath() {
      return [{ dataset: {} }, target];
    },
  };

  await controller.handleEvent(event);

  assert.equal(prevented, 1);
  assert.deepEqual(router.current(), {
    name: "animals",
    params: { groupId: "GR-1" },
  });
});

test("invalid action JSON and handler failures are normalized and recorded", async () => {
  const { store, controller } = setup();
  const target = {
    dataset: {
      action: "app.navigate",
      route: "animals",
      routeParams: "{invalid",
    },
  };

  await assert.rejects(
    () =>
      controller.handleEvent({
        type: "click",
        composedPath: () => [target],
      }),
    (error) =>
      error.code === "validation" &&
      error.operation === "action:app.navigate" &&
      error.details.path === "data-route-params",
  );
  assert.equal(
    store.getState().requests["action:app.navigate"].status,
    "error",
  );

  controller.register("test.fail", () => {
    throw Object.assign(new Error("offline"), { code: "transport" });
  });
  await assert.rejects(
    () => controller.dispatch("test.fail", {}),
    (error) => error.code === "transport" && error.operation === "action:test.fail",
  );
  assert.equal(store.getState().requests["action:test.fail"].error.code, "transport");
});

test("structural navigation rejects a missing route instead of silently returning home", async () => {
  const { controller } = setup();

  await assert.rejects(
    () => controller.dispatch("app.navigate", {}),
    (error) =>
      error.code === "validation" &&
      error.operation === "action:app.navigate" &&
      error.details.path === "route",
  );
});

test("action failures cannot preserve an unrelated colliding request token", async () => {
  const { store, controller } = setup();
  const previous = store.beginRequest("action:test.fail");
  controller.register("test.fail", () => {
    throw Object.assign(new Error("offline"), { code: "transport" });
  });

  await assert.rejects(() => controller.dispatch("test.fail", {}));

  assert.equal(store.isCurrentRequest(previous), false);
  assert.equal(store.getState().requests["action:test.fail"].status, "error");
});

test("runLatest discards an older async result", async () => {
  const { store, controller } = setup();
  const first = deferred();
  const second = deferred();
  const apply = (state, value) => ({
    ...state,
    settings: { status: "ready", data: value, error: null },
  });

  const firstRun = controller.runLatest(
    "dashboard",
    () => first.promise,
    apply,
  );
  const secondRun = controller.runLatest(
    "dashboard",
    () => second.promise,
    apply,
  );
  second.resolve("new");
  const secondResult = await secondRun;
  first.resolve("old");
  const firstResult = await firstRun;

  assert.deepEqual(secondResult, { applied: true, result: "new" });
  assert.deepEqual(firstResult, { applied: false, result: "old" });
  assert.equal(store.getState().settings.data, "new");
});

test("runLatest discards a failure after its route was left", async () => {
  const { store, router, controller } = setup();
  const request = deferred();
  controller.register("test.load-detail", () =>
    controller.runLatest(
      "animal-detail",
      () => request.promise,
      (state, value) => ({
        ...state,
        settings: { status: "ready", data: value, error: null },
      }),
    ),
  );

  const dispatched = controller.dispatch("test.load-detail", {});
  router.navigate("tasks");
  request.reject(Object.assign(new Error("late failure"), { code: "transport" }));
  const result = await dispatched;

  assert.equal(result.applied, false);
  assert.equal(result.error.code, "transport");
  assert.deepEqual(store.getState().requests, {});
  assert.equal(store.getState().settings.data, null);
});

test("runLatest exposes client context and stores current failures", async () => {
  const { store, client, controller } = setup();
  let received;

  await assert.rejects(
    () =>
      controller.runLatest(
        "animal-detail",
        (context) => {
          received = context;
          throw Object.assign(new Error("connection lost"), {
            code: "transport",
          });
        },
        (state) => state,
      ),
    (error) =>
      error.code === "transport" &&
      error.operation === "request:animal-detail",
  );

  assert.equal(received.client, client);
  assert.equal(received.store, store);
  assert.equal(received.token.key, "animal-detail");
  assert.equal(store.getState().requests["animal-detail"].status, "error");
  assert.equal(
    store.getState().requests["animal-detail"].error.operation,
    "request:animal-detail",
  );
});
