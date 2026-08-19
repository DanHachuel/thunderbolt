from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from . import storage


SKILL_FILENAME = "moneyprinterturbo-video.md"

MCP_DEFAULTS: list[dict[str, Any]] = [
    {
        "id": "short-video-maker",
        "name": "Short Video Maker",
        "repository": "https://github.com/gyoridavid/short-video-maker",
        "protocol": "MCP + REST",
        "description": "Servidor externo para criação de vídeos curtos, com MCP e API REST.",
        "port": 3123,
        "active": False,
        "endpoint_note": "Porta documentada pelo projecto: 3123.",
    },
    {
        "id": "autovio",
        "name": "AutoVio",
        "repository": "https://github.com/Auto-Vio/autovio",
        "protocol": "MCP + REST",
        "description": "Pipeline externo de vídeo com API REST e servidor MCP separado.",
        "port": 3001,
        "active": False,
        "endpoint_note": "Porta padrão da API backend documentada pelo projecto: 3001.",
    },
    {
        "id": "openmontage",
        "name": "OpenMontage",
        "repository": "https://github.com/calesthio/OpenMontage",
        "protocol": "Agente local",
        "description": "Sistema externo de produção agentic de vídeo; o README não documenta um servidor MCP/HTTP padrão.",
        "port": 8000,
        "active": False,
        "endpoint_note": "Porta editável de referência; o projecto não documenta uma porta local padrão.",
    },
    {
        "id": "opencut",
        "name": "OpenCut",
        "repository": "https://github.com/opencut-app/opencut",
        "protocol": "API em desenvolvimento",
        "description": "Editor externo; o README actual indica API/MCP em desenvolvimento e documenta um servidor API local.",
        "port": 8787,
        "active": False,
        "endpoint_note": "Porta padrão da API documentada pelo projecto: 8787; frontend usa 5173.",
    },
]


def _merge_defaults(saved: Any) -> list[dict[str, Any]]:
    saved_by_id = {
        str(item.get("id")): item
        for item in (saved if isinstance(saved, list) else [])
        if isinstance(item, dict) and item.get("id")
    }
    merged: list[dict[str, Any]] = []
    for default in MCP_DEFAULTS:
        item = {**default, **saved_by_id.get(default["id"], {})}
        try:
            item["port"] = max(1, min(65535, int(item.get("port", default["port"]))))
        except (TypeError, ValueError):
            item["port"] = default["port"]
        item["active"] = bool(item.get("active", False))
        merged.append(item)
    return merged


def load_integrations() -> list[dict[str, Any]]:
    return _merge_defaults(storage.read_json("mcp_integrations.json", MCP_DEFAULTS))


def save_integrations(integrations: list[dict[str, Any]]) -> None:
    cleaned: list[dict[str, Any]] = []
    allowed = {item["id"] for item in MCP_DEFAULTS}
    for item in integrations:
        if not isinstance(item, dict) or item.get("id") not in allowed:
            continue
        copy = dict(item)
        try:
            copy["port"] = max(1, min(65535, int(copy.get("port", 1))))
        except (TypeError, ValueError):
            continue
        copy["active"] = bool(copy.get("active", False))
        cleaned.append(copy)
    storage.write_json("mcp_integrations.json", _merge_defaults(cleaned))


def update_integration(integration_id: str, **updates: Any) -> list[dict[str, Any]]:
    integrations = load_integrations()
    for item in integrations:
        if item.get("id") == integration_id:
            item.update(updates)
            break
    save_integrations(integrations)
    return load_integrations()


def detect_local_service(integration: dict[str, Any], timeout: float = 0.35) -> dict[str, Any]:
    """Detecta apenas um serviço local já iniciado; nunca inicia ou instala processos."""
    port = integration.get("port")
    try:
        port = int(port)
    except (TypeError, ValueError):
        return {"available": False, "message": "Porta inválida."}
    try:
        response = requests.get(f"http://127.0.0.1:{port}/", timeout=timeout)
        return {
            "available": True,
            "message": f"Serviço respondeu em localhost:{port} (HTTP {response.status_code}).",
        }
    except requests.RequestException:
        return {"available": False, "message": f"Nenhum serviço detectado em localhost:{port}."}


def skill_source_path() -> Path:
    return Path(__file__).resolve().parents[1] / "seed" / "skills" / SKILL_FILENAME


def skill_destination_path() -> Path:
    return storage.STORAGE / "skills" / SKILL_FILENAME


def install_skill_locally(*, overwrite: bool = True) -> Path:
    source = skill_source_path()
    if not source.exists():
        raise FileNotFoundError("A skill MoneyPrinterTurbo não está disponível no pacote local.")
    destination = skill_destination_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if overwrite or not destination.exists():
        destination.write_bytes(source.read_bytes())
    return destination


def read_packaged_skill() -> bytes:
    source = skill_source_path()
    if not source.exists():
        raise FileNotFoundError("A skill MoneyPrinterTurbo não está disponível no pacote local.")
    return source.read_bytes()
