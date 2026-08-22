#!/usr/bin/env node
import { existsSync, mkdirSync, readFileSync, rmSync, renameSync, cpSync, copyFileSync, readdirSync, writeFileSync } from "node:fs";
import { homedir, platform } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";

const root = resolve(fileURLToPath(new URL(".", import.meta.url)), "..");
const args = process.argv.slice(2);

function getUserHome() {
  if (platform() !== "win32") return homedir();
  const driveHome = process.env.HOMEDRIVE && process.env.HOMEPATH ? `${process.env.HOMEDRIVE}${process.env.HOMEPATH}` : null;
  const candidates = [process.env.USERPROFILE, driveHome, homedir()].filter(Boolean);
  const slash = String.fromCharCode(92);
  for (const candidate of candidates) {
    const normalized = candidate.replaceAll("/", slash);
    const lower = normalized.toLowerCase();
    const userMarker = `${slash}users${slash}`;
    const suffixes = [
      `${slash}appdata${slash}local${slash}hermes`,
      `${slash}appdata${slash}local${slash}hermes-ui`,
      `${slash}appdata${slash}roaming${slash}mobaxterm${slash}home`,
    ];
    const suffix = suffixes.find((value) => lower.endsWith(value));
    if (suffix && lower.includes(userMarker)) return normalized.slice(0, -suffix.length);
    if (lower.includes(userMarker)) return normalized;
  }
  return candidates[0] || homedir();
}

const home = getUserHome();
const explicitThunderboltHome = process.env.THUNDERBOLT_HOME || "";
const defaultThunderboltHome = platform() === "win32"
  ? join(process.env.LOCALAPPDATA || join(home, "AppData", "Local"), "THUNDERBOLT")
  : join(home, ".thunderbolt");
const thunderboltHome = resolve(explicitThunderboltHome || defaultThunderboltHome);
const venvPath = process.env.THUNDERBOLT_VENV || process.env.HERMES_VENV || join(thunderboltHome, ".venv");
const pythonBin = platform() === "win32" ? join(venvPath, "Scripts", "python.exe") : join(venvPath, "bin", "python");
const defaultMpt = process.env.MONEYPRINTER_PATH || join(thunderboltHome, "MoneyPrinterTurbo");
const dependencyStatePath = join(thunderboltHome, "storage", "state", "install-state.json");
const forceDeps = args.includes("--force-deps");
const refreshMoneyPrinter = args.includes("--refresh-moneyprinter");

function legacyRoots() {
  const userProfile = process.env.USERPROFILE || home;
  const localAppData = process.env.LOCALAPPDATA || join(userProfile, "AppData", "Local");
  const roots = [
    join(home, "Hermes-UI"),
    join(localAppData, "hermes"),
    join(localAppData, "Hermes-UI"),
    join(userProfile, ".content-hermes"),
    join(userProfile, "hermes"),
  ];
  return [...new Set(roots.map((candidate) => resolve(candidate)))].filter((candidate) => candidate !== thunderboltHome);
}

function commandExists(command) {
  const result = spawnSync(platform() === "win32" ? "where" : "which", [command], { stdio: "ignore" });
  return result.status === 0;
}

function run(command, commandArgs, options = {}) {
  console.log(`\n> ${command} ${commandArgs.join(" ")}`);
  const result = spawnSync(command, commandArgs, { stdio: "inherit", ...options });
  if (result.status !== 0) process.exit(result.status || 1);
}

function probePython(command, commandArgs = []) {
  const result = spawnSync(command, [...commandArgs, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"], { encoding: "utf8" });
  if (result.status !== 0) return null;
  const versionText = result.stdout.trim();
  const version = versionText.split(".").map(Number);
  if (version[0] > 3 || (version[0] === 3 && version[1] >= 11)) return { command, args: commandArgs, version: versionText };
  return null;
}

function findPython() {
  const candidates = [];
  if (existsSync(pythonBin)) candidates.push({ command: pythonBin, args: [] });
  if (process.env.THUNDERBOLT_PYTHON || process.env.HERMES_PYTHON) {
    candidates.push({ command: process.env.THUNDERBOLT_PYTHON || process.env.HERMES_PYTHON, args: [] });
  }
  candidates.push(...(platform() === "win32"
    ? [{ command: "py", args: ["-3.11"] }, { command: "py", args: [] }, { command: "python", args: [] }, { command: "python3", args: [] }]
    : [{ command: "python3.11", args: [] }, { command: "python3", args: [] }, { command: "python", args: [] }]));
  for (const candidate of candidates) {
    const found = probePython(candidate.command, candidate.args);
    if (found) return found;
  }
  return null;
}

function ensureDirs() {
  const storageRoot = join(thunderboltHome, "storage");
  const directories = [
    thunderboltHome,
    storageRoot,
    join(storageRoot, "state"),
    join(storageRoot, "blueprints"),
    join(storageRoot, "blueprints", "canais"),
    join(storageRoot, "blueprints", "nichos"),
    join(storageRoot, "blueprints", "importados"),
    join(storageRoot, "blueprints", "brandings"),
    join(storageRoot, "tiktok"),
    join(storageRoot, "tiktok", "prompts_master"),
    join(storageRoot, "metadata_cleaner"),
    join(storageRoot, "metadata_cleaner", "originals"),
    join(storageRoot, "metadata_cleaner", "outputs"),
    join(storageRoot, "artifacts"),
    join(storageRoot, "skills"),
    join(storageRoot, "music"),
    join(storageRoot, "voice_previews"),
    join(storageRoot, "data"),
    join(storageRoot, "data", "niches"),
  ];
  for (const directory of directories) mkdirSync(directory, { recursive: true });
  copySeedBlueprints(storageRoot);
  copySeedPromptMasters(storageRoot);
}

function copySeedBlueprints(storageRoot) {
  const seedRoot = join(root, "seed", "blueprints");
  const destination = join(storageRoot, "blueprints", "importados");
  if (!existsSync(seedRoot)) return;
  for (const filename of readdirSync(seedRoot)) {
    if (!filename.endsWith(".json")) continue;
    const source = join(seedRoot, filename);
    const target = join(destination, filename);
    if (!existsSync(target)) copyFileSync(source, target);
  }
}

function copySeedPromptMasters(storageRoot) {
  const seedRoot = join(root, "seed", "prompt_masters");
  const destination = join(storageRoot, "tiktok", "prompts_master");
  if (!existsSync(seedRoot)) return;
  mkdirSync(destination, { recursive: true });
  for (const filename of readdirSync(seedRoot)) {
    if (!filename.endsWith(".md")) continue;
    const source = join(seedRoot, filename);
    const target = join(destination, filename);
    if (!existsSync(target)) copyFileSync(source, target);
  }
}

function copyOrMove(source, target, label) {
  if (!existsSync(source) || existsSync(target)) return false;
  mkdirSync(dirname(target), { recursive: true });
  try {
    renameSync(source, target);
    console.log(`Migração concluída: ${label} -> ${target}`);
  } catch {
    cpSync(source, target, { recursive: true });
    console.log(`Dados copiados para Thunderbolt: ${label} -> ${target}`);
  }
  return true;
}

function migrateLegacyInstallation() {
  if (explicitThunderboltHome) return;
  const candidates = legacyRoots();
  const legacy = candidates.find((candidate) => existsSync(join(candidate, "storage")) || existsSync(join(candidate, ".venv")) || existsSync(join(candidate, "MoneyPrinterTurbo")));
  if (!legacy) return;
  console.warn(`Foi encontrada uma instalação antiga em ${legacy}. O Thunderbolt usará ${thunderboltHome}.`);
  copyOrMove(join(legacy, "storage"), join(thunderboltHome, "storage"), "storage legado");
  copyOrMove(join(legacy, ".venv"), join(thunderboltHome, ".venv"), "ambiente Python legado");
  copyOrMove(join(legacy, "MoneyPrinterTurbo"), join(thunderboltHome, "MoneyPrinterTurbo"), "MoneyPrinterTurbo legado");
  console.log("A pasta legada não será usada pelo Thunderbolt; foi preservada quando a cópia foi necessária.");
}

function removePath(path) {
  if (!existsSync(path)) return;
  console.log(`A remover componente técnico: ${path}`);
  try {
    rmSync(path, { recursive: true, force: true });
  } catch (error) {
    console.error(`Não foi possível remover ${path}: ${error.message}`);
    console.error("Feche processos Thunderbolt/Node/Python que estejam a usar a pasta e execute novamente.");
    process.exit(1);
  }
}

function containsUserData(path) {
  return [
    join(path, "storage", "blueprints"),
    join(path, "storage", "brandings"),
    join(path, "storage", "state"),
  ].some((candidate) => existsSync(candidate));
}

function cleanInstallationRoots(moneyprinterPath) {
  if (args.includes("--purge-data")) {
    console.warn("ATENÇÃO: --purge-data apaga Blueprints, Brandings, configurações, storage e artefactos locais.");
    removePath(thunderboltHome);
    return;
  }

  if (refreshMoneyPrinter && resolve(moneyprinterPath).startsWith(thunderboltHome)) removePath(moneyprinterPath);
  for (const legacyRoot of legacyRoots()) {
    if (existsSync(legacyRoot) && containsUserData(legacyRoot)) {
      console.warn(`Instalação antiga com dados preservada para revisão manual: ${legacyRoot}`);
    }
  }
}

function installPythonWindows() {
  if (process.env.THUNDERBOLT_SKIP_PYTHON_INSTALL === "1" || process.env.HERMES_SKIP_PYTHON_INSTALL === "1") return null;
  if (!commandExists("winget")) {
    console.error("Python 3.11+ não foi encontrado e o winget também não está disponível.");
    console.error("Instale Python 3.11+ a partir de https://www.python.org/downloads/windows/ ou instale o App Installer da Microsoft para obter o winget.");
    console.error("Depois execute novamente: npx.cmd --yes @danhachuel/thunderbolt install");
    process.exit(1);
  }
  console.log("Python 3.11+ não encontrado. A instalar Python automaticamente através do winget...");
  const result = spawnSync("winget", ["install", "--exact", "--id", "Python.Python.3.11", "--source", "winget", "--scope", "user", "--accept-source-agreements", "--accept-package-agreements", "--silent"], { stdio: "inherit" });
  if (result.status !== 0) process.exit(result.status || 1);
  const found = findPython();
  if (!found) {
    console.error("Python foi instalado, mas o terminal actual ainda não encontrou o comando. Feche e reabra o terminal e repita.");
    process.exit(1);
  }
  return found;
}

function ensurePython() {
  let found = findPython();
  if (found) {
    console.log(`Python compatível encontrado: ${found.command} ${found.args.join(" ")} (${found.version})`);
    return found;
  }
  if (existsSync(venvPath)) removePath(venvPath);
  found = findPython();
  if (!found && platform() === "win32") found = installPythonWindows();
  if (!found) {
    console.error("Python 3.11 ou superior não foi encontrado. Instale Python 3.11+ e execute novamente.");
    process.exit(1);
  }
  return found;
}

function cloneMoneyPrinter(path) {
  if (existsSync(join(path, ".git")) || existsSync(join(path, "pyproject.toml"))) {
    console.log(`MoneyPrinterTurbo já existe em ${path}; será reutilizado.`);
    return;
  }
  if (!commandExists("git")) {
    console.error("Git não encontrado. Instale Git ou defina MONEYPRINTER_PATH para uma cópia local do MoneyPrinterTurbo.");
    process.exit(1);
  }
  const destination = resolve(path);
  const parent = resolve(destination, "..");
  mkdirSync(parent, { recursive: true });
  run("git", ["clone", "--depth", "1", "https://github.com/harry0703/MoneyPrinterTurbo.git", basename(destination)], { cwd: parent });
}

function fileHash(path) {
  if (!existsSync(path)) return "missing";
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function readDependencyState() {
  if (!existsSync(dependencyStatePath)) return {};
  try { return JSON.parse(readFileSync(dependencyStatePath, "utf8")); } catch { return {}; }
}

function writeDependencyState(updates) {
  mkdirSync(dirname(dependencyStatePath), { recursive: true });
  const state = { ...readDependencyState(), ...updates, updated_at: new Date().toISOString() };
  writeFileSync(dependencyStatePath, JSON.stringify(state, null, 2) + "\n", "utf8");
}

function importsAvailable(modules) {
  if (!existsSync(pythonBin)) return false;
  const code = `import importlib.util,sys; missing=[m for m in ${JSON.stringify(modules)} if importlib.util.find_spec(m) is None]; sys.exit(1 if missing else 0)`;
  return spawnSync(pythonBin, ["-c", code], { stdio: "ignore" }).status === 0;
}

function installRequirementIfNeeded(requirementsPath, stateKey, modules, label) {
  if (!existsSync(requirementsPath)) return;
  const currentHash = fileHash(requirementsPath);
  const state = readDependencyState();
  const importsOk = importsAvailable(modules);
  const hashMatches = state[stateKey] === currentHash;
  if (!forceDeps && importsOk && (hashMatches || !state[stateKey])) {
    console.log(`${label}: dependências detectadas e reutilizadas; nenhuma reinstalação necessária.`);
    writeDependencyState({ [stateKey]: currentHash });
    return;
  }
  console.log(`${label}: dependências ausentes, incompletas ou alteradas; a instalar agora.`);
  run(pythonBin, ["-m", "pip", "install", "-r", requirementsPath]);
  writeDependencyState({ [stateKey]: currentHash });
}

function writeSettings(moneyprinterPath) {
  const stateDir = join(thunderboltHome, "storage", "state");
  mkdirSync(stateDir, { recursive: true });
  const settingsPath = join(stateDir, "settings.json");
  let settings = {};
  if (existsSync(settingsPath)) {
    try { settings = JSON.parse(readFileSync(settingsPath, "utf8")); } catch { settings = {}; }
  }
  settings.moneyprinter_path = moneyprinterPath;
  settings.port = Number(process.env.THUNDERBOLT_PORT || process.env.HERMES_PORT || settings.port || 3030);
  writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + "\n", "utf8");
}

function installThunderboltDependencies(python) {
  if (!existsSync(pythonBin)) run(python.command, [...python.args, "-m", "venv", venvPath]);
  installRequirementIfNeeded(join(root, "requirements.txt"), "thunderbolt_requirements_sha256", ["streamlit", "requests", "pandas", "toml", "imageio_ffmpeg", "edge_tts", "google.auth", "google_auth_oauthlib", "googleapiclient"], "Thunderbolt");
}

function installMoneyPrinterDependencies(moneyprinterPath) {
  installRequirementIfNeeded(join(moneyprinterPath, "requirements.txt"), "moneyprinter_requirements_sha256", ["fastapi", "moviepy", "PIL", "numpy", "requests"], "MoneyPrinterTurbo");
}

function main() {
  const skipMpt = args.includes("--skip-moneyprinter");
  const skipDeps = args.includes("--skip-python-deps");
  const moneyprinterPath = process.env.MONEYPRINTER_PATH || defaultMpt;
  migrateLegacyInstallation();
  cleanInstallationRoots(moneyprinterPath);
  ensureDirs();
  const python = skipDeps ? null : ensurePython();
  if (!skipMpt) cloneMoneyPrinter(moneyprinterPath);
  if (!skipDeps) installThunderboltDependencies(python);
  if (!skipDeps && !skipMpt) installMoneyPrinterDependencies(moneyprinterPath);
  writeSettings(moneyprinterPath);
  console.log("\nInstalação do Thunderbolt concluída.");
  console.log(`Pasta Thunderbolt: ${thunderboltHome}`);
  console.log(`Ambiente Python: ${venvPath}`);
  console.log(`Motor de vídeo: ${moneyprinterPath}`);
  console.log("Execute `npx.cmd --yes @danhachuel/thunderbolt` no Windows ou `npx --yes @danhachuel/thunderbolt` noutros sistemas.");
}

main();
