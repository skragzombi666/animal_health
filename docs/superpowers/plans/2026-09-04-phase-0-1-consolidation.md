# Phase 0–1 Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze Animal Health 0.9.41 as a machine-readable legacy reference and replace runtime frontend concatenation with one deterministic, byte-identical bundle consumed by Home Assistant and Android.

**Architecture:** The existing 99 fragments remain temporarily in place as immutable reference inputs listed by an explicit manifest. A Python inventory tool records and guards the legacy architecture; a dependency-free Node build tool creates the checked-in dist bundle. Home Assistant reads only that bundle, while Android copies the same bundle and brand asset into generated app assets.

**Tech Stack:** Python 3.13, pytest, Node.js standard library, Kotlin Gradle DSL, GitHub Actions, Home Assistant custom panel, Android WebView

**Spec:** `docs/architecture/2026-09-04-consolidation-target-architecture.md`

## Global Constraints

- Reference behavior is Animal Health 0.9.41 at commit `4df86bc382b99db3a4276cb451edfacc0eaf502d`.
- The 99 fragments are temporary legacy evidence, not the target architecture.
- No `animal-health-panel.part100.js` or other new numbered fragment may be added.
- No existing user flow, API, service, database schema, ID, or persisted record may change.
- Home Assistant and Android must consume byte-identical `custom_components/animal_health/frontend/dist/animal-health-panel.js`.
- HACS installation must not require Node.js; the dist bundle stays checked in.
- The first build step uses no third-party JavaScript dependency.
- Existing frontend fragments remain at their current paths during Phase 0–1.
- Existing runtime patches are inventoried and frozen; they are not removed in this phase.
- Every production-code change follows red-green-refactor.

---

## File Map

### New files

- `docs/architecture/inventory/legacy-baseline.json` — generated immutable architecture reference and guardrail allowance.
- `docs/architecture/inventory/README.md` — documents the inventory fields and regeneration policy.
- `custom_components/animal_health/frontend/legacy/manifest.json` — explicit ordered list of all 99 legacy inputs.
- `custom_components/animal_health/frontend/dist/animal-health-panel.js` — generated runtime bundle used by both hosts.
- `scripts/architecture_inventory.py` — deterministic inventory generator and guardrail checker.
- `scripts/build_frontend.mjs` — deterministic dependency-free bundle builder and checker.
- `tests/test_architecture_consolidation.py` — Phase 0 inventory and anti-growth tests.
- `tests/test_frontend_bundle.py` — Phase 1 manifest, bundle and host-consumption tests.
- `.github/workflows/phase01-generate.yml` — temporary branch-only workflow that materializes generated files; removed before completion.

### Modified files

- `custom_components/animal_health/panel.py` — read the dist bundle instead of globbing and concatenating fragments.
- `android/app/build.gradle.kts` — copy the checked-in bundle and brand asset; remove fragment concatenation.
- `.github/workflows/validate.yml` — check inventory guardrails, bundle reproducibility and dist syntax.
- `.github/workflows/android.yml` — run for shared-frontend changes and verify the bundle before Gradle.
- `tests/test_android_alpha.py` — assert Android consumes the shared dist bundle.
- `tests/test_branding_assets.py` — inspect the dist bundle rather than runtime-concatenating fragments.
- `tests/test_v0941_release.py` — assert the 99-part reference through the manifest and remove the obsolete Android count contract.
- `docs/android-alpha3-regression.md` — document the new single-bundle invariant.

---

### Task 1: Lock the Phase 0 and Phase 1 Contracts with Failing Tests

**Files:**
- Create: `tests/test_architecture_consolidation.py`
- Create: `tests/test_frontend_bundle.py`

**Interfaces:**
- Consumes: existing repository tree and current 0.9.41 files.
- Produces: executable contracts for `collect_inventory(root)`, `check_guardrails(root, baseline)`, `legacy/manifest.json`, `build_frontend.mjs`, the dist bundle, `panel.py`, and Android Gradle wiring.

- [ ] **Step 1: Add the failing architecture tests**

```python
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_SCRIPT = ROOT / "scripts" / "architecture_inventory.py"
BASELINE = ROOT / "docs" / "architecture" / "inventory" / "legacy-baseline.json"


def _load_inventory_module():
    spec = importlib.util.spec_from_file_location("architecture_inventory", INVENTORY_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_phase0_inventory_is_machine_readable_and_complete() -> None:
    assert INVENTORY_SCRIPT.is_file()
    assert BASELINE.is_file()
    module = _load_inventory_module()
    inventory = module.collect_inventory(ROOT)
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert inventory["reference_version"] == "0.9.41"
    assert inventory["frontend"]["part_count"] == 99
    assert inventory["frontend"]["parts"][0]["path"].endswith("part01.js")
    assert inventory["frontend"]["parts"][-1]["path"].endswith("part99.js")
    assert inventory["frontend"]["prototype_mutations"]
    assert inventory["frontend"]["actions"]
    assert inventory["frontend"]["dialogs"]
    assert inventory["backend"]["patch_registration_order"]
    assert inventory["backend"]["runtime_method_assignments"]
    assert baseline == inventory


def test_phase0_guardrails_accept_only_reductions_from_the_baseline() -> None:
    result = subprocess.run(
        [sys.executable, str(INVENTORY_SCRIPT), "--check", "--root", str(ROOT)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
```

- [ ] **Step 2: Add the failing bundle tests**

```python
from __future__ import annotations

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "animal_health" / "frontend"
LEGACY_MANIFEST = FRONTEND / "legacy" / "manifest.json"
DIST = FRONTEND / "dist" / "animal-health-panel.js"
BUILD_SCRIPT = ROOT / "scripts" / "build_frontend.mjs"


def test_phase1_manifest_names_exactly_the_frozen_99_parts() -> None:
    manifest = json.loads(LEGACY_MANIFEST.read_text(encoding="utf-8"))
    expected = [f"../animal-health-panel.part{index:02d}.js" for index in range(1, 100)]
    assert manifest == {
        "schema_version": 1,
        "reference_version": "0.9.41",
        "parts": expected,
    }


def test_phase1_dist_bundle_is_reproducible_and_valid_javascript() -> None:
    check = subprocess.run(
        ["node", str(BUILD_SCRIPT), "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert check.returncode == 0, check.stderr or check.stdout
    subprocess.run(["node", "--check", str(DIST)], check=True)


def test_phase1_dist_is_exact_legacy_concatenation() -> None:
    manifest = json.loads(LEGACY_MANIFEST.read_text(encoding="utf-8"))
    expected = "".join(
        (LEGACY_MANIFEST.parent / relative).resolve().read_text(encoding="utf-8")
        for relative in manifest["parts"]
    )
    assert DIST.read_text(encoding="utf-8") == expected


def test_phase1_home_assistant_and_android_reference_only_the_dist_bundle() -> None:
    panel = (ROOT / "custom_components" / "animal_health" / "panel.py").read_text(encoding="utf-8")
    gradle = (ROOT / "android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    assert '"dist" / "animal-health-panel.js"' in panel
    assert 'glob("animal-health-panel.part*.js")' not in panel
    assert 'resolve("dist/animal-health-panel.js")' in gradle
    assert 'animal-health-panel.part*.js' not in gradle
    assert 'ordered.size == 99' not in gradle
```

- [ ] **Step 3: Commit the red tests**

```bash
git add tests/test_architecture_consolidation.py tests/test_frontend_bundle.py
git commit -m "test: define phase 0 and phase 1 consolidation contracts"
```

- [ ] **Step 4: Verify the tests fail for the intended missing artifacts**

Run:

```bash
python -m pytest -q tests/test_architecture_consolidation.py tests/test_frontend_bundle.py
```

Expected: failures identify the missing inventory script, baseline, manifest, build script, dist bundle, and old host wiring. No failure may be caused by a syntax error in the tests.

---

### Task 2: Implement the Machine-Readable Inventory and Guardrails

**Files:**
- Create: `scripts/architecture_inventory.py`
- Create generated: `docs/architecture/inventory/legacy-baseline.json`
- Create: `docs/architecture/inventory/README.md`
- Create temporary: `.github/workflows/phase01-generate.yml`
- Test: `tests/test_architecture_consolidation.py`

**Interfaces:**
- Produces: `collect_inventory(root: Path) -> dict[str, object]`, `write_inventory(root: Path, destination: Path) -> None`, and `check_guardrails(root: Path, baseline: dict[str, object]) -> list[str]`.
- Guardrail rule: current legacy part paths and digests must exactly match the baseline; all risky-pattern occurrence sets must be subsets of the baseline.

- [ ] **Step 1: Implement deterministic inventory collection**

The script must:

1. sort every file path relative to repository root;
2. record each legacy fragment path, byte length, SHA-256 and Git-style blob SHA-1;
3. record frontend prototype mutations as stable fingerprints of `path`, normalized statement and owning prototype alias;
4. record `data-action`, action comparisons, `data-view`, assigned views, dialog types, WebSocket command strings, service names, translation keys and `<style` count;
5. record backend `apply_*_patches` functions, their call order in `__init__.py`, direct runtime method assignments and monkey-patch targets;
6. emit stable sorted JSON with `indent=2` and a trailing newline;
7. exclude `frontend/dist`, generated inventory files and `.git`.

Required CLI:

```bash
python scripts/architecture_inventory.py --root . --write
python scripts/architecture_inventory.py --root . --check
python scripts/architecture_inventory.py --root . --stdout
```

`--check` loads `docs/architecture/inventory/legacy-baseline.json`, recomputes current inventory and reports each added or changed legacy fingerprint. It permits removals from risky-pattern collections but not additions. Legacy fragment paths and digests remain exact until their later dedicated relocation phase.

- [ ] **Step 2: Add the temporary generator workflow**

```yaml
name: Phase 0-1 Generated Artifacts

on:
  push:
    branches:
      - "consolidation/phase-0-1"
    paths:
      - "scripts/architecture_inventory.py"
      - "scripts/build_frontend.mjs"
      - "custom_components/animal_health/frontend/legacy/manifest.json"
      - ".github/workflows/phase01-generate.yml"

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          ref: "consolidation/phase-0-1"
      - uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - name: Generate architecture baseline
        run: python scripts/architecture_inventory.py --root . --write
      - name: Generate frontend bundle when the builder exists
        run: |
          if test -f scripts/build_frontend.mjs; then
            node scripts/build_frontend.mjs
          fi
      - name: Commit generated artifacts
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add docs/architecture/inventory/legacy-baseline.json custom_components/animal_health/frontend/dist/animal-health-panel.js
          if git diff --cached --quiet; then
            exit 0
          fi
          git commit -m "chore: refresh phase 0-1 generated artifacts"
          git push origin HEAD:"consolidation/phase-0-1"
```

The `git add` command must tolerate the dist file not existing during the inventory-only commit by constructing its path list conditionally.

- [ ] **Step 3: Add inventory documentation**

Document that the baseline is generated once from 0.9.41, is not manually edited, and may only shrink through dedicated migrations. Include the exact write and check commands.

- [ ] **Step 4: Commit implementation and trigger generation**

```bash
git add scripts/architecture_inventory.py docs/architecture/inventory/README.md .github/workflows/phase01-generate.yml
git commit -m "feat: inventory and freeze the legacy architecture"
```

- [ ] **Step 5: Verify the generator creates and commits the baseline**

Expected generated file:

```text
docs/architecture/inventory/legacy-baseline.json
```

Run after the generated commit:

```bash
python -m pytest -q tests/test_architecture_consolidation.py
python scripts/architecture_inventory.py --root . --check
```

Expected: PASS and exit code 0.

---

### Task 3: Implement the Explicit Legacy Manifest and Deterministic Bundle

**Files:**
- Create: `custom_components/animal_health/frontend/legacy/manifest.json`
- Create: `scripts/build_frontend.mjs`
- Create generated: `custom_components/animal_health/frontend/dist/animal-health-panel.js`
- Test: `tests/test_frontend_bundle.py`

**Interfaces:**
- Produces: `loadManifest()`, `buildBundle()` and `writeOrCheckBundle({ check })` within the Node module.
- Bundle semantics: UTF-8 contents of manifest entries joined with an empty separator and no added newline.

- [ ] **Step 1: Add the exact manifest**

```json
{
  "schema_version": 1,
  "reference_version": "0.9.41",
  "parts": [
    "../animal-health-panel.part01.js",
    "../animal-health-panel.part02.js"
  ]
}
```

Continue the explicit list through `part99.js`. Do not generate the path list at runtime; reviewability of the order is the purpose of the manifest.

- [ ] **Step 2: Implement the dependency-free Node builder**

```javascript
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const FRONTEND = path.join(ROOT, "custom_components", "animal_health", "frontend");
const MANIFEST = path.join(FRONTEND, "legacy", "manifest.json");
const OUTPUT = path.join(FRONTEND, "dist", "animal-health-panel.js");

export async function loadManifest() {
  const manifest = JSON.parse(await readFile(MANIFEST, "utf8"));
  if (manifest.schema_version !== 1) throw new Error("Unsupported legacy manifest schema");
  if (manifest.reference_version !== "0.9.41") throw new Error("Unexpected legacy reference version");
  if (!Array.isArray(manifest.parts) || manifest.parts.length !== 99) {
    throw new Error(`Expected 99 frozen legacy parts, found ${manifest.parts?.length ?? 0}`);
  }
  if (new Set(manifest.parts).size !== manifest.parts.length) throw new Error("Duplicate legacy part");
  return manifest;
}

export async function buildBundle() {
  const manifest = await loadManifest();
  return (await Promise.all(manifest.parts.map(relative => readFile(path.resolve(path.dirname(MANIFEST), relative), "utf8")))).join("");
}
```

`--check` must compare bytes and fail with a direct regeneration command when stale. Normal mode creates the output directory and writes the bundle.

- [ ] **Step 3: Commit builder and manifest**

```bash
git add custom_components/animal_health/frontend/legacy/manifest.json scripts/build_frontend.mjs
git commit -m "feat: build the frozen frontend deterministically"
```

- [ ] **Step 4: Verify the generator commits the dist bundle**

Run after the generated commit:

```bash
node scripts/build_frontend.mjs --check
node --check custom_components/animal_health/frontend/dist/animal-health-panel.js
python -m pytest -q tests/test_frontend_bundle.py::test_phase1_manifest_names_exactly_the_frozen_99_parts tests/test_frontend_bundle.py::test_phase1_dist_bundle_is_reproducible_and_valid_javascript tests/test_frontend_bundle.py::test_phase1_dist_is_exact_legacy_concatenation
```

Expected: PASS.

---

### Task 4: Switch Home Assistant to the Dist Bundle

**Files:**
- Modify: `custom_components/animal_health/panel.py`
- Modify: `tests/test_branding_assets.py`
- Modify: `tests/test_v0941_release.py`
- Test: `tests/test_frontend_bundle.py`

**Interfaces:**
- Consumes: `frontend/dist/animal-health-panel.js`.
- Preserves: `PANEL_MODULE_URL`, version replacement, cache headers and `FRONTEND_REVISION` behavior.

- [ ] **Step 1: Verify the host-consumption test remains red**

Run:

```bash
python -m pytest -q tests/test_frontend_bundle.py::test_phase1_home_assistant_and_android_reference_only_the_dist_bundle
```

Expected: FAIL because `panel.py` still contains the fragment glob.

- [ ] **Step 2: Replace runtime concatenation in `panel.py`**

Replace `_FRONTEND_PARTS` with:

```python
_FRONTEND_BUNDLE_PATH = _FRONTEND_DIR / "dist" / "animal-health-panel.js"
```

Implement:

```python
def _frontend_source() -> str:
    if not _FRONTEND_BUNDLE_PATH.is_file():
        raise RuntimeError("Animal Health frontend bundle is missing")
    source = _FRONTEND_BUNDLE_PATH.read_text(encoding="utf-8")
    version = _integration_version()
    return re.sub(
        r'const V="[^"]+",D="animal_health";',
        f'const V="{version}",D="animal_health";',
        source,
        count=1,
    )
```

Do not change endpoint URLs or caching behavior.

- [ ] **Step 3: Update tests that assemble the full frontend**

In `tests/test_branding_assets.py`, read `frontend/dist/animal-health-panel.js`.

In `tests/test_v0941_release.py`, assert:

- the manifest contains 99 entries ending in part99;
- the dist bundle contains the 0.9.41 version marker;
- the Android app version remains alpha.7;
- obsolete `ordered.size == 99` assertions are removed.

- [ ] **Step 4: Run focused tests**

```bash
python -m pytest -q tests/test_frontend_bundle.py tests/test_branding_assets.py tests/test_v089_frontend_cache.py tests/test_v0941_release.py
```

Expected: the Home Assistant half passes; Android assertions may remain red until Task 5.

- [ ] **Step 5: Commit**

```bash
git add custom_components/animal_health/panel.py tests/test_branding_assets.py tests/test_v0941_release.py
git commit -m "refactor: serve the checked-in frontend bundle"
```

---

### Task 5: Switch Android to the Same Dist Bundle

**Files:**
- Modify: `android/app/build.gradle.kts`
- Modify: `.github/workflows/android.yml`
- Modify: `tests/test_android_alpha.py`
- Test: `tests/test_frontend_bundle.py`

**Interfaces:**
- Consumes: the exact dist bundle and existing `animal-health-brand.svg`.
- Produces: generated Android assets named `animal-health-panel.js` and `animal-health-brand.svg` without reading any numbered fragment.

- [ ] **Step 1: Verify Android assertions are red**

```bash
python -m pytest -q tests/test_android_alpha.py::test_android_alpha_uses_shared_frontend_and_full_local_adapter tests/test_frontend_bundle.py::test_phase1_home_assistant_and_android_reference_only_the_dist_bundle
```

Expected: FAIL on the old `bundleSharedFrontend` task and fragment glob.

- [ ] **Step 2: Replace Android fragment concatenation**

Use explicit input files:

```kotlin
val sharedFrontendRoot = file("../../custom_components/animal_health/frontend")
val sharedFrontendBundle = sharedFrontendRoot.resolve("dist/animal-health-panel.js")
val sharedFrontendBrand = sharedFrontendRoot.resolve("animal-health-brand.svg")
val generatedSharedUiAssets = layout.buildDirectory.dir("generated/animalHealthSharedUi")

val prepareSharedFrontendAssets by tasks.registering {
    inputs.files(sharedFrontendBundle, sharedFrontendBrand)
    outputs.files(
        generatedSharedUiAssets.map { it.file("animal-health-panel.js") },
        generatedSharedUiAssets.map { it.file("animal-health-brand.svg") },
    )
    doLast {
        require(sharedFrontendBundle.isFile) { "Missing shared frontend bundle: $sharedFrontendBundle" }
        require(sharedFrontendBrand.isFile) { "Missing shared frontend brand: $sharedFrontendBrand" }
        val target = generatedSharedUiAssets.get().asFile
        target.mkdirs()
        sharedFrontendBundle.copyTo(target.resolve("animal-health-panel.js"), overwrite = true)
        sharedFrontendBrand.copyTo(target.resolve("animal-health-brand.svg"), overwrite = true)
    }
}
```

Remove the frontend root from static asset directories. Keep catalogs and generated assets. Change `preBuild` to depend on `prepareSharedFrontendAssets` and `prepareAlphaSigning`.

- [ ] **Step 3: Expand Android workflow paths and add bundle verification**

Add pull-request paths:

```yaml
- "custom_components/animal_health/frontend/**"
- "scripts/build_frontend.mjs"
```

Add before Gradle:

```yaml
- name: Verify shared frontend bundle
  run: node scripts/build_frontend.mjs --check
```

Retain the independent Android alpha artifact build.

- [ ] **Step 4: Update Android tests**

Read the full frontend from `frontend/dist/animal-health-panel.js`. Assert:

```text
sharedFrontendBundle
resolve("dist/animal-health-panel.js")
prepareSharedFrontendAssets
copyTo(target.resolve("animal-health-panel.js")
```

Assert the old glob, `bundleSharedFrontend`, `ordered.size == 99`, and `ordered.joinToString` are absent.

- [ ] **Step 5: Run focused verification**

```bash
python -m pytest -q tests/test_android_alpha.py tests/test_frontend_bundle.py
gradle -p android :app:assembleDebug --stacktrace
```

Expected: PASS and an APK under `android/app/build/outputs/apk/debug/`.

- [ ] **Step 6: Commit**

```bash
git add android/app/build.gradle.kts .github/workflows/android.yml tests/test_android_alpha.py
git commit -m "refactor: package one shared frontend bundle on Android"
```

---

### Task 6: Make CI Enforce Reproducibility and Architecture Freeze

**Files:**
- Modify: `.github/workflows/validate.yml`
- Modify: `docs/android-alpha3-regression.md`
- Delete: `.github/workflows/phase01-generate.yml`
- Test: all Phase 0–1 tests

**Interfaces:**
- Consumes: inventory checker and frontend builder.
- Produces: permanent CI gates without an auto-commit workflow.

- [ ] **Step 1: Update Validate workflow**

Add permanent steps:

```yaml
- name: Verify architecture guardrails
  run: python scripts/architecture_inventory.py --root . --check
- name: Verify generated frontend bundle
  run: node scripts/build_frontend.mjs --check
- name: Validate bundled frontend syntax
  run: node --check custom_components/animal_health/frontend/dist/animal-health-panel.js
```

Replace the previous `cat ...part*.js` syntax step. Existing pytest and smoke-test steps remain.

- [ ] **Step 2: Update the Android regression document**

State that the historical 99 fragments are build inputs only, their order comes from `legacy/manifest.json`, the checked-in dist bundle is the sole runtime asset, and Home Assistant plus Android consume the same bytes.

- [ ] **Step 3: Remove the temporary generator workflow**

Delete `.github/workflows/phase01-generate.yml` only after the baseline and dist bundle are committed and reproducible.

- [ ] **Step 4: Run the complete validation suite**

```bash
python -m compileall custom_components tests scripts
python scripts/architecture_inventory.py --root . --check
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
gradle -p android :app:assembleDebug --stacktrace
```

Expected: every command exits 0 with no generated-file diff.

- [ ] **Step 5: Commit permanent CI and documentation**

```bash
git add .github/workflows/validate.yml docs/android-alpha3-regression.md
git rm .github/workflows/phase01-generate.yml
git commit -m "ci: enforce the consolidation baseline and shared bundle"
```

---

### Task 7: Final Structural Review and Pull Request

**Files:**
- Review all changed files.
- No production change unless a failing test demonstrates a defect.

**Interfaces:**
- Produces: a reviewable Phase 0–1 PR based on the corrected architecture branch.

- [ ] **Step 1: Confirm changed-file scope**

Expected categories only:

```text
architecture documentation and inventory
frontend manifest, builder and dist bundle
Home Assistant bundle loading
Android bundle packaging
CI guardrails
Phase 0–1 tests
```

- [ ] **Step 2: Confirm forbidden patterns did not grow**

```bash
python scripts/architecture_inventory.py --root . --check
```

Expected: exit 0.

- [ ] **Step 3: Confirm generated files are current**

```bash
node scripts/build_frontend.mjs --check
git diff --exit-code
```

Expected: exit 0.

- [ ] **Step 4: Confirm the full CI matrix is green**

Require successful GitHub Actions jobs for:

```text
Validate
HACS validation
hassfest
Android Alpha
```

- [ ] **Step 5: Request technical review**

Review specifically:

- exact legacy manifest order;
- no runtime fragment glob remains in `panel.py` or Gradle;
- Home Assistant version substitution and revision hashing are preserved;
- Android still packages the brand asset;
- baseline checker permits reductions but rejects additions;
- temporary generator workflow is absent;
- the dist bundle is checked in and reproducible.

- [ ] **Step 6: Keep the PR as draft until all checks are green**

The PR base remains `architecture/consolidation-target-0941` until the architecture PR is merged. It can then be retargeted to `main` without changing implementation commits.
