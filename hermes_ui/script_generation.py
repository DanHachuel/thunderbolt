"""Blueprint-aware generation of video scripts and music lyrics."""

from __future__ import annotations

import json
from typing import Any

from .creative_generation import CreativeGenerationError, _chat_json, channel_context


DOCUMENT_TYPES = {
    "Roteiro de vídeo": "video_script",
    "Letra de música": "music_lyrics",
}


def generate_script_document(
    settings: dict[str, Any],
    *,
    document_type: str,
    title: str,
    brief: str,
    language: str,
    channel: dict[str, Any] | None = None,
    blueprint: dict[str, Any] | None = None,
    structure_notes: str = "",
    generation_settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate an editable Markdown document from the configured LLM.

    The function deliberately returns text only. It never writes to storage; the UI
    decides whether the generated draft should be saved after the user reviews it.
    """
    normalized_type = DOCUMENT_TYPES.get(document_type, document_type)
    if normalized_type not in {"video_script", "music_lyrics"}:
        raise CreativeGenerationError("Escolha Roteiro de vídeo ou Letra de música.")
    if not brief.strip():
        raise CreativeGenerationError("Escreva um tema ou briefing antes de gerar o documento.")

    channel_context_value = channel_context(channel or {}, blueprint or {})
    blueprint_payload = blueprint or {}
    generation_settings_payload = generation_settings or {}
    if normalized_type == "video_script":
        output_requirements = {
            "content": "roteiro completo em Markdown, com título, gancho, cenas, narração e indicações visuais/sonoras",
            "summary": "resumo editorial em uma frase",
        }
        system = (
            "És um roteirista editorial de vídeos faceless. Cria um roteiro original, natural e executável, "
            "alinhado exclusivamente ao nicho e às regras do Blueprint fornecido. Não inventes factos sensíveis, "
            "não uses introduções genéricas, não escrevas comentários sobre IA e não incluas um CTA vazio. "
            "Responde apenas com JSON válido nas chaves title, summary e content."
        )
    else:
        output_requirements = {
            "content": "letra completa em Markdown, com secções [Verso], [Pré-refrão], [Refrão], [Ponte] quando fizer sentido",
            "summary": "resumo da intenção musical em uma frase",
        }
        system = (
            "És um compositor de letras originais. Cria uma letra cantável, coerente com o tema, idioma, "
            "Blueprint e direcção musical fornecidos. Não copies letras existentes, não cites artistas sem pedido "
            "e não acrescentes explicações dentro da letra. Responde apenas com JSON válido nas chaves title, summary e content."
        )

    user = json.dumps(
        {
            "document_type": normalized_type,
            "requested_title": title.strip(),
            "brief": brief.strip(),
            "language": language.strip(),
            "channel": channel_context_value,
            "blueprint": blueprint_payload,
            "structure_notes": structure_notes.strip(),
            "generation_settings": generation_settings_payload,
            "output_requirements": output_requirements,
        },
        ensure_ascii=False,
    )
    result = _chat_json(settings, system, user)
    content = str(result.get("content") or "").strip()
    if not content:
        raise CreativeGenerationError("O provider LLM devolveu um documento sem conteúdo.")
    return {
        "document_type": normalized_type,
        "title": str(result.get("title") or title or brief).strip(),
        "summary": str(result.get("summary") or "").strip(),
        "content": content,
        "language": language.strip(),
        "blueprint_id": str(blueprint_payload.get("id") or ""),
        "blueprint_name": str(blueprint_payload.get("name") or "SEM BLUEPRINT CONFIGURADO"),
        "channel_id": str((channel or {}).get("id") or ""),
        "channel_name": str((channel or {}).get("name") or "Documento independente"),
        "generation_settings": generation_settings_payload,
        "generated_by": "configured_llm",
    }
