import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  MODERN_SEPARATOR,
  buildBundle,
  buildLegacyPrelude,
  buildModernRuntime,
} from "../../scripts/build_frontend.mjs";

const DIST = new URL(
  "../../custom_components/animal_health/frontend/dist/animal-health-panel.js",
  import.meta.url,
);

test("active bundle preserves the exact Legacy prefix and appends one IIFE", async () => {
  const legacy = await buildLegacyPrelude();
  const modern = await buildModernRuntime();
  const bundle = await buildBundle();

  assert.equal(bundle.slice(0, legacy.length), legacy);
  assert.equal(bundle.slice(legacy.length, legacy.length + MODERN_SEPARATOR.length), MODERN_SEPARATOR);
  assert.equal(bundle, `${legacy}${MODERN_SEPARATOR}${modern}`);
  assert.match(modern, /installLegacyReadOnlyAnimalsSlice/);
  assert.match(modern, /createReadOnlyAnimalsRuntime/);
  assert.doesNotMatch(modern, /^\s*import\s/m);
  assert.doesNotMatch(modern, /^\s*export\s/m);
  assert.equal((bundle.match(/ANIMAL_HEALTH_MODERN_RUNTIME/g) || []).length, 1);
});

test("checked-in dist equals the deterministic active bundle", async () => {
  assert.equal(await readFile(DIST, "utf8"), await buildBundle());
});

test("modern runtime is appended after the final frozen fragment", async () => {
  const legacy = await buildLegacyPrelude();
  const bundle = await buildBundle();
  assert.match(legacy.slice(-2500), /part99|AH099|customElements|AnimalHealthPanel/);
  assert.equal(bundle.indexOf(MODERN_SEPARATOR), legacy.length);
  assert.match(bundle.slice(legacy.length), /ANIMAL_HEALTH_MODERN_RUNTIME/);
});
