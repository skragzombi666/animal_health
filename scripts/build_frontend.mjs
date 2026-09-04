import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const FRONTEND = path.join(
  ROOT,
  "custom_components",
  "animal_health",
  "frontend",
);
const MANIFEST = path.join(FRONTEND, "legacy", "manifest.json");
const OUTPUT = path.join(FRONTEND, "dist", "animal-health-panel.js");
const REFERENCE_VERSION = "0.9.41";
const EXPECTED_PARTS = Array.from(
  { length: 99 },
  (_, index) =>
    `../animal-health-panel.part${String(index + 1).padStart(2, "0")}.js`,
);

export async function loadManifest() {
  const manifest = JSON.parse(await readFile(MANIFEST, "utf8"));
  if (manifest.schema_version !== 1) {
    throw new Error(
      `Unsupported legacy manifest schema: ${manifest.schema_version}`,
    );
  }
  if (manifest.reference_version !== REFERENCE_VERSION) {
    throw new Error(
      `Unexpected legacy reference version: ${manifest.reference_version}`,
    );
  }
  if (!Array.isArray(manifest.parts)) {
    throw new Error("Legacy manifest parts must be an array");
  }
  if (new Set(manifest.parts).size !== manifest.parts.length) {
    throw new Error("Legacy manifest contains duplicate parts");
  }
  if (
    manifest.parts.length !== EXPECTED_PARTS.length ||
    manifest.parts.some((part, index) => part !== EXPECTED_PARTS[index])
  ) {
    throw new Error(
      "Legacy manifest must list the frozen part01.js through part99.js sequence exactly",
    );
  }
  return manifest;
}

export async function buildBundle() {
  const manifest = await loadManifest();
  const manifestDirectory = path.dirname(MANIFEST);
  const sources = await Promise.all(
    manifest.parts.map(async (relative) => {
      const sourcePath = path.resolve(manifestDirectory, relative);
      const relativeToFrontend = path.relative(FRONTEND, sourcePath);
      if (
        relativeToFrontend.startsWith("..") ||
        path.isAbsolute(relativeToFrontend)
      ) {
        throw new Error(`Legacy source escapes the frontend root: ${relative}`);
      }
      return readFile(sourcePath, "utf8");
    }),
  );
  return sources.join("");
}

export async function writeOrCheckBundle({ check = false } = {}) {
  const bundle = await buildBundle();
  if (check) {
    let current;
    try {
      current = await readFile(OUTPUT, "utf8");
    } catch (error) {
      if (error?.code === "ENOENT") {
        throw new Error(
          "Frontend dist bundle is missing. Run: node scripts/build_frontend.mjs",
        );
      }
      throw error;
    }
    if (current !== bundle) {
      throw new Error(
        "Frontend dist bundle is stale. Run: node scripts/build_frontend.mjs",
      );
    }
    console.log(
      `Frontend bundle is reproducible (${Buffer.byteLength(bundle, "utf8")} bytes)`,
    );
    return;
  }

  await mkdir(path.dirname(OUTPUT), { recursive: true });
  await writeFile(OUTPUT, bundle, "utf8");
  console.log(
    `Wrote ${path.relative(ROOT, OUTPUT)} (${Buffer.byteLength(bundle, "utf8")} bytes)`,
  );
}

async function main() {
  const arguments_ = process.argv.slice(2);
  const unknown = arguments_.filter((argument) => argument !== "--check");
  if (unknown.length) {
    throw new Error(`Unknown argument(s): ${unknown.join(", ")}`);
  }
  await writeOrCheckBundle({ check: arguments_.includes("--check") });
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
}
