#!/usr/bin/env node
import { spawn, spawnSync } from "node:child_process";
import http from "node:http";
import net from "node:net";
import { existsSync, mkdirSync, readFileSync, copyFileSync, readdirSync } from "node:fs";
import { homedir, platform } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL(".", import.meta.url)), "..");
const args = process.argv.slice(2);

function getUserHome() {
  if (platform() !== "win32") return homedir();
  const driveHome = process.env.HOMEDRIVE && process.env.HOMEPATH ? `${process.env.HOMEDRIVE}${process.env.HOMEPATH}` : null;
  return process.env.USERPROFILE || driveHome || homedir();
}

const userHome = getUserHome();
const defaultThunderboltHome = platform() === "win32"
  ? join(process.env.LOCALAPPDATA || join(userHome, "AppData", "Local"), "THUNDERBOLT")
  : join(userHome, ".thunderbolt");
const thunderboltHome = resolve(process.env.THUNDERBOLT_HOME || defaultThunderboltHome);
const venvDir = process.env.THUNDERBOLT_VENV || process.env.HERMES_VENV || join(thunderboltHome, ".venv");
const venvPython = platform() === "win32" ? join(venvDir, "Scripts", "python.exe") : join(venvDir, "bin", "python");
const python = process.env.THUNDERBOLT_PYTHON || process.env.HERMES_PYTHON || (existsSync(venvPython) ? venvPython : (platform() === "win32" ? "python" : "python3"));
const main = resolve(root, "app", "main.py");
const settingsPath = join(thunderboltHome, "storage", "state", "settings.json");

function run(command, commandArgs, label = "comando") {
  console.log(`Thunderbolt: a iniciar ${label}...`);
  const result = spawnSync(command, commandArgs, {
    stdio: "inherit",
    env: process.env,
    cwd: root,
    windowsHide: false,
  });
  if (result.error) {
    console.error(`Thunderbolt: não foi possível iniciar ${label}: ${result.error.message}`);
    process.exit(1);
  }
  if (result.signal) {
    console.error(`Thunderbolt: ${label} terminou pelo sinal ${result.signal}.`);
    process.exit(1);
  }
  process.exit(result.status ?? 1);
}

function pythonVersion() {
  return spawnSync(python, ["-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"], { encoding: "utf8" });
}

function moduleAvailable(moduleName) {
  const code = `import importlib.util,sys; sys.exit(0 if importlib.util.find_spec(${JSON.stringify(moduleName)}) else 1)`;
  return spawnSync(python, ["-c", code], { stdio: "ignore" }).status === 0;
}

function configuredMoneyPrinterPath() {
  if (!existsSync(settingsPath)) return join(thunderboltHome, "MoneyPrinterTurbo");
  try {
    const settings = JSON.parse(readFileSync(settingsPath, "utf8"));
    return settings.moneyprinter_path || join(thunderboltHome, "MoneyPrinterTurbo");
  } catch {
    return join(thunderboltHome, "MoneyPrinterTurbo");
  }
}

function ensureRuntimeStorage() {
  const storageRoot = process.env.THUNDERBOLT_STORAGE_DIR || join(thunderboltHome, "storage");
  const directories = [
    storageRoot,
    join(storageRoot, "state"),
    join(storageRoot, "blueprints"),
    join(storageRoot, "blueprints", "canais"),
    join(storageRoot, "blueprints", "nichos"),
    join(storageRoot, "blueprints", "importados"),
    join(storageRoot, "blueprints", "brandings"),
    join(storageRoot, "metadata_cleaner"),
    join(storageRoot, "metadata_cleaner", "originals"),
    join(storageRoot, "metadata_cleaner", "outputs"),
    join(storageRoot, "skills"),
    join(storageRoot, "music"),
    join(storageRoot, "voice_previews"),
    join(storageRoot, "data"),
    join(storageRoot, "data", "niches"),
  ];
  for (const directory of directories) mkdirSync(directory, { recursive: true });
  const seedRoot = resolve(root, "seed", "blueprints");
  const destination = join(storageRoot, "blueprints", "importados");
  if (existsSync(seedRoot)) {
    for (const filename of readdirSync(seedRoot)) {
      if (!filename.endsWith(".json")) continue;
      const target = join(destination, filename);
      if (!existsSync(target)) copyFileSync(join(seedRoot, filename), target);
    }
  }
}

function check() {
  const version = pythonVersion();
  if (version.status !== 0) {
    console.error(`Python não encontrado. Execute: npx.cmd --yes @danhachuel/thunderbolt install`);
    process.exit(1);
  }
  const requiredModules = ["streamlit", "requests", "pandas", "toml", "imageio_ffmpeg", "edge_tts", "sklearn", "mlxtend", "plotly", "seaborn", "kagglehub"];
  const missing = requiredModules.filter((moduleName) => !moduleAvailable(moduleName));
  const ffmpeg = moduleAvailable("imageio_ffmpeg");
  const mptPath = configuredMoneyPrinterPath();
  const mptReady = existsSync(join(mptPath, "requirements.txt")) || existsSync(join(mptPath, "pyproject.toml"));
  console.log(`Thunderbolt: ${thunderboltHome}`);
  console.log(`Python: ${version.stdout.trim()}`);
  console.log(`Dependências da aplicação: ${missing.length ? `em falta (${missing.join(", ")})` : "OK"}`);
  console.log(`FFmpeg: ${ffmpeg ? "OK via imageio-ffmpeg" : "em falta"}`);
  console.log(`Motor de vídeo: ${mptReady ? `OK (${mptPath})` : `não encontrado (${mptPath})`}`);
  if (missing.length || !ffmpeg) {
    console.error("Instalação incompleta. Execute `npx.cmd --yes @danhachuel/thunderbolt install`; dependências já válidas serão reutilizadas.");
    process.exit(1);
  }
}

if (args[0] === "install" || args[0] === "--install") {
  const installer = resolve(root, "scripts", "install.mjs");
  if (!existsSync(installer)) {
    console.error(`Thunderbolt: instalador não encontrado: ${installer}`);
    process.exit(1);
  }
  run(process.execPath, [installer, ...args.slice(1)], "a instalação");
}
if (args[0] === "doctor" || args.includes("--check")) {
  check();
  process.exit(0);
}
if (!existsSync(main)) {
  console.error(`Entrada não encontrada: ${main}`);
  process.exit(1);
}
ensureRuntimeStorage();
const storageDir = process.env.THUNDERBOLT_STORAGE_DIR || join(thunderboltHome, "storage");
const runtimeEnv = {
  ...process.env,
  THUNDERBOLT_STORAGE_DIR: storageDir,
  STREAMLIT_BROWSER_GATHER_USAGE_STATS: "false",
  STREAMLIT_SERVER_HEADLESS: "true",
};

if (args[0] === "worker" || args.includes("--worker")) {
  run(python, ["-m", "hermes_ui.automation_worker", ...args.filter((arg) => arg !== "worker" && arg !== "--worker")], "worker de automação");
}

if (args[0] === "pipeline-worker" || args.includes("--pipeline-worker")) {
  run(python, ["-m", "hermes_ui.pipeline_worker", ...args.filter((arg) => arg !== "pipeline-worker" && arg !== "--pipeline-worker")], "worker do pipeline de vídeos");
}

const port = process.env.THUNDERBOLT_PORT || process.env.HERMES_PORT || "3030";
const publicPort = Number.parseInt(String(port), 10);
const backendPort = Number.isFinite(publicPort) ? publicPort + 1 : 3031;
const supportedLanguages = new Set(["en", "zh", "de", "vi", "tr", "pt", "ru", "es", "id", "it"]);

const proxy = http.createServer((request, response) => {
  const requestUrl = new URL(request.url || "/", `http://localhost:${publicPort}`);
  const pathParts = requestUrl.pathname.split("/").filter(Boolean);
  const languagePrefix = pathParts.length === 1 && supportedLanguages.has(pathParts[0]) ? pathParts[0] : "";
  if (languagePrefix) {
    requestUrl.pathname = "/";
    requestUrl.searchParams.set("lang", languagePrefix);
    response.writeHead(302, { Location: `${requestUrl.pathname}?${requestUrl.searchParams.toString()}` });
    response.end();
    return;
  }
  const upstream = http.request({
    hostname: "127.0.0.1",
    port: backendPort,
    method: request.method,
    path: `${requestUrl.pathname}${requestUrl.search}`,
    headers: { ...request.headers, host: `127.0.0.1:${backendPort}` },
  }, (upstreamResponse) => {
    response.writeHead(upstreamResponse.statusCode || 502, upstreamResponse.headers);
    upstreamResponse.pipe(response);
  });
  upstream.on("error", (error) => {
    response.writeHead(502, { "content-type": "text/plain; charset=utf-8" });
    response.end(`Thunderbolt backend indisponível: ${error.message}`);
  });
  request.pipe(upstream);
});

proxy.on("upgrade", (request, clientSocket, head) => {
  const upstreamSocket = net.connect(backendPort, "127.0.0.1", () => {
    const headers = Object.entries(request.headers)
      .map(([name, value]) => `${name}: ${Array.isArray(value) ? value.join(", ") : value}`)
      .join("\r\n");
    upstreamSocket.write(`GET ${request.url} HTTP/1.1\r\n${headers}\r\n\r\n`);
    if (head.length) upstreamSocket.write(head);
    clientSocket.pipe(upstreamSocket).pipe(clientSocket);
  });
  upstreamSocket.on("error", () => clientSocket.destroy());
});

proxy.listen(publicPort, "127.0.0.1");
const worker = spawn(python, ["-m", "hermes_ui.automation_worker"], {
  cwd: root,
  stdio: "inherit",
  env: runtimeEnv,
  windowsHide: false,
});
const pipelineWorker = spawn(python, ["-m", "hermes_ui.pipeline_worker"], {
  cwd: root,
  stdio: "inherit",
  env: runtimeEnv,
  windowsHide: false,
});
const child = spawn(python, ["-m", "streamlit", "run", main, "--server.port", String(backendPort), "--server.address", "127.0.0.1"], {
  cwd: root,
  stdio: "inherit",
  env: runtimeEnv,
  windowsHide: false,
});

const stopWorker = () => {
  proxy.close();
  if (!worker.killed) worker.kill();
  if (!pipelineWorker.killed) pipelineWorker.kill();
};
process.on("SIGINT", stopWorker);
process.on("SIGTERM", stopWorker);
child.on("exit", (code, signal) => {
  stopWorker();
  process.exit(code ?? (signal ? 1 : 0));
});
worker.on("error", (error) => console.error(`Thunderbolt worker: ${error.message}`));
pipelineWorker.on("error", (error) => console.error(`Thunderbolt pipeline worker: ${error.message}`));
