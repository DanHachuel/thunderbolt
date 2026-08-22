import base64
import binascii
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import requests

from hermes_ui.storage import STORAGE, ensure_storage


GEMINI_INTERACTIONS_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
DEFAULT_GEMINI_IMAGE_MODEL = "gemini-3.1-flash-image"
DEFAULT_ASPECT_RATIO = "16:9"
DEFAULT_IMAGE_SIZE = "1K"
DEFAULT_MIME_TYPE = "image/jpeg"
DEFAULT_IMAGE_EXTENSION = ".jpg"


class ThumbnailGenerationError(RuntimeError):
    """Raised when Nano Banana cannot produce a thumbnail image."""


def _clean_detail(value: Any, api_key: str) -> str:
    detail = str(value or "").strip()[:600]
    return detail.replace(api_key, "[REDACTED]") if api_key else detail


def _decode_image_data(value: Any) -> bytes | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.startswith("data:") and "," in raw:
        raw = raw.split(",", 1)[1]
    try:
        data = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError):
        return None
    return data or None


def _image_from_content(content: Any) -> bytes | None:
    if not isinstance(content, dict) or content.get("type") != "image":
        return None
    return _decode_image_data(content.get("data"))


def _extract_image_bytes(payload: dict[str, Any]) -> bytes:
    """Extract the last inline image from an Interactions API response."""
    steps = payload.get("steps") or []
    for step in reversed(steps if isinstance(steps, list) else []):
        content = step.get("content") if isinstance(step, dict) else None
        for block in reversed(content if isinstance(content, list) else []):
            image = _image_from_content(block)
            if image:
                return image

    output_image = payload.get("output_image")
    image = _image_from_content(output_image)
    if image:
        return image

    outputs = payload.get("outputs")
    for output in reversed(outputs if isinstance(outputs, list) else []):
        image = _image_from_content(output)
        if image:
            return image

    raise ThumbnailGenerationError("O Gemini concluiu a interação, mas não devolveu uma imagem inline.")


def _thumbnail_filename(prompt: str, topic: str, variant_index: int, model: str) -> str:
    source = f"{model}\n{topic.strip()}\n{variant_index}\n{prompt.strip()}".encode("utf-8")
    digest = hashlib.sha256(source).hexdigest()[:20]
    return f"gemini-thumbnail-{digest}{DEFAULT_IMAGE_EXTENSION}"


def generate_thumbnail_image(
    settings: dict[str, Any],
    prompt: str,
    *,
    topic: str = "",
    variant_index: int = 0,
) -> Path:
    api_key = str(settings.get("gemini_image_api_key") or "").strip()
    if not api_key:
        raise ThumbnailGenerationError("Configure a API key Nano Banana em Configurações Técnicas > API Keys.")
    clean_prompt = str(prompt or "").strip()
    if not clean_prompt:
        raise ThumbnailGenerationError("A thumbnail não tem um prompt de imagem para gerar.")

    model = str(settings.get("gemini_image_model") or DEFAULT_GEMINI_IMAGE_MODEL).strip()
    aspect_ratio = str(settings.get("gemini_image_aspect_ratio") or DEFAULT_ASPECT_RATIO).strip()
    image_size = str(settings.get("gemini_image_size") or DEFAULT_IMAGE_SIZE).strip()
    body = {
        "model": model,
        "input": clean_prompt,
        "response_format": {
            "type": "image",
            "mime_type": DEFAULT_MIME_TYPE,
            "delivery": "inline",
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
        },
        "store": False,
    }
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    try:
        response = requests.post(
            GEMINI_INTERACTIONS_ENDPOINT,
            headers=headers,
            json=body,
            timeout=180,
        )
    except requests.RequestException as exc:
        raise ThumbnailGenerationError(f"Não foi possível contactar a API Nano Banana: {exc}") from exc
    if response.status_code >= 400:
        try:
            detail = response.json().get("error", response.text)
        except ValueError:
            detail = response.text
        raise ThumbnailGenerationError(f"A API Nano Banana devolveu HTTP {response.status_code}: {_clean_detail(detail, api_key)}")
    try:
        payload = response.json()
    except ValueError as exc:
        raise ThumbnailGenerationError("A API Nano Banana devolveu uma resposta que não é JSON.") from exc
    if str(payload.get("status") or "completed").lower() not in {"completed", "succeeded"}:
        raise ThumbnailGenerationError(f"A interação Nano Banana terminou com estado inesperado: {payload.get('status') or 'desconhecido'}.")
    image_bytes = _extract_image_bytes(payload)

    ensure_storage()
    output_dir = STORAGE / "thumbnails"
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / _thumbnail_filename(clean_prompt, topic, variant_index, model)
    fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=output_dir)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(image_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, destination)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return destination


__all__ = [
    "DEFAULT_ASPECT_RATIO",
    "DEFAULT_GEMINI_IMAGE_MODEL",
    "DEFAULT_IMAGE_SIZE",
    "GEMINI_INTERACTIONS_ENDPOINT",
    "ThumbnailGenerationError",
    "generate_thumbnail_image",
]
