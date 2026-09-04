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

function requireHass(getHass, operation) {
  if (typeof getHass !== "function") {
    throw validationError("getHass must be a function", "getHass");
  }
  const hass = getHass();
  if (hass === null || typeof hass !== "object") {
    throw new AnimalHealthError("Home Assistant is not available", {
      code: ERROR_CODES.UNAVAILABLE,
      operation,
    });
  }
  return hass;
}

async function run(operation, callback) {
  try {
    return await callback();
  } catch (error) {
    throw normalizeError(error, { operation });
  }
}

export function createHomeAssistantTransport({
  getHass,
  downloadHandler = null,
  notificationHandler = null,
} = {}) {
  const transport = {
    async request(command, payload = {}) {
      const name = requireName(command, "command");
      const data = requirePayload(payload);
      return run(`request:${name}`, async () => {
        const hass = requireHass(getHass, `request:${name}`);
        if (typeof hass.callWS !== "function") {
          throw new AnimalHealthError("Home Assistant WebSocket API is unavailable", {
            code: ERROR_CODES.UNAVAILABLE,
            operation: `request:${name}`,
          });
        }
        return hass.callWS({ ...data, type: name });
      });
    },

    async callService(service, payload = {}, options = {}) {
      const name = requireName(service, "service");
      const data = requirePayload(payload);
      const settings = requirePayload(options, "options");
      return run(`service:${name}`, async () => {
        const hass = requireHass(getHass, `service:${name}`);
        if (settings.response === true) {
          if (typeof hass.callWS !== "function") {
            throw new AnimalHealthError(
              "Home Assistant response service API is unavailable",
              {
                code: ERROR_CODES.UNAVAILABLE,
                operation: `service:${name}`,
              },
            );
          }
          return hass.callWS({
            type: "call_service",
            domain: DOMAIN,
            service: name,
            service_data: data,
            return_response: true,
          });
        }
        if (typeof hass.callService !== "function") {
          throw new AnimalHealthError("Home Assistant service API is unavailable", {
            code: ERROR_CODES.UNAVAILABLE,
            operation: `service:${name}`,
          });
        }
        return hass.callService(DOMAIN, name, data);
      });
    },

    async download(resource) {
      const value = requirePayload(resource, "resource");
      if (typeof downloadHandler !== "function") {
        throw new AnimalHealthError("Download handling is unavailable", {
          code: ERROR_CODES.UNAVAILABLE,
          operation: "download",
        });
      }
      return run("download", () => downloadHandler(value));
    },

    notify(message, options = {}) {
      const text = requireName(message, "message");
      const settings = requirePayload(options, "options");
      if (typeof notificationHandler !== "function") {
        throw new AnimalHealthError("Notification handling is unavailable", {
          code: ERROR_CODES.UNAVAILABLE,
          operation: "notify",
        });
      }
      try {
        return notificationHandler(text, settings);
      } catch (error) {
        throw normalizeError(error, { operation: "notify" });
      }
    },
  };

  return assertTransport(transport);
}
