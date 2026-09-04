import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  createReadOnlyAnimalsRuntime,
} from "../../custom_components/animal_health/frontend/src/app/read-only-animals.js";
import {
  normalizeAnimalDetail,
  normalizeAnimalDirectory,
} from "../../custom_components/animal_health/frontend/src/api/normalizers/index.js";
import {
  installLegacyReadOnlyAnimalsSlice,
} from "../../custom_components/animal_health/frontend/src/legacy/compatibility-bridge.js";

const fixture = JSON.parse(
  await readFile(
    new URL("./fixtures/phase2-snapshots-0.9.41.json", import.meta.url),
    "utf8",
  ),
);

function directory() {
  return normalizeAnimalDirectory({
    dashboard: fixture.dashboard,
    catalog: fixture.catalog,
    features: fixture.features,
    tagState: fixture.tagState,
  });
}

function detail(name = "Tartar") {
  const value = normalizeAnimalDetail(fixture.animalDetail, {
    today: "2026-09-04",
  });
  return {
    ...value,
    animal: { ...value.animal, name },
  };
}

function panel() {
  return {
    h: { language: "de" },
    view: "overview",
    modal: null,
    d: null,
    detail: null,
    shadowRoot: {
      innerHTML: "",
      querySelector() {
        return null;
      },
    },
    hasAttribute() {
      return false;
    },
    renderCalls: 0,
    render() {
      this.renderCalls += 1;
    },
  };
}

function legacy(value) {
  return {
    async load() {
      value.d = { loaded: true };
    },
    render() {
      value.shadowRoot.innerHTML = `<legacy route="${value.view}"></legacy>`;
    },
    loadDetail() {},
    handleClick() {},
    handleInput() {},
  };
}

function event({ action = null, view = null, value = "", start = null } = {}) {
  const target = {
    value,
    selectionStart: start,
    selectionEnd: start,
    dataset: {
      ...(action ? { action } : {}),
      ...(view ? { view } : {}),
    },
  };
  return {
    target,
    composedPath: () => [target],
  };
}

test("returning from Legacy to the already-current modern route renders immediately", async () => {
  const host = panel();
  const runtime = createReadOnlyAnimalsRuntime({
    panel: host,
    legacy: legacy(host),
    client: {
      async getAnimalDirectory() {
        return directory();
      },
      async getAnimalDetail() {
        return detail();
      },
    },
  });

  await runtime.load();
  runtime.render();
  await runtime.navigate("tasks");
  assert.match(host.shadowRoot.innerHTML, /<legacy/);

  await runtime.navigate("overview");

  assert.match(host.shadowRoot.innerHTML, /data-modern-route="overview"/);
  assert.doesNotMatch(host.shadowRoot.innerHTML, /<legacy/);
});

test("text filters restore focus and caret after the full route render", async () => {
  const host = panel();
  const replacement = {
    focusCalls: 0,
    ranges: [],
    focus() {
      this.focusCalls += 1;
    },
    setSelectionRange(start, end) {
      this.ranges.push([start, end]);
    },
  };
  host.shadowRoot.querySelector = (selector) =>
    selector === '[data-action="animals-filter"]' ? replacement : null;
  const runtime = createReadOnlyAnimalsRuntime({
    panel: host,
    legacy: legacy(host),
    client: {
      async getAnimalDirectory() {
        return directory();
      },
      async getAnimalDetail() {
        return detail();
      },
    },
  });
  await runtime.load();
  await runtime.navigate("animals");

  await runtime.handleEvent(
    event({ action: "animals-filter", value: "tartar", start: 4 }),
  );

  assert.equal(runtime.store.getState().animals.filters.query, "tartar");
  assert.equal(replacement.focusCalls, 1);
  assert.deepEqual(replacement.ranges, [[4, 4]]);
});

test("DOM action failures resolve into state instead of becoming unhandled rejections", async () => {
  const host = panel();
  const runtime = createReadOnlyAnimalsRuntime({
    panel: host,
    legacy: legacy(host),
    client: {
      async getAnimalDirectory() {
        throw Object.assign(new Error("offline"), { code: "transport" });
      },
      async getAnimalDetail() {
        return detail();
      },
    },
  });

  const result = await runtime.handleEvent(event({ action: "refresh" }));

  assert.equal(result.applied, false);
  assert.equal(result.error.code, "transport");
  assert.equal(runtime.store.getState().animals.status, "error");
});

test("refreshing an active animal detail reloads directory and detail", async () => {
  const host = panel();
  const client = {
    directoryCalls: 0,
    detailCalls: 0,
    async getAnimalDirectory() {
      this.directoryCalls += 1;
      return directory();
    },
    async getAnimalDetail() {
      this.detailCalls += 1;
      return detail(this.detailCalls === 1 ? "Vorher" : "Nachher");
    },
  };
  const runtime = createReadOnlyAnimalsRuntime({
    panel: host,
    legacy: legacy(host),
    client,
  });

  await runtime.load();
  await runtime.openAnimal("AH-CHICKEN-1");
  assert.equal(runtime.store.getState().animals.detail.data.animal.name, "Vorher");

  await runtime.refreshCurrentRoute();

  assert.equal(client.directoryCalls, 2);
  assert.equal(client.detailCalls, 2);
  assert.equal(runtime.store.getState().animals.detail.data.animal.name, "Nachher");
});

test("a completed Legacy write refreshes the complete active detail route", async () => {
  const calls = [];
  class LegacyPanel {
    constructor() {
      this.view = "animal-detail";
      this.modal = { type: "weight" };
      this.d = { loaded: true };
      this.h = { language: "de" };
      this.shadowRoot = { innerHTML: "" };
    }
  }
  LegacyPanel.prototype.render = function () {};
  LegacyPanel.prototype.load = async function () {};
  LegacyPanel.prototype.loadDetail = async function () {};
  LegacyPanel.prototype.handleClick = async function () {};
  LegacyPanel.prototype.handleInput = function () {};
  LegacyPanel.prototype.handleSubmit = async function () {
    this.modal = null;
    return "saved";
  };

  installLegacyReadOnlyAnimalsSlice(LegacyPanel, {
    runtimeFactory() {
      return {
        render() {},
        load(options) {
          calls.push(["load", options]);
        },
        refreshCurrentRoute() {
          calls.push(["refreshCurrentRoute"]);
        },
        handlesEvent() {
          return false;
        },
        handleEvent() {},
        openAnimal() {},
        ensureLegacyReady() {},
      };
    },
  });
  const host = new LegacyPanel();

  assert.equal(await host.handleSubmit({}), "saved");
  assert.deepEqual(calls, [["refreshCurrentRoute"]]);
});
