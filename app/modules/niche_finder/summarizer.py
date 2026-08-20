from __future__ import annotations

from typing import Any

import requests


DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "moonshot": "https://api.moonshot.cn/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "groq": "https://api.groq.com/openai/v1",
}


class SummarizationError(RuntimeError):
    """Raised when the configured LLM cannot summarize a transcript."""


def _content_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts: list[str] = []
        for part in value:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and isinstance(part.get("text"), str):
                parts.append(part["text"])
        return "".join(parts).strip()
    return ""


def summarize_transcript(transcript: str, settings: dict[str, Any], *, timeout: int = 90) -> str:
    transcript = str(transcript or "").strip()
    if not transcript:
        raise SummarizationError("A transcrição está vazia.")
    provider = str(settings.get("llm_provider", "") or "").strip().lower()
    api_key = str(settings.get(f"{provider}_api_key", "") or "").strip()
    base_url = str(settings.get(f"{provider}_base_url", "") or "").strip().rstrip("/")
    model = str(settings.get(f"{provider}_model_name", "") or "").strip()
    if provider == "openai":
        api_key = api_key or str(settings.get("openai_api_key", "") or "").strip()
        base_url = base_url or str(settings.get("openai_base_url", "") or "").strip().rstrip("/")
        model = model or str(settings.get("openai_model_name", "") or "").strip()
    if not base_url:
        base_url = DEFAULT_BASE_URLS.get(provider, "")
    if not api_key or not base_url or not model:
        raise SummarizationError(f"Configure provider, API key, Base URL e modelo para o LLM seleccionado ({provider or 'não definido'}).")
    endpoint = base_url if base_url.endswith("/chat/completions") else f"{base_url}/chat/completions"
    system_prompt = (
        "És um assistente de análise de vídeos. Resume apenas informação presente na transcrição, "
        "sem inventar, inferir ou acrescentar factos. Responde em português do Brasil e usa exactamente "
        "esta estrutura: INTRODUÇÃO: um parágrafo sobre como o vídeo começa. ESTRUTURA: uma lista com "
        "os pontos principais e subpontos da progressão do vídeo."
    )
    payload = {
        "model": model,
        "temperature": 0.2,
        "max_tokens": 1200,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript[:120000]},
        ],
    }
    try:
        response = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise SummarizationError(f"Não foi possível contactar o provider LLM: {exc}") from exc
    if response.status_code >= 400:
        raise SummarizationError(f"O provider LLM devolveu HTTP {response.status_code}: {response.text[:300]}")
    try:
        body = response.json()
    except ValueError as exc:
        raise SummarizationError("O provider LLM devolveu uma resposta JSON inválida.") from exc
    choices = body.get("choices") if isinstance(body, dict) else None
    if not isinstance(choices, list) or not choices:
        raise SummarizationError("O provider LLM não devolveu escolhas de resposta.")
    choice = choices[0] if isinstance(choices[0], dict) else {}
    message = choice.get("message") if isinstance(choice, dict) else {}
    content = _content_value(message.get("content") if isinstance(message, dict) else "")
    if not content:
        raise SummarizationError("O provider LLM devolveu uma resposta sem texto.")
    return content


def summarize_items(items: list[dict[str, Any]], settings: dict[str, Any], *, on_item: Any = None) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        current = dict(item)
        if current.get("transcript"):
            try:
                current["summary"] = summarize_transcript(current["transcript"], settings)
                current["summary_status"] = "concluído"
            except SummarizationError as exc:
                current["summary"] = ""
                current["summary_status"] = f"erro: {exc}"
        else:
            current["summary_status"] = "não aplicável"
        enriched.append(current)
        if on_item:
            on_item(index, len(items), current)
    return enriched
