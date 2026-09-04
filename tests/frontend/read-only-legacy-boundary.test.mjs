import assert from "node:assert/strict";
import test from "node:test";

import { createReadOnlyAnimalsRuntime } from "../../custom_components/animal_health/frontend/src/app/read-only-animals.js";

function event({ action = null, view = null, id = null } = {}) {
  const target = {
    value: "",
    dataset: {
      ...(action ? { action } : {}),
      ...(view ? { view } : {}),
      ...(id ? { id } : {}),
    },
  };
  return { target, composedPath: () => [target] };
}

function runtimeFor(panel) {
  const legacy = {
    async load() {
      panel.d = { loaded: true };
    },
    render() {},
    loadDetail() {},
    handleClick() {},
    handleInput() {},
  };
  const client = {
    async getAnimalDirectory() {
      return {
        version: "0.9.41",
        generatedAt: null,
        timeZone: "Europe/Zurich",
        today: "2026-09-04",
        summary: {},
        exports: {},
        animals: [],
        groups: [],
        tags: [],
        catalog: {},
        tasks: [],
        occurrences: [],
        events: [],
      };
    },
    async getAnimalDetail() {
      return {
        animal: { id: "A-1", name: "Tier" },
        tasks: [],
        occurrences: [],
        events: [],
        attachments: [],
      };
    },
  };
  return createReadOnlyAnimalsRuntime({ panel, legacy, client });
}

test("refresh remains a Legacy action while a Legacy route is active", () => {
  const panel = {
    h: { language: "de" },
    view: "tasks",
    modal: null,
    d: { loaded: true },
    detail: null,
    shadowRoot: { innerHTML: "" },
    hasAttribute: () => false,
    render() {},
  };
  const runtime = runtimeFor(panel);

  assert.equal(runtime.handlesEvent(event({ action: "refresh" })), false);
  assert.equal(runtime.handlesEvent(event({ action: "home-search" })), false);
  assert.equal(runtime.handlesEvent(event({ action: "animal-detail", id: "A-1" })), true);
  assert.equal(runtime.handlesEvent(event({ view: "overview" })), true);
  assert.equal(runtime.handlesEvent(event({ view: "calendar" })), true);
});

test("refresh and filters remain modern while a migrated route is active", () => {
  const panel = {
    h: { language: "de" },
    view: "animals",
    modal: null,
    d: null,
    detail: null,
    shadowRoot: { innerHTML: "" },
    hasAttribute: () => false,
    render() {},
  };
  const runtime = runtimeFor(panel);

  assert.equal(runtime.handlesEvent(event({ action: "refresh" })), true);
  assert.equal(runtime.handlesEvent(event({ action: "animals-filter" })), true);
  assert.equal(runtime.handlesEvent(event({ action: "edit-animal", id: "A-1" })), false);
});
