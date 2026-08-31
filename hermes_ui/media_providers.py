"""Configuration schema for independent image and video provider pools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


MEDIA_CARDS_KEY = "media_provider_cards"
MEDIA_IMAGE_ACTIVE_CARD_KEY = "media_image_active_card_id"
MEDIA_VIDEO_ACTIVE_CARD_KEY = "media_video_active_card_id"
MEDIA_IMAGE_ACTIVE_PROVIDER_KEY = "media_image_provider"
MEDIA_VIDEO_ACTIVE_PROVIDER_KEY = "media_video_provider"

FULL_IA_VIDEO_PROVIDER_CODES = (
    "fal_ai",
    "kie_ai",
    "agnes",
    "nano_banana",
    "replicate",
    "pollinations",
    "huggingface",
    "inferenceport",
    "heygen",
)

# Mantidos internamente para preservar compatibilidade e controlar o prompt dos providers.
INTERNAL_IMAGE_ASPECT_RATIO = "16:9"
INTERNAL_IMAGE_SIZE = "1K"
INTERNAL_VIDEO_ASPECT_RATIO = "16:9"
INTERNAL_VIDEO_SIZE = "1080p"


@dataclass(frozen=True, slots=True)
class MediaProviderDefinition:
    code: str
    label: str
    default_base_url: str = ""
    requires_api_key: bool = True
    supports_image: bool = False
    supports_video: bool = False
    supports_text: bool = False
    local: bool = False
    api_style: str = "custom"
    extra_fields: tuple[str, ...] = ()
    description: str = ""


MEDIA_PROVIDER_CATALOG: tuple[MediaProviderDefinition, ...] = (
    MediaProviderDefinition(
        "nano_banana",
        "Nano Banana",
        default_base_url="https://generativelanguage.googleapis.com/v1beta",
        supports_image=True,
        api_style="gemini_interactions",
        description="Geração de imagem nativa Gemini para thumbnails e artes.",
    ),
    MediaProviderDefinition(
        "pollinations",
        "Pollinations.ai",
        default_base_url="https://gen.pollinations.ai/v1",
        supports_image=True,
        supports_video=True,
        supports_text=True,
        api_style="openai_compatible",
        description="Gateway multimodal com endpoints compatíveis e catálogo próprio.",
    ),
    MediaProviderDefinition(
        "replicate",
        "Replicate AI",
        default_base_url="https://api.replicate.com/v1",
        supports_image=True,
        supports_video=True,
        supports_text=False,
        api_style="replicate",
        description="Predictions assíncronas; o campo Modelo aceita model ou model:version conforme a Replicate.",
    ),
    MediaProviderDefinition(
        "agnes",
        "Agnes AI",
        default_base_url="https://apihub.agnes-ai.com/v1",
        supports_image=True,
        supports_video=True,
        supports_text=True,
        api_style="agnes",
        description="Gateway multimodal Agnes para texto, imagem e vídeo.",
    ),
    MediaProviderDefinition(
        "huggingface",
        "Hugging Face Inference API",
        default_base_url="https://router.huggingface.co/v1",
        supports_image=True,
        supports_text=True,
        api_style="huggingface",
        description="Inference Providers; a capacidade depende do modelo seleccionado.",
    ),
    MediaProviderDefinition(
        "cloudflare_workers_ai",
        "Cloudflare Workers AI",
        default_base_url="https://api.cloudflare.com/client/v4",
        supports_image=True,
        api_style="cloudflare",
        extra_fields=("account_id",),
        description="Workers AI com Account ID e API token; a rota de modelo é derivada.",
    ),
    MediaProviderDefinition(
        "inferenceport",
        "InferencePort Proxy",
        default_base_url="http://localhost:8080/v1",
        requires_api_key=False,
        supports_image=True,
        supports_video=True,
        supports_text=True,
        local=True,
        api_style="openai_compatible",
        description="Proxy local OpenAI-compatible; não exige API key por defeito.",
    ),
    MediaProviderDefinition(
        "alibaba_cloud",
        "阿里云 (Alibaba Cloud Model Studio)",
        default_base_url="https://dashscope-intl.aliyuncs.com/api/v1",
        supports_image=True,
        supports_video=True,
        supports_text=True,
        api_style="dashscope",
        extra_fields=("region",),
        description="DashScope/Model Studio; tarefas de imagem e vídeo podem ser assíncronas.",
    ),
    MediaProviderDefinition(
        "kie_ai",
        "KIE AI",
        default_base_url="https://api.kie.ai/api/v1",
        supports_image=True,
        supports_video=True,
        supports_text=True,
        api_style="kie",
        description="Gateway multimodal com tarefas e consulta de resultados.",
    ),
    MediaProviderDefinition(
        "fal_ai",
        "FAL AI",
        default_base_url="https://queue.fal.run",
        supports_image=True,
        supports_video=True,
        api_style="fal_queue",
        description="Model APIs da FAL com queue, status e resultado.",
    ),
    MediaProviderDefinition(
        "heygen",
        "HeyGen",
        default_base_url="https://api.heygen.com",
        supports_video=True,
        api_style="heygen",
        extra_fields=("avatar_id", "voice_id"),
        description="Vídeos com avatar, script ou áudio pela API V3 da HeyGen.",
    ),
)

_MEDIA_BY_CODE = {item.code: item for item in MEDIA_PROVIDER_CATALOG}


def media_provider_catalog() -> list[dict[str, Any]]:
    return [
        {
            "code": item.code,
            "label": item.label,
            "default_base_url": item.default_base_url,
            "requires_api_key": item.requires_api_key,
            "supports_image": item.supports_image,
            "supports_video": item.supports_video,
            "supports_text": item.supports_text,
            "local": item.local,
            "api_style": item.api_style,
            "extra_fields": item.extra_fields,
            "description": item.description,
        }
        for item in MEDIA_PROVIDER_CATALOG
    ]


def media_provider_definition(provider: Any) -> MediaProviderDefinition:
    code = str(provider or "").strip().lower()
    return _MEDIA_BY_CODE.get(code, _MEDIA_BY_CODE["inferenceport"])


def normalize_media_card(card: Any, index: int = 0) -> dict[str, Any]:
    source = dict(card) if isinstance(card, Mapping) else {}
    provider = str(source.get("provider") or "nano_banana").strip().lower()
    definition = media_provider_definition(provider)
    if provider not in _MEDIA_BY_CODE:
        provider = definition.code
    card_id = str(source.get("id") or f"media-{provider}-{index + 1}").strip()
    result: dict[str, Any] = {
        "id": card_id,
        "provider": provider,
        "api_key": str(source.get("api_key") or source.get("key") or "").strip(),
        "model": str(source.get("model") or source.get("model_name") or "").strip(),
        "base_url": str(source.get("base_url") or "").strip() or definition.default_base_url,
        "enabled": bool(source.get("enabled", True)),
        "priority": max(0, int(source.get("priority", index)) if str(source.get("priority", index)).strip().lstrip("-").isdigit() else index),
        "supports_image": bool(source.get("supports_image", definition.supports_image)),
        "supports_video": bool(source.get("supports_video", definition.supports_video)),
        "supports_text": bool(source.get("supports_text", definition.supports_text)),
        "api_style": definition.api_style,
        "local": definition.local,
    }
    for field in definition.extra_fields:
        result[field] = str(source.get(field) or "").strip()
    if provider == "nano_banana":
        result["aspect_ratio"] = str(source.get("aspect_ratio") or INTERNAL_IMAGE_ASPECT_RATIO).strip()
        result["image_size"] = str(source.get("image_size") or INTERNAL_IMAGE_SIZE).strip()
    test_result = source.get("test_result")
    if isinstance(test_result, Mapping) and str(test_result.get("status") or "") in {"success", "error"}:
        result["test_result"] = {
            "status": str(test_result.get("status")),
            "message": str(test_result.get("message") or "")[:240],
            "tested_at": str(test_result.get("tested_at") or "")[:64],
        }
    return result


def new_media_card(provider: Any, *, card_id: str | None = None) -> dict[str, Any]:
    code = str(provider or "").strip().lower()
    if code not in _MEDIA_BY_CODE:
        raise ValueError("Provider de imagem/vídeo inválido.")
    definition = _MEDIA_BY_CODE[code]
    return normalize_media_card(
        {
            "id": card_id or f"media-{code}-1",
            "provider": code,
            "model": "gemini-3.1-flash-image" if code == "nano_banana" else ("agnes-image-2.1-flash" if code == "agnes" else ""),
            "base_url": definition.default_base_url,
            "enabled": True,
        }
    )


def ensure_media_provider_cards(settings: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
    result = dict(settings)
    raw_cards = result.get(MEDIA_CARDS_KEY)
    changed = False
    if isinstance(raw_cards, list) and raw_cards:
        cards = [normalize_media_card(item, index) for index, item in enumerate(raw_cards)]
        changed = cards != raw_cards
    else:
        cards: list[dict[str, Any]] = []
        legacy_key = str(result.get("gemini_image_api_key") or "").strip()
        legacy_model = str(result.get("gemini_image_model") or "gemini-3.1-flash-image").strip()
        cards.append(
            normalize_media_card(
                {
                    "id": "media-nano-banana-default",
                    "provider": "nano_banana",
                    "api_key": legacy_key,
                    "model": legacy_model,
                    "base_url": "https://generativelanguage.googleapis.com/v1beta",
                    "aspect_ratio": str(result.get("gemini_image_aspect_ratio") or INTERNAL_IMAGE_ASPECT_RATIO),
                    "image_size": str(result.get("gemini_image_size") or INTERNAL_IMAGE_SIZE),
                    "enabled": True,
                },
                0,
            )
        )
        changed = True
    result[MEDIA_CARDS_KEY] = cards

    for pool, key, capability in (
        ("image", MEDIA_IMAGE_ACTIVE_CARD_KEY, "supports_image"),
        ("video", MEDIA_VIDEO_ACTIVE_CARD_KEY, "supports_video"),
    ):
        active_id = str(result.get(key) or "").strip()
        valid = [card for card in cards if card.get(capability) and card.get("enabled", True)]
        if active_id not in {str(card.get("id")) for card in cards} or not any(str(card.get("id")) == active_id and card.get(capability) and card.get("enabled", True) for card in cards):
            active_id = str(valid[0].get("id")) if valid else ""
            if result.get(key) != active_id:
                result[key] = active_id
                changed = True
        legacy_provider_key = MEDIA_IMAGE_ACTIVE_PROVIDER_KEY if pool == "image" else MEDIA_VIDEO_ACTIVE_PROVIDER_KEY
        active_card = next((card for card in cards if str(card.get("id")) == active_id), None)
        active_provider = str(active_card.get("provider") or "") if active_card else ""
        if result.get(legacy_provider_key) != active_provider:
            result[legacy_provider_key] = active_provider
            changed = True
    return result, changed


def apply_media_provider_cards_to_settings(settings: Mapping[str, Any], cards: list[Mapping[str, Any]], image_active_id: str = "", video_active_id: str = "") -> dict[str, Any]:
    result = dict(settings)
    normalized = [normalize_media_card(item, index) for index, item in enumerate(cards)]
    if not normalized:
        normalized = [new_media_card("nano_banana", card_id="media-nano-banana-default")]
    result[MEDIA_CARDS_KEY] = normalized
    for key, wanted, capability in (
        (MEDIA_IMAGE_ACTIVE_CARD_KEY, image_active_id, "supports_image"),
        (MEDIA_VIDEO_ACTIVE_CARD_KEY, video_active_id, "supports_video"),
    ):
        selected = next((card for card in normalized if str(card.get("id")) == str(wanted) and card.get(capability) and card.get("enabled", True)), None)
        if selected is None:
            selected = next((card for card in normalized if card.get(capability) and card.get("enabled", True)), None)
        result[key] = str(selected.get("id")) if selected else ""
    image_card = next((card for card in normalized if str(card.get("id")) == result[MEDIA_IMAGE_ACTIVE_CARD_KEY]), None)
    video_card = next((card for card in normalized if str(card.get("id")) == result[MEDIA_VIDEO_ACTIVE_CARD_KEY]), None)
    result[MEDIA_IMAGE_ACTIVE_PROVIDER_KEY] = str(image_card.get("provider") or "") if image_card else ""
    result[MEDIA_VIDEO_ACTIVE_PROVIDER_KEY] = str(video_card.get("provider") or "") if video_card else ""
    nano_card = next((card for card in normalized if card.get("provider") == "nano_banana"), None)
    if nano_card:
        result["gemini_image_api_key"] = str(nano_card.get("api_key") or "")
        result["gemini_image_model"] = str(nano_card.get("model") or "gemini-3.1-flash-image")
        result["gemini_image_aspect_ratio"] = str(nano_card.get("aspect_ratio") or result.get("gemini_image_aspect_ratio") or INTERNAL_IMAGE_ASPECT_RATIO)
        result["gemini_image_size"] = str(nano_card.get("image_size") or result.get("gemini_image_size") or INTERNAL_IMAGE_SIZE)
    return result


def media_cards_for_pool(settings: Mapping[str, Any], pool: str) -> list[dict[str, Any]]:
    migrated, _ = ensure_media_provider_cards(settings)
    capability = "supports_image" if pool == "image" else "supports_video" if pool == "video" else "supports_text"
    active_key = MEDIA_IMAGE_ACTIVE_CARD_KEY if pool == "image" else MEDIA_VIDEO_ACTIVE_CARD_KEY if pool == "video" else ""
    active_id = str(migrated.get(active_key) or "")
    cards = [dict(item) for item in migrated.get(MEDIA_CARDS_KEY, []) if item.get("enabled", True) and item.get(capability)]
    # A prioridade é o contrato principal do failover. O cartão activo legado
    # só serve de desempate entre cartões com a mesma prioridade, para não
    # ignorar uma escolha explícita do utilizador por causa de estado antigo.
    cards.sort(key=lambda card: (int(card.get("priority", 0)), 0 if str(card.get("id")) == active_id else 1))
    return cards
