import { installLegacyReadOnlyAnimalsSlice } from "./legacy/compatibility-bridge.js";

installLegacyReadOnlyAnimalsSlice(AnimalHealthPanel, {
  integrationVersion: typeof V === "string" ? V : "unknown",
});
