import { readdir } from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SOURCE = path.join(
  ROOT,
  "custom_components",
  "animal_health",
  "frontend",
  "src",
);
const ENTRY = path.join(SOURCE, "entry.js");
const EXPECTED_EXPORTS = Object.freeze([
  "AnimalHealthClient",
  "AnimalHealthError",
  "COMMANDS",
  "DTO_SCHEMA_VERSION",
  "ERROR_CODES",
  "createAndroidTransport",
  "createHomeAssistantTransport",
  "normalizeAnimalDetail",
  "normalizeAnimalDirectory",
  "normalizeProductState",
  "normalizeSettingsState",
  "normalizeTaskOccurrence",
]);

async function javascriptFiles(directory) {
  const result = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      result.push(...(await javascriptFiles(target)));
    } else if (entry.isFile() && entry.name.endsWith(".js")) {
      result.push(target);
    }
  }
  return result.sort();
}

function checkSyntax(file) {
  const result = spawnSync(process.execPath, ["--check", file], {
    cwd: ROOT,
    encoding: "utf8",
  });
  if (result.status !== 0) {
    throw new Error(
      `JavaScript syntax check failed for ${path.relative(ROOT, file)}\n${result.stderr || result.stdout}`,
    );
  }
}

async function checkEntrySideEffects() {
  const before = new Set(Reflect.ownKeys(globalThis));
  const registrations = [];
  const hadCustomElements = Object.hasOwn(globalThis, "customElements");
  const previousCustomElements = globalThis.customElements;
  Object.defineProperty(globalThis, "customElements", {
    configurable: true,
    value: {
      define(name) {
        registrations.push(String(name));
      },
      get() {
        return undefined;
      },
    },
  });

  let module;
  try {
    module = await import(`${pathToFileURL(ENTRY).href}?check=${Date.now()}`);
  } finally {
    if (hadCustomElements) {
      Object.defineProperty(globalThis, "customElements", {
        configurable: true,
        value: previousCustomElements,
      });
    } else {
      delete globalThis.customElements;
    }
  }

  if (registrations.length) {
    throw new Error(
      `Phase 2 entry registered custom elements: ${registrations.join(", ")}`,
    );
  }
  const after = new Set(Reflect.ownKeys(globalThis));
  const added = [...after].filter((key) => !before.has(key));
  if (added.length) {
    throw new Error(
      `Phase 2 entry created global properties: ${added.map(String).join(", ")}`,
    );
  }
  const missing = EXPECTED_EXPORTS.filter((name) => !(name in module));
  if (missing.length) {
    throw new Error(`Phase 2 entry is missing exports: ${missing.join(", ")}`);
  }
  if (module.DTO_SCHEMA_VERSION !== 1) {
    throw new Error(
      `Unexpected DTO schema version: ${module.DTO_SCHEMA_VERSION}`,
    );
  }
}

async function main() {
  const files = await javascriptFiles(SOURCE);
  if (!files.length) throw new Error("No modular frontend sources found");
  for (const file of files) checkSyntax(file);
  await checkEntrySideEffects();
  console.log(`Checked ${files.length} modular frontend source files`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
