# Phase 4 Read-only Animal Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Activate the modular overview, animal directory, and animal-detail routes while preserving every remaining Legacy route and write action.

**Architecture:** Pure selectors and HTML renderers consume Phase-2 canonical DTOs. A Phase-4 runtime composes the Phase-3 store/router/controller with the API client. A single installer in `legacy/compatibility-bridge.js` dispatches complete routes between the new runtime and the frozen Legacy implementation. `esbuild` bundles `runtime-entry.js` as an IIFE appended after the exact 99-part Legacy prelude.

**Tech Stack:** JavaScript ES modules, JSDoc, Node built-in test runner, esbuild 0.25.9, Python/pytest architecture tests, Home Assistant custom panel, Android WebView.

**Spec:** `docs/superpowers/specs/2026-09-04-phase-4-readonly-animals-design.md`

## Global Constraints

- Activate only `overview`, `animals`, and `animal-detail`.
- All write operations remain Legacy operations.
- Tasks, calendar, timeline, settings, dialogs, and every other route remain on the Legacy renderer.
- Do not modify any `animal-health-panel.part*.js` file.
- Do not add `part100.js`.
- Do not add a second compatibility bridge or prototype-patching file.
- New views consume canonical camelCase DTOs only.
- Do not recalculate overdue status; consume `occurrence.timing`.
- Date-only values must not pass through `new Date("YYYY-MM-DD")`.
- Home Assistant and Android continue to consume the same checked-in dist bundle.
- HACS installation requires no Node runtime.
- No new backend command, service, schema, ID, or data migration.

---

## File Map

### New production files

- `custom_components/animal_health/frontend/src/domain/animals/selectors.js` — pure filtering, grouping, and read-model selection.
- `custom_components/animal_health/frontend/src/ui/read-only/i18n.js` — complete German/English dictionary for the activated slice.
- `custom_components/animal_health/frontend/src/ui/read-only/format.js` — escaping and locale-safe date/number/label formatting.
- `custom_components/animal_health/frontend/src/ui/read-only/components.js` — shared shell, cards, task rows, event rows, and loading/error states.
- `custom_components/animal_health/frontend/src/ui/read-only/styles.js` — single static style block for the activated slice.
- `custom_components/animal_health/frontend/src/ui/views/overview.js` — overview route renderer.
- `custom_components/animal_health/frontend/src/ui/views/animals.js` — animal directory route renderer.
- `custom_components/animal_health/frontend/src/ui/views/animal-detail.js` — animal detail route renderer.
- `custom_components/animal_health/frontend/src/app/read-only-animals.js` — canonical store loading, route actions, and route rendering.
- `custom_components/animal_health/frontend/src/runtime-entry.js` — production activation entry bundled as an IIFE.

### Modified production files

- `custom_components/animal_health/frontend/src/legacy/compatibility-bridge.js` — only allowed Legacy prototype integration point.
- `custom_components/animal_health/frontend/src/entry.js` — side-effect-free exports for tests and future slices.
- `scripts/build_frontend.mjs` — exact Legacy prelude plus modern esbuild IIFE.
- `package.json` — pinned esbuild development dependency and build script.
- `.github/workflows/validate.yml` — install the pinned dependency and validate the active bundle.
- `.github/workflows/android.yml` — install the pinned dependency before shared bundle checks.
- `custom_components/animal_health/frontend/src/README.md` — Phase-4 activation status.

### New tests

- `tests/frontend/read-only-selectors.test.mjs`
- `tests/frontend/read-only-format.test.mjs`
- `tests/frontend/read-only-views.test.mjs`
- `tests/frontend/read-only-runtime.test.mjs`
- `tests/frontend/legacy-read-only-bridge.test.mjs`
- `tests/frontend/bundle-runtime.test.mjs`
- `tests/test_frontend_phase4.py`

### Modified tests

- `tests/test_frontend_bundle.py`
- `tests/test_frontend_phase2.py`
- `tests/test_frontend_phase3.py`
- `scripts/check_frontend_modules.mjs`

---

### Task 1: Pure animal selectors

**Files:**
- Create: `tests/frontend/read-only-selectors.test.mjs`
- Create: `custom_components/animal_health/frontend/src/domain/animals/selectors.js`

**Interfaces:**
- Produces: `selectAnimalById(state, animalId)`
- Produces: `selectGroupById(state, groupId)`
- Produces: `selectVisibleAnimals(state)`
- Produces: `selectGroupedAnimals(state)`
- Produces: `selectNextOccurrenceForAnimal(state, animalId)`
- Produces: `selectOpenOccurrencesForAnimal(state, animalId)`
- Produces: `selectUrgentOccurrences(state)`
- Produces: `selectRecentEvents(state, limit)`

- [ ] **Step 1: Write failing selector tests**

Use canonical DTOs only:

```javascript
const state = {
  animals: {
    items: [
      { id: "A-2", name: "Zora", species: "chicken", status: "active", isArchived: false, groupId: "G-1", tagIds: ["T-1"], breed: "Hybrid", color: "Braun" },
      { id: "A-1", name: "Alma", species: "chicken", status: "active", isArchived: false, groupId: null, tagIds: [], breed: null, color: null },
      { id: "A-3", name: "Archiv", species: "cat", status: "rehomed", isArchived: true, groupId: null, tagIds: [], breed: null, color: null },
    ],
    groups: [{ id: "G-1", name: "Legehennen" }],
    tags: [{ id: "T-1", name: "Senior" }],
    filters: { query: "", groupId: "all", tagId: "all", includeArchived: true },
  },
  tasks: {
    occurrences: [
      { id: "O-2", target: { animalIds: ["A-2"] }, status: "pending", timing: "today", dueDate: "2026-09-04", scheduledAt: "2026-09-04T08:00:00+02:00" },
      { id: "O-1", target: { animalIds: ["A-2"] }, status: "pending", timing: "overdue", dueDate: "2026-09-03", scheduledAt: "2026-09-03T08:00:00+02:00" },
    ],
  },
  timeline: { items: [{ id: "E-1", occurredAt: "2026-09-04T10:00:00+02:00" }] },
};
```

Assert:

- visible animals are sorted by archive state then locale-insensitive name;
- group, tag, archive, and query filters combine;
- query includes group name, tag name, technical ID, colour, and breed;
- grouped output includes an `ungrouped` bucket;
- urgent occurrences are ordered `overdue` before `today` and never inspect raw `is_overdue` aliases;
- the next animal occurrence uses due date/time ordering;
- recent events are descending and respect the limit.

- [ ] **Step 2: Verify RED**

Run:

```bash
node --test tests/frontend/read-only-selectors.test.mjs
```

Expected: `ERR_MODULE_NOT_FOUND` for `domain/animals/selectors.js`.

- [ ] **Step 3: Implement selectors**

Use no DOM, host, date-construction, or mutation. Required target helper:

```javascript
function targetsAnimal(occurrence, animalId) {
  return occurrence.target?.animalId === animalId ||
    occurrence.target?.animalIds?.includes(animalId) ||
    occurrence.target?.memberSnapshot?.includes(animalId);
}
```

Timing order:

```javascript
const TIMING_ORDER = Object.freeze({ overdue: 0, today: 1, upcoming: 2, closed: 3 });
```

- [ ] **Step 4: Run focused and full frontend tests**

```bash
node --test tests/frontend/read-only-selectors.test.mjs
npm run test:frontend
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/frontend/read-only-selectors.test.mjs custom_components/animal_health/frontend/src/domain/animals/selectors.js
git commit -m "feat: add canonical animal read selectors"
```

---

### Task 2: Read-only formatting, translations, styles, and components

**Files:**
- Create: `tests/frontend/read-only-format.test.mjs`
- Create: `custom_components/animal_health/frontend/src/ui/read-only/i18n.js`
- Create: `custom_components/animal_health/frontend/src/ui/read-only/format.js`
- Create: `custom_components/animal_health/frontend/src/ui/read-only/styles.js`
- Create: `custom_components/animal_health/frontend/src/ui/read-only/components.js`

**Interfaces:**
- Produces: `createTranslator(languageCode)`
- Produces: `escapeHtml(value)`, `escapeAttribute(value)`
- Produces: `formatDateOnly(value, locale)`, `formatDateTime(value, locale)`, `formatNumber(value, locale, digits)`
- Produces: `formatEnum(value, translate)`, `speciesLabel(animal, state, translate)`
- Produces shared component renderers used by all three routes.

- [ ] **Step 1: Write failing format and translation tests**

```javascript
test("date-only formatting never shifts the calendar date", () => {
  assert.equal(formatDateOnly("2026-03-29", "de-CH"), "29.03.2026");
  assert.equal(formatDateOnly("2026-03-29", "en-GB"), "29/03/2026");
});

test("all Phase-4 translation keys exist in German and English", () => {
  assert.deepEqual(Object.keys(MESSAGES.de).sort(), Object.keys(MESSAGES.en).sort());
  assert.equal(createTranslator("de")("animals"), "Tiere");
  assert.equal(createTranslator("en")("animals"), "Animals");
});

test("dynamic HTML is escaped", () => {
  assert.equal(escapeHtml('<b title="x">&</b>'), "&lt;b title=&quot;x&quot;&gt;&amp;&lt;/b&gt;");
});
```

Also test null/invalid values, number formatting, event/task labels, and species catalogue fallback.

- [ ] **Step 2: Verify RED**

Run: `node --test tests/frontend/read-only-format.test.mjs`

Expected: missing read-only UI modules.

- [ ] **Step 3: Implement dictionary and formatters**

The dictionary must contain every visible label used in the three views, including status, sex, task timing, event origins, groups, tags, retry, loading, and write-action labels.

`formatDateOnly` must parse with a regular expression and construct display text from numeric parts. It must not call `new Date(value)`.

- [ ] **Step 4: Implement one shared stylesheet and component functions**

Component exports:

```javascript
renderHeader(context)
renderHeading(title, actions)
renderQuickActions(animalId, translate)
renderStats(items)
renderAnimalTile(animal, context)
renderAnimalCard(animal, context)
renderOccurrenceRow(occurrence, context)
renderEventRow(event, context)
renderEmpty(message)
renderLoading(message)
renderError(error, retryAction, context)
renderShell(content, context)
```

Preserve established classes where useful: `heading`, `quick`, `stats`, `cols`, `card`, `row`, `animal`, `animalHead`, `animalMeta`, `hero`.

- [ ] **Step 5: Run tests**

```bash
node --test tests/frontend/read-only-format.test.mjs
npm run test:frontend
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add tests/frontend/read-only-format.test.mjs custom_components/animal_health/frontend/src/ui/read-only
git commit -m "feat: add shared read-only UI primitives"
```

---

### Task 3: Route renderers

**Files:**
- Create: `tests/frontend/read-only-views.test.mjs`
- Create: `custom_components/animal_health/frontend/src/ui/views/overview.js`
- Create: `custom_components/animal_health/frontend/src/ui/views/animals.js`
- Create: `custom_components/animal_health/frontend/src/ui/views/animal-detail.js`

**Interfaces:**
- Produces: `renderOverview(state, context)`
- Produces: `renderAnimals(state, context)`
- Produces: `renderAnimalDetail(state, context)`

- [ ] **Step 1: Write failing view tests using the Phase-2 fixture**

Normalize `tests/frontend/fixtures/phase2-snapshots-0.9.41.json` before rendering.

Required assertions:

```javascript
assert.match(overview, /data-view="animals"/);
assert.match(overview, /Tartar/);
assert.match(overview, /Meloxidyl geben/);
assert.match(overview, /Überfällig/);
assert.doesNotMatch(overview, /animal_id|scheduled_for|is_overdue/);

assert.match(animals, /data-action="animal-detail" data-id="AH-CHICKEN-1"/);
assert.match(detail, /Legehennen/);
assert.match(detail, /1[’']250|1250/);
assert.match(detail, /Aus Aufgabe/);
```

Also render English, empty data, filtered data, archived animals, dangerous HTML input, and a detail loading/error state.

- [ ] **Step 2: Verify RED**

Run: `node --test tests/frontend/read-only-views.test.mjs`

Expected: missing view modules.

- [ ] **Step 3: Implement overview renderer**

Render summary stats, quick actions, grouped animal tiles, filter toolbar, urgent occurrences, and recent events. Use only selectors and shared components.

- [ ] **Step 4: Implement animal list renderer**

Render heading, create action, search/filter toolbar, and animal cards from `selectVisibleAnimals(state)`.

- [ ] **Step 5: Implement animal detail renderer**

Use the current route `animalId`. Render directory identity while detail is loading. When loaded, render master data, open occurrences grouped by timing, and recent events. Do not add attachment preview behavior.

- [ ] **Step 6: Run tests**

```bash
node --test tests/frontend/read-only-views.test.mjs
npm run test:frontend
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add tests/frontend/read-only-views.test.mjs custom_components/animal_health/frontend/src/ui/views
git commit -m "feat: render migrated animal read routes"
```

---

### Task 4: Read-only slice runtime

**Files:**
- Create: `tests/frontend/read-only-runtime.test.mjs`
- Create: `custom_components/animal_health/frontend/src/app/read-only-animals.js`
- Modify: `custom_components/animal_health/frontend/src/entry.js`

**Interfaces:**
- Produces: `MIGRATED_READ_ROUTES`
- Produces: `createReadOnlyAnimalsRuntime({panel, legacy, integrationVersion})`
- Produces: `renderReadOnlyAnimalsRoute(state, context)`

- [ ] **Step 1: Write failing runtime tests**

Use a recording transport/client and a fake panel. Assert:

- first `load()` calls `getAnimalDirectory()` once;
- repeated non-forced load reuses ready data;
- refresh performs a new read while retaining existing data;
- `openAnimal("A-1")` navigates to `animal-detail` and loads detail;
- a slower previous detail response is discarded;
- group, tag, query, and archive filter actions update canonical `animals.filters`;
- a migrated navigation uses the Phase-3 router;
- a Legacy navigation calls `legacy.load` when `panel.d` is absent;
- a write action calls the original Legacy handler only after Legacy data is available.

- [ ] **Step 2: Verify RED**

Run: `node --test tests/frontend/read-only-runtime.test.mjs`

Expected: missing `app/read-only-animals.js`.

- [ ] **Step 3: Implement canonical loading**

Directory application:

```javascript
function applyDirectory(state, directory) {
  return {
    ...state,
    animals: {
      ...state.animals,
      status: "ready",
      items: directory.animals,
      groups: directory.groups,
      tags: directory.tags,
      catalog: directory.catalog,
      directoryMeta: {
        version: directory.version,
        timeZone: directory.timeZone,
        today: directory.today,
        summary: directory.summary,
        exports: directory.exports,
      },
      error: null,
    },
    tasks: {
      ...state.tasks,
      status: "ready",
      definitions: directory.tasks,
      occurrences: directory.occurrences,
      error: null,
    },
    timeline: {
      ...state.timeline,
      status: "ready",
      items: directory.events,
      error: null,
    },
  };
}
```

Merge group/tag fields from the directory animal into the loaded detail animal.

- [ ] **Step 4: Register runtime actions**

Modern actions:

```text
read.refresh
animal-detail
home-group-toggle
home-group-select
home-tag-toggle
home-tag-select
home-search-toggle
home-filter-reset
animals.filter
animals.toggle-archived
```

The runtime must expose `handlesEvent(event)` so the bridge can distinguish modern navigation/filter events from untouched Legacy actions.

- [ ] **Step 5: Implement route rendering**

`render()` derives language from `panel.h?.language`, narrow state from the panel attribute, and version from the injected integration version. It writes one complete `<style>…</style>${shell}` string.

- [ ] **Step 6: Run tests**

```bash
node --test tests/frontend/read-only-runtime.test.mjs
npm run check:frontend
npm run test:frontend
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add tests/frontend/read-only-runtime.test.mjs custom_components/animal_health/frontend/src/app/read-only-animals.js custom_components/animal_health/frontend/src/entry.js
git commit -m "feat: add canonical animal read runtime"
```

---

### Task 5: Install the single Legacy route bridge

**Files:**
- Create: `tests/frontend/legacy-read-only-bridge.test.mjs`
- Modify: `custom_components/animal_health/frontend/src/legacy/compatibility-bridge.js`
- Create: `custom_components/animal_health/frontend/src/runtime-entry.js`

**Interfaces:**
- Produces: `installLegacyReadOnlyAnimalsSlice(LegacyPanelClass, options)`
- Activates the slice exactly once when `runtime-entry.js` is bundled after the Legacy prelude.

- [ ] **Step 1: Write failing integration tests**

Build a fake Legacy panel prototype with counters for `render`, `load`, `loadDetail`, `handleClick`, and `handleInput`.

Assert:

- installation is idempotent;
- migrated route rendering calls the new runtime and not Legacy render;
- non-migrated route rendering calls Legacy render;
- any open Legacy modal calls Legacy render even on a migrated route;
- migrated `load` and `loadDetail` use the new runtime;
- non-migrated loading remains Legacy;
- modern filter/navigation events go to the runtime;
- unknown/write actions go to Legacy;
- write actions await Legacy data loading when `panel.d` is absent;
- no other file accesses `LegacyPanelClass.prototype`.

- [ ] **Step 2: Verify RED**

Run: `node --test tests/frontend/legacy-read-only-bridge.test.mjs`

Expected: `installLegacyReadOnlyAnimalsSlice` is not exported.

- [ ] **Step 3: Implement the installer**

Required stored methods:

```javascript
const legacy = Object.freeze({
  render: prototype.render,
  load: prototype.load,
  loadDetail: prototype.loadDetail,
  handleClick: prototype.handleClick,
  handleInput: prototype.handleInput,
});
```

Use a module-scoped `WeakSet` for installed classes and a `WeakMap` for panel runtimes. Dispatch by complete route and modal state; do not place view HTML in the bridge.

- [ ] **Step 4: Implement production activation entry**

```javascript
import { installLegacyReadOnlyAnimalsSlice } from "./legacy/compatibility-bridge.js";

installLegacyReadOnlyAnimalsSlice(AnimalHealthPanel, {
  integrationVersion: typeof V === "string" ? V : "unknown",
});
```

`runtime-entry.js` is intentionally side-effectful and is not exported from `entry.js`.

- [ ] **Step 5: Run tests**

```bash
node --test tests/frontend/legacy-read-only-bridge.test.mjs
npm run check:frontend
npm run test:frontend
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add tests/frontend/legacy-read-only-bridge.test.mjs custom_components/animal_health/frontend/src/legacy/compatibility-bridge.js custom_components/animal_health/frontend/src/runtime-entry.js
git commit -m "feat: activate animal routes through one Legacy bridge"
```

---

### Task 6: Build active modern IIFE after the frozen Legacy prelude

**Files:**
- Create: `tests/frontend/bundle-runtime.test.mjs`
- Modify: `package.json`
- Modify: `scripts/build_frontend.mjs`
- Modify generated: `custom_components/animal_health/frontend/dist/animal-health-panel.js`
- Modify: `tests/test_frontend_bundle.py`
- Modify: `tests/test_frontend_phase2.py`
- Modify: `tests/test_frontend_phase3.py`

**Interfaces:**
- `buildLegacyPrelude()` returns the exact concatenation of the manifest files.
- `buildModernRuntime()` returns the esbuild IIFE text.
- `buildBundle()` returns `${legacyPrelude}${MODERN_SEPARATOR}${modernRuntime}`.

- [ ] **Step 1: Write failing bundle tests**

```javascript
test("active bundle preserves exact Legacy prefix and appends one IIFE", async () => {
  const legacy = await buildLegacyPrelude();
  const modern = await buildModernRuntime();
  const bundle = await buildBundle();
  assert.equal(bundle.slice(0, legacy.length), legacy);
  assert.match(bundle.slice(legacy.length), /ANIMAL_HEALTH_MODERN_RUNTIME/);
  assert.match(modern, /installLegacyReadOnlyAnimalsSlice/);
  assert.doesNotMatch(modern, /^\s*import\s/m);
  assert.doesNotMatch(modern, /^\s*export\s/m);
});
```

Python tests must stop asserting total bundle equality with the Legacy prelude and instead assert exact prefix equality plus the runtime marker.

- [ ] **Step 2: Verify RED**

Run:

```bash
node --test tests/frontend/bundle-runtime.test.mjs
python -m pytest -q tests/test_frontend_bundle.py tests/test_frontend_phase2.py tests/test_frontend_phase3.py
```

Expected: failures because the current builder emits only the Legacy prelude.

- [ ] **Step 3: Pin esbuild and add build script**

`package.json`:

```json
{
  "scripts": {
    "build:frontend": "node scripts/build_frontend.mjs",
    "check:frontend": "node scripts/check_frontend_modules.mjs",
    "test:frontend": "node --test tests/frontend/*.test.mjs"
  },
  "devDependencies": {
    "esbuild": "0.25.9"
  }
}
```

- [ ] **Step 4: Extend the builder**

Use:

```javascript
import { build } from "esbuild";

const RUNTIME_ENTRY = path.join(FRONTEND, "src", "runtime-entry.js");
const MODERN_SEPARATOR = "\n/* ANIMAL_HEALTH_MODERN_RUNTIME */\n";

export async function buildModernRuntime() {
  const result = await build({
    entryPoints: [RUNTIME_ENTRY],
    bundle: true,
    write: false,
    format: "iife",
    target: ["es2022"],
    legalComments: "none",
    minify: false,
    sourcemap: false,
  });
  return result.outputFiles[0].text;
}
```

- [ ] **Step 5: Generate and syntax-check dist**

```bash
npm install --no-package-lock
npm run build:frontend
node scripts/build_frontend.mjs --check
node --check custom_components/animal_health/frontend/dist/animal-health-panel.js
```

Expected: all exit 0.

- [ ] **Step 6: Run bundle and historical contract tests**

```bash
node --test tests/frontend/bundle-runtime.test.mjs
python -m pytest -q tests/test_frontend_bundle.py tests/test_frontend_phase2.py tests/test_frontend_phase3.py
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add package.json scripts/build_frontend.mjs custom_components/animal_health/frontend/dist/animal-health-panel.js tests/frontend/bundle-runtime.test.mjs tests/test_frontend_bundle.py tests/test_frontend_phase2.py tests/test_frontend_phase3.py
git commit -m "build: append the active modular runtime"
```

---

### Task 7: Permanent architecture and CI enforcement

**Files:**
- Create: `tests/test_frontend_phase4.py`
- Modify: `scripts/check_frontend_modules.mjs`
- Modify: `.github/workflows/validate.yml`
- Modify: `.github/workflows/android.yml`
- Modify: `custom_components/animal_health/frontend/src/README.md`

**Interfaces:**
- Produces permanent checks for active-route boundaries and shared bundle reproducibility.

- [ ] **Step 1: Write failing Phase-4 architecture tests**

Assert:

- every planned Phase-4 file exists;
- only `legacy/compatibility-bridge.js` contains `LegacyPanelClass.prototype`;
- only `runtime-entry.js` contains `AnimalHealthPanel` as an activation identifier;
- views contain no snake_case backend aliases;
- views contain no `hass`, bridge, `window`, `globalThis`, `localStorage`, or service calls;
- runtime marks exactly the three approved routes migrated;
- build marker exists after the exact 99-part prefix;
- no new fragment exists;
- the read-only runtime contains no `callService` use;
- README declares the three active routes and Legacy writes.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest -q tests/test_frontend_phase4.py`

Expected: failures until checker, workflows, and README are updated.

- [ ] **Step 3: Extend the module checker**

Add required exports:

```text
createReadOnlyAnimalsRuntime
installLegacyReadOnlyAnimalsSlice
renderReadOnlyAnimalsRoute
selectVisibleAnimals
selectUrgentOccurrences
```

Continue importing only `entry.js`, never `runtime-entry.js`.

- [ ] **Step 4: Update CI dependency installation**

In both Validate and Android Alpha, before any build command:

```yaml
- name: Install frontend build dependency
  run: npm install --no-package-lock
```

Then preserve module checks, tests, bundle check, Python suite, smoke tests, and Android build.

- [ ] **Step 5: Update source README**

Document active routes, remaining Legacy routes, Legacy write delegation, and exact-prefix bundle rule.

- [ ] **Step 6: Run focused tests**

```bash
python -m pytest -q tests/test_frontend_phase4.py
npm run check:frontend
npm run test:frontend
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add tests/test_frontend_phase4.py scripts/check_frontend_modules.mjs .github/workflows/validate.yml .github/workflows/android.yml custom_components/animal_health/frontend/src/README.md
git commit -m "ci: enforce the first active modular routes"
```

---

### Task 8: Final integration verification and stacked pull request

**Files:**
- Review all changed files.
- No behavior change unless a failing regression test demonstrates a defect.

- [ ] **Step 1: Run complete verification**

```bash
python -m compileall custom_components tests scripts
python scripts/architecture_inventory.py --root . --check
npm install --no-package-lock
npm run check:frontend
npm run test:frontend
node scripts/build_frontend.mjs --check
node --check custom_components/animal_health/frontend/dist/animal-health-panel.js
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
```

Expected: every command exits 0.

- [ ] **Step 2: Confirm frozen files are unchanged**

Compare every `animal-health-panel.part*.js` blob and `legacy/manifest.json` against `441d507f774a6f26f899eb029db946d17815eb0b`. Expected: no changes.

- [ ] **Step 3: Request code review**

Review specifically:

- complete route dispatch rather than partial method migration;
- no write call from the modern runtime;
- no stale response leakage;
- correct Legacy modal fallback;
- exact Legacy prefix in the active bundle;
- escaping and date-only handling;
- Android compatibility classes and shared bundle use.

- [ ] **Step 4: Fix Critical and Important review findings with failing tests first**

Run the relevant focused test before and after each fix.

- [ ] **Step 5: Open stacked draft PR**

Base: `consolidation/phase-3-app-shell`  
Head: `consolidation/phase-4-readonly-animals`

The PR body must state that Phase 3 must merge first and list the three active routes plus the preserved Legacy write path.

- [ ] **Step 6: Require successful PR workflows**

Required:

```text
Validate
Android Alpha
HACS Validation
hassfest
```
