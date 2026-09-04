import assert from "node:assert/strict";
import test from "node:test";

import { installLegacyReadOnlyAnimalsSlice } from "../../custom_components/animal_health/frontend/src/legacy/compatibility-bridge.js";

function event({ action = null, view = null } = {}) {
  const target = {
    dataset: {
      ...(action ? { action } : {}),
      ...(view ? { view } : {}),
    },
  };
  return { target, composedPath: () => [target] };
}

function setup() {
  const legacyCalls = [];
  class LegacyPanel {
    constructor() {
      this.view = "overview";
      this.modal = null;
      this.d = null;
      this.h = { language: "de" };
      this.detail = null;
      this.shadowRoot = { innerHTML: "" };
    }
  }
  LegacyPanel.prototype.render = function () {
    legacyCalls.push(["render", this.view, Boolean(this.modal)]);
    this.shadowRoot.innerHTML = `<legacy>${this.view}</legacy>`;
    return "legacy-render";
  };
  LegacyPanel.prototype.load = async function () {
    legacyCalls.push(["load", this.view]);
    this.d = { loaded: true };
    this.render();
    return this.d;
  };
  LegacyPanel.prototype.loadDetail = async function (id) {
    legacyCalls.push(["loadDetail", id]);
    return `legacy-detail:${id}`;
  };
  LegacyPanel.prototype.handleClick = async function (value) {
    legacyCalls.push(["handleClick", value.target.dataset.action || value.target.dataset.view]);
    if (value.target.dataset.action === "create-animal") {
      this.modal = { type: "create-animal" };
      this.render();
    }
    if (value.target.dataset.action === "archive") {
      await this.load();
    }
    return "legacy-click";
  };
  LegacyPanel.prototype.handleInput = function (value) {
    legacyCalls.push(["handleInput", value.target.dataset.action || "legacy"]);
    return "legacy-input";
  };
  LegacyPanel.prototype.handleSubmit = async function () {
    legacyCalls.push(["handleSubmit", this.modal?.type || null]);
    this.modal = null;
    await this.load();
    return "legacy-submit";
  };

  const runtimes = [];
  function runtimeFactory({ panel }) {
    const calls = [];
    const runtime = {
      calls,
      panel,
      async load(options = {}) {
        calls.push(["load", options]);
        return "modern-load";
      },
      async openAnimal(id) {
        calls.push(["openAnimal", id]);
        panel.view = "animal-detail";
        return `modern-detail:${id}`;
      },
      render() {
        calls.push(["render", panel.view]);
        panel.shadowRoot.innerHTML = `<modern>${panel.view}</modern>`;
        return "modern-render";
      },
      handlesEvent(value) {
        const target = value.composedPath()[0];
        return Boolean(target.dataset.view) || [
          "refresh",
          "animal-detail",
          "home-search",
        ].includes(target.dataset.action);
      },
      async handleEvent(value) {
        const target = value.composedPath()[0];
        calls.push(["handleEvent", target.dataset.action || target.dataset.view]);
        if (target.dataset.view) panel.view = target.dataset.view;
        return "modern-event";
      },
      async ensureLegacyReady() {
        calls.push(["ensureLegacyReady"]);
        if (!panel.d) await legacyMethods.load.call(panel);
        return panel.d;
      },
    };
    runtimes.push(runtime);
    return runtime;
  }

  const legacyMethods = {
    render: LegacyPanel.prototype.render,
    load: LegacyPanel.prototype.load,
    loadDetail: LegacyPanel.prototype.loadDetail,
    handleClick: LegacyPanel.prototype.handleClick,
    handleInput: LegacyPanel.prototype.handleInput,
    handleSubmit: LegacyPanel.prototype.handleSubmit,
  };

  return { LegacyPanel, legacyCalls, runtimes, runtimeFactory };
}

test("installer is idempotent and creates one runtime per panel", () => {
  const { LegacyPanel, runtimes, runtimeFactory } = setup();
  assert.equal(installLegacyReadOnlyAnimalsSlice(LegacyPanel, { runtimeFactory }), true);
  assert.equal(installLegacyReadOnlyAnimalsSlice(LegacyPanel, { runtimeFactory }), false);

  const first = new LegacyPanel();
  const second = new LegacyPanel();
  first.render();
  first.render();
  second.render();

  assert.equal(runtimes.length, 2);
  assert.deepEqual(runtimes[0].calls, [
    ["render", "overview"],
    ["render", "overview"],
  ]);
});

test("render and load dispatch complete routes and preserve modal Legacy rendering", async () => {
  const { LegacyPanel, legacyCalls, runtimes, runtimeFactory } = setup();
  installLegacyReadOnlyAnimalsSlice(LegacyPanel, { runtimeFactory });
  const panel = new LegacyPanel();

  assert.equal(panel.render(), "modern-render");
  assert.equal(await panel.load(), "modern-load");
  panel.view = "tasks";
  assert.equal(panel.render(), "legacy-render");
  assert.deepEqual(await panel.load(), { loaded: true });

  panel.view = "overview";
  panel.modal = { type: "create-animal" };
  assert.equal(panel.render(), "legacy-render");

  assert.deepEqual(runtimes[0].calls.slice(0, 2), [
    ["render", "overview"],
    ["load", {}],
  ]);
  assert.ok(legacyCalls.some(([name, route]) => name === "render" && route === "tasks"));
  assert.ok(legacyCalls.some(([name, route]) => name === "render" && route === "overview"));
});

test("migrated detail loading uses the modern runtime", async () => {
  const { LegacyPanel, legacyCalls, runtimes, runtimeFactory } = setup();
  installLegacyReadOnlyAnimalsSlice(LegacyPanel, { runtimeFactory });
  const panel = new LegacyPanel();

  assert.equal(await panel.loadDetail("A-1"), "modern-detail:A-1");
  assert.deepEqual(runtimes[0].calls, [["openAnimal", "A-1"]]);
  assert.equal(legacyCalls.length, 0);

  panel.view = "tasks";
  assert.equal(await panel.loadDetail("A-2"), "legacy-detail:A-2");
});

test("modern navigation and filters are intercepted from any non-modal route", async () => {
  const { LegacyPanel, legacyCalls, runtimes, runtimeFactory } = setup();
  installLegacyReadOnlyAnimalsSlice(LegacyPanel, { runtimeFactory });
  const panel = new LegacyPanel();
  panel.view = "tasks";

  assert.equal(await panel.handleClick(event({ view: "overview" })), "modern-event");
  assert.equal(panel.view, "overview");
  assert.equal(await panel.handleClick(event({ action: "refresh" })), "modern-event");
  assert.equal(await panel.handleInput(event({ action: "home-search" })), "modern-event");
  assert.deepEqual(runtimes[0].calls, [
    ["handleEvent", "overview"],
    ["handleEvent", "refresh"],
    ["handleEvent", "home-search"],
  ]);
  assert.equal(legacyCalls.length, 0);
});

test("write actions load Legacy data before invoking the original handler", async () => {
  const { LegacyPanel, legacyCalls, runtimes, runtimeFactory } = setup();
  installLegacyReadOnlyAnimalsSlice(LegacyPanel, { runtimeFactory });
  const panel = new LegacyPanel();

  assert.equal(await panel.handleClick(event({ action: "create-animal" })), "legacy-click");
  assert.deepEqual(runtimes[0].calls[0], ["ensureLegacyReady"]);
  assert.deepEqual(legacyCalls.slice(0, 3), [
    ["load", "overview"],
    ["render", "overview", false],
    ["handleClick", "create-animal"],
  ]);
  assert.equal(panel.modal.type, "create-animal");
  assert.equal(panel.shadowRoot.innerHTML, "<legacy>overview</legacy>");
});

test("legacy submit refreshes Legacy state internally then the modern directory", async () => {
  const { LegacyPanel, legacyCalls, runtimes, runtimeFactory } = setup();
  installLegacyReadOnlyAnimalsSlice(LegacyPanel, { runtimeFactory });
  const panel = new LegacyPanel();
  panel.d = { loaded: true };
  panel.modal = { type: "create-animal" };

  assert.equal(await panel.handleSubmit({}), "legacy-submit");

  assert.deepEqual(legacyCalls, [
    ["handleSubmit", "create-animal"],
    ["load", "overview"],
    ["render", "overview", false],
  ]);
  assert.deepEqual(runtimes[0].calls, [["load", { force: true }]]);
});

test("modal interactions and ordinary Legacy inputs never enter the modern runtime", async () => {
  const { LegacyPanel, legacyCalls, runtimes, runtimeFactory } = setup();
  installLegacyReadOnlyAnimalsSlice(LegacyPanel, { runtimeFactory });
  const panel = new LegacyPanel();
  panel.modal = { type: "create-animal" };

  await panel.handleClick(event({ action: "refresh" }));
  assert.equal(panel.handleInput(event({ action: "legacy-field" })), "legacy-input");

  assert.equal(runtimes.length, 0);
  assert.deepEqual(legacyCalls.map(([name]) => name), ["handleClick", "handleInput"]);
});
