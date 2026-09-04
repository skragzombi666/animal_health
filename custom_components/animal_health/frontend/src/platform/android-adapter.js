import {
  AnimalHealthError,
  ERROR_CODES,
  normalizeError,
  validationError,
} from "../api/errors.js";
import {
  assertTransport,
  requireName,
  requirePayload,
} from "./transport.js";

const DOMAIN = "animal_health";

function requireBridge(bridge) {
  if (bridge === null || typeof bridge !== "object") {
    throw validationError("bridge must be an object", "bridge");
  }
  if (typeof bridge.call !== "function") {
    throw validationError("bridge.call must be a function", "bridge.call");
  }
  return bridge;
}

async function invoke(bridge, request, operation) {
  try {
    const raw = await bridge.call(JSON.stringify(request));
    let value = raw;
    if (typeof raw === "string") {
      value = raw.trim() ? JSON.parse(raw) : null;
    }
    if (value && typeof value === "object" && value.__error) {
      throw {
        code: value.code || value.error_code || "android_bridge_error",
        message: String(value.__error),
        details: value.details,
      };
    }
    return value;
  } catch (error) {
    throw normalizeError(error, { operation });
  }
}

export function createAndroidTransport({ bridge } = {}) {
  const nativeBridge = requireBridge(bridge);
  const transport = {
    async request(command, payload = {}) {
      const name = requireName(command, "command");
      const data = requirePayload(payload);
      return invoke(nativeBridge, { ...data, type: name }, `request:${name}`);
    },

    async callService(service, payload = {}, options = {}) {
      const name = requireName(service, "service");
      const data = requirePayload(payload);
      const settings = requirePayload(options, "options");
      return invoke(
        nativeBridge,
        {
          type: "call_service",
          domain: DOMAIN,
          service: name,
          service_data: data,
          ...(settings.response === true ? { return_response: true } : {}),
        },
        `service:${name}`,
      );
    },

    async download(resource) {
      const value = requirePayload(resource, "resource");
      if (typeof nativeBridge.exportData !== "function") {
        throw new AnimalHealthError("Android export handling is unavailable", {
          code: ERROR_CODES.UNAVAILABLE,
          operation: "download",
        });
      }
      const kind = requireName(value.kind, "resource.kind");
      const resourceId = value.resourceId == null ? "" : String(value.resourceId);
      try {
        return await nativeBridge.exportData(kind, resourceId);
      } catch (error) {
        throw normalizeError(error, { operation: "download" });
      }
    },

    notify(message, options = {}) {
      const text = requireName(message, "message");
      const settings = requirePayload(options, "options");
      if (typeof nativeBridge.toast !== "function") {
        throw new AnimalHealthError("Android notification handling is unavailable", {
          code: ERROR_CODES.UNAVAILABLE,
          operation: "notify",
        });
      }
      try {
        return nativeBridge.toast(text, settings.severity === "error");
      } catch (error) {
        throw normalizeError(error, { operation: "notify" });
      }
    },
  };

  return assertTransport(transport);
}
