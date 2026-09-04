import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { normalizeAnimalDetail, normalizeAnimalDirectory } from "../../custom_components/animal_health/frontend/src/api/normalizers/index.js";
import {
  MIGRATED_READ_ROUTES,
  createReadOnlyAnimalsRuntime,
  renderReadOnlyAnimalsRoute,
} from "../../custom_components/animal_health/frontend/src/app/read-only-animals.js";

const fixture = JSON.parse(
  await readFile(new URL("./fixtures/phase2-snapshots-0.9.41.json", import.meta.url), "utf8"),
);

function canonicalDirectory() {
  return normalizeAnimalDirectory({
    dashboard: fixture.dashboard,
    catalog: fixture.catalog,
    features: fixture.features,
    tagState: fixture.tagState,
  });
}

function canonicalDetail() {
  return normalizeAnimalDetail(fixture.animalDetail, { today: "2026-09-04" });
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

function fakePanel() {
  return {
    h: { language: "de" },
    view: "overview",
    modal: null,
    d: null,
    detail: null,
    shadowRoot: { innerHTML: "" },
    hasAttribute(name) {
      return name === "narrow" && this.narrow === true;
    },
    renderCalls: 0,
    render() {
      this.renderCalls += 1;
    },
  };
}

function recordingLegacy(panel) {
  const calls = [];
  return {
    calls,
    async load() {
      calls.push(["load", this.view]);
      this.d = { loaded: true };
    },
    render() {
      calls.push(["render", this.view]);
      this.shadowRoot.innerHTML = `<legacy route="${this.view}"></legacy>`;
    },
    loadDetail(id) {
      calls.push(["loadDetail", id]);
    },
    handleClick(event) {
      calls.push(["handleClick", event]);
    },
    handleInput(event) {
      calls.push(["handleInput", event]);
    },
  };
}

function targetEvent({ action = null, view = null, id = null, value = "" } = {}) {
  const target = {
    value,
    dataset: {
      ...(action ? { action } : {}),
      ...(view ? { view } : {}),
      ...(id ? { id } : {}),
    },
  };
  return {
    target,
    composedPath: () => [target],
  };
}

test("runtime declares exactly the first three migrated routes", () => {
  assert.deepEqual([...MIGRATED_READ_ROUTES], [
    "overview",
    "animals",
    "animal-detail",
  ]);
});

test("directory load is cached until an explicit refresh", async () => {
  const panel = fakePanel();
  const legacy = recordingLegacy(panel);
  const directory = canonicalDirectory();
  const client = {
    directoryCalls: 0,
    async getAnimalDirectory() {
      this.directoryCalls += 1;
      return directory;
    },
    async getAnimalDetail() {
      return canonicalDetail();
    },
  };
  const runtime = createReadOnlyAnimalsRuntime({
    panel,
    legacy,
    client,
    integrationVersion: "0.9.41",
  });

  await runtime.load();
  await runtime.load();
  assert.equal(client.directoryCalls, 1);
  assert.equal(runtime.store.getState().animals.status, "ready");
  assert.equal(runtime.store.getState().animals.items[0].name, "Tartar");
  assert.equal(runtime.store.getState().tasks.occurrences.length, 2);
  assert.match(runtime.render(), /data-modern-route="overview"/);

  await runtime.load({ force: true });
  assert.equal(client.directoryCalls, 2);
});

test("refresh retains loaded directory data while request is pending", async () => {
  const panel = fakePanel();
  const legacy = recordingLegacy(panel);
  const second = deferred();
  const directory = canonicalDirectory();
  let call = 0;
  const client = {
    getAnimalDirectory() {
      call += 1;
      return call === 1 ? Promise.resolve(directory) : second.promise;
    },
    async getAnimalDetail() {
      return canonicalDetail();
    },
  };
  const runtime = createReadOnlyAnimalsRuntime({ panel, legacy, client });
  await runtime.load();

  const refresh = runtime.load({ force: true });
  assert.equal(runtime.store.getState().animals.status, "loading");
  assert.equal(runtime.store.getState().animals.items[0].name, "Tartar");
  second.resolve(directory);
  await refresh;
  assert.equal(runtime.store.getState().animals.status, "ready");
});

test("opening animals loads detail and discards a slower previous response", async () => {
  const panel = fakePanel();
  const legacy = recordingLegacy(panel);
  const directory = canonicalDirectory();
  directory.animals.push({
    ...directory.animals[0],
    id: "AH-CHICKEN-2",
    name: "Zweite",
    groupId: null,
    tagIds: [],
  });
  const first = deferred();
  const second = deferred();
  const client = {
    async getAnimalDirectory() {
      return directory;
    },
    getAnimalDetail(id) {
      return id === "AH-CHICKEN-1" ? first.promise : second.promise;
    },
  };
  const runtime = createReadOnlyAnimalsRuntime({ panel, legacy, client });
  await runtime.load();

  const firstOpen = runtime.openAnimal("AH-CHICKEN-1");
  const secondOpen = runtime.openAnimal("AH-CHICKEN-2");
  second.resolve({
    ...canonicalDetail(),
    animal: { ...canonicalDetail().animal, id: "AH-CHICKEN-2", name: "Zweite" },
  });
  await secondOpen;
  first.resolve(canonicalDetail());
  await firstOpen;

  const state = runtime.store.getState();
  assert.equal(state.navigation.current.params.animalId, "AH-CHICKEN-2");
  assert.equal(state.animals.detail.data.animal.id, "AH-CHICKEN-2");
  assert.equal(panel.view, "animal-detail");
});

test("runtime handles canonical filters and migrated navigation events", async () => {
  const panel = fakePanel();
  const legacy = recordingLegacy(panel);
  const client = {
    async getAnimalDirectory() {
      return canonicalDirectory();
    },
    async getAnimalDetail() {
      return canonicalDetail();
    },
  };
  const runtime = createReadOnlyAnimalsRuntime({ panel, legacy, client });
  await runtime.load();

  await runtime.handleEvent(targetEvent({ action: "home-group-toggle" }));
  assert.equal(runtime.store.getState().animals.filters.openPanel, "group");
  await runtime.handleEvent(targetEvent({ action: "home-group-select", id: "GR-FLOCK" }));
  assert.equal(runtime.store.getState().animals.filters.groupId, "GR-FLOCK");
  await runtime.handleEvent(targetEvent({ action: "home-tag-select", id: "TG-RESCUE" }));
  assert.equal(runtime.store.getState().animals.filters.tagId, "TG-RESCUE");
  await runtime.handleEvent(targetEvent({ action: "home-search", value: "tartar" }));
  assert.equal(runtime.store.getState().animals.filters.query, "tartar");
  await runtime.handleEvent(targetEvent({ action: "animals-toggle-archived" }));
  assert.equal(runtime.store.getState().animals.filters.includeArchived, false);
  await runtime.handleEvent(targetEvent({ view: "animals" }));
  assert.equal(runtime.store.getState().navigation.current.name, "animals");
  assert.equal(panel.view, "animals");
});

test("legacy navigation loads Legacy state once and uses its renderer", async () => {
  const panel = fakePanel();
  const legacy = recordingLegacy(panel);
  const client = {
    async getAnimalDirectory() {
      return canonicalDirectory();
    },
    async getAnimalDetail() {
      return canonicalDetail();
    },
  };
  const runtime = createReadOnlyAnimalsRuntime({ panel, legacy, client });

  await runtime.navigate("tasks");
  await runtime.navigate("calendar");

  assert.equal(panel.view, "calendar");
  assert.deepEqual(legacy.calls.filter(([name]) => name === "load"), [["load", "tasks"]]);
  assert.deepEqual(legacy.calls.filter(([name]) => name === "render"), [
    ["render", "tasks"],
    ["render", "calendar"],
  ]);
});

test("runtime identifies modern events but leaves write actions to Legacy", () => {
  const panel = fakePanel();
  const runtime = createReadOnlyAnimalsRuntime({
    panel,
    legacy: recordingLegacy(panel),
    client: {
      async getAnimalDirectory() {
        return canonicalDirectory();
      },
      async getAnimalDetail() {
        return canonicalDetail();
      },
    },
  });

  assert.equal(runtime.handlesEvent(targetEvent({ view: "overview" })), true);
  assert.equal(runtime.handlesEvent(targetEvent({ view: "tasks" })), true);
  assert.equal(runtime.handlesEvent(targetEvent({ action: "refresh" })), true);
  assert.equal(runtime.handlesEvent(targetEvent({ action: "animal-detail", id: "A-1" })), true);
  assert.equal(runtime.handlesEvent(targetEvent({ action: "edit-animal", id: "A-1" })), false);
  assert.equal(runtime.handlesEvent(targetEvent({ action: "archive", id: "A-1" })), false);
});

test("render route dispatches only the three approved views", () => {
  const directory = canonicalDirectory();
  const base = {
    language: { code: "de", locale: "de-CH" },
    animals: {
      status: "ready",
      items: directory.animals,
      groups: directory.groups,
      tags: directory.tags,
      catalog: directory.catalog,
      directoryMeta: {
        version: directory.version,
        timeZone: directory.timeZone,
        today: directory.today,
        summary: directory.summary,
      },
      filters: { query: "", groupId: "all", tagId: "all", includeArchived: true },
    },
    tasks: { occurrences: directory.occurrences },
    timeline: { items: directory.events },
  };
  assert.match(renderReadOnlyAnimalsRoute({ ...base, navigation: { current: { name: "overview", params: {} } } }), /data-modern-route="overview"/);
  assert.match(renderReadOnlyAnimalsRoute({ ...base, navigation: { current: { name: "animals", params: {} } } }), /data-modern-route="animals"/);
  assert.throws(
    () => renderReadOnlyAnimalsRoute({ ...base, navigation: { current: { name: "tasks", params: {} } } }),
    (error) => error.code === "validation" && error.details.path === "route.name",
  );
});
