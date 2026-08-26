"""Catálogo e compatibilidade dos cartões de providers LLM do Thunderbolt.

Este módulo não conhece Streamlit. Mantém o formato novo de cartões separado da UI,
conserva os campos legados usados pelo pipeline e centraliza a validação do estado.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from integrations.openai_model_discovery import (
    DEFAULT_NVIDIA_NIM_BASE_URL,
    OpenAICompatibleAPIError,
    fetch_openai_compatible_models,
    validate_openai_compatible_api_key,
)


LLM_CARDS_KEY = "llm_provider_cards"
LLM_ACTIVE_CARD_KEY = "llm_active_card_id"
LLM_TELEGRAM_CARD_KEY = "llm_telegram_card_id"
DEFAULT_LLM_PROVIDER = "openai"
DEFAULT_LLM_CARD_ID = "llm-openai-default"
DEFAULT_LLM_PRIORITY = 1


@dataclass(frozen=True, slots=True)
class LlmProviderDefinition:
    code: str
    label: str
    requires_api_key: bool = True
    show_base_url: bool = False
    default_base_url: str = ""
    local: bool = False
    supports_model_discovery: bool = True
    extra_fields: tuple[str, ...] = ()
    description: str = ""


# Só estão aqui providers que o adaptador OpenAI-compatible existente consegue
# consumir, ou que são explicitamente apresentados como locais/customizáveis. A
# lista é extensível sem alterar o schema dos cartões.
LLM_PROVIDER_CATALOG: tuple[LlmProviderDefinition, ...] = (
    LlmProviderDefinition(
        "openai",
        "OpenAI / NVIDIA NIM",
        show_base_url=True,
        default_base_url=DEFAULT_NVIDIA_NIM_BASE_URL,
        description="OpenAI ou NVIDIA NIM através do protocolo OpenAI-compatible.",
    ),
    LlmProviderDefinition("openrouter", "OpenRouter", default_base_url="https://openrouter.ai/api/v1"),
    LlmProviderDefinition("moonshot", "Moonshot / Kimi", default_base_url="https://api.moonshot.ai/v1"),
    LlmProviderDefinition("shengsuanyun", "Shengsuan Cloud", show_base_url=True),
    LlmProviderDefinition(
        "gemini",
        "Google Gemini",
        default_base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    ),
    LlmProviderDefinition("deepseek", "DeepSeek", default_base_url="https://api.deepseek.com"),
    LlmProviderDefinition("azure", "Azure OpenAI", show_base_url=True, extra_fields=("api_version",), description="Requer a Base URL do recurso Azure e a versão da API."),
    LlmProviderDefinition(
        "qwen",
        "Alibaba Qwen / DashScope",
        default_base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    ),
    LlmProviderDefinition("mistral", "Mistral", default_base_url="https://api.mistral.ai/v1"),
    LlmProviderDefinition("groq", "Groq", default_base_url="https://api.groq.com/openai/v1"),
    LlmProviderDefinition("grok", "xAI Grok", default_base_url="https://api.x.ai/v1"),
    LlmProviderDefinition("volcengine", "VolcEngine Ark", default_base_url="https://ark.cn-beijing.volces.com/api/v3"),
    LlmProviderDefinition("minimax", "MiniMax", default_base_url="https://api.minimax.io/v1"),
    LlmProviderDefinition("mimo", "Xiaomi MiMo", show_base_url=True),
    LlmProviderDefinition(
        "cloudflare",
        "Cloudflare Workers AI",
        show_base_url=False,
        supports_model_discovery=False,
        extra_fields=("account_id", "gateway_id"),
        description="Requer Account ID; o endpoint é construído pelo adaptador Cloudflare.",
    ),
    LlmProviderDefinition("modelscope", "ModelScope", show_base_url=True),
    LlmProviderDefinition("aihubmix", "AIHubMix", default_base_url="https://aihubmix.com/v1"),
    LlmProviderDefinition("aimlapi", "AIML API", default_base_url="https://api.aimlapi.com/v1"),
    LlmProviderDefinition("evolink", "EvoLink", default_base_url="https://api.evolink.ai/v1"),
    LlmProviderDefinition(
        "ollama",
        "Ollama",
        requires_api_key=False,
        show_base_url=True,
        default_base_url="http://127.0.0.1:11434/v1",
        local=True,
    ),
    LlmProviderDefinition(
        "lmstudio",
        "LM Studio",
        requires_api_key=False,
        show_base_url=True,
        default_base_url="http://127.0.0.1:1234/v1",
        local=True,
    ),
    LlmProviderDefinition(
        "llamacpp",
        "llama.cpp",
        requires_api_key=False,
        show_base_url=True,
        default_base_url="http://127.0.0.1:8080/v1",
        local=True,
    ),
    LlmProviderDefinition("oneapi", "OneAPI", show_base_url=True),
    LlmProviderDefinition("litellm", "LiteLLM Proxy", requires_api_key=False, show_base_url=True),
    LlmProviderDefinition(
        "pollinations",
        "Pollinations AI",
        requires_api_key=True,
        default_base_url="https://gen.pollinations.ai/v1",
    ),
    LlmProviderDefinition("together", "Together AI", default_base_url="https://api.together.ai/v1"),
    LlmProviderDefinition("fireworks", "Fireworks AI", default_base_url="https://api.fireworks.ai/inference/v1"),
    LlmProviderDefinition("siliconflow", "SiliconFlow", default_base_url="https://api.siliconflow.com/v1"),
    LlmProviderDefinition("cohere", "Cohere", default_base_url="https://api.cohere.ai/compatibility/v1"),
    LlmProviderDefinition("huggingface", "Hugging Face", default_base_url="https://router.huggingface.co/v1"),
    LlmProviderDefinition("github_models", "GitHub Models", default_base_url="https://models.github.ai/inference"),
    LlmProviderDefinition("cerebras", "Cerebras", default_base_url="https://api.cerebras.ai/v1"),
    LlmProviderDefinition("sambanova", "SambaNova", default_base_url="https://api.sambanova.ai/v1"),
    LlmProviderDefinition("perplexity", "Perplexity", default_base_url="https://api.perplexity.ai"),
    LlmProviderDefinition("openai_compatible", "OpenAI-compatible personalizado", show_base_url=True),
)

_PROVIDER_BY_CODE = {item.code: item for item in LLM_PROVIDER_CATALOG}
_PROVIDER_ALIASES = {
    "open_router": "openrouter",
    "xai": "grok",
    "google": "gemini",
    "google_gemini": "gemini",
    "azure_openai": "azure",
    "custom": "openai_compatible",
}
_LEGACY_PREFIX = {
    "openrouter": "openrouter",
    "openai_compatible": "openai",
    "github_models": "github_models",
}


def provider_definition(provider: Any) -> LlmProviderDefinition:
    code = normalize_provider_code(provider)
    return _PROVIDER_BY_CODE.get(code, _PROVIDER_BY_CODE["openai_compatible"])


def normalize_provider_code(provider: Any) -> str:
    value = str(provider or "").strip().lower().replace(" ", "_")
    return _PROVIDER_ALIASES.get(value, value or DEFAULT_LLM_PROVIDER)


def _legacy_prefix(provider: str) -> str:
    return _LEGACY_PREFIX.get(provider, provider)


def _legacy_value(settings: Mapping[str, Any], provider: str, suffix: str) -> str:
    prefix = _legacy_prefix(provider)
    return str(settings.get(f"{prefix}_{suffix}") or "").strip()


def _legacy_card(settings: Mapping[str, Any], provider: str, card_id: str, *, priority: int = DEFAULT_LLM_PRIORITY) -> dict[str, Any]:
    definition = provider_definition(provider)
    code = normalize_provider_code(provider)
    base_url = _legacy_value(settings, code, "base_url") or definition.default_base_url
    api_key = _legacy_value(settings, code, "api_key")
    model = _legacy_value(settings, code, "model_name")
    extra: dict[str, str] = {}
    if code == "cloudflare":
        extra = {
            "account_id": str(settings.get("cloudflare_account_id") or "").strip(),
            "gateway_id": str(settings.get("cloudflare_gateway_id") or "").strip(),
        }
    return {
        "id": card_id,
        "provider": code,
        "api_key": api_key,
        "model": model,
        "base_url": base_url,
        "enabled": True,
        "priority": max(1, int(priority)),
        "telegram_llm": False,
        **extra,
    }


def new_llm_card(provider: Any, *, card_id: str | None = None) -> dict[str, Any]:
    code = normalize_provider_code(provider)
    definition = provider_definition(code)
    return {
        "id": str(card_id or "llm-" + code),
        "provider": code,
        "api_key": "",
        "model": "",
        "base_url": definition.default_base_url,
        "enabled": True,
        "priority": DEFAULT_LLM_PRIORITY,
        "telegram_llm": False,
        **{field: "" for field in definition.extra_fields},
    }


def _clean_test_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    status = str(value.get("status") or "").strip().lower()
    if status not in {"success", "error"}:
        return {}
    return {
        "status": status,
        "message": str(value.get("message") or "")[:240],
        "tested_at": str(value.get("tested_at") or "")[:64],
    }


def _normalise_priority(value: Any, fallback: int = DEFAULT_LLM_PRIORITY) -> int:
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return max(1, int(fallback or DEFAULT_LLM_PRIORITY))


def normalize_llm_card(card: Any, index: int = 0) -> dict[str, Any]:
    source = dict(card) if isinstance(card, Mapping) else {}
    code = normalize_provider_code(source.get("provider") or source.get("provider_code"))
    definition = provider_definition(code)
    raw_id = str(source.get("id") or "").strip()
    card_id = raw_id or (DEFAULT_LLM_CARD_ID if code == "openai" and index == 0 else f"llm-{code}-{index + 1}")
    result: dict[str, Any] = {
        "id": card_id,
        "provider": code,
        "api_key": str(source.get("api_key") or source.get("key") or "").strip(),
        "model": str(source.get("model") or source.get("model_name") or "").strip(),
        "base_url": str(source.get("base_url") or "").strip() or definition.default_base_url,
        "enabled": bool(source.get("enabled", True)),
        "priority": _normalise_priority(source.get("priority", index + 1), index + 1),
        "telegram_llm": bool(source.get("telegram_llm", source.get("llm_telegram", False))),
    }
    for field in definition.extra_fields:
        result[field] = str(source.get(field) or "").strip()
    test_result = _clean_test_result(source.get("test_result"))
    if test_result:
        result["test_result"] = test_result
    return result


def _card_has_legacy_configuration(settings: Mapping[str, Any], provider: str) -> bool:
    definition = provider_definition(provider)
    values = [_legacy_value(settings, provider, "api_key"), _legacy_value(settings, provider, "model_name")]
    if definition.show_base_url:
        values.append(_legacy_value(settings, provider, "base_url"))
    values.extend(str(settings.get(f"{provider}_{field}") or "").strip() for field in definition.extra_fields)
    return any(values)


def ensure_llm_provider_cards(settings: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
    """Return settings with a stable card collection and legacy values untouched."""
    result = dict(settings) if isinstance(settings, Mapping) else {}
    raw_cards = result.get(LLM_CARDS_KEY)
    cards = [normalize_llm_card(item, index) for index, item in enumerate(raw_cards)] if isinstance(raw_cards, list) else []
    changed = not isinstance(raw_cards, list)

    selected_provider = normalize_provider_code(result.get("llm_provider") or DEFAULT_LLM_PROVIDER)
    legacy_selected_provider = selected_provider != DEFAULT_LLM_PROVIDER and _card_has_legacy_configuration(result, selected_provider)
    active_id = str(result.get(LLM_ACTIVE_CARD_KEY) or "").strip()

    # O primeiro card OpenAI/NVIDIA NIM é estrutural e nunca é removido pela migração.
    # Quando uma configuração legada apontava para outro provider, esse provider
    # recebe prioridade 1 e o cartão estrutural fica logo a seguir.
    if not any(card.get("provider") == DEFAULT_LLM_PROVIDER for card in cards):
        cards.insert(0, _legacy_card(result, DEFAULT_LLM_PROVIDER, DEFAULT_LLM_CARD_ID, priority=2 if legacy_selected_provider else 1))
        changed = True
    elif cards[0].get("provider") != DEFAULT_LLM_PROVIDER:
        openai_card = next(card for card in cards if card.get("provider") == DEFAULT_LLM_PROVIDER)
        cards.remove(openai_card)
        cards.insert(0, openai_card)
        changed = True

    if not str(result.get("llm_provider") or "").strip():
        result["llm_provider"] = DEFAULT_LLM_PROVIDER
        changed = True
    # A migração preserva uma configuração explícita antiga que ainda não tinha card.
    if legacy_selected_provider:
        if not any(card.get("provider") == selected_provider for card in cards):
            cards.append(_legacy_card(result, selected_provider, f"llm-{selected_provider}-legacy", priority=1))
            changed = True

    # Instalações anteriores só tinham um cartão activo. Transformamos essa
    # escolha na prioridade 1 uma única vez, sem apagar a preferência do utilizador.
    if isinstance(raw_cards, list) and not any(isinstance(item, Mapping) and "priority" in item for item in raw_cards):
        preferred_id = active_id or next((str(card.get("id")) for card in cards if card.get("provider") == selected_provider), "")
        if preferred_id:
            for card in cards:
                old_priority = int(card.get("priority", DEFAULT_LLM_PRIORITY))
                card["priority"] = 1 if str(card.get("id")) == preferred_id else max(2, old_priority)
            changed = True

    cards = _ordered_cards(cards)
    serialized_before = raw_cards if isinstance(raw_cards, list) else None
    if serialized_before != cards:
        changed = True
    result[LLM_CARDS_KEY] = cards

    ids = {str(card.get("id")) for card in cards}
    ordered = _ordered_cards(cards)
    first_enabled = next(
        (card for card in ordered if card.get("enabled", True) and not card.get("telegram_llm", False)),
        None,
    )
    desired_active_id = str(first_enabled["id"]) if first_enabled else ""
    if active_id != desired_active_id:
        result[LLM_ACTIVE_CARD_KEY] = desired_active_id
        changed = True
    if not any(card.get("telegram_llm") for card in cards):
        if result.get(LLM_TELEGRAM_CARD_KEY):
            result[LLM_TELEGRAM_CARD_KEY] = ""
            changed = True
    else:
        telegram_card = next(card for card in cards if card.get("telegram_llm"))
        if result.get(LLM_TELEGRAM_CARD_KEY) != telegram_card["id"]:
            result[LLM_TELEGRAM_CARD_KEY] = telegram_card["id"]
            changed = True
    return result, changed


def _ordered_cards(cards: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    indexed = [(index, normalize_llm_card(card, index)) for index, card in enumerate(cards)]
    indexed.sort(key=lambda pair: (pair[1].get("priority", pair[0] + 1), pair[0]))
    return [card for _index, card in indexed]


def llm_cards(settings: Mapping[str, Any]) -> list[dict[str, Any]]:
    migrated, _ = ensure_llm_provider_cards(settings)
    cards = migrated.get(LLM_CARDS_KEY, [])
    return _ordered_cards(cards) if isinstance(cards, list) else []


def active_llm_card(settings: Mapping[str, Any]) -> dict[str, Any]:
    migrated, _ = ensure_llm_provider_cards(settings)
    cards = migrated.get(LLM_CARDS_KEY, [])
    ordered = _ordered_cards(cards) if isinstance(cards, list) else []
    for card in ordered:
        if card.get("enabled", True) and not card.get("telegram_llm", False):
            return dict(card)
    return new_llm_card(DEFAULT_LLM_PROVIDER, card_id=DEFAULT_LLM_CARD_ID)


def telegram_llm_card(settings: Mapping[str, Any]) -> dict[str, Any] | None:
    for card in llm_cards(settings):
        if card.get("telegram_llm") and card.get("enabled", True):
            return card
    return None


def apply_llm_cards_to_settings(
    settings: Mapping[str, Any], cards: list[Mapping[str, Any]], active_card_id: str = ""
) -> dict[str, Any]:
    """Persist priority-ordered cards and mirror priority 1 to the legacy runtime contract."""
    result = dict(settings)
    normalized = [normalize_llm_card(item, index) for index, item in enumerate(cards)]
    if not normalized or not any(card.get("provider") == DEFAULT_LLM_PROVIDER for card in normalized):
        normalized.insert(0, _legacy_card(result, DEFAULT_LLM_PROVIDER, DEFAULT_LLM_CARD_ID))

    # Checkbox Telegram é exclusivo: o último card marcado vence e todos os outros
    # ficam desmarcados. O ID explícito torna o roteamento determinístico.
    telegram = next((card for card in reversed(normalized) if card.get("telegram_llm")), None)
    for card in normalized:
        card["telegram_llm"] = bool(telegram and card["id"] == telegram["id"])

    if active_card_id and not any(isinstance(item, Mapping) and "priority" in item for item in cards):
        for card in normalized:
            old_priority = int(card.get("priority", DEFAULT_LLM_PRIORITY))
            card["priority"] = 1 if str(card.get("id")) == str(active_card_id) else max(2, old_priority)
    ordered = _ordered_cards(normalized)
    normal_enabled = [card for card in ordered if card.get("enabled", True) and not card.get("telegram_llm", False)]
    active = normal_enabled[0] if normal_enabled else None
    result[LLM_CARDS_KEY] = normalized
    result[LLM_ACTIVE_CARD_KEY] = active["id"] if active else ""
    result[LLM_TELEGRAM_CARD_KEY] = telegram["id"] if telegram else ""
    result["llm_provider"] = active["provider"] if active else DEFAULT_LLM_PROVIDER

    if active:
        prefix = _legacy_prefix(str(active["provider"]))
        result[f"{prefix}_api_key"] = str(active.get("api_key") or "").strip()
        result[f"{prefix}_model_name"] = str(active.get("model") or "").strip()
        result[f"{prefix}_base_url"] = str(active.get("base_url") or "").strip()
        definition = provider_definition(active["provider"])
        for field in definition.extra_fields:
            result[f"{prefix}_{field}"] = str(active.get(field) or "").strip()
        if active.get("provider") == "cloudflare":
            result["cloudflare_account_id"] = str(active.get("account_id") or "").strip()
            result["cloudflare_gateway_id"] = str(active.get("gateway_id") or "").strip()
    return result


def _redact(text: Any, secrets: tuple[str, ...]) -> str:
    message = str(text or "")
    for secret in secrets:
        if secret:
            message = message.replace(secret, "[REDACTED]")
    return message[:240]


def test_llm_provider_card(card: Mapping[str, Any]) -> dict[str, Any]:
    """Perform a bounded provider check without returning secrets or raw exceptions."""
    normalized = normalize_llm_card(card)
    definition = provider_definition(normalized["provider"])
    api_key = str(normalized.get("api_key") or "").strip()
    base_url = str(normalized.get("base_url") or "").strip()
    secrets = (api_key,)
    if definition.requires_api_key and not api_key:
        return {"ok": False, "status": "error", "message": "Missing key — introduza a API key antes do teste."}
    if definition.show_base_url and not base_url:
        return {"ok": False, "status": "error", "message": "Missing configuration — introduza a Base URL antes do teste."}
    if not base_url:
        return {"ok": False, "status": "error", "message": "Missing configuration — este provider não tem endpoint configurado."}
    model = str(normalized.get("model") or "").strip()
    if not model:
        return {"ok": False, "status": "error", "message": "Missing configuration — introduza o modelo antes do teste."}
    try:
        validate_openai_compatible_api_key(api_key, base_url, model)
    except OpenAICompatibleAPIError as exc:
        return {
            "ok": False,
            "status": "error",
            "message": _redact(str(exc), secrets),
        }
    except Exception:
        return {"ok": False, "status": "error", "message": "A chamada de teste falhou de forma inesperada."}
    return {
        "ok": True,
        "status": "success",
        "message": "API Key OK",
    }


# This callable is a production diagnostic helper, not a pytest test function.
test_llm_provider_card.__test__ = False


def stamp_test_result(result: Mapping[str, Any]) -> dict[str, Any]:
    status = "success" if result.get("ok") else "error"
    return {
        "status": status,
        "message": str(result.get("message") or "")[:240],
        "tested_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
