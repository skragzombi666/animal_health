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
export { createAnimalHealthApplication } from "./app/application.js";
export {
  createAnimalHealthPanelClass,
  renderApplicationShell,
} from "./app/animal-health-panel.js";
export { createController } from "./app/controller.js";
export {
  MIGRATED_READ_ROUTES,
  createReadOnlyAnimalsRuntime,
  renderReadOnlyAnimalsRoute,
} from "./app/read-only-animals.js";
export { createRouter } from "./app/router.js";
export { createInitialState, createRoute } from "./app/state.js";
export { createStore } from "./app/store.js";
export {
  selectAnimalById,
  selectGroupById,
  selectGroupedAnimals,
  selectNextOccurrenceForAnimal,
  selectOpenOccurrencesForAnimal,
  selectRecentEvents,
  selectUrgentOccurrences,
  selectVisibleAnimals,
} from "./domain/animals/selectors.js";
export {
  createCompatibilityBridge,
  installLegacyReadOnlyAnimalsSlice,
} from "./legacy/compatibility-bridge.js";
export { createAndroidTransport } from "./platform/android-adapter.js";
export { createHomeAssistantTransport } from "./platform/home-assistant-adapter.js";
export {
  assertTransport,
  isPlainObject,
  requireName,
  requirePayload,
} from "./platform/transport.js";
export { createTranslator, MESSAGES } from "./ui/read-only/i18n.js";
export {
  escapeAttribute,
  escapeHtml,
  formatDateOnly,
  formatDateTime,
  formatEnum,
  formatNumber,
  formatWeight,
  speciesLabel,
} from "./ui/read-only/format.js";
export { renderAnimalDetail } from "./ui/views/animal-detail.js";
export { renderAnimals } from "./ui/views/animals.js";
export { renderOverview } from "./ui/views/overview.js";
