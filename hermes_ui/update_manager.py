"""Verificação e actualização local da versão distribuída pelo NPM.

O módulo não recebe nem manipula credenciais. A instalação só é iniciada após o
clique explícito do utilizador na interface local.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Callable

import requests


PACKAGE_NAME = "@danhachuel/thunderbolt"
REGISTRY_URL = "https://registry.npmjs.org/@danhachuel/thunderbolt/latest"
UPDATE_TIMEOUT_SECONDS = 20 * 60
LAUNCHER_RESTART_EXIT_CODE = 75


@dataclass(frozen=True)
class VersionCheck:
    """Version information displayed on the local home page."""

    current_version: str
    latest_version: str = ""
    error: str = ""

    @property
    def update_available(self) -> bool:
        latest_key = _version_key(self.latest_version)
        current_key = _version_key(self.current_version)
        if latest_key is not None and current_key is not None:
            return latest_key > current_key
        return bool(self.latest_version and self.current_version and self.latest_version != self.current_version)


def _version_key(value: str) -> tuple[int, int, int] | None:
    """Return a numeric SemVer core so zero-padded patches compare correctly."""
    raw = str(value or "").strip().lstrip("v")
    core = raw.split("+", 1)[0].split("-", 1)[0]
    parts = core.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


@dataclass(frozen=True)
class UpdateResult:
    """Sanitised result of an explicit local package update request."""

    ok: bool
    latest_version: str = ""
    message: str = ""
    restart_required: bool = False


def restart_current_process(*, exec_fn: Callable[..., Any] = os.execv, exit_fn: Callable[[int], Any] = os._exit) -> None:
    """Ask the launcher to restart Streamlit, or re-exec standalone callers."""
    if os.environ.get("THUNDERBOLT_LAUNCHER_RESTART") == "1":
        exit_fn(LAUNCHER_RESTART_EXIT_CODE)
        return
    executable = sys.executable
    exec_fn(executable, [executable, *sys.argv])


def latest_package_version(*, timeout: int = 8, get: Callable[..., Any] = requests.get) -> str:
    """Return the latest public package version without sending local configuration."""
    response = get(REGISTRY_URL, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    version = str(payload.get("version") or "").strip() if isinstance(payload, dict) else ""
    if not version:
        raise ValueError("O registry NPM não devolveu uma versão válida.")
    return version


def check_version(current_version: str, *, timeout: int = 8, get: Callable[..., Any] = requests.get) -> VersionCheck:
    """Fetch only the package metadata needed for the version badge."""
    current = str(current_version or "").strip()
    try:
        return VersionCheck(current_version=current, latest_version=latest_package_version(timeout=timeout, get=get))
    except (requests.RequestException, ValueError) as exc:
        return VersionCheck(current_version=current, error=f"Não foi possível verificar actualizações agora ({type(exc).__name__}).")


def update_command() -> list[str]:
    """Build the same cross-platform install command documented for Thunderbolt."""
    executable = "npx.cmd" if os.name == "nt" else "npx"
    return [executable, "--yes", "--prefer-online", PACKAGE_NAME, "install"]


def update_to_latest(
    current_version: str,
    *,
    timeout: int = UPDATE_TIMEOUT_SECONDS,
    get: Callable[..., Any] = requests.get,
    run: Callable[..., Any] = subprocess.run,
) -> UpdateResult:
    """Install the latest package only after an explicit UI action.

    The running local process keeps its current code until it is restarted. No
    subprocess output is returned to the UI, preventing accidental display of
    environment values from third-party installers.
    """
    status = check_version(current_version, get=get)
    if status.error:
        return UpdateResult(False, message=status.error)
    if not status.update_available:
        return UpdateResult(True, latest_version=status.latest_version, message="O Thunderbolt já está na versão mais recente.")
    try:
        completed = run(
            update_command(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return UpdateResult(False, latest_version=status.latest_version, message=f"Não foi possível concluir a actualização ({type(exc).__name__}).")
    if int(getattr(completed, "returncode", 1)) != 0:
        return UpdateResult(False, latest_version=status.latest_version, message="A actualização não foi concluída. Feche processos Thunderbolt em execução e tente novamente.")
    return UpdateResult(
        True,
        latest_version=status.latest_version,
        restart_required=True,
        message=(
            f"A versão {status.latest_version} foi instalada. Reinicie o Thunderbolt para abrir a versão nova; "
            "os dados e configurações locais foram preservados."
        ),
    )
