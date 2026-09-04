import { COMMANDS } from "./commands.js";
import { AnimalHealthError, normalizeError } from "./errors.js";
import {
  normalizeAnimalDetail,
  normalizeAnimalDirectory,
  normalizeAttachment,
  normalizeCatalog,
  normalizeDashboard,
  normalizeFeatureState,
  normalizeMasterDataState,
  normalizeProductState,
  normalizeSettingsState,
  normalizeTreatmentState,
} from "./normalizers/index.js";
import {
  asArray,
  asRecord,
  firstDefined,
  requiredText,
} from "./normalizers/common.js";
import { assertTransport, requirePayload } from "../platform/transport.js";

function domainError(error, operation) {
  const normalized = normalizeError(error, { operation });
  if (normalized.operation === operation) return normalized;
  return new AnimalHealthError(normalized.message, {
    code: normalized.code,
    operation,
    details: {
      ...normalized.details,
      ...(normalized.operation
        ? { transportOperation: normalized.operation }
        : {}),
    },
    cause: normalized,
  });
}

function attachmentRecords(rawValue) {
  const raw = asRecord(rawValue, "attachmentsResponse");
  return asArray(
    firstDefined(raw, ["attachments"], []),
    "attachmentsResponse.attachments",
  );
}

export class AnimalHealthClient {
  constructor(transport) {
    this.transport = assertTransport(transport);
  }

  async _request(command, payload, operation) {
    try {
      return await this.transport.request(command, payload);
    } catch (error) {
      throw domainError(error, operation);
    }
  }

  async getDashboard() {
    return normalizeDashboard(
      await this._request(COMMANDS.dashboard, {}, "getDashboard"),
    );
  }

  async getCatalog() {
    return normalizeCatalog(
      await this._request(COMMANDS.catalog, {}, "getCatalog"),
    );
  }

  async getFeatureState() {
    const [features, tagState] = await Promise.all([
      this._request(COMMANDS.features, {}, "getFeatureState.features"),
      this._request(COMMANDS.tagState, {}, "getFeatureState.tags"),
    ]);
    return normalizeFeatureState(features, tagState);
  }

  async getAnimalDirectory() {
    const [dashboard, catalog, features, tagState] = await Promise.all([
      this._request(COMMANDS.dashboard, {}, "getAnimalDirectory.dashboard"),
      this._request(COMMANDS.catalog, {}, "getAnimalDirectory.catalog"),
      this._request(COMMANDS.features, {}, "getAnimalDirectory.features"),
      this._request(COMMANDS.tagState, {}, "getAnimalDirectory.tags"),
    ]);
    return normalizeAnimalDirectory({ dashboard, catalog, features, tagState });
  }

  async getAnimalDetail(
    animalId,
    { eventLimit = 300, today = null } = {},
  ) {
    const id = requiredText(animalId, "animalId");
    const limit = Number(eventLimit);
    if (!Number.isInteger(limit) || limit < 1 || limit > 500) {
      throw domainError(
        {
          code: "validation",
          message: "eventLimit must be an integer from 1 to 500",
          details: { path: "eventLimit" },
        },
        "getAnimalDetail",
      );
    }
    const [detail, attachmentResponse] = await Promise.all([
      this._request(
        COMMANDS.animalDetail,
        { animal_id: id, event_limit: limit },
        "getAnimalDetail.detail",
      ),
      this._request(
        COMMANDS.attachmentsList,
        { animal_id: id },
        "getAnimalDetail.attachments",
      ),
    ]);
    return normalizeAnimalDetail(
      {
        ...asRecord(detail, "animalDetailResponse"),
        attachments: attachmentRecords(attachmentResponse),
      },
      { today },
    );
  }

  async listAttachments({ animalId = null, eventId = null } = {}) {
    const payload = {};
    if (animalId != null) payload.animal_id = requiredText(animalId, "animalId");
    if (eventId != null) payload.event_id = requiredText(eventId, "eventId");
    return attachmentRecords(
      await this._request(
        COMMANDS.attachmentsList,
        payload,
        "listAttachments",
      ),
    ).map(normalizeAttachment);
  }

  async getTreatmentState() {
    return normalizeTreatmentState(
      await this._request(
        COMMANDS.treatmentState,
        {},
        "getTreatmentState",
      ),
    );
  }

  async getMasterDataState() {
    return normalizeMasterDataState(
      await this._request(
        COMMANDS.masterDataState,
        {},
        "getMasterDataState",
      ),
    );
  }

  async getSettingsState() {
    const [treatments, masterData] = await Promise.all([
      this._request(
        COMMANDS.treatmentState,
        {},
        "getSettingsState.treatments",
      ),
      this._request(
        COMMANDS.masterDataState,
        {},
        "getSettingsState.masterData",
      ),
    ]);
    return normalizeSettingsState(treatments, masterData);
  }

  async getProductState() {
    return normalizeProductState(
      await this._request(COMMANDS.productState, {}, "getProductState"),
    );
  }

  async requestDownload({ kind, resourceId = null } = {}) {
    const payload = { kind: requiredText(kind, "kind") };
    if (resourceId != null) {
      payload.resource_id = requiredText(resourceId, "resourceId");
    }
    return this._request(COMMANDS.download, payload, "requestDownload");
  }

  async callService(service, payload = {}, options = {}) {
    const name = requiredText(service, "service");
    try {
      return await this.transport.callService(
        name,
        requirePayload(payload),
        requirePayload(options, "options"),
      );
    } catch (error) {
      throw domainError(error, `callService:${name}`);
    }
  }

  async download(resource) {
    try {
      return await this.transport.download(requirePayload(resource, "resource"));
    } catch (error) {
      throw domainError(error, "download");
    }
  }

  notify(message, options = {}) {
    try {
      return this.transport.notify(
        requiredText(message, "message"),
        requirePayload(options, "options"),
      );
    } catch (error) {
      throw domainError(error, "notify");
    }
  }
}
