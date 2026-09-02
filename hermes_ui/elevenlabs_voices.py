"""ElevenLabs personal voice catalogue with local, credential-safe caching."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable

import requests

from . import storage

CACHE_FILENAME = "elevenlabs_voices.json"
DEFAULT_CACHE_TTL_SECONDS = 6 * 60 * 60
VOICES_ENDPOINT = "https://api.elevenlabs.io/v1/voices"


class ElevenLabsVoicesError(RuntimeError):
    """A safe, user-facing error raised while reading the ElevenLabs catalogue."""


def cache_path() -> Path:
    return storage.STATE / CACHE_FILENAME


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalise_voice(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    voice_id = str(item.get("voice_id") or "").strip()
    category = str(item.get("category") or "").strip().casefold()
    name = str(item.get("name") or "").strip()
    if not voice_id or not name or category != "personal":
        return None
    labels = item.get("labels") if isinstance(item.get("labels"), dict) else {}
    samples = item.get("samples") if isinstance(item.get("samples"), list) else []
    return {
        "voice_id": voice_id,
        "name": name,
        "category": "personal",
        "labels": {str(key): str(value) for key, value in labels.items()},
        "samples": [sample for sample in samples if isinstance(sample, dict)],
    }


def normalise_voices(payload: Any) -> list[dict[str, Any]]:
    items = payload.get("voices", []) if isinstance(payload, dict) else []
    if not isinstance(items, list):
        raise ElevenLabsVoicesError("A API ElevenLabs devolveu uma lista de vozes inválida.")
    result = [_normalise_voice(item) for item in items]
    return [item for item in result if item is not None]


def _read_cache() -> dict[str, Any] | None:
    payload = storage.read_json(CACHE_FILENAME, {})
    return payload if isinstance(payload, dict) and isinstance(payload.get("voices"), list) else None


def _cache_is_fresh(cache: dict[str, Any], ttl_seconds: int) -> bool:
    try:
        updated = datetime.fromisoformat(str(cache.get("updated_at")).replace("Z", "+00:00"))
        return (_utc_now() - updated).total_seconds() < ttl_seconds
    except (TypeError, ValueError, OverflowError):
        return False


def _save_cache(voices: list[dict[str, Any]], *, source: str) -> dict[str, Any]:
    payload = {"updated_at": _utc_now().isoformat(), "source": source, "voices": voices}
    storage.write_json(CACHE_FILENAME, payload)
    return payload


def fetch_personal_voices(
    settings: dict[str, Any],
    *,
    force: bool = False,
    ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
    request_get: Callable[..., Any] = requests.get,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return personal voices, using cache unless force is requested."""
    cache = _read_cache()
    if cache and not force and _cache_is_fresh(cache, ttl_seconds):
        return list(cache["voices"]), {"source": "cache", "updated_at": cache.get("updated_at")}

    api_key = str(settings.get("elevenlabs_api_key") or "").strip()
    if not api_key:
        if cache:
            return list(cache["voices"]), {"source": "cache", "updated_at": cache.get("updated_at"), "stale": True}
        raise ElevenLabsVoicesError("Configure a API Key do ElevenLabs em Configuração API antes de actualizar as vozes.")
    try:
        response = request_get(VOICES_ENDPOINT, headers={"xi-api-key": api_key}, timeout=30)
        status = int(getattr(response, "status_code", 200))
        if status == 401:
            raise ElevenLabsVoicesError("A API Key do ElevenLabs foi recusada. Confirme a chave em Configuração API.")
        if status == 429:
            raise ElevenLabsVoicesError("O limite de pedidos do ElevenLabs foi atingido. Tente novamente mais tarde.")
        response.raise_for_status()
        voices = normalise_voices(response.json())
        saved = _save_cache(voices, source="elevenlabs_api")
        return voices, {"source": "api", "updated_at": saved["updated_at"]}
    except ElevenLabsVoicesError:
        if cache:
            return list(cache["voices"]), {"source": "cache", "updated_at": cache.get("updated_at"), "stale": True}
        raise
    except requests.Timeout as exc:
        if cache:
            return list(cache["voices"]), {"source": "cache", "updated_at": cache.get("updated_at"), "stale": True}
        raise ElevenLabsVoicesError("O ElevenLabs demorou demasiado tempo a responder. Tente novamente.") from exc
    except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
        if cache:
            return list(cache["voices"]), {"source": "cache", "updated_at": cache.get("updated_at"), "stale": True}
        raise ElevenLabsVoicesError("Não foi possível obter as vozes do ElevenLabs. Verifique a ligação e a API Key.") from exc


def personal_voice_options(settings: dict[str, Any]) -> dict[str, str]:
    """Return voice_id -> display label without contacting the remote API."""
    cache = _read_cache()
    if not cache:
        return {}
    return {
        str(voice["voice_id"]): f"{voice.get('name', voice['voice_id'])} · ElevenLabs personal"
        for voice in cache.get("voices", [])
        if isinstance(voice, dict) and voice.get("voice_id")
    }
