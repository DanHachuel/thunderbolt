from __future__ import annotations

import json
import re
import base64
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from . import storage
from .notifications import record_notification

MUSIC_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
VOICEOVER_EXTENSIONS = set(MUSIC_EXTENSIONS)


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
    record_notification(
        "music_completed",
        f"Música concluída: {target.stem}",
        f"O ficheiro de música {target.name} foi guardado no storage local.",
        metadata={"filename": target.name, "source": "local_storage"},
        dedupe_key=f"music:{target.name}:{target.stat().st_mtime_ns}",
    )
    return target


def voiceover_directory() -> Path:
    directory = storage.STORAGE / "voiceovers"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def safe_voiceover_name(name: str) -> str:
    stem = re.sub(r"[^\w\-. ]+", "_", Path(name).stem, flags=re.UNICODE).strip() or "voiceover"
    suffix = Path(name).suffix.lower()
    if suffix not in VOICEOVER_EXTENSIONS:
        suffix = ".mp3"
    return f"{stem}{suffix}"


def store_voiceover_file(name: str, content: bytes) -> Path:
    if not content:
        raise ValueError("O ficheiro de narração está vazio.")
    suffix = Path(name).suffix.lower()
    if suffix not in VOICEOVER_EXTENSIONS:
        allowed = ", ".join(sorted(VOICEOVER_EXTENSIONS))
        raise ValueError(f"Formato de narração não suportado: {suffix or '(sem extensão)'}. Use {allowed}.")
    target = voiceover_directory() / safe_voiceover_name(name)
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


def request_suno_generation(
    settings: dict[str, Any],
    prompt: str,
    title: str = "",
    duration_seconds: int = 120,
    *,
    make_instrumental: bool = True,
) -> dict[str, Any]:
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
    payload = {
        "prompt": prompt.strip(),
        "title": title.strip(),
        "duration": max(120, int(duration_seconds)),
        "make_instrumental": bool(make_instrumental),
    }
    try:
        response = requests.post(url, json=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, timeout=30)
        if response.status_code >= 400:
            return {"ok": False, "message": f"Suno devolveu HTTP {response.status_code}: {response.text[:240]}", "data": {"status_code": response.status_code}}
        body = response.json() if response.content else {}
        return {"ok": True, "message": "Pedido de música enviado ao endpoint Suno configurado.", "data": body if isinstance(body, dict) else {"response": body}}
    except (requests.RequestException, ValueError) as exc:
        return {"ok": False, "message": f"Não foi possível contactar o endpoint Suno configurado: {exc}", "data": {}}


def list_music_tasks() -> list[dict[str, Any]]:
    """Return only tasks created for the independent audio-generation queue."""
    records = storage.read_json("music_tasks.json", [])
    if not isinstance(records, list):
        return []
    return [dict(record) for record in records if isinstance(record, dict) and str(record.get("id") or "").strip()]


def _save_music_tasks(tasks: list[dict[str, Any]]) -> None:
    storage.write_json("music_tasks.json", tasks)


def create_music_task(
    provider: str,
    prompt: str,
    title: str,
    model: str = "",
    *,
    language: str = "",
    genre: str = "",
    vocal: str = "",
    references: str = "",
    theme: str = "",
    voice_id: str = "",
    voice_gender: str = "",
) -> dict[str, Any]:
    """Enqueue one audio-only generation; no video task or video worker is used."""
    cleaned_prompt = str(prompt or "").strip()
    if not cleaned_prompt:
        raise ValueError("Escreva um prompt musical antes de adicionar à fila.")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    task = {
        "id": f"music_{uuid.uuid4().hex[:12]}",
        "kind": "audio_generation",
        "provider": "lyria" if str(provider).strip().casefold() == "google lyria" else ("eleven_music" if str(provider).strip().casefold() == "eleven music" else "suno"),
        "model": str(model or "").strip(),
        "title": str(title or "Música sem título").strip() or "Música sem título",
        "prompt": cleaned_prompt,
        "language": str(language or "").strip(),
        "genre": str(genre or "").strip(),
        "vocal": str(vocal or "").strip(),
        "references": str(references or "").strip(),
        "theme": str(theme or "").strip(),
        "voice_id": str(voice_id or "").strip(),
        "voice_gender": str(voice_gender or "").strip().casefold(),
        "duration_seconds": 120,
        "state": "to_do",
        "stage": "music_generation",
        "progress": 0,
        "audio_path": "",
        "error": "",
        "created_at": now,
        "updated_at": now,
    }
    tasks = list_music_tasks()
    tasks.insert(0, task)
    _save_music_tasks(tasks)
    return task


def _update_music_task(task_id: str, **changes: Any) -> dict[str, Any] | None:
    tasks = list_music_tasks()
    updated: dict[str, Any] | None = None
    for task in tasks:
        if str(task.get("id") or "") == str(task_id):
            task.update(changes)
            task["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            updated = dict(task)
            break
    if updated is not None:
        _save_music_tasks(tasks)
    return updated


def transition_music_task(task_id: str, state: str) -> dict[str, Any] | None:
    """Change only an independent audio queue state."""
    if state not in {"to_do", "doing", "blocked", "done", "failed", "cancelled"}:
        raise ValueError("Estado de música inválido.")
    return _update_music_task(task_id, state=state)


def _extract_lyria_audio(payload: dict[str, Any]) -> bytes:
    """Extract a base64 audio block from Gemini Interactions without logging the payload."""
    candidates: list[Any] = []
    output_audio = payload.get("output_audio") if isinstance(payload, dict) else None
    if isinstance(output_audio, dict):
        candidates.append(output_audio.get("data"))
    for step in payload.get("steps", []) if isinstance(payload, dict) else []:
        if not isinstance(step, dict):
            continue
        content = step.get("content")
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and str(block.get("type") or "").casefold() == "audio":
                candidates.append(block.get("data"))
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            try:
                decoded = base64.b64decode(candidate, validate=True)
            except (ValueError, TypeError):
                continue
            if decoded:
                return decoded
    return b""


def request_lyria_generation(settings: dict[str, Any], prompt: str, title: str = "", model: str = "") -> dict[str, Any]:
    """Generate audio through Google Lyria's Interactions API without invoking video tooling."""
    api_key = str(settings.get("lyria_api_key") or settings.get("gemini_api_key") or "").strip()
    selected_model = str(model or settings.get("lyria_model") or "lyria-3-clip-preview").strip()
    if not api_key:
        return {"ok": False, "message": "Configure a Google Lyria API key em Configurações antes de solicitar uma música.", "data": {}}
    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/interactions",
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json={"model": selected_model, "input": str(prompt or "").strip()},
            timeout=180,
        )
        if response.status_code >= 400:
            return {"ok": False, "message": f"Google Lyria devolveu HTTP {response.status_code}.", "data": {"status_code": response.status_code}}
        body = response.json() if response.content else {}
        audio = _extract_lyria_audio(body if isinstance(body, dict) else {})
        if not audio:
            return {"ok": False, "message": "Google Lyria não devolveu áudio na resposta.", "data": {}}
        output = store_music_file(f"{title or 'lyria-generated'}.mp3", audio)
        return {"ok": True, "message": "Música gerada por Google Lyria.", "data": {"audio_path": str(output), "model": selected_model}}
    except (requests.RequestException, ValueError):
        return {"ok": False, "message": "Não foi possível contactar Google Lyria.", "data": {}}


def request_eleven_music_generation(settings: dict[str, Any], prompt: str, title: str = "", model: str = "music_v2", *, voice_id: str = "", voice_gender: str = "") -> dict[str, Any]:
    """Generate music through Eleven Music's synchronous Music API."""
    api_key = str(settings.get("elevenlabs_api_key") or "").strip()
    if not api_key:
        return {"ok": False, "message": "Configure a API Key do ElevenLabs em Configuração API antes de solicitar Eleven Music.", "data": {}}
    clean_prompt = str(prompt or "").strip()
    if voice_id:
        gender = voice_gender if voice_gender in {"male", "female"} else "unspecified"
        clean_prompt = f"{clean_prompt}\nVocal principal: voz personalizada ElevenLabs seleccionada ({gender}). Não usar coro."
    try:
        response = requests.post(
            "https://api.elevenlabs.io/v1/music",
            params={"output_format": "mp3_44100_128"},
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            json={"prompt": clean_prompt[:4100], "model_id": model or "music_v2", "force_instrumental": False},
            timeout=300,
        )
        if response.status_code >= 400:
            return {"ok": False, "message": f"Eleven Music devolveu HTTP {response.status_code}.", "data": {"status_code": response.status_code}}
        if not response.content:
            return {"ok": False, "message": "Eleven Music não devolveu áudio.", "data": {}}
        output = store_music_file(f"{title or 'eleven-music-generated'}.mp3", response.content)
        return {"ok": True, "message": "Música gerada por Eleven Music.", "data": {"audio_path": str(output), "model": model or "music_v2", "voice_id": voice_id, "voice_gender": voice_gender}}
    except (requests.RequestException, OSError, ValueError) as exc:
        return {"ok": False, "message": f"Não foi possível contactar Eleven Music: {exc}", "data": {}}


def run_music_task(task_id: str, settings: dict[str, Any]) -> dict[str, Any] | None:
    """Run exactly one queued audio generation and persist only its audio artefact."""
    task = next((record for record in list_music_tasks() if str(record.get("id") or "") == str(task_id)), None)
    if not task:
        return None
    _update_music_task(task_id, state="doing", stage="music_generation", progress=15, error="")
    provider = str(task.get("provider") or "suno").casefold()
    if provider == "lyria":
        result = request_lyria_generation(settings, str(task.get("prompt") or ""), str(task.get("title") or ""), str(task.get("model") or ""))
        audio_path = str((result.get("data") or {}).get("audio_path") or "")
    elif provider == "eleven_music":
        result = request_eleven_music_generation(settings, str(task.get("prompt") or ""), str(task.get("title") or ""), str(task.get("model") or "music_v2"), voice_id=str(task.get("voice_id") or ""), voice_gender=str(task.get("voice_gender") or ""))
        audio_path = str((result.get("data") or {}).get("audio_path") or "")
    else:
        result = request_suno_generation(
            settings,
            str(task.get("prompt") or ""),
            str(task.get("title") or ""),
            int(task.get("duration_seconds") or 120),
            make_instrumental=not bool(str(task.get("vocal") or "").strip()),
        )
        try:
            output = materialize_suno_audio(result.get("data") or {}, str(task.get("title") or "suno-generated.mp3")) if result.get("ok") else None
            audio_path = str(output or "")
        except (OSError, requests.RequestException, ValueError):
            audio_path = ""
            result = {"ok": False, "message": "A música Suno foi solicitada, mas não foi possível guardar o áudio devolvido.", "data": {}}
    if result.get("ok") and audio_path:
        completed = _update_music_task(task_id, state="done", stage="completed", progress=100, audio_path=audio_path, error="")
        record_notification("music_completed", f"Música concluída: {task.get('title') or 'Música'}", "Áudio guardado no Music Backlog.", metadata={"task_id": task_id, "provider": provider, "filename": Path(audio_path).name}, dedupe_key=f"music-task:{task_id}:{audio_path}")
        return completed
    return _update_music_task(task_id, state="failed", stage="failed", progress=100, error=str(result.get("message") or "A geração musical falhou.")[:500])
