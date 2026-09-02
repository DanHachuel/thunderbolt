from __future__ import annotations

from hermes_ui import music, storage


class Response:
    status_code = 200
    content = b"audio"

    def raise_for_status(self):
        return None


def test_create_music_task_persists_eleven_music_voice(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "STORAGE", tmp_path)
    monkeypatch.setattr(storage, "STATE", tmp_path / "state")
    task = music.create_music_task("Eleven Music", "song prompt", "Song", voice_id="voice-123", voice_gender="female")
    assert task["provider"] == "eleven_music"
    assert task["voice_id"] == "voice-123"
    assert task["voice_gender"] == "female"


def test_eleven_music_request_uses_gender_and_disables_coral(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "STORAGE", tmp_path)
    captured = {}

    def post(url, **kwargs):
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(music.requests, "post", post)
    result = music.request_eleven_music_generation({"elevenlabs_api_key": "secret"}, "cinematic song", "Test", voice_id="v1", voice_gender="male")
    assert result["ok"] is True
    assert "male" in captured["json"]["prompt"]
    assert "Não usar coro" in captured["json"]["prompt"]
    assert captured["headers"]["xi-api-key"] == "secret"


def test_eleven_music_requires_key():
    result = music.request_eleven_music_generation({}, "song")
    assert result["ok"] is False
    assert "API Key" in result["message"]
