from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.modules.niche_finder import apify
from app.modules.niche_finder.apify import ApifyError, ApifyRun, build_actor_input, clean_srt, normalize_video_item, start_actor_run, vsc_ratio
from app.modules.niche_finder.summarizer import SummarizationError, summarize_transcript


def response(payload, status_code=200):
    return SimpleNamespace(status_code=status_code, text=str(payload), content=b"{}", json=lambda: payload)


def test_build_actor_input_preserves_three_keywords_and_limits():
    payload = build_actor_input([" Healthy food ", "", "Protein"], max_results=500, max_results_shorts=-2)
    assert payload["searchQueries"] == ["Healthy food", "Protein"]
    assert payload["maxResults"] == 100
    assert payload["maxResultsShorts"] == 0
    assert payload["downloadSubtitles"] is True


def test_build_actor_input_requires_keyword():
    with pytest.raises(ApifyError, match="palavra-chave"):
        build_actor_input(["", " ", None])


def test_clean_srt_and_normalize_video_item_calculates_vsc():
    item = normalize_video_item(
        {
            "id": "abc",
            "url": "https://youtube.com/watch?v=abc",
            "title": "Video",
            "channelName": "Canal",
            "viewCount": 1000,
            "numberOfSubscribers": 100,
            "commentsCount": 10,
            "duration": "08:00",
            "subtitles": [{"srt": "1\n00:00:00,000 --> 00:00:01,000\nHello world\n\n2\n00:00:01,000 --> 00:00:02,000\nNext point"}],
        }
    )
    assert clean_srt("1\n00:00:00,000 --> 00:00:01,000\nHello") == "Hello"
    assert item["transcript"] == "Hello world Next point"
    assert item["transcript_status"] == "disponível"
    assert item["vsc_ratio"] == vsc_ratio(1000, 100, 10)
    assert item["summary_status"] == "pendente"


def test_vsc_ratio_handles_zero_divisions():
    assert vsc_ratio(0, 0, 10) == 0.0
    assert vsc_ratio(100, 0, 0) == 0.0


def test_start_actor_run_uses_actor_endpoint_and_bearer(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return response({"data": {"id": "run-1", "status": "RUNNING", "defaultDatasetId": "dataset-1"}})

    monkeypatch.setattr(apify.requests, "post", fake_post)
    run = start_actor_run("secret", "streamers~youtube-scraper", {"searchQueries": ["food"]})
    assert run == ApifyRun("run-1", "RUNNING", "dataset-1", "streamers~youtube-scraper")
    assert calls[0][1]["headers"]["Authorization"] == "Bearer secret"
    assert calls[0][1]["json"]["searchQueries"] == ["food"]


def test_start_actor_run_rejects_missing_token():
    with pytest.raises(ApifyError, match="API Token"):
        start_actor_run("", "actor", {})


def test_wait_for_actor_run_polls_until_success(monkeypatch):
    statuses = iter([ApifyRun("run-1", "RUNNING", "dataset-1"), ApifyRun("run-1", "SUCCEEDED", "dataset-1")])
    monkeypatch.setattr(apify, "get_actor_run", lambda *args, **kwargs: next(statuses))
    monkeypatch.setattr("time.sleep", lambda *_args: None)
    result = apify.wait_for_actor_run("secret", ApifyRun("run-1", "RUNNING", "dataset-1"), poll_interval=1, timeout_seconds=30)
    assert result.status == "SUCCEEDED"
    assert result.dataset_id == "dataset-1"


def test_summarize_transcript_uses_openai_compatible_response(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return response({"choices": [{"message": {"content": "INTRODUÇÃO: começa. ESTRUTURA: ponto 1."}}]})

    monkeypatch.setattr("app.modules.niche_finder.summarizer.requests.post", fake_post)
    result = summarize_transcript(
        "Uma transcrição curta.",
        {"llm_provider": "openai", "openai_api_key": "secret", "openai_base_url": "https://llm.test/v1", "openai_model_name": "model"},
    )
    assert result.startswith("INTRODUÇÃO")
    assert calls[0][0] == "https://llm.test/v1/chat/completions"
    assert calls[0][1]["headers"]["Authorization"] == "Bearer secret"


def test_summarize_transcript_requires_configured_llm():
    with pytest.raises(SummarizationError, match="Configure provider"):
        summarize_transcript("Texto", {"llm_provider": "openai"})


def test_apify_page_is_independent_from_kaggle_page():
    from pathlib import Path

    source_path = Path(__file__).parents[1] / "app" / "main.py"
    source = source_path.read_text(encoding="utf-8")
    apify_start = source.index("def render_niche_finder_apify():")
    apify_end = source.index("def render_videos():", apify_start)
    apify_source = source[apify_start:apify_end]

    assert "download_kaggle_dataset" not in apify_source
    assert "run_niche_analysis" not in apify_source
    assert "niche_results" not in apify_source
    assert "niche_apify_results" in apify_source
    assert 'read_json("niche_apify_runs.json"' in apify_source
    assert 'st.session_state["niche_apify_active_run"]' in apify_source
