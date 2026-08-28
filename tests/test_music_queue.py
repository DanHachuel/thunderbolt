from __future__ import annotations

import base64
from unittest.mock import Mock, patch

from hermes_ui import music


def test_create_music_task_uses_the_dedicated_audio_queue(monkeypatch, tmp_path):
    monkeypatch.setattr(music.storage, "STATE", tmp_path / "state")
    monkeypatch.setattr(music.storage, "STORAGE", tmp_path / "storage")

    task = music.create_music_task("Suno AI", "instrumental calmo", "Faixa de teste")

    assert task["id"].startswith("music_")
    assert task["kind"] == "audio_generation"
    assert task["provider"] == "suno"
    assert task["state"] == "to_do"
    assert task["audio_path"] == ""
    assert len(music.list_music_tasks()) == 1
    assert music.storage.read_json("tasks.json", []) == []


def test_lyria_audio_extraction_reads_audio_without_returning_the_provider_payload():
    encoded = base64.b64encode(b"audio-data").decode("ascii")
    payload = {"steps": [{"content": [{"type": "text", "text": "metadata"}, {"type": "audio", "data": encoded}]}]}

    assert music._extract_lyria_audio(payload) == b"audio-data"


def test_lyria_generation_posts_only_to_the_music_interactions_endpoint(monkeypatch, tmp_path):
    monkeypatch.setattr(music.storage, "STATE", tmp_path / "state")
    monkeypatch.setattr(music.storage, "STORAGE", tmp_path / "storage")
    audio = base64.b64encode(b"lyria-audio").decode("ascii")
    response = Mock(status_code=200, content=b"response")
    response.json.return_value = {"output_audio": {"data": audio}}

    with patch.object(music.requests, "post", return_value=response) as post:
        result = music.request_lyria_generation({"lyria_api_key": "secret", "lyria_model": "lyria-3-clip-preview"}, "instrumental", "faixa")

    assert result["ok"] is True
    assert result["data"]["audio_path"].endswith(".mp3")
    assert post.call_args.args[0] == "https://generativelanguage.googleapis.com/v1beta/interactions"
    assert post.call_args.kwargs["json"] == {"model": "lyria-3-clip-preview", "input": "instrumental"}
    assert "secret" not in str(result)
