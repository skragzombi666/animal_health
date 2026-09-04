import assert from "node:assert/strict";
import test from "node:test";

import {
  AnimalHealthError,
  ERROR_CODES,
  normalizeError,
} from "../../custom_components/animal_health/frontend/src/api/errors.js";
import { createAndroidTransport } from "../../custom_components/animal_health/frontend/src/platform/android-adapter.js";
import { createHomeAssistantTransport } from "../../custom_components/animal_health/frontend/src/platform/home-assistant-adapter.js";
import { assertTransport } from "../../custom_components/animal_health/frontend/src/platform/transport.js";

test("Home Assistant adapter sends commands and prevents payload type override", async () => {
  const requests = [];
  const hass = {
    callWS: async (request) => {
      requests.push(request);
      return { ok: true };
    },
    callService: async () => undefined,
  };
  const transport = createHomeAssistantTransport({ getHass: () => hass });

  assert.deepEqual(
    await transport.request("animal_health/dashboard", {
      type: "ignored",
      ignoredType: true,
    }),
    { ok: true },
  );
  assert.deepEqual(requests, [
    { type: "animal_health/dashboard", ignoredType: true },
  ]);
});

test("Home Assistant adapter supports response services and optional host callbacks", async () => {
  const calls = [];
  const notifications = [];
  const downloads = [];
  const hass = {
    callWS: async (request) => {
      calls.push(request);
      return { response: { saved: true } };
    },
    callService: async (domain, service, payload) => {
      calls.push({ domain, service, payload });
    },
  };
  const transport = createHomeAssistantTransport({
    getHass: () => hass,
    downloadHandler: async (resource) => downloads.push(resource),
    notificationHandler: (message, options) =>
      notifications.push({ message, options }),
  });

  await transport.callService("create_record_task", { title: "Test" }, { response: true });
  await transport.callService("archive_animal", { device_id: "device-1" });
  await transport.download({ kind: "json", resourceId: null });
  transport.notify("Gespeichert", { severity: "success" });

  assert.deepEqual(calls, [
    {
      type: "call_service",
      domain: "animal_health",
      service: "create_record_task",
      service_data: { title: "Test" },
      return_response: true,
    },
    {
      domain: "animal_health",
      service: "archive_animal",
      payload: { device_id: "device-1" },
    },
  ]);
  assert.deepEqual(downloads, [{ kind: "json", resourceId: null }]);
  assert.deepEqual(notifications, [
    { message: "Gespeichert", options: { severity: "success" } },
  ]);
});

test("Home Assistant adapter reports unavailable optional capabilities when invoked", async () => {
  const transport = createHomeAssistantTransport({
    getHass: () => ({ callWS: async () => ({}), callService: async () => {} }),
  });

  await assert.rejects(
    () => transport.download({ kind: "json" }),
    (error) =>
      error instanceof AnimalHealthError &&
      error.code === ERROR_CODES.UNAVAILABLE &&
      error.operation === "download",
  );
});

test("Android adapter parses bridge responses and maps services", async () => {
  const calls = [];
  const exports = [];
  const toasts = [];
  const bridge = {
    call: async (serialized) => {
      const request = JSON.parse(serialized);
      calls.push(request);
      return JSON.stringify({ echoed: request.type });
    },
    exportData: (kind, resourceId) => exports.push({ kind, resourceId }),
    toast: (message, bad) => toasts.push({ message, bad }),
  };
  const transport = createAndroidTransport({ bridge });

  assert.deepEqual(await transport.request("animal_health/dashboard", {}), {
    echoed: "animal_health/dashboard",
  });
  await transport.callService("archive_animal", { device_id: "device-1" });
  await transport.download({ kind: "animal_pdf", resourceId: "AH-1" });
  transport.notify("Fehler", { severity: "error" });

  assert.deepEqual(calls, [
    { type: "animal_health/dashboard" },
    {
      type: "call_service",
      domain: "animal_health",
      service: "archive_animal",
      service_data: { device_id: "device-1" },
    },
  ]);
  assert.deepEqual(exports, [{ kind: "animal_pdf", resourceId: "AH-1" }]);
  assert.deepEqual(toasts, [{ message: "Fehler", bad: true }]);
});

test("Android adapter rejects native __error responses", async () => {
  const transport = createAndroidTransport({
    bridge: {
      call: () => JSON.stringify({ __error: "Animal does not exist" }),
      exportData() {},
      toast() {},
    },
  });

  await assert.rejects(
    () => transport.request("animal_health/animal_detail", { animal_id: "missing" }),
    (error) =>
      error instanceof AnimalHealthError &&
      error.code === ERROR_CODES.NOT_FOUND &&
      error.operation === "request:animal_health/animal_detail",
  );
});

test("transport validation rejects incomplete transports and invalid payloads", async () => {
  assert.throws(
    () => assertTransport({ request() {} }),
    (error) => error.code === ERROR_CODES.VALIDATION,
  );
  const transport = createHomeAssistantTransport({
    getHass: () => ({ callWS: async () => ({}), callService: async () => {} }),
  });
  await assert.rejects(
    () => transport.request("", {}),
    (error) => error.code === ERROR_CODES.VALIDATION,
  );
  await assert.rejects(
    () => transport.request("animal_health/dashboard", []),
    (error) => error.code === ERROR_CODES.VALIDATION,
  );
});

test("normalizeError exposes stable codes instead of host-specific codes", () => {
  const notFound = normalizeError(
    { code: "animal_not_found", message: "The selected animal no longer exists" },
    { operation: "getAnimalDetail" },
  );
  const conflict = normalizeError(
    { status: 409, message: "duplicate" },
    { operation: "save" },
  );
  const existing = new AnimalHealthError("kept", {
    code: ERROR_CODES.PERMISSION,
  });

  assert.equal(notFound.code, ERROR_CODES.NOT_FOUND);
  assert.equal(notFound.operation, "getAnimalDetail");
  assert.equal(conflict.code, ERROR_CODES.CONFLICT);
  assert.equal(normalizeError(existing), existing);
});
