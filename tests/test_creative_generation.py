from __future__ import annotations

import json

import pytest

from hermes_ui.creative_generation import CreativeGenerationError, generate_creative_package, generate_title_and_keywords, generate_topic_for_channel, generate_video_description


class _Response:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload, ensure_ascii=False)

    def json(self):
        return self._payload


def _settings():
    return {"llm_provider": "openai", "openai_api_key": "test-key", "openai_base_url": "https://llm.example/v1", "openai_model_name": "test-model"}


def _channel():
    return {"id": "channel_1", "name": "Canal História", "description": "História e civilizações", "language": "36 – Português (Brasil)", "default_blueprint_id": "bp-history", "default_voice": "pt-BR-FranciscaNeural-Female"}


def test_generate_topic_uses_structured_json(monkeypatch):
    from hermes_ui import creative_generation

    response = {"choices": [{"message": {"content": json.dumps({"topic": "A cidade que desapareceu", "angle": "O detalhe ignorado", "hook": "Ninguém sabe onde foi parar", "niche": "história", "rationale": "Tema coerente com o canal"})}}]}
    captured = {}
    monkeypatch.setattr(creative_generation.requests, "post", lambda url, **kwargs: captured.update({"url": url, "kwargs": kwargs}) or _Response(response))

    result = generate_topic_for_channel(_settings(), _channel(), {"id": "bp-history", "name": "História"})

    assert result["topic"] == "A cidade que desapareceu"
    assert result["topic_source"] == "llm"
    assert captured["url"].endswith("/chat/completions")
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer test-key"


def test_generate_topic_for_english_channel_requires_english_output(monkeypatch):
    from hermes_ui import creative_generation

    response = {"choices": [{"message": {"content": json.dumps({"topic": "How the U.S. Navy Tracks Russian Submarines", "angle": "Silent surveillance", "hook": "The Atlantic is being watched", "niche": "military history", "rationale": "English channel"})}}]}
    captured = {}
    channel = {**_channel(), "language": "en"}
    monkeypatch.setattr(creative_generation.requests, "post", lambda url, **kwargs: captured.update({"system": kwargs["json"]["messages"][0]["content"], "user": kwargs["json"]["messages"][1]["content"]}) or _Response(response))

    result = generate_topic_for_channel(_settings(), channel, {"id": "bp-history", "name": "History"})

    assert result["topic"].startswith("How the U.S. Navy")
    assert "English (en)" in captured["system"]
    assert '"output_language": "English (en)"' in captured["user"]


def test_generate_title_for_english_channel_requires_english_output(monkeypatch):
    from hermes_ui import creative_generation

    titles = [{"title": f"English title {index}", "formula": "list", "curiosity_score": 2, "specificity_score": 2, "emotional_score": 2} for index in range(20)]
    response = {"choices": [{"message": {"content": json.dumps({"selected_title": "English title 3", "title_candidates": titles, "keywords": ["navy", "submarines"]})}}]}
    captured = {}
    channel = {**_channel(), "language": "en"}
    monkeypatch.setattr(creative_generation.requests, "post", lambda url, **kwargs: captured.update({"system": kwargs["json"]["messages"][0]["content"], "user": kwargs["json"]["messages"][1]["content"]}) or _Response(response))

    result = generate_title_and_keywords(_settings(), channel, "How the U.S. Navy Tracks Russian Submarines", {"id": "bp-history", "name": "History"})

    assert result["title"] == "English title 3"
    assert "English (en)" in captured["system"]
    assert '"language": "en"' in captured["user"]


def test_generate_title_and_keywords_excludes_thumbnail_fields(monkeypatch):
    from hermes_ui import creative_generation

    titles = [{"title": f"Título {index}", "formula": "list", "curiosity_score": 2, "specificity_score": 2, "emotional_score": 2} for index in range(20)]
    response = {"choices": [{"message": {"content": json.dumps({"selected_title": "Título 3", "title_candidates": titles, "keywords": ["história", "civilização"]})}}]}
    captured = {}
    monkeypatch.setattr(creative_generation.requests, "post", lambda url, **kwargs: captured.update({"url": url, "kwargs": kwargs}) or _Response(response))

    result = generate_title_and_keywords(_settings(), _channel(), "A cidade que desapareceu", {"id": "bp-history", "name": "História"})

    assert result["title"] == "Título 3"
    assert len(result["title_candidates"]) == 20
    assert result["keywords"] == ["história", "civilização"]
    assert "thumbnail_variants" not in result
    assert captured["url"].endswith("/chat/completions")


def test_generate_video_description_uses_text_llm_and_requested_language(monkeypatch):
    from hermes_ui import creative_generation

    captured = {}
    response = {"choices": [{"message": {"content": json.dumps({"description": "Descrição em dois parágrafos.\n\nConvite para acompanhar o canal."})}}]}
    monkeypatch.setattr(creative_generation.requests, "post", lambda url, **kwargs: captured.update({"payload": kwargs["json"]}) or _Response(response))

    description = generate_video_description(_settings(), _channel(), "A cidade que desapareceu", title="O mistério da cidade", tags=["história", "mistério"], language="en")

    assert description.startswith("Descrição em dois parágrafos")
    assert '"language": "en"' in captured["payload"]["messages"][1]["content"]
    assert '"tags": ["história", "mistério"]' in captured["payload"]["messages"][1]["content"]


def test_generate_creative_requires_twenty_titles_and_three_variants(monkeypatch):
    from hermes_ui import creative_generation

    titles = [{"title": f"Título {index}", "formula": "list", "curiosity_score": 2, "specificity_score": 2, "emotional_score": 2} for index in range(20)]
    variants = [{"concept": f"Conceito {index}", "overlay_text": "SEGREDO OCULTO", "composition": "sujeito à esquerda", "color_palette": "azul e laranja", "subject": "cidade antiga", "image_prompt": "YouTube thumbnail, no text", "title_synergy": "complementa o título"} for index in range(3)]
    response = {"choices": [{"message": {"content": json.dumps({"selected_title": "Título 3", "title_candidates": titles, "thumbnail_variants": variants})}}]}
    monkeypatch.setattr(creative_generation.requests, "post", lambda *args, **kwargs: _Response(response))

    result = generate_creative_package(_settings(), _channel(), "A cidade que desapareceu", {"id": "bp-history", "name": "História"})

    assert result["title"] == "Título 3"
    assert len(result["title_candidates"]) == 20
    assert len(result["thumbnail_variants"]) == 3
    assert result["thumbnail_status"] == "prompt_ready"
    assert result["thumbnail_variant"]["overlay_text"] == "SEGREDO OCULTO"


def test_generate_creative_rejects_incomplete_provider_response(monkeypatch):
    from hermes_ui import creative_generation

    response = {"choices": [{"message": {"content": json.dumps({"selected_title": "Título", "title_candidates": [], "thumbnail_variants": []})}}]}
    monkeypatch.setattr(creative_generation.requests, "post", lambda *args, **kwargs: _Response(response))

    with pytest.raises(CreativeGenerationError, match="20 títulos"):
        generate_creative_package(_settings(), _channel(), "Tema")


def test_provider_without_credentials_fails_actionably():
    with pytest.raises(CreativeGenerationError, match="API key"):
        generate_topic_for_channel({"llm_provider": "openai", "openai_model_name": "test-model", "openai_base_url": "https://llm.example/v1"}, _channel())
