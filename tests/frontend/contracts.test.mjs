import assert from "node:assert/strict";
import test from "node:test";

import { DTO_SCHEMA_VERSION } from "../../custom_components/animal_health/frontend/src/api/contracts.js";
import * as publicApi from "../../custom_components/animal_health/frontend/src/entry.js";

test("Phase 2 publishes an explicit canonical DTO contract version", () => {
  assert.equal(DTO_SCHEMA_VERSION, 1);
  assert.equal(publicApi.DTO_SCHEMA_VERSION, DTO_SCHEMA_VERSION);
});
