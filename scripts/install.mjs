#!/usr/bin/env node
import { cpSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { homedir, platform, arch } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const root = resolve(fileURLToPath(new URL(".", import.meta.url)), "..");
const args = process.argv.slice(2);
const home = platform() === "win32" ? (process.env.USERPROFILE || homedir()) : homedir();
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

function probePython(command, commandArgs = []) {
  const result = spawnSync(command, [...commandArgs, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"], { encoding: "utf8" });
  if (result.status !== 0) return null;
  const versionText = result.stdout.trim();
  const version = versionText.split(".").map(Number);
  if (version[0] > 3 || (version[0] === 3 && version[1] >= 11)) return { command, args: commandArgs, version: versionText };
  return null;
}

function findPython() {
  if (process.env.HERMES_PYTHON) return probePython(process.env.HERMES_PYTHON);
  const candidates = platform() === "win32"
    ? [{ command: "py", args: ["-3.11"] }, { command: "py", args: [] }, { command: "python", args: [] }, { command: "python3", args: [] }]
    : [{ command: "python3.11", args: [] }, { command: "python3", args: [] }, { command: "python", args: [] }];
  for (const candidate of candidates) {
    const found = probePython(candidate.command, candidate.args);
    if (found) return found;
  }
  return null;
}

function ensureDirs() {
  mkdirSync(hermesHome, { recursive: true });
  mkdirSync(join(hermesHome, "storage"), { recursive: true });
}

function isManagedLegacyRoot(candidate) {
  if (!candidate || resolve(candidate) === resolve(hermesHome) || !existsSync(candidate)) return false;
  return ["MoneyPrinterTurbo", ".venv", "storage"].some((name) => existsSync(join(candidate, name)));
}

function cleanupLegacyInstallations() {
  if (process.env.HERMES_HOME || process.env.MONEYPRINTER_PATH || process.env.HERMES_KEEP_LEGACY === "1") return;
  if (platform() !== "win32") return;
  const userProfile = process.env.USERPROFILE || home;
  const localAppData = process.env.LOCALAPPDATA || join(userProfile, "AppData", "Local");
  const candidates = [
    join(localAppData, "hermes"),
    join(localAppData, "Hermes-UI"),
    join(userProfile, ".content-hermes"),
    join(userProfile, "hermes"),
  ];
  for (const candidate of candidates) {
    if (!isManagedLegacyRoot(candidate)) continue;
    if (!existsSync(hermesHome)) {
      console.log(`A migrar instalação antiga de ${candidate} para ${hermesHome}`);
      mkdirSync(resolve(hermesHome, ".."), { recursive: true });
      try {
        cpSync(candidate, hermesHome, { recursive: true, force: false, errorOnExist: false });
        rmSync(candidate, { recursive: true, force: true });
      } catch (error) {
        console.error(`Não foi possível migrar ${candidate}: ${error.message}`);
        console.error("A instalação foi interrompida para evitar duplicação ou perda de dados.");
        process.exit(1);
      }
    } else if (resolve(candidate) !== resolve(hermesHome)) {
      console.log(`A remover instalação antiga detectada em ${candidate}`);
      rmSync(candidate, { recursive: true, force: true });
    }
  }
}

function installPythonWindows() {
  if (process.env.HERMES_SKIP_PYTHON_INSTALL === "1") return null;
  if (!commandExists("winget")) {
    console.error("Python 3.11+ não foi encontrado e o winget também não está disponível.");
    console.error("Instale Python 3.11+ a partir de https://www.python.org/downloads/windows/ ou instale o App Installer da Microsoft para obter o winget.");
    console.error("Depois execute novamente: npx.cmd --yes @danhachuel/content-hermes-ui install");
    process.exit(1);
  }
  console.log("Python 3.11+ não encontrado. A instalar Python automaticamente através do winget...");
  const result = spawnSync("winget", ["install", "--exact", "--id", "Python.Python.3.11", "--source", "winget", "--scope", "user", "--accept-source-agreements", "--accept-package-agreements", "--silent"], { stdio: "inherit" });
  if (result.status !== 0) {
    console.error("A instalação automática do Python pelo winget falhou.");
    console.error("Tente abrir um novo PowerShell e executar: winget install --exact --id Python.Python.3.11 --source winget");
    process.exit(result.status || 1);
  }
  const found = findPython();
  if (!found) {
    console.error("Python foi instalado, mas o terminal actual ainda não encontrou o comando.");
    console.error("Feche e reabra o PowerShell e execute novamente o comando de instalação.");
    process.exit(1);
  }
  return found;
}

function ensurePython() {
  let found = findPython();
  if (!found && platform() === "win32") found = installPythonWindows();
  if (!found) {
    console.error("Python 3.11 ou superior não foi encontrado. Instale Python 3.11+ e execute novamente, ou defina HERMES_PYTHON.");
    process.exit(1);
  }
  console.log(`Python compatível encontrado: ${found.command} ${found.args.join(" ")} (${found.version})`);
  return found;
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

function installContentHermesDependencies(python) {
  if (!existsSync(pythonBin)) run(python.command, [...python.args, "-m", "venv", venvPath]);
  run(pythonBin, ["-m", "pip", "install", "--upgrade", "pip"]);
  run(pythonBin, ["-m", "pip", "install", "-r", join(root, "requirements.txt")]);
  run(pythonBin, ["-m", "pip", "install", "imageio-ffmpeg"]);
}

function installMoneyPrinterDependencies(moneyprinterPath) {
  if (existsSync(join(moneyprinterPath, "requirements.txt"))) {
    run(pythonBin, ["-m", "pip", "install", "-r", join(moneyprinterPath, "requirements.txt")]);
  }
}

function main() {
  const skipMpt = args.includes("--skip-moneyprinter");
  const skipDeps = args.includes("--skip-python-deps");
  const moneyprinterPath = process.env.MONEYPRINTER_PATH || defaultMpt;
  cleanupLegacyInstallations();
  ensureDirs();
  const python = skipDeps ? null : ensurePython();
  if (!skipDeps) installContentHermesDependencies(python);
  if (!skipMpt) cloneMoneyPrinter(moneyprinterPath);
  if (!skipDeps && !skipMpt) installMoneyPrinterDependencies(moneyprinterPath);
  writeSettings(moneyprinterPath);
  console.log("\\nInstalação concluída.");
  console.log(`Pasta Content-Hermes: ${hermesHome}`);
  console.log(`Ambiente Python: ${venvPath}`);
  console.log(`MoneyPrinterTurbo: ${moneyprinterPath}`);
  console.log("Execute `npx.cmd --yes @danhachuel/content-hermes-ui` no Windows ou `npx --yes @danhachuel/content-hermes-ui` noutros sistemas.");
}

main();
