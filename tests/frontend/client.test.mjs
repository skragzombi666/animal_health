import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { AnimalHealthClient } from "../../custom_components/animal_health/frontend/src/api/client.js";
import { COMMANDS } from "../../custom_components/animal_health/frontend/src/api/commands.js";
import { AnimalHealthError } from "../../custom_components/animal_health/frontend/src/api/errors.js";

const fixture = JSON.parse(
  await readFile(
    new URL("./fixtures/phase2-snapshots-0.9.41.json", import.meta.url),
    "utf8",
  ),
);

class RecordingTransport {
  constructor(responses = {}) {
    this.responses = responses;
    this.requests = [];
    this.services = [];
    this.downloads = [];
    this.notifications = [];
  }

  async request(command, payload = {}) {
    this.requests.push({ command, payload });
    if (!(command in this.responses)) {
      throw new Error(`No response for ${command}`);
    }
    return structuredClone(this.responses[command]);
  }

  async callService(service, payload = {}, options = {}) {
    this.services.push({ service, payload, options });
    return { ok: true };
  }

  async download(resource) {
    this.downloads.push(resource);
  }

  notify(message, options = {}) {
    this.notifications.push({ message, options });
  }
}

function createTransport() {
  const rawAnimalDetail = structuredClone(fixture.animalDetail);
  delete rawAnimalDetail.attachments;
  return new RecordingTransport({
    [COMMANDS.dashboard]: fixture.dashboard,
    [COMMANDS.catalog]: fixture.catalog,
    [COMMANDS.features]: fixture.features,
    [COMMANDS.tagState]: fixture.tagState,
    [COMMANDS.animalDetail]: rawAnimalDetail,
    [COMMANDS.attachmentsList]: {
      attachments: fixture.animalDetail.attachments,
    },
    [COMMANDS.download]: { url: "/download/token" },
    [COMMANDS.treatmentState]: fixture.treatmentState,
    [COMMANDS.masterDataState]: fixture.masterDataState,
    [COMMANDS.productState]: fixture.productState,
  });
}

test("client maps current commands to normalized read methods", async () => {
  const transport = createTransport();
  const client = new AnimalHealthClient(transport);

  const dashboard = await client.getDashboard();
  const detail = await client.getAnimalDetail("AH-CHICKEN-1", {
    eventLimit: 250,
    today: "2026-09-04",
  });
  const attachments = await client.listAttachments({
    animalId: "AH-CHICKEN-1",
    eventId: "EV-MED-1",
  });
  const download = await client.requestDownload({
    kind: "attachment",
    resourceId: "ATT-EVENT-1",
  });
  const products = await client.getProductState();

  assert.equal(dashboard.animals[0].name, "Tartar");
  assert.equal(detail.events[0].attachments[0].id, "ATT-EVENT-1");
  assert.equal(detail.attachments[0].id, "ATT-EVENT-1");
  assert.equal(attachments[0].filename, "gabe.jpg");
  assert.deepEqual(download, { url: "/download/token" });
  assert.equal(products.databases.length, 2);
  assert.deepEqual(transport.requests, [
    { command: COMMANDS.dashboard, payload: {} },
    {
      command: COMMANDS.animalDetail,
      payload: { animal_id: "AH-CHICKEN-1", event_limit: 250 },
    },
    {
      command: COMMANDS.attachmentsList,
      payload: { animal_id: "AH-CHICKEN-1" },
    },
    {
      command: COMMANDS.attachmentsList,
      payload: { animal_id: "AH-CHICKEN-1", event_id: "EV-MED-1" },
    },
    {
      command: COMMANDS.download,
      payload: { kind: "attachment", resource_id: "ATT-EVENT-1" },
    },
    { command: COMMANDS.productState, payload: {} },
  ]);
});

test("animal directory performs four independent reads and normalizes once", async () => {
  const transport = createTransport();
  const client = new AnimalHealthClient(transport);

  const directory = await client.getAnimalDirectory();
  const commands = transport.requests.map(({ command }) => command).sort();

  assert.deepEqual(commands, [
    COMMANDS.catalog,
    COMMANDS.dashboard,
    COMMANDS.features,
    COMMANDS.tagState,
  ].sort());
  assert.equal(directory.animals[0].groupId, "GR-FLOCK");
  assert.deepEqual(directory.animals[0].tagIds, ["TG-RESCUE"]);
});

test("feature and settings reads combine their legacy endpoints behind one client method", async () => {
  const transport = createTransport();
  const client = new AnimalHealthClient(transport);

  const features = await client.getFeatureState();
  const settings = await client.getSettingsState();

  assert.equal(features.groups[0].id, "GR-FLOCK");
  assert.equal(features.tags[0].id, "TG-RESCUE");
  assert.equal(settings.treatmentPlans[0].name, "Schmerztherapie");
  assert.equal(settings.entryTypes[0].label, "Beobachtung allgemein");
  assert.deepEqual(
    transport.requests.map(({ command }) => command),
    [
      COMMANDS.features,
      COMMANDS.tagState,
      COMMANDS.treatmentState,
      COMMANDS.masterDataState,
    ],
  );
});

test("client service and host operations preserve the transport contract", async () => {
  const transport = createTransport();
  const client = new AnimalHealthClient(transport);

  await client.callService("archive_animal", { device_id: "device-tartar" });
  await client.download({ kind: "json", resourceId: null });
  client.notify("Gespeichert", { severity: "success" });

  assert.deepEqual(transport.services, [
    {
      service: "archive_animal",
      payload: { device_id: "device-tartar" },
      options: {},
    },
  ]);
  assert.deepEqual(transport.downloads, [{ kind: "json", resourceId: null }]);
  assert.deepEqual(transport.notifications, [
    { message: "Gespeichert", options: { severity: "success" } },
  ]);
});

test("client errors retain the domain operation and preserve transport context", async () => {
  const transport = createTransport();
  transport.request = async () => {
    throw new AnimalHealthError("offline", {
      code: "transport",
      operation: "request:animal_health/dashboard",
    });
  };
  const client = new AnimalHealthClient(transport);

  await assert.rejects(
    () => client.getDashboard(),
    (error) =>
      error.code === "transport" &&
      error.operation === "getDashboard" &&
      error.details.transportOperation === "request:animal_health/dashboard",
  );
});
