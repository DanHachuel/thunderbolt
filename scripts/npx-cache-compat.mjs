import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const npxCacheRoot = resolve(packageRoot, "../../..");
const pathParts = npxCacheRoot.split(/[\\/]+/).filter(Boolean).map((part) => part.toLowerCase());
const isNpxCache = pathParts.includes("_npx");
const packageJsonPath = resolve(npxCacheRoot, "package.json");

if (isNpxCache && !existsSync(packageJsonPath)) {
  mkdirSync(npxCacheRoot, { recursive: true });
  writeFileSync(packageJsonPath, JSON.stringify({ private: true }, null, 2) + "\n", "utf8");
}

