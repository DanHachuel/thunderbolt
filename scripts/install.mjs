#!/usr/bin/env node
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir, platform } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const root = resolve(fileURLToPath(new URL(".", import.meta.url)), "..");
const args = process.argv.slice(2);
const home = homedir();
const hermesHome = process.env.HERMES_HOME || join(home, "Hermes-UI");
const venvPath = process.env.HERMES_VENV || join(hermesHome, ".venv");
const defaultMpt = process.env.MONEYPRINTER_PATH || join(hermesHome, "MoneyPrinterTurbo");
const pythonBin = platform() === "win32" ? join(venvPath, "Scripts", "python.exe") : join(venvPath, "bin", "python");

function commandExists(command) {
  const result = spawnSync(platform() === "win32" ? "where" : "which", [command], { stdio: "ignore" });
  return result.status === 0;
}

function run(command, commandArgs, options = {}) {
  console.log(`\\n> ${command} ${commandArgs.join(" ")}`);
  const result = spawnSync(command, commandArgs, { stdio: "inherit", ...options });
  if (result.status !== 0) process.exit(result.status || 1);
}

function findPython() {
  const candidates = process.env.HERMES_PYTHON ? [process.env.HERMES_PYTHON] : platform() === "win32" ? ["py", "python"] : ["python3.11", "python3", "python"];
  for (const candidate of candidates) {
    const result = spawnSync(candidate, ["-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"], { encoding: "utf8" });
    if (result.status === 0) {
      const version = result.stdout.trim().split(".").map(Number);
      if (version[0] > 3 || (version[0] === 3 && version[1] >= 11)) return { command: candidate, version: result.stdout.trim() };
    }
  }
  return null;
}

function ensureDirs() {
  mkdirSync(hermesHome, { recursive: true });
  mkdirSync(join(hermesHome, "storage"), { recursive: true });
}

function cloneMoneyPrinter(path) {
  if (existsSync(join(path, ".git")) || existsSync(join(path, "pyproject.toml"))) {
    console.log(`MoneyPrinterTurbo já existe em ${path}`);
    return;
  }
  if (!commandExists("git")) {
    console.error("Git não encontrado. Instale Git ou defina MONEYPRINTER_PATH para uma cópia local do MoneyPrinterTurbo.");
    process.exit(1);
  }
  mkdirSync(resolve(path, ".."), { recursive: true });
  run("git", ["clone", "--depth", "1", "https://github.com/harry0703/MoneyPrinterTurbo.git", path]);
}

function writeSettings(moneyprinterPath) {
  const stateDir = join(hermesHome, "storage", "state");
  mkdirSync(stateDir, { recursive: true });
  const settingsPath = join(stateDir, "settings.json");
  let settings = {};
  if (existsSync(settingsPath)) {
    try { settings = JSON.parse(readFileSync(settingsPath, "utf8")); } catch { settings = {}; }
  }
  settings.moneyprinter_path = moneyprinterPath;
  settings.port = Number(process.env.HERMES_PORT || settings.port || 3030);
  writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + "\\n", "utf8");
}

function installPythonDependencies(moneyprinterPath) {
  const sourcePython = findPython();
  if (!sourcePython) {
    console.error("Python 3.11 ou superior não foi encontrado. Instale Python 3.11+ e execute novamente, ou defina HERMES_PYTHON.");
    process.exit(1);
  }
  console.log(`Python compatível encontrado: ${sourcePython.command} (${sourcePython.version})`);
  if (!existsSync(pythonBin)) run(sourcePython.command, ["-m", "venv", venvPath]);
  run(pythonBin, ["-m", "pip", "install", "--upgrade", "pip"]);
  run(pythonBin, ["-m", "pip", "install", "-r", join(root, "requirements.txt")]);
  if (moneyprinterPath && existsSync(join(moneyprinterPath, "requirements.txt"))) {
    run(pythonBin, ["-m", "pip", "install", "-r", join(moneyprinterPath, "requirements.txt")]);
  }
  run(pythonBin, ["-m", "pip", "install", "imageio-ffmpeg"]);
}

function main() {
  const skipMpt = args.includes("--skip-moneyprinter");
  const skipDeps = args.includes("--skip-python-deps");
  const moneyprinterPath = process.env.MONEYPRINTER_PATH || defaultMpt;
  ensureDirs();
  if (!skipMpt) cloneMoneyPrinter(moneyprinterPath);
  if (!skipDeps) installPythonDependencies(moneyprinterPath);
  writeSettings(moneyprinterPath);
  console.log("\\nInstalação concluída.");
  console.log(`Ambiente Python: ${venvPath}`);
  console.log(`MoneyPrinterTurbo: ${moneyprinterPath}`);
  console.log("Execute `npx --yes @danhachuel/content-hermes-ui` para iniciar a UI.");
}

main();
