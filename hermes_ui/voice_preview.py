from __future__ import annotations

import asyncio
import base64
import inspect
import json
import uuid
from pathlib import Path
from typing import Any

import requests

from . import storage

DEFAULT_SAMPLE = "Esta é uma amostra de voz do Thunderbolt. O resultado é apenas um teste e não altera nenhum vídeo ou tarefa da pipeline."


def preview_directory() -> Path:
    directory = storage.STORAGE / "voice_previews"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _edge_voice_name(value: str) -> str:
    return str(value or "en-US-AriaNeural-Female").split("-Female", 1)[0].split("-Male", 1)[0]


async def _save_edge_async(text: str, voice: str, output: Path, rate: str) -> None:
    import edge_tts

    kwargs: dict[str, Any] = {"rate": rate}
    if "boundary" in inspect.signature(edge_tts.Communicate).parameters:
        kwargs["boundary"] = "WordBoundary"
    communicate = edge_tts.Communicate(text, _edge_voice_name(voice), **kwargs)
    if hasattr(communicate, "save"):
        result = communicate.save(str(output))
        if inspect.isawaitable(result):
            await result
        return
    raise RuntimeError("A versão instalada de edge-tts não possui save().")


def _save_edge(text: str, voice: str, output: Path, rate: str) -> None:
    asyncio.run(_save_edge_async(text, voice, output, rate))


def _save_azure_speech(text: str, voice: str, output: Path, settings: dict[str, Any], rate: str) -> None:
    key = str(settings.get("azure_speech_key", "") or "").strip()
    region = str(settings.get("azure_speech_region", "") or "").strip()
    if not key or not region:
        raise RuntimeError("Configure Azure Speech key e região antes de testar Azure Speech.")
    endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    ssml = f"<speak version='1.0' xml:lang='pt-BR'><voice name='{_edge_voice_name(voice)}'><prosody rate='{rate}'>{text}</prosody></voice></speak>"
    response = requests.post(endpoint, data=ssml.encode("utf-8"), headers={"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/ssml+xml", "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3"}, timeout=45)
    response.raise_for_status()
    output.write_bytes(response.content)


def _save_openai_compatible(text: str, voice: str, output: Path, settings: dict[str, Any], provider: str) -> None:
    if provider == "elevenlabs":
        api_key = str(settings.get("elevenlabs_api_key", "") or "").strip()
        base = "https://api.elevenlabs.io/v1/text-to-speech"
        voice_id = voice.split("|", 1)[-1] if "|" in voice else voice
        endpoint = f"{base}/{voice_id or '21m00Tcm4TlvDq8ikWAM'}"
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        payload = {"text": text, "model_id": settings.get("elevenlabs_model_id", "eleven_multilingual_v2")}
    elif provider == "minimax":
        api_key = str(settings.get("minimax_tts_api_key", "") or "").strip()
        endpoint = str(settings.get("minimax_tts_base_url", "") or "").strip().rstrip("/")
        endpoint = f"{endpoint}/v1/t2a_v2" if endpoint and not endpoint.endswith("/t2a_v2") else endpoint
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": settings.get("minimax_tts_model_id", "speech-2.8-hd"), "text": text, "voice_setting": {"voice_id": voice or settings.get("minimax_tts_voice_id", "English_expressive_narrator"), "speed": 1, "vol": 1, "pitch": 0}}
    else:
        api_key = str(settings.get(f"{provider}_tts_api_key", "") or settings.get(f"{provider}_api_key", "") or "").strip()
        endpoint = str(settings.get(f"{provider}_tts_base_url", "") or settings.get(f"{provider}_base_url", "") or "").strip().rstrip("/")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": settings.get(f"{provider}_model_id", settings.get(f"{provider}_model_name", "")), "input": text, "voice": voice}
    if not api_key or not endpoint:
        raise RuntimeError(f"Configure a API key e o endpoint de {provider} antes do teste.")
    response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        body = response.json()
        audio = body.get("audio") or body.get("audio_base64") or body.get("data")
        if isinstance(audio, dict):
            audio = audio.get("audio") or audio.get("url")
        if isinstance(audio, str) and audio.startswith("http"):
            audio_response = requests.get(audio, timeout=60)
            audio_response.raise_for_status()
            output.write_bytes(audio_response.content)
        elif isinstance(audio, str):
            output.write_bytes(base64.b64decode(audio))
        else:
            raise RuntimeError("O provider devolveu JSON sem áudio reconhecível.")
    else:
        output.write_bytes(response.content)


def synthesize_preview(text: str, provider: str, voice: str, settings: dict[str, Any], rate: str = "+0%") -> Path:
    text = (text or "").strip()
    if not text:
        raise ValueError("Introduza um texto para testar a voz.")
    if len(text) > 1000:
        raise ValueError("O texto de teste deve ter no máximo 1000 caracteres.")
    provider = provider.lower().strip()
    extension = ".mp3"
    output = preview_directory() / f"voice-preview-{uuid.uuid4().hex[:10]}{extension}"
    if provider in {"edge", "azure_v1"}:
        _save_edge(text, voice, output, rate)
    elif provider == "azure_speech":
        _save_azure_speech(text, voice, output, settings, rate)
    elif provider in {"elevenlabs", "minimax", "siliconflow", "gemini", "chatterbox"}:
        _save_openai_compatible(text, voice, output, settings, provider)
    else:
        raise ValueError(f"Provider de preview não suportado: {provider}")
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("O provider não gerou um ficheiro de áudio válido.")
    return output
