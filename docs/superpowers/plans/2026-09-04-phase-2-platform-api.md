# Phase 2 Platform Adapter and API Normalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce a testable, host-independent frontend data boundary for Home Assistant and Android without activating or changing the existing 0.9.41 user interface.

**Architecture:** New ES modules live under `custom_components/animal_health/frontend/src/`. Platform adapters are the only modules allowed to know Home Assistant or the Android JavaScript bridge. `AnimalHealthClient` maps current versioned WebSocket commands to domain-oriented methods and immediately normalizes all raw responses into stable camelCase DTOs. Phase 2 source remains inactive at runtime; the checked-in legacy dist bundle stays byte-identical until the new application shell is introduced in Phase 3.

**Tech Stack:** JavaScript ES modules, JSDoc, Node.js built-in test runner, Python static boundary tests, GitHub Actions, current Home Assistant WebSocket/service APIs, current Android `AndroidBridge`

**Spec:** `docs/architecture/2026-09-04-consolidation-target-architecture.md`

## Global Constraints

- Reference behavior remains Animal Health 0.9.41.
- No existing UI route, dialog, API, service, database schema, persisted ID, or stored record changes.
- The 99 legacy fragments remain frozen and unchanged.
- `frontend/dist/animal-health-panel.js` remains an exact concatenation of the 99 legacy fragments in Phase 2.
- No Phase 2 module mutates `AnimalHealthPanel.prototype`, appends to `shadowRoot.innerHTML`, registers a custom element, or writes global runtime state.
- Only `platform/home-assistant-adapter.js` may call `hass.callWS` or `hass.callService`.
- Only `platform/android-adapter.js` may invoke an Android bridge object.
- Versioned command strings are confined to `api/commands.js`.
- Historical response aliases are confined to normalizers.
- Canonical DTO property names use camelCase.
- Date-only values remain `YYYY-MM-DD`; normalizers must not pass them through `new Date()`.
- No third-party JavaScript runtime or build dependency is introduced in this phase.
- New source is validated with Node.js and has no runtime inclusion until Phase 3.
- All implementation changes follow red-green-refactor with focused commits.

---

## File Map

### New source files

- `package.json` — declares ES-module mode and frontend test/check scripts.
- `custom_components/animal_health/frontend/src/entry.js` — side-effect-free public export surface for Phase 2.
- `custom_components/animal_health/frontend/src/platform/transport.js` — transport contract validation and payload guards.
- `custom_components/animal_health/frontend/src/platform/home-assistant-adapter.js` — Home Assistant host adapter.
- `custom_components/animal_health/frontend/src/platform/android-adapter.js` — Android bridge adapter.
- `custom_components/animal_health/frontend/src/api/commands.js` — current command names in one compatibility registry.
- `custom_components/animal_health/frontend/src/api/errors.js` — stable frontend error model and classification.
- `custom_components/animal_health/frontend/src/api/client.js` — domain-oriented read client and service/download pass-through.
- `custom_components/animal_health/frontend/src/api/normalizers/common.js` — primitive conversion, field lookup, validation paths and alias isolation.
- `custom_components/animal_health/frontend/src/api/normalizers/animals.js` — animals, latest weight, groups, tags and attachments.
- `custom_components/animal_health/frontend/src/api/normalizers/tasks.js` — task definitions, concrete occurrences, targets and timing.
- `custom_components/animal_health/frontend/src/api/normalizers/timeline.js` — health events and task-origin metadata.
- `custom_components/animal_health/frontend/src/api/normalizers/catalog.js` — catalog lists, species and breeds.
- `custom_components/animal_health/frontend/src/api/normalizers/features.js` — groups, memberships, tags, profiles and export metadata.
- `custom_components/animal_health/frontend/src/api/normalizers/dashboard.js` — dashboard, animal detail and merged animal-directory snapshots.
- `custom_components/animal_health/frontend/src/api/normalizers/products.js` — product databases and product records.
- `custom_components/animal_health/frontend/src/api/normalizers/treatments.js` — treatment plans, components and scheduled status changes.
- `custom_components/animal_health/frontend/src/api/normalizers/settings.js` — master data and combined settings snapshot.
- `custom_components/animal_health/frontend/src/api/normalizers/index.js` — explicit normalizer export surface.
- `scripts/check_frontend_modules.mjs` — syntax/import/boundary check for all Phase 2 source modules.
- `tests/frontend/fixtures/phase2-snapshots-0.9.41.json` — representative raw responses from current contracts.
- `tests/frontend/platform.test.mjs` — transport and adapter behavior.
- `tests/frontend/normalizers.test.mjs` — canonical DTO contracts.
- `tests/frontend/client.test.mjs` — command mapping and normalized client outputs.
- `tests/test_frontend_phase2.py` — repository-level architecture boundaries.
- `custom_components/animal_health/frontend/src/README.md` — source boundaries and extension rules.

### Modified files

- `.github/workflows/validate.yml` — run Phase 2 module checks and Node tests.
- `.github/workflows/android.yml` — validate shared source contracts before the APK build when frontend source changes.

---

### Task 1: Define Phase 2 Contracts with Failing Tests

**Files:**
- Create: `package.json`
- Create: `tests/frontend/fixtures/phase2-snapshots-0.9.41.json`
- Create: `tests/frontend/platform.test.mjs`
- Create: `tests/frontend/normalizers.test.mjs`
- Create: `tests/frontend/client.test.mjs`
- Create: `tests/test_frontend_phase2.py`

**Interfaces:**
- Consumes: current 0.9.41 response field names and host APIs.
- Produces: executable contracts for adapters, errors, DTOs and `AnimalHealthClient`.

- [ ] **Step 1: Add ES-module package metadata**

```json
{
  "name": "animal-health-frontend",
  "private": true,
  "type": "module",
  "scripts": {
    "check:frontend": "node scripts/check_frontend_modules.mjs",
    "test:frontend": "node --test tests/frontend/*.test.mjs"
  }
}
```

- [ ] **Step 2: Add representative raw fixtures**

The fixture document contains these top-level keys:

```text
dashboard
animalDetail
features
tagState
catalog
treatmentState
masterDataState
productState
```

It must include:

- one active chicken with latest weight, group, tag and profile image;
- one recurring medication task;
- one overdue and one current occurrence of that same task;
- one task-generated medication event;
- one image attachment;
- one treatment plan with medication and action components;
- one master-data override;
- one enabled official product database, one local database and products with source/original metadata.

- [ ] **Step 3: Write adapter tests**

Required assertions:

```javascript
const transport = createHomeAssistantTransport({ getHass: () => hass });
await transport.request("animal_health/dashboard", { ignoredType: true });
assert.deepEqual(hass.requests[0], {
  type: "animal_health/dashboard",
  ignoredType: true,
});
```

Also cover response-returning services, missing host methods, Android JSON parsing, Android `__error`, bridge download, notifications, invalid commands and normalized errors.

- [ ] **Step 4: Write normalizer tests**

Assert exact camelCase DTOs for:

- date-only preservation;
- merged group/tag/profile animal metadata;
- task definition versus occurrence separation;
- `seriesId` fallback only for recurring definitions;
- `timing` values `overdue`, `today`, `upcoming`, `closed`;
- task-origin event metadata;
- product source, local modification and original snapshot;
- treatment components and settings aggregate;
- validation error path on missing required IDs.

- [ ] **Step 5: Write client tests**

Use a recording fake transport and assert exact commands:

```text
animal_health/dashboard
animal_health/catalog
animal_health/features
animal_health/v080/state
animal_health/animal_detail
animal_health/attachments/list
animal_health/download
animal_health/v0912/state
animal_health/v0924/state
animal_health/v0928/state
```

Verify `getAnimalDirectory()` performs the four required reads and returns one merged canonical snapshot. Verify `getSettingsState()` combines treatment and master-data state.

- [ ] **Step 6: Write Python architecture-boundary tests**

Assert:

- source files exist;
- only `home-assistant-adapter.js` contains `.callWS` or `.callService`;
- only `android-adapter.js` contains `bridge.call`, `bridge.toast` or `bridge.exportData`;
- only `api/commands.js` contains `animal_health/v0` command literals;
- no source contains `AnimalHealthPanel.prototype`, `shadowRoot.innerHTML +=`, `customElements.define` or assignment to `globalThis`/`window`;
- the Phase 1 dist bundle remains exact legacy concatenation;
- package scripts point to the permanent module checker and Node tests.

- [ ] **Step 7: Commit red tests**

```bash
git add package.json tests/frontend tests/test_frontend_phase2.py
git commit -m "test: define phase 2 platform and API contracts"
```

- [ ] **Step 8: Verify intended failure**

```bash
npm run test:frontend
python -m pytest -q tests/test_frontend_phase2.py
```

Expected: failure only because Phase 2 modules and checker do not yet exist.

---

### Task 2: Implement Stable Errors and the Platform Transport Boundary

**Files:**
- Create: `custom_components/animal_health/frontend/src/api/errors.js`
- Create: `custom_components/animal_health/frontend/src/platform/transport.js`
- Create: `custom_components/animal_health/frontend/src/platform/home-assistant-adapter.js`
- Create: `custom_components/animal_health/frontend/src/platform/android-adapter.js`
- Test: `tests/frontend/platform.test.mjs`

**Interfaces:**
- Produces: `AnimalHealthError`, `ERROR_CODES`, `normalizeError`, `validationError`, `assertTransport`, `createHomeAssistantTransport`, `createAndroidTransport`.

- [ ] **Step 1: Implement the stable error model**

`AnimalHealthError` properties:

```text
name = "AnimalHealthError"
code = validation | not_found | conflict | permission | transport | unavailable | internal
operation = string | null
details = plain object
cause = original value | null
```

Classification must inspect explicit error code, HTTP-like status and message without exposing host-specific codes to consumers.

- [ ] **Step 2: Implement transport validation**

`assertTransport(value)` must require callable methods:

```text
request
callService
download
notify
```

Commands and service names must be non-empty strings. Payloads must be plain objects and cannot be arrays.

- [ ] **Step 3: Implement Home Assistant adapter**

The factory accepts:

```javascript
createHomeAssistantTransport({
  getHass,
  downloadHandler = null,
  notificationHandler = null,
})
```

Behavior:

- `request(command, payload)` calls `hass.callWS({ ...payload, type: command })` so payload cannot override `type`;
- `callService(service, payload, { response: true })` uses `callWS` with `type: "call_service"`, domain `animal_health`, `return_response: true`;
- ordinary services use `hass.callService("animal_health", service, payload)`;
- missing optional host callbacks produce `unavailable` only when invoked;
- all rejected host calls become `AnimalHealthError` with operation metadata.

- [ ] **Step 4: Implement Android adapter**

The factory accepts `{ bridge }`. `bridge.call` may return a JSON string, an object, or a promise of either. `__error` responses become normalized failures. Services are encoded as `call_service`; downloads use `bridge.exportData(kind, resourceId)`; notifications use `bridge.toast(message, severity === "error")`.

- [ ] **Step 5: Run focused tests**

```bash
npm run test:frontend -- --test-name-pattern="transport|adapter|error"
```

Expected: platform tests pass; normalizer and client tests remain red.

- [ ] **Step 6: Commit**

```bash
git add custom_components/animal_health/frontend/src/api/errors.js custom_components/animal_health/frontend/src/platform
git commit -m "feat: add host-independent frontend transports"
```

---

### Task 3: Implement Core DTO Normalizers

**Files:**
- Create: `custom_components/animal_health/frontend/src/api/normalizers/common.js`
- Create: `custom_components/animal_health/frontend/src/api/normalizers/animals.js`
- Create: `custom_components/animal_health/frontend/src/api/normalizers/tasks.js`
- Create: `custom_components/animal_health/frontend/src/api/normalizers/timeline.js`
- Create: `custom_components/animal_health/frontend/src/api/normalizers/catalog.js`
- Create: `custom_components/animal_health/frontend/src/api/normalizers/features.js`
- Create: `custom_components/animal_health/frontend/src/api/normalizers/dashboard.js`
- Test: `tests/frontend/normalizers.test.mjs`

**Interfaces:**
- Produces: `normalizeAnimal`, `normalizeAttachment`, `normalizeTarget`, `normalizeTaskDefinition`, `normalizeTaskOccurrence`, `normalizeHealthEvent`, `normalizeCatalog`, `normalizeFeatureState`, `normalizeDashboard`, `normalizeAnimalDetail`, `normalizeAnimalDirectory`.

- [ ] **Step 1: Implement primitive and alias helpers**

Helpers must accept a field path and throw `validationError` for missing required values. Required helpers include:

```text
asRecord
asArray
firstDefined
requiredText
optionalText
booleanValue
numberValue
integerValue
stringList
dateOnly
dateTime
snakeToCamel
collectPrefixedFields
```

`dateOnly` validates `YYYY-MM-DD` text without constructing a JavaScript `Date`.

- [ ] **Step 2: Normalize animals and attachments**

Canonical animal properties:

```text
id, name, species, breed, color, sex, birthDate, arrivalDate,
status, statusChangedAt, isArchived, archivedAt, createdAt, updatedAt,
deviceId, latestWeight, groupId, tagIds, profileAttachmentId
```

Canonical attachment properties:

```text
id, animalId, eventId, filename, mediaType, sizeBytes, title, createdAt,
thumbnailUrl, previewUrl, downloadUrl
```

- [ ] **Step 3: Normalize task definitions and occurrences**

Definitions and occurrences remain separate DTOs. `normalizeTaskOccurrence` receives `{ taskById, today }`. It derives `timing` from explicit flags first and from `scheduledDate` plus `today` only when flags are absent. Closed statuses always produce `closed`.

All legacy `planned_*` fields are collected once into `planned` with camelCase keys.

- [ ] **Step 4: Normalize health events**

Create `source` metadata from `task_id`, `task_occurrence_id` and event payload source fields. Keep the domain payload under `payload`. Attachments are associated by event ID through a supplied index.

- [ ] **Step 5: Normalize catalog and feature state**

`normalizeFeatureState(features, tagState)` combines groups, primary-group memberships, tags, tag memberships, profiles, export paths and attachment limits. It returns serializable objects, not `Map` instances.

- [ ] **Step 6: Normalize dashboard, detail and directory snapshots**

`normalizeAnimalDirectory({ dashboard, catalog, features, tagState })` merges group/tag/profile metadata into each animal without mutating any input. It returns summary, animals, groups, tags, catalog, exports and host time metadata.

- [ ] **Step 7: Run focused tests**

```bash
npm run test:frontend -- --test-name-pattern="normaliz|dashboard|animal|task|timeline|catalog|feature"
```

Expected: core normalizer tests pass; product/settings and client tests remain red.

- [ ] **Step 8: Commit**

```bash
git add custom_components/animal_health/frontend/src/api/normalizers
git commit -m "feat: normalize core Animal Health read models"
```

---

### Task 4: Implement Product, Treatment and Settings Normalizers

**Files:**
- Create: `custom_components/animal_health/frontend/src/api/normalizers/products.js`
- Create: `custom_components/animal_health/frontend/src/api/normalizers/treatments.js`
- Create: `custom_components/animal_health/frontend/src/api/normalizers/settings.js`
- Create: `custom_components/animal_health/frontend/src/api/normalizers/index.js`
- Test: `tests/frontend/normalizers.test.mjs`

**Interfaces:**
- Produces: `normalizeProductDatabase`, `normalizeProduct`, `normalizeProductState`, `normalizeTreatmentComponent`, `normalizeTreatmentPlan`, `normalizeTreatmentState`, `normalizeMasterItem`, `normalizeMasterDataState`, `normalizeSettingsState`.

- [ ] **Step 1: Normalize product databases**

Canonical fields:

```text
id, name, description, productTypes, sourceName, sourceType, version,
dataAsOf, priority, updateMode, licenseNotice, sourceUrl, enabled,
isSystem, supportsLocalOverrides, viewOf, itemCount, modifiedCount
```

- [ ] **Step 2: Normalize products**

Canonical fields include source identity, kind, name, target species, active ingredient data, concentration, dosage form, routes, authorization metadata, hidden/custom/modified flags, classifications and an optional original snapshot. Avoid recursive `original.original` values.

- [ ] **Step 3: Normalize treatments**

Canonical treatment plan fields:

```text
id, name, speciesId, listAs, description, defaultUnit, defaultRoute,
components
```

Components use `type`, `name`, `dose`, `unit`, `route`, `instructions`.

- [ ] **Step 4: Normalize master data and combined settings**

`normalizeSettingsState(treatmentRaw, masterDataRaw)` combines `offLabelMode`, treatment plans, status changes, entry types and symptoms. Product databases remain in `normalizeProductState` and are not duplicated into settings.

- [ ] **Step 5: Export the public normalizer surface**

`normalizers/index.js` explicitly re-exports public functions. Internal primitive helpers remain imported from their concrete file and are not exposed unless tests or future modules require them.

- [ ] **Step 6: Run all normalizer tests**

```bash
npm run test:frontend -- --test-name-pattern="normaliz|product|treatment|settings"
```

Expected: all normalizer tests pass.

- [ ] **Step 7: Commit**

```bash
git add custom_components/animal_health/frontend/src/api/normalizers
git commit -m "feat: normalize products treatments and settings"
```

---

### Task 5: Implement the Domain-Oriented API Client

**Files:**
- Create: `custom_components/animal_health/frontend/src/api/commands.js`
- Create: `custom_components/animal_health/frontend/src/api/client.js`
- Create: `custom_components/animal_health/frontend/src/entry.js`
- Test: `tests/frontend/client.test.mjs`

**Interfaces:**
- Produces: `COMMANDS`, `AnimalHealthClient` and the side-effect-free Phase 2 export surface.

- [ ] **Step 1: Define the command registry**

```javascript
export const COMMANDS = Object.freeze({
  dashboard: "animal_health/dashboard",
  catalog: "animal_health/catalog",
  features: "animal_health/features",
  tagState: "animal_health/v080/state",
  animalDetail: "animal_health/animal_detail",
  attachmentsList: "animal_health/attachments/list",
  download: "animal_health/download",
  treatmentState: "animal_health/v0912/state",
  masterDataState: "animal_health/v0924/state",
  productState: "animal_health/v0928/state",
});
```

No other Phase 2 source file may contain these versioned literals.

- [ ] **Step 2: Implement the client constructor and request wrapper**

`new AnimalHealthClient(transport)` calls `assertTransport`. Private requests attach operation metadata and normalize all failures.

- [ ] **Step 3: Implement read methods**

```text
getDashboard()
getCatalog()
getFeatureState()
getAnimalDirectory()
getAnimalDetail(animalId, { eventLimit = 300, today = null } = {})
listAttachments({ animalId = null, eventId = null } = {})
getTreatmentState()
getMasterDataState()
getSettingsState()
getProductState()
requestDownload({ kind, resourceId = null })
```

`getFeatureState()` combines `features` and `tagState`. `getAnimalDirectory()` fetches dashboard, catalog, features and tag state directly in one `Promise.all` and normalizes once. `getSettingsState()` fetches treatment and master-data state together.

- [ ] **Step 4: Implement service and host pass-throughs**

```text
callService(service, payload, options)
download(resource)
notify(message, options)
```

These methods do not normalize domain data; they preserve the transport contract.

- [ ] **Step 5: Add the side-effect-free entry module**

`entry.js` re-exports client, commands, errors, adapters and public normalizers. It must not register a custom element or write to global state.

- [ ] **Step 6: Run client and platform tests**

```bash
npm run test:frontend
```

Expected: all Node tests pass.

- [ ] **Step 7: Commit**

```bash
git add custom_components/animal_health/frontend/src/api/commands.js custom_components/animal_health/frontend/src/api/client.js custom_components/animal_health/frontend/src/entry.js
git commit -m "feat: add the normalized Animal Health API client"
```

---

### Task 6: Add Permanent Module Validation and Documentation

**Files:**
- Create: `scripts/check_frontend_modules.mjs`
- Create: `custom_components/animal_health/frontend/src/README.md`
- Modify: `.github/workflows/validate.yml`
- Modify: `.github/workflows/android.yml`
- Test: `tests/test_frontend_phase2.py`

**Interfaces:**
- Consumes: all `frontend/src/**/*.js` files and package scripts.
- Produces: permanent syntax/import/boundary validation in both shared-frontend CI paths.

- [ ] **Step 1: Implement source validation**

The checker recursively finds source `.js` files, runs `node --check` on each, imports `frontend/src/entry.js`, verifies expected exports and confirms import does not create `customElements` registrations or new global properties.

- [ ] **Step 2: Document extension rules**

The source README states:

- host access only through adapters;
- versioned commands only through the registry;
- aliases only in normalizers;
- no UI activation before Phase 3;
- no direct legacy prototype access;
- exact local validation commands.

- [ ] **Step 3: Extend Validate workflow**

Add after the existing bundle checks:

```yaml
- name: Check modular frontend source
  run: npm run check:frontend
- name: Test modular frontend contracts
  run: npm run test:frontend
```

No `npm install` step is needed because Phase 2 has no dependency.

- [ ] **Step 4: Extend Android workflow**

Before the bundle check, run:

```yaml
- name: Check shared modular frontend source
  run: npm run check:frontend
- name: Test shared modular frontend contracts
  run: npm run test:frontend
```

This prevents an Android build from accepting a broken future shared module even though Phase 2 modules are not yet active.

- [ ] **Step 5: Run focused repository checks**

```bash
npm run check:frontend
npm run test:frontend
python -m pytest -q tests/test_frontend_phase2.py tests/test_architecture_consolidation.py tests/test_frontend_bundle.py
python scripts/architecture_inventory.py --root . --check
node scripts/build_frontend.mjs --check
```

Expected: all pass, and the dist bundle is unchanged.

- [ ] **Step 6: Commit**

```bash
git add scripts/check_frontend_modules.mjs custom_components/animal_health/frontend/src/README.md .github/workflows/validate.yml .github/workflows/android.yml
git commit -m "ci: validate the modular frontend data boundary"
```

---

### Task 7: Full Verification and Pull Request

**Files:**
- Review all Phase 2 changes.
- No production change unless a failing contract proves a defect.

**Interfaces:**
- Produces: a reviewable Phase 2 PR based on `consolidation/phase-0-1`.

- [ ] **Step 1: Verify source boundaries**

```bash
python -m pytest -q tests/test_frontend_phase2.py
python scripts/architecture_inventory.py --root . --check
```

Expected: no new legacy growth or forbidden source pattern.

- [ ] **Step 2: Verify the inactive-source guarantee**

```bash
node scripts/build_frontend.mjs --check
git diff --exit-code custom_components/animal_health/frontend/dist/animal-health-panel.js
```

Expected: the Phase 1 dist bundle remains exact and unchanged.

- [ ] **Step 3: Run complete validation**

```bash
python -m compileall custom_components tests scripts
npm run check:frontend
npm run test:frontend
python -m pytest -q
python tests/dashboard_frontend_smoke.py
python tests/ai_assist_smoke.py
python tests/v081_workflow_smoke.py
python tests/v084_features_smoke.py
python tests/feature_export_smoke.py
python tests/v080_feature_smoke.py
python tests/breed_catalog_smoke.py
python tests/download_stabilization_smoke.py
python tests/task_record_schema_smoke.py
python tests/task_overdue_smoke.py
python tests/task_resolution_smoke.py
python tests/catalog_selector_smoke.py
python tests/task_action_resolution_smoke.py
python tests/task_batch_atomicity_smoke.py
python tests/test_task_service_translations.py
gradle -p android :app:assembleDebug --stacktrace
```

Expected: every command exits 0.

- [ ] **Step 4: Review architectural scope**

Confirm:

- no existing UI or backend production file changed except CI metadata;
- no source module has host-specific access outside adapters;
- all raw aliases terminate inside normalizers;
- client methods use current commands only through `COMMANDS`;
- public DTOs are camelCase and serializable;
- no global or custom-element side effect occurs;
- no dependency or runtime bundle change was introduced.

- [ ] **Step 5: Open a draft pull request**

Base: `consolidation/phase-0-1`  
Head: `consolidation/phase-2-platform-api`

Keep it draft until Validate, Android Alpha, HACS validation and hassfest are green.
