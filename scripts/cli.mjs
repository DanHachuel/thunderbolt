#!/usr/bin/env node
import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { homedir, platform } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL(".", import.meta.url)), "..");
const args = process.argv.slice(2);
const userHome = platform() === "win32" ? (process.env.USERPROFILE || homedir()) : homedir();
const hermesHome = process.env.HERMES_HOME || join(userHome, "Hermes-UI");
const venvDir = process.env.HERMES_VENV || join(hermesHome, ".venv");
const venvPython = platform() === "win32" ? join(venvDir, "Scripts", "python.exe") : join(venvDir, "bin", "python");
const python = process.env.HERMES_PYTHON || (existsSync(venvPython) ? venvPython : (platform() === "win32" ? "python" : "python3"));
const main = resolve(root, "app", "main.py");

function run(command, commandArgs) {
  const result = spawnSync(command, commandArgs, { stdio: "inherit", env: process.env });
  process.exit(result.status ?? 1);
}

function pythonVersion() {
  return spawnSync(python, ["-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"], { encoding: "utf8" });
}

function check() {
  const version = pythonVersion();
  if (version.status !== 0) {
    console.error(`Python não encontrado. Execute: npx --yes @danhachuel/content-hermes-ui install`);
    process.exit(1);
  }
  const streamlit = spawnSync(python, ["-c", "import streamlit; print(streamlit.__version__)"], { stdio: "pipe", encoding: "utf8" });
  if (streamlit.status !== 0) {
    console.error(`Streamlit não está instalado neste ambiente Python. Execute: npx --yes @danhachuel/content-hermes-ui install`);
    process.exit(1);
  }
  const ffmpeg = spawnSync(python, ["-c", "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"], { stdio: "pipe", encoding: "utf8" });
  console.log(`Ambiente OK. Python: ${version.stdout.trim()}; Streamlit: ${streamlit.stdout.trim()}; FFmpeg: ${ffmpeg.status === 0 ? ffmpeg.stdout.trim() : "não detectado"}`);
}

if (args[0] === "install") run(process.execPath, [resolve(root, "scripts", "install.mjs"), ...args.slice(1)]);
if (args[0] === "doctor" || args.includes("--check")) {
  check();
  process.exit(0);
}
if (!existsSync(main)) {
  console.error(`Entrada não encontrada: ${main}`);
  process.exit(1);
}
const port = process.env.HERMES_PORT || "3030";
const child = spawn(python, ["-m", "streamlit", "run", main, "--server.port", port, "--server.address", "localhost"], { cwd: root, stdio: "inherit", env: { ...process.env, HERMES_STORAGE_DIR: process.env.HERMES_STORAGE_DIR || join(hermesHome, "storage") } });
child.on("exit", (code, signal) => process.exit(code ?? (signal ? 1 : 0)));
