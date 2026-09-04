export { AnimalHealthClient } from "./api/client.js";
export { COMMANDS } from "./api/commands.js";
export { DTO_SCHEMA_VERSION } from "./api/contracts.js";
export {
  AnimalHealthError,
  ERROR_CODES,
  classifyErrorCode,
  normalizeError,
  validationError,
} from "./api/errors.js";
export * from "./api/normalizers/index.js";
export { createAndroidTransport } from "./platform/android-adapter.js";
export { createHomeAssistantTransport } from "./platform/home-assistant-adapter.js";
export {
  assertTransport,
  isPlainObject,
  requireName,
  requirePayload,
} from "./platform/transport.js";
