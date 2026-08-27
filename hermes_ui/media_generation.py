"""Provider adapters for the independent image and video pools.

Adapters are intentionally small and response-shape tolerant: providers can return
base64, data URLs, direct URLs, or asynchronous task identifiers. The router owns
failover; this module owns provider-specific HTTP contracts.
"""

from __future__ import annotations

import base64
import binascii
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urljoin

import requests

from .media_providers import (
    INTERNAL_IMAGE_ASPECT_RATIO,
    INTERNAL_IMAGE_SIZE,
    INTERNAL_VIDEO_ASPECT_RATIO,
    INTERNAL_VIDEO_SIZE,
    media_cards_for_pool,
    media_provider_definition,
)
from .provider_routing import (
    POOL_IMAGE,
    POOL_VIDEO,
    ProviderCallError,
    ProviderRoutingError,
    route_json_request,
)
from .storage import STORAGE, ensure_storage
from .thumbnail_generation import generate_thumbnail_image


class MediaGenerationError(RuntimeError):
    """Raised when an image/video adapter cannot produce a usable artifact."""


def _api_key(card: Mapping[str, Any]) -> str:
    return str(card.get("api_key") or "").strip()


def _model(card: Mapping[str, Any]) -> str:
    return str(card.get("model") or "").strip()


def _base_url(card: Mapping[str, Any]) -> str:
    return str(card.get("base_url") or "").strip().rstrip("/")


def _headers(card: Mapping[str, Any], *, fal: bool = False) -> dict[str, str]:
    key = _api_key(card)
    provider = str(card.get("provider") or "").strip().lower()
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if key:
        if provider == "heygen":
            headers["X-Api-Key"] = key
        else:
            headers["Authorization"] = f"Key {key}" if fal else f"Bearer {key}"
    return headers


def _append_generation_constraints(
    prompt: str,
    *,
    kind: str,
    aspect_ratio: str = "",
    size: str = "",
) -> str:
    """Append controlled rendering constraints without exposing editable UI fields."""
    clean = str(prompt or "").strip()
    if kind == "image":
        ratio = str(aspect_ratio or INTERNAL_IMAGE_ASPECT_RATIO).strip()
        resolution = str(size or INTERNAL_IMAGE_SIZE).strip()
        constraints = f"Target image composition: {ratio} aspect ratio, {resolution} resolution."
    else:
        ratio = str(aspect_ratio or INTERNAL_VIDEO_ASPECT_RATIO).strip()
        resolution = str(size or INTERNAL_VIDEO_SIZE).strip()
        constraints = f"Target video composition: {ratio} aspect ratio, {resolution} resolution."
    if not clean:
        return constraints
    return f"{clean}\n\n{constraints}"


def _decode_data(value: Any) -> bytes | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.startswith("data:") and "," in raw:
        raw = raw.split(",", 1)[1]
    try:
        return base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError):
        return None


def _image_value(payload: Any) -> tuple[bytes | None, str]:
    if isinstance(payload, (bytes, bytearray)):
        return bytes(payload), ""
    if not isinstance(payload, Mapping):
        return None, ""
    direct = payload.get("image") or payload.get("output_image")
    if isinstance(direct, Mapping):
        direct = direct.get("data") or direct.get("url")
    data = _decode_data(direct)
    if data:
        return data, ""
    if isinstance(direct, str) and direct.startswith(("http://", "https://")):
        return None, direct
    entries = payload.get("data") or payload.get("outputs") or payload.get("images")
    if isinstance(entries, list) and entries:
        first = entries[0]
        if isinstance(first, Mapping):
            data = _decode_data(first.get("b64_json") or first.get("base64") or first.get("data"))
            if data:
                return data, ""
            url = str(first.get("url") or first.get("image_url") or "").strip()
            if url:
                return None, url
    output = payload.get("output")
    if isinstance(output, list) and output:
        output = output[0]
    if isinstance(output, Mapping):
        output = output.get("url") or output.get("image_url") or output.get("image")
    if isinstance(output, str):
        if output.startswith(("http://", "https://")):
            return None, output
        output_data = _decode_data(output)
        if output_data:
            return output_data, ""
    result = payload.get("result")
    if isinstance(result, Mapping):
        data = _decode_data(result.get("image") or result.get("b64_json") or result.get("data"))
        if data:
            return data, ""
        url = str(result.get("url") or result.get("image_url") or "").strip()
        if url:
            return None, url
    return None, ""


def _image_request_id(payload: Any) -> str:
    if not isinstance(payload, Mapping):
        return ""
    for key in ("id", "prediction_id", "request_id", "task_id", "job_id"):
        value = str(payload.get(key) or "").strip()
        if value:
            return value
    return ""


def _poll_image(card: Mapping[str, Any], request_id: str, *, attempts: int = 24, interval_seconds: float = 5.0) -> tuple[bytes | None, str]:
    """Resolve a Replicate image prediction without exposing its token."""
    style = str(card.get("api_style") or media_provider_definition(card.get("provider")).api_style)
    base = _base_url(card)
    endpoint = str(card.get("status_endpoint") or "").strip().replace("{id}", request_id)
    if not endpoint:
        if style != "replicate":
            return None, ""
        endpoint = f"{base}/predictions/{request_id}"
    for index in range(max(1, attempts)):
        try:
            response = requests.get(endpoint, headers=_headers(card), timeout=60)
            if response.status_code >= 400:
                raise MediaGenerationError(f"Consulta de imagem devolveu HTTP {response.status_code}.")
            payload = response.json()
        except requests.RequestException as exc:
            raise MediaGenerationError(f"Falha ao consultar a imagem: {str(exc)[:180]}") from exc
        image_bytes, url = _image_value(payload if isinstance(payload, Mapping) else {})
        if image_bytes or url:
            return image_bytes, url
        status = str((payload or {}).get("status") or "").lower() if isinstance(payload, Mapping) else ""
        if status in {"failed", "error", "cancelled", "canceled"}:
            raise MediaGenerationError("O provider marcou a tarefa de imagem como falhada.")
        if index + 1 < attempts:
            time.sleep(max(0.2, interval_seconds))
    raise MediaGenerationError("O provider de imagem não concluiu dentro do limite de polling.")


def _download_or_write(image_bytes: bytes | None, url: str, destination: Path, card: Mapping[str, Any]) -> Path:
    if image_bytes is None and url:
        try:
            response = requests.get(url, headers={"Authorization": f"Bearer {_api_key(card)}"} if _api_key(card) else {}, timeout=180)
            response.raise_for_status()
            image_bytes = response.content
        except requests.RequestException as exc:
            raise MediaGenerationError(f"Não foi possível descarregar a imagem devolvida pelo provider: {exc}") from exc
    if not image_bytes:
        raise MediaGenerationError("O provider concluiu a chamada mas não devolveu uma imagem utilizável.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(image_bytes)
    return destination


def _image_endpoint(card: Mapping[str, Any]) -> str:
    definition = media_provider_definition(card.get("provider"))
    style = str(card.get("api_style") or definition.api_style)
    base = _base_url(card)
    explicit = str(card.get("image_endpoint") or "").strip()
    if explicit:
        return explicit
    if style in {"openai_compatible", "huggingface", "agnes", "kie"}:
        return f"{base}/images/generations"
    if style == "replicate":
        return f"{base}/predictions"
    if style == "cloudflare":
        account_id = str(card.get("account_id") or "").strip()
        if not account_id:
            raise MediaGenerationError("Cloudflare Workers AI requer Account ID no cartão de media.")
        model = _model(card) or "@cf/stabilityai/stable-diffusion-xl-base-1.0"
        model = model if model.startswith("@") else f"@{model}"
        return f"{base}/accounts/{account_id}/ai/run/{model}"
    if style == "fal_queue":
        if not _model(card):
            raise MediaGenerationError("FAL AI requer o identificador da rota/modelo para gerar imagem.")
        return f"{base}/{_model(card).lstrip('/')}"
    if style == "dashscope":
        return f"{base}/services/aigc/text2image/image-synthesis"
    raise MediaGenerationError(f"O provider {card.get('provider')} não tem endpoint de imagem configurado.")


def _image_request(card: dict[str, Any], prompt: str) -> Any:
    provider = str(card.get("provider") or "").strip().lower()
    style = str(card.get("api_style") or media_provider_definition(provider).api_style)
    endpoint = _image_endpoint(card)
    constrained_prompt = _append_generation_constraints(
        prompt,
        kind="image",
        aspect_ratio=str(card.get("aspect_ratio") or ""),
        size=str(card.get("image_size") or ""),
    )
    if style == "cloudflare":
        return requests.post(endpoint, headers=_headers(card), json={"prompt": constrained_prompt}, timeout=180)
    if style == "fal_queue":
        return requests.post(endpoint, headers=_headers(card, fal=True), json={"prompt": constrained_prompt, "num_images": 1}, timeout=180)
    if style == "dashscope":
        body = {"model": _model(card), "input": {"prompt": constrained_prompt}, "parameters": {"n": 1}}
        return requests.post(endpoint, headers=_headers(card), json=body, timeout=180)
    if style == "replicate":
        body = {"version": _model(card), "input": {"prompt": constrained_prompt}}
        return requests.post(endpoint, headers=_headers(card), json=body, timeout=180)
    body = {"model": _model(card), "prompt": constrained_prompt, "n": 1, "response_format": "b64_json"}
    return requests.post(endpoint, headers=_headers(card), json=body, timeout=180)


def generate_image_for_card(
    settings: Mapping[str, Any],
    card: Mapping[str, Any],
    prompt: str,
    *,
    topic: str = "",
    variant_index: int = 0,
    lettering_text: str = "",
    lettering_prompt: str = "",
    reference_image: Path | None = None,
) -> Path:
    """Generate one image with the selected media card."""
    card = dict(card)
    provider = str(card.get("provider") or "").strip().lower()
    if provider == "nano_banana":
        merged = dict(settings)
        merged["gemini_image_api_key"] = _api_key(card)
        merged["gemini_image_model"] = _model(card) or merged.get("gemini_image_model") or "gemini-3.1-flash-image"
        merged["gemini_image_aspect_ratio"] = str(card.get("aspect_ratio") or INTERNAL_IMAGE_ASPECT_RATIO)
        merged["gemini_image_size"] = str(card.get("image_size") or INTERNAL_IMAGE_SIZE)
        try:
            return generate_thumbnail_image(
                merged,
                _append_generation_constraints(
                    prompt,
                    kind="image",
                    aspect_ratio=str(card.get("aspect_ratio") or ""),
                    size=str(card.get("image_size") or ""),
                ),
                topic=topic,
                variant_index=variant_index,
                lettering_text=lettering_text,
                lettering_prompt=lettering_prompt,
                reference_image=reference_image,
            )
        except Exception as exc:
            raise MediaGenerationError(str(exc)) from exc

    ensure_storage()
    destination = STORAGE / "thumbnails" / f"media-{provider}-{abs(hash((topic, prompt, variant_index))) & 0xffffffffffffffff:x}.jpg"

    def request(current: dict[str, Any]) -> Any:
        return _image_request(current, prompt)

    try:
        routed = route_json_request(settings, pool=POOL_IMAGE, cards=[card], request=request)
    except ProviderRoutingError as exc:
        raise MediaGenerationError(str(exc)) from exc
    image_bytes, url = _image_value(routed.payload)
    if not image_bytes and not url:
        request_id = _image_request_id(routed.payload)
        style = str(routed.card.get("api_style") or media_provider_definition(routed.card.get("provider")).api_style)
        if request_id and style == "replicate":
            image_bytes, url = _poll_image(routed.card, request_id)
    return _download_or_write(image_bytes, url, destination, routed.card)


def _is_retryable_media_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    if any(marker in text for marker in ("http 400", "http 401", "http 403", "http 404", "invalid request", "missing", "não tem endpoint")):
        return False
    return any(marker in text for marker in ("http 408", "http 425", "http 429", "http 500", "http 502", "http 503", "http 504", "timeout", "timed out", "connection", "temporarily", "cooldown"))


def generate_image_from_pool(
    settings: Mapping[str, Any],
    prompt: str,
    *,
    topic: str = "",
    variant_index: int = 0,
    lettering_text: str = "",
    lettering_prompt: str = "",
    reference_image: Path | None = None,
) -> Path:
    """Try eligible image cards in priority order, without cross-pool fallback."""
    cards = media_cards_for_pool(settings, "image")
    if not cards:
        raise MediaGenerationError("Não existem providers activos no pool de imagem.")
    errors: list[str] = []
    for card in cards:
        try:
            return generate_image_for_card(
                settings,
                card,
                prompt,
                topic=topic,
                variant_index=variant_index,
                lettering_text=lettering_text,
                lettering_prompt=lettering_prompt,
                reference_image=reference_image,
            )
        except MediaGenerationError as exc:
            errors.append(f"{card.get('provider')}: {str(exc)[:180]}")
            if not _is_retryable_media_error(exc):
                raise
    raise MediaGenerationError("Todos os providers do pool de imagem falharam: " + " | ".join(errors))


def _video_endpoint(card: Mapping[str, Any]) -> str:
    explicit = str(card.get("video_endpoint") or "").strip()
    if explicit:
        return explicit
    definition = media_provider_definition(card.get("provider"))
    style = str(card.get("api_style") or definition.api_style)
    base = _base_url(card)
    if style == "heygen":
        return f"{base}/v3/videos"
    if style == "fal_queue":
        if not _model(card):
            raise MediaGenerationError("FAL AI requer o identificador da rota/modelo para gerar vídeo.")
        return f"{base}/{_model(card).lstrip('/')}"
    if style in {"openai_compatible", "agnes", "kie"}:
        return f"{base}/videos/generations"
    if style == "replicate":
        return f"{base}/predictions"
    if style == "dashscope":
        return f"{base}/services/aigc/video-generation/video-synthesis"
    raise MediaGenerationError(f"O provider {card.get('provider')} não tem endpoint de vídeo configurado.")


def _video_request(card: dict[str, Any], prompt: str, image_url: str = "") -> Any:
    style = str(card.get("api_style") or media_provider_definition(card.get("provider")).api_style)
    endpoint = _video_endpoint(card)
    body: dict[str, Any] = {
        "model": _model(card),
        "prompt": _append_generation_constraints(
            prompt,
            kind="video",
            aspect_ratio=str(card.get("aspect_ratio") or ""),
            size=str(card.get("video_size") or ""),
        ),
    }
    if image_url:
        body["image_url"] = image_url
    if style == "heygen":
        avatar_id = str(card.get("avatar_id") or "").strip()
        if not avatar_id:
            raise MediaGenerationError("HeyGen requer Avatar ID no cartão de media para gerar vídeo.")
        heygen_body: dict[str, Any] = {
            "type": "avatar",
            "avatar_id": avatar_id,
            "script": body["prompt"],
            "aspect_ratio": str(card.get("aspect_ratio") or INTERNAL_VIDEO_ASPECT_RATIO),
            "output_format": "mp4",
        }
        voice_id = str(card.get("voice_id") or "").strip()
        if voice_id:
            heygen_body["voice_id"] = voice_id
        return requests.post(endpoint, headers=_headers(card), json=heygen_body, timeout=180)
    if style == "fal_queue":
        body.pop("model", None)
        return requests.post(endpoint, headers=_headers(card, fal=True), json=body, timeout=180)
    if style == "replicate":
        image_input_key = str(card.get("image_input_key") or "image").strip() or "image"
        input_payload = {"prompt": body["prompt"]}
        if image_url:
            input_payload[image_input_key] = image_url
        return requests.post(endpoint, headers=_headers(card), json={"version": _model(card), "input": input_payload}, timeout=180)
    return requests.post(endpoint, headers=_headers(card), json=body, timeout=180)


def _video_result(payload: Mapping[str, Any]) -> tuple[str, str]:
    raw_output = payload.get("output")
    if isinstance(raw_output, list) and raw_output:
        raw_output = raw_output[0]
    direct = str(payload.get("video_url") or payload.get("url") or raw_output or "").strip()
    if direct.startswith(("http://", "https://")):
        return direct, ""
    result = payload.get("result")
    if isinstance(result, Mapping):
        direct = str(result.get("video_url") or result.get("url") or result.get("output") or "").strip()
        if direct:
            return direct, ""
    for key in ("request_id", "id", "task_id", "job_id"):
        value = str(payload.get(key) or "").strip()
        if value:
            return "", value
    data = payload.get("data")
    if isinstance(data, Mapping):
        direct = str(data.get("video_url") or data.get("url") or "").strip()
        if direct.startswith(("http://", "https://")):
            return direct, ""
        for key in ("video_id", "id", "request_id", "task_id", "job_id"):
            value = str(data.get(key) or "").strip()
            if value:
                return "", value
    if isinstance(data, list) and data and isinstance(data[0], Mapping):
        first = data[0]
        direct = str(first.get("url") or first.get("video_url") or "").strip()
        if direct:
            return direct, ""
    return "", ""


def _poll_video(card: Mapping[str, Any], request_id: str, *, attempts: int = 24, interval_seconds: float = 5.0) -> str:
    definition = media_provider_definition(card.get("provider"))
    style = str(card.get("api_style") or definition.api_style)
    explicit_status = str(card.get("status_endpoint") or "").strip()
    base = _base_url(card)
    if explicit_status:
        endpoint = explicit_status.replace("{id}", request_id)
    elif style == "fal_queue":
        endpoint = f"{base}/requests/{request_id}/status"
    elif style == "replicate":
        endpoint = f"{base}/predictions/{request_id}"
    elif style == "heygen":
        endpoint = f"{base}/v3/videos/{request_id}"
    else:
        endpoint = f"{base}/videos/{request_id}"
    headers = _headers(card, fal=style == "fal_queue")
    for index in range(max(1, attempts)):
        try:
            response = requests.get(endpoint, headers=headers, timeout=60)
            if response.status_code >= 400:
                category = "quota" if response.status_code == 429 else "transient" if response.status_code >= 500 else "endpoint_or_model"
                raise ProviderCallError(f"Consulta de vídeo devolveu HTTP {response.status_code}.", status_code=response.status_code, category=category, retryable=category in {"quota", "transient"})
            payload = response.json()
        except requests.RequestException as exc:
            raise ProviderCallError(f"Falha ao consultar o vídeo: {str(exc)[:180]}", category="transient", retryable=True) from exc
        url, _ = _video_result(payload if isinstance(payload, Mapping) else {})
        if url:
            return url
        status_payload = payload.get("data") if isinstance(payload, Mapping) and isinstance(payload.get("data"), Mapping) else payload
        status = str((status_payload or {}).get("status") or "").lower() if isinstance(status_payload, Mapping) else ""
        if status in {"failed", "error", "cancelled", "canceled"}:
            if style == "heygen" and isinstance(status_payload, Mapping):
                code = str(status_payload.get("failure_code") or "").strip()
                detail = str(status_payload.get("failure_message") or "").strip()
                suffix = f" ({code})" if code else ""
                raise ProviderCallError(f"HeyGen marcou a tarefa como falhada{suffix}: {detail or 'sem detalhe'}", category="provider", retryable=False)
            raise ProviderCallError("O provider marcou a tarefa de vídeo como falhada.", category="provider", retryable=False)
        if index + 1 < attempts:
            time.sleep(max(0.2, interval_seconds))
    raise ProviderCallError("O provider de vídeo não concluiu dentro do limite de polling.", category="transient", retryable=True)


def generate_video_for_card(
    settings: Mapping[str, Any],
    card: Mapping[str, Any],
    prompt: str,
    *,
    image_url: str = "",
    output_path: Path | None = None,
) -> Path:
    """Submit and resolve one video generation request."""
    card = dict(card)
    provider = str(card.get("provider") or "").strip().lower()

    def request(current: dict[str, Any]) -> Any:
        return _video_request(current, prompt, image_url=image_url)

    try:
        routed = route_json_request(settings, pool=POOL_VIDEO, cards=[card], request=request)
    except ProviderRoutingError as exc:
        raise MediaGenerationError(str(exc)) from exc
    url, request_id = _video_result(routed.payload)
    if not url and request_id:
        try:
            url = _poll_video(routed.card, request_id)
        except ProviderCallError as exc:
            raise MediaGenerationError(str(exc)) from exc
    if not url:
        raise MediaGenerationError(f"O provider {provider} não devolveu URL nem identificador de vídeo.")
    destination = output_path or (STORAGE / "videos" / f"media-{provider}-{abs(hash((prompt, url))) & 0xffffffffffffffff:x}.mp4")
    try:
        response = requests.get(url, headers=_headers(routed.card), timeout=300)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise MediaGenerationError(f"Não foi possível descarregar o vídeo gerado: {exc}") from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)
    return destination


def generate_video_from_pool(
    settings: Mapping[str, Any],
    prompt: str,
    *,
    image_url: str = "",
    output_path: Path | None = None,
    allowed_providers: set[str] | None = None,
) -> Path:
    """Try eligible video cards in priority order, optionally restricted to a route."""
    cards = media_cards_for_pool(settings, "video")
    if allowed_providers is not None:
        allowed = {str(provider).strip().lower() for provider in allowed_providers}
        cards = [card for card in cards if str(card.get("provider") or "").strip().lower() in allowed]
    if not cards:
        raise MediaGenerationError("Não existem providers activos no pool de vídeo.")
    errors: list[str] = []
    for card in cards:
        try:
            return generate_video_for_card(settings, card, prompt, image_url=image_url, output_path=output_path)
        except MediaGenerationError as exc:
            errors.append(f"{card.get('provider')}: {str(exc)[:180]}")
            if not _is_retryable_media_error(exc):
                raise
    raise MediaGenerationError("Todos os providers do pool de vídeo falharam: " + " | ".join(errors))
