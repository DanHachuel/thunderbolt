from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import requests

from . import storage

MUSIC_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}


def music_directory() -> Path:
    directory = storage.STORAGE / "music"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def list_music_files() -> list[Path]:
    return sorted((path for path in music_directory().iterdir() if path.is_file() and path.suffix.lower() in MUSIC_EXTENSIONS), key=lambda path: path.stat().st_mtime, reverse=True)


def safe_music_name(name: str) -> str:
    stem = re.sub(r"[^\w\-. ]+", "_", Path(name).stem, flags=re.UNICODE).strip() or "music"
    suffix = Path(name).suffix.lower()
    if suffix not in MUSIC_EXTENSIONS:
        suffix = ".mp3"
    return f"{stem}{suffix}"


def store_music_file(name: str, content: bytes) -> Path:
    if not content:
        raise ValueError("O ficheiro de música está vazio.")
    target = music_directory() / safe_music_name(name)
    target.write_bytes(content)
    return target


def materialize_suno_audio(data: dict[str, Any], title: str = "suno-generated.mp3") -> Path | None:
    candidates: list[str] = []
    for key in ("audio_url", "audioUrl", "download_url", "downloadUrl", "url"):
        value = data.get(key) if isinstance(data, dict) else None
        if isinstance(value, str) and value.startswith("http"):
            candidates.append(value)
    clips = data.get("clips") if isinstance(data, dict) else None
    if isinstance(clips, list):
        for clip in clips:
            if isinstance(clip, dict):
                for key in ("audio_url", "audioUrl", "download_url", "downloadUrl", "url"):
                    value = clip.get(key)
                    if isinstance(value, str) and value.startswith("http"):
                        candidates.append(value)
    if not candidates:
        return None
    response = requests.get(candidates[0], timeout=120)
    response.raise_for_status()
    return store_music_file(title, response.content)


def request_suno_generation(settings: dict[str, Any], prompt: str, title: str = "", duration_seconds: int = 120) -> dict[str, Any]:
    """Request music from a configured Suno-compatible endpoint.

    Suno-compatible deployments expose different endpoint paths; the UI therefore
    requires an explicit base URL and never invents a public credential or endpoint.
    """
    api_key = str(settings.get("suno_api_key", "") or "").strip()
    base_url = str(settings.get("suno_api_base_url", "") or "").strip().rstrip("/")
    endpoint = str(settings.get("suno_api_endpoint", "/api/generate") or "/api/generate").strip()
    if not api_key or not base_url:
        return {"ok": False, "message": "Configure Suno API Key e Suno API Base URL em Configurações antes de solicitar uma música.", "data": {}}
    url = endpoint if endpoint.startswith("http") else f"{base_url}/{endpoint.lstrip('/')}"
    payload = {"prompt": prompt.strip(), "title": title.strip(), "duration": max(120, int(duration_seconds)), "make_instrumental": True}
    try:
        response = requests.post(url, json=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, timeout=30)
        if response.status_code >= 400:
            return {"ok": False, "message": f"Suno devolveu HTTP {response.status_code}: {response.text[:240]}", "data": {"status_code": response.status_code}}
        body = response.json() if response.content else {}
        return {"ok": True, "message": "Pedido de música enviado ao endpoint Suno configurado.", "data": body if isinstance(body, dict) else {"response": body}}
    except (requests.RequestException, ValueError) as exc:
        return {"ok": False, "message": f"Não foi possível contactar o endpoint Suno configurado: {exc}", "data": {}}
