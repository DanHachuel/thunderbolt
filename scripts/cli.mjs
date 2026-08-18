#!/usr/bin/env node
import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const args = process.argv.slice(2);
const python = process.env.HERMES_PYTHON || (process.platform === "win32" ? "python" : "python3");
const main = resolve(root, "app", "main.py");

function check() {
  const result = spawnSync(python, ["-c", "import streamlit; print(streamlit.__version__)"], { stdio: "pipe", encoding: "utf8" });
  if (result.status !== 0) {
    console.error(`Python/Streamlit indisponível. Instale as dependências com: ${python} -m pip install -r requirements.txt`);
    process.exit(1);
  }
  console.log(`Ambiente OK. Python: ${python}; Streamlit: ${result.stdout.trim()}`);
}

if (args.includes("--check")) check();
if (!existsSync(main)) {
  console.error(`Entrada não encontrada: ${main}`);
  process.exit(1);
}
if (args.includes("--check")) process.exit(0);
const port = process.env.HERMES_PORT || "3030";
const child = spawn(python, ["-m", "streamlit", "run", main, "--server.port", port, "--server.address", "localhost"], { cwd: root, stdio: "inherit", env: process.env });
child.on("exit", (code, signal) => process.exit(code ?? (signal ? 1 : 0)));
