from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
REFERENCES_DIR = ROOT / "seed" / "references"

REFERENCE_FILES = {
    "title_formulas": "title-formulas.md",
    "viral_titles": "viral-titles.md",
    "thumbnail_checklist": "thumbnail-checklist.md",
    "viral_thumbnails": "viral-thumbnails.md",
    "trend_intelligence": "trend-intelligence.md",
    "humanize": "humanize-integration.md",
    "ai_tells": "ai-tells.md",
}


class CreativeGenerationError(RuntimeError):
    """Raised when a configured LLM cannot produce a valid creative package."""


def _provider_config(settings: dict[str, Any]) -> tuple[str, str, str, str]:
    provider = str(settings.get("llm_provider") or "openai").strip().lower()
    key = str(settings.get(f"{provider}_api_key") or "").strip()
    base_url = str(settings.get(f"{provider}_base_url") or "").strip()
    model = str(settings.get(f"{provider}_model_name") or "").strip()
    if provider == "openai":
        base_url = base_url or "https://api.openai.com/v1"
    elif provider == "ollama":
        base_url = base_url or "http://127.0.0.1:11434/v1"
    if not base_url:
        raise CreativeGenerationError(
            f"O provider LLM '{provider}' não tem Base URL configurada em Configuração API > API Keys > Serviços e modelos."
        )
    if not model:
        raise CreativeGenerationError(
            f"O provider LLM '{provider}' não tem modelo configurado em Configuração API > API Keys > Serviços e modelos."
        )
    if provider not in {"ollama", "litellm"} and not key:
        raise CreativeGenerationError(
            f"Configure a API key do provider LLM '{provider}' em Configuração API > API Keys > Serviços e modelos."
        )
    return provider, key, base_url.rstrip("/"), model


@lru_cache(maxsize=1)
def reference_bundle() -> str:
    sections: list[str] = []
    for label, filename in REFERENCE_FILES.items():
        path = REFERENCES_DIR / filename
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        # Keep prompts bounded while preserving the concrete rules from the attachments.
        sections.append(f"[{label}]\n{content[:4200]}")
    return "\n\n".join(sections)


def _json_content(payload: dict[str, Any]) -> dict[str, Any]:
    choices = payload.get("choices") or []
    if not choices:
        raise CreativeGenerationError("O endpoint LLM devolveu uma resposta sem choices.")
    message = (choices[0] or {}).get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        content = "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
    text = str(content or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CreativeGenerationError("O endpoint LLM não devolveu JSON válido.") from exc
    if not isinstance(parsed, dict):
        raise CreativeGenerationError("A resposta do endpoint LLM não é um objecto JSON.")
    return parsed


def _chat_json(settings: dict[str, Any], system_prompt: str, user_prompt: str) -> dict[str, Any]:
    _provider, api_key, base_url, model = _provider_config(settings)
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    endpoint = f"{base_url}/chat/completions"
    try:
        response = requests.post(endpoint, headers=headers, json=body, timeout=120)
    except requests.RequestException as exc:
        raise CreativeGenerationError(f"Não foi possível contactar o provider LLM: {exc}") from exc
    if response.status_code >= 400:
        detail = response.text[:500].replace(api_key, "[REDACTED]") if api_key else response.text[:500]
        raise CreativeGenerationError(f"O provider LLM devolveu HTTP {response.status_code}: {detail}")
    try:
        payload = response.json()
    except ValueError as exc:
        raise CreativeGenerationError("O provider LLM devolveu uma resposta que não é JSON.") from exc
    return _json_content(payload)


def channel_context(channel: dict[str, Any], blueprint: dict[str, Any] | None = None) -> dict[str, Any]:
    blueprint = blueprint or {}
    metadata = blueprint.get("metadata") if isinstance(blueprint.get("metadata"), dict) else {}
    return {
        "channel_name": str(channel.get("name") or "Canal sem nome"),
        "handle": str(channel.get("handle") or ""),
        "description": str(channel.get("description") or ""),
        "language": str(channel.get("language") or "Português"),
        "style_wide": str(channel.get("style_wide") or "pexels"),
        "blueprint_id": str(blueprint.get("id") or channel.get("default_blueprint_id") or channel.get("blueprint_id") or ""),
        "blueprint_name": str(blueprint.get("name") or "SEM BLUEPRINT CONFIGURADO"),
        "blueprint_niche": str(blueprint.get("target_niche") or blueprint.get("niche") or metadata.get("target_niche") or metadata.get("niche") or ""),
        "default_voice": str(channel.get("default_voice") or channel.get("voice") or ""),
    }


def generate_topic_for_channel(
    settings: dict[str, Any],
    channel: dict[str, Any],
    blueprint: dict[str, Any] | None = None,
    user_context: str = "",
) -> dict[str, Any]:
    context = channel_context(channel, blueprint)
    system = (
        "És o estratega editorial de um canal faceless. Gera um briefing específico para este canal. "
        "Não inventes factos sobre o canal. Se o contexto já tiver um tópico, desenvolve-o sem trocar o nicho. "
        "Escreve de forma natural, sem introduções artificiais, frases de IA, clickbait enganoso ou CTA genérico. "
        "Responde apenas com JSON válido com as chaves topic, angle, hook, niche e rationale."
    )
    user = json.dumps(
        {
            "channel": context,
            "user_context": user_context.strip(),
            "reference_rules": reference_bundle(),
            "requirements": [
                "topic em uma frase clara",
                "angle contrarian ou inesperado quando fizer sentido",
                "hook para os primeiros segundos",
                "niche coerente com o Blueprint e descrição",
                "rationale curta e prática",
            ],
        },
        ensure_ascii=False,
    )
    result = _chat_json(settings, system, user)
    required = ("topic", "angle", "hook", "niche", "rationale")
    if any(not str(result.get(key) or "").strip() for key in required):
        raise CreativeGenerationError("O briefing gerado veio incompleto; tente novamente.")
    result["topic_source"] = "llm"
    result["channel_id"] = str(channel.get("id") or "")
    return result


def _score(value: Any) -> int:
    try:
        return max(0, min(3, int(value)))
    except (TypeError, ValueError):
        return 0


def _short_overlay(value: Any) -> str:
    words = re.findall(r"\S+", str(value or "").strip())
    return " ".join(words[:4])


def _keywords_from_text(*values: str) -> list[str]:
    """Build a small deterministic keyword fallback when the LLM omits keywords."""
    blocked = {"para", "como", "sobre", "mais", "esse", "esta", "that", "this", "with", "from", "video"}
    result: list[str] = []
    for value in values:
        for word in re.findall(r"[\wÀ-ÿ]{4,}", str(value or "").casefold(), flags=re.UNICODE):
            if word not in blocked and word not in result:
                result.append(word)
    return result[:15]


def generate_creative_package(
    settings: dict[str, Any],
    channel: dict[str, Any],
    topic: str,
    blueprint: dict[str, Any] | None = None,
    language: str = "",
) -> dict[str, Any]:
    if not topic.strip():
        raise CreativeGenerationError("É necessário um tópico ou briefing antes de gerar título e thumbnail.")
    context = channel_context(channel, blueprint)
    system = (
        "És director editorial e de thumbnails para YouTube. Cria um pacote coerente de título e thumbnail "
        "para o tópico fornecido. Gera exactamente pelo menos 20 títulos candidatos e entre 3 e 5 variantes de thumbnail. "
        "O título deve carregar keywords no início, ter curiosidade, especificidade e emoção, sem clickbait falso. "
        "A thumbnail deve ter no máximo três elementos, alto contraste, uma composição clara, texto opcional de até 4 palavras, "
        "safe zones e leitura em 120px. O texto da thumbnail não pode repetir o título integralmente. Remove AI tells. "
        "Responde apenas com JSON válido nas chaves selected_title, title_candidates, keywords e thumbnail_variants."
    )
    user = json.dumps(
        {
            "channel": context,
            "language": language or context["language"],
            "topic": topic.strip(),
            "reference_rules": reference_bundle(),
            "keywords_schema": ["lista de 8 a 15 keywords SEO curtas, sem hashtags"],
            "title_candidates_schema": {
                "title": "string",
                "formula": "string",
                "curiosity_score": "integer 0-3",
                "specificity_score": "integer 0-3",
                "emotional_score": "integer 0-3",
            },
            "thumbnail_variant_schema": {
                "concept": "string",
                "overlay_text": "string, maximum 4 words",
                "composition": "string",
                "color_palette": "string",
                "subject": "string",
                "image_prompt": "string, no text rendered in the image",
                "title_synergy": "string",
            },
        },
        ensure_ascii=False,
    )
    result = _chat_json(settings, system, user)
    raw_titles = result.get("title_candidates")
    if not isinstance(raw_titles, list) or len(raw_titles) < 20:
        raise CreativeGenerationError("O provider deve devolver pelo menos 20 títulos candidatos.")
    titles: list[dict[str, Any]] = []
    for item in raw_titles[:30]:
        if not isinstance(item, dict) or not str(item.get("title") or "").strip():
            continue
        title = str(item["title"]).strip()
        titles.append(
            {
                "title": title,
                "formula": str(item.get("formula") or "custom").strip(),
                "curiosity_score": _score(item.get("curiosity_score")),
                "specificity_score": _score(item.get("specificity_score")),
                "emotional_score": _score(item.get("emotional_score")),
            }
        )
    if len(titles) < 20:
        raise CreativeGenerationError("Os títulos devolvidos pelo provider não têm conteúdo suficiente.")
    raw_keywords = result.get("keywords")
    keywords = [str(item).strip() for item in raw_keywords if str(item).strip()] if isinstance(raw_keywords, list) else []
    selected_title = str(result.get("selected_title") or titles[0]["title"]).strip()
    if selected_title not in {item["title"] for item in titles}:
        selected_title = titles[0]["title"]
    if not keywords:
        keywords = _keywords_from_text(topic, selected_title)

    variants_raw = result.get("thumbnail_variants")
    if not isinstance(variants_raw, list) or len(variants_raw) < 3:
        raise CreativeGenerationError("O provider deve devolver pelo menos 3 variantes de thumbnail.")
    variants: list[dict[str, Any]] = []
    for item in variants_raw[:5]:
        if not isinstance(item, dict):
            continue
        if not str(item.get("concept") or "").strip() or not str(item.get("image_prompt") or "").strip():
            continue
        variants.append(
            {
                "concept": str(item.get("concept") or "").strip(),
                "overlay_text": _short_overlay(item.get("overlay_text")),
                "composition": str(item.get("composition") or "").strip(),
                "color_palette": str(item.get("color_palette") or "").strip(),
                "subject": str(item.get("subject") or "").strip(),
                "image_prompt": str(item.get("image_prompt") or "").strip(),
                "title_synergy": str(item.get("title_synergy") or "").strip(),
                "status": "prompt_ready",
            }
        )
    if len(variants) < 3:
        raise CreativeGenerationError("As variantes de thumbnail devolvidas pelo provider estão incompletas.")
    return {
        "title": selected_title,
        "title_candidates": titles,
        "keywords": keywords[:15],
        "thumbnail_variant": variants[0],
        "thumbnail_variants": variants,
        "thumbnail_status": "prompt_ready",
        "topic_source": "llm",
        "generated_by": "configured_llm",
    }
