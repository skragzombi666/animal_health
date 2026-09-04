from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "custom_components/animal_health/frontend/src/app/read-only-animals.js"
BRIDGE = ROOT / "custom_components/animal_health/frontend/src/legacy/compatibility-bridge.js"
BRIDGE_TEST = ROOT / "tests/frontend/legacy-read-only-bridge.test.mjs"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {path.relative_to(ROOT)}, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_runtime() -> None:
    replace_once(
        RUNTIME,
        '''  "animals-toggle-archived",
]);

function migrated(routeName) {''',
        '''  "animals-toggle-archived",
]);

const TEXT_FILTER_ACTIONS = new Set([
  "home-search",
  "animals-filter",
]);

function migrated(routeName) {''',
    )
    replace_once(
        RUNTIME,
        '''    }));
  }

  async function load({ force = false } = {}) {''',
        '''    }));
  }

  function restoreTextInput(action, selectionStart, selectionEnd) {
    if (typeof panel.shadowRoot.querySelector !== "function") return;
    const replacement = panel.shadowRoot.querySelector(
      `[data-action="${action}"]`,
    );
    if (!replacement) return;
    replacement.focus?.();
    if (
      Number.isInteger(selectionStart) &&
      typeof replacement.setSelectionRange === "function"
    ) {
      replacement.setSelectionRange(
        selectionStart,
        Number.isInteger(selectionEnd) ? selectionEnd : selectionStart,
      );
    }
  }

  async function load({ force = false } = {}) {''',
    )
    replace_once(
        RUNTIME,
        '''  async function openAnimal(animalId) {''',
        '''  async function refreshCurrentRoute() {
    const directoryResult = await load({ force: true });
    if (directoryResult?.applied === false) return directoryResult;
    const route = router.current();
    if (route.name === "animal-detail" && route.params?.animalId) {
      return loadDetail(route.params.animalId, { force: true });
    }
    return store.getState();
  }

  async function openAnimal(animalId) {''',
    )
    replace_once(
        RUNTIME,
        '''    if (migrated(name)) {
      panel.view = name;
      router.navigate({ name, params: {} });
      if (store.getState().animals.status === "idle") await load();
      return { mode: "new", route: router.current() };
    }''',
        '''    if (migrated(name)) {
      panel.view = name;
      router.navigate({ name, params: {} });
      if (store.getState().animals.status === "idle") await load();
      render();
      return { mode: "new", route: router.current() };
    }''',
    )
    replace_once(
        RUNTIME,
        '''      "read.refresh": () => load({ force: true }),
      refresh: () =>
        router.current().name === "animal-detail"
          ? loadDetail(router.current().params.animalId, { force: true })
          : load({ force: true }),''',
        '''      "read.refresh": () => refreshCurrentRoute(),
      refresh: () => refreshCurrentRoute(),''',
    )
    replace_once(
        RUNTIME,
        '''  async function handleEvent(event) {
    const target = targetFromEvent(event);
    if (!target) return false;
    if (target.dataset.view) return navigate(target.dataset.view);
    const action = String(target.dataset.action || "");
    if (!modernActionAllowed(action)) return false;
    return controller.dispatch(action, {
      event,
      target,
      id: target.dataset.id || null,
      value: target.value,
    });
  }''',
        '''  async function handleEvent(event) {
    const target = targetFromEvent(event);
    if (!target) return false;
    const action = String(target.dataset.action || "");
    if (!target.dataset.view && !modernActionAllowed(action)) return false;
    const restoreFocus = TEXT_FILTER_ACTIONS.has(action);
    const selectionStart = Number.isInteger(target.selectionStart)
      ? target.selectionStart
      : null;
    const selectionEnd = Number.isInteger(target.selectionEnd)
      ? target.selectionEnd
      : selectionStart;
    try {
      const result = target.dataset.view
        ? await navigate(target.dataset.view)
        : await controller.dispatch(action, {
            event,
            target,
            id: target.dataset.id || null,
            value: target.value,
          });
      if (restoreFocus) {
        restoreTextInput(action, selectionStart, selectionEnd);
      }
      return result;
    } catch (error) {
      return {
        applied: false,
        error: normalizeError(error, {
          operation: target.dataset.view
            ? `navigate:${target.dataset.view}`
            : `event:${action}`,
        }),
      };
    }
  }''',
    )
    replace_once(
        RUNTIME,
        '''    load,
    loadDetail,
    openAnimal,''',
        '''    load,
    loadDetail,
    refreshCurrentRoute,
    openAnimal,''',
    )


def patch_bridge() -> None:
    replace_once(
        BRIDGE,
        '''      await runtimeFor(panel, state).load({ force: true }).catch(() => undefined);''',
        '''      await runtimeFor(panel, state).refreshCurrentRoute().catch(() => undefined);''',
    )


def patch_bridge_test() -> None:
    replace_once(
        BRIDGE_TEST,
        '''      async load(options = {}) {
        calls.push(["load", options]);
        return "modern-load";
      },
      async openAnimal(id) {''',
        '''      async load(options = {}) {
        calls.push(["load", options]);
        return "modern-load";
      },
      async refreshCurrentRoute() {
        calls.push(["refreshCurrentRoute"]);
        return "modern-refresh";
      },
      async openAnimal(id) {''',
    )
    replace_once(
        BRIDGE_TEST,
        '''test("legacy submit refreshes Legacy state internally then the modern directory", async () => {''',
        '''test("legacy submit refreshes Legacy state internally then the complete modern route", async () => {''',
    )
    replace_once(
        BRIDGE_TEST,
        '''  assert.deepEqual(runtimes[0].calls, [["load", { force: true }]]);''',
        '''  assert.deepEqual(runtimes[0].calls, [["refreshCurrentRoute"]]);''',
    )


def main() -> None:
    patch_runtime()
    patch_bridge()
    patch_bridge_test()
    print("Applied Phase 4 runtime lifecycle fixes")


if __name__ == "__main__":
    main()
