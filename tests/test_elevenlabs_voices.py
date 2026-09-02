from __future__ import annotations

from datetime import datetime, timedelta, timezone

import hermes_ui.elevenlabs_voices as voices
from hermes_ui import storage


class Response:
    status_code = 200

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


def isolated_storage(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "STORAGE", tmp_path)
    monkeypatch.setattr(storage, "STATE", tmp_path / "state")
    storage.ensure_storage()


def test_normalise_voices_keeps_only_personal_fields():
    result = voices.normalise_voices({"voices": [
        {"voice_id": "personal-1", "name": "My Voice", "category": "personal", "labels": {"accent": "pt"}, "samples": [{"sample_id": "x"}]},
        {"voice_id": "default-1", "name": "Default", "category": "default"},
    ]})
    assert result == [{"voice_id": "personal-1", "name": "My Voice", "category": "personal", "labels": {"accent": "pt"}, "samples": [{"sample_id": "x"}]}]


def test_fetch_uses_fresh_cache_without_api(monkeypatch, tmp_path):
    isolated_storage(monkeypatch, tmp_path)
    storage.write_json(voices.CACHE_FILENAME, {"updated_at": datetime.now(timezone.utc).isoformat(), "source": "api", "voices": [{"voice_id": "v", "name": "Voice"}]})
    def fail(*args, **kwargs):
        raise AssertionError("API não deveria ser chamada")
    result, metadata = voices.fetch_personal_voices({}, request_get=fail)
    assert result[0]["voice_id"] == "v"
    assert metadata["source"] == "cache"


def test_fetch_filters_api_and_saves_cache(monkeypatch, tmp_path):
    isolated_storage(monkeypatch, tmp_path)
    result, metadata = voices.fetch_personal_voices(
        {"elevenlabs_api_key": "secret"}, force=True,
        request_get=lambda *args, **kwargs: Response({"voices": [{"voice_id": "v", "name": "Voice", "category": "personal"}, {"voice_id": "x", "name": "Default", "category": "default"}]}),
    )
    assert [item["voice_id"] for item in result] == ["v"]
    assert metadata["source"] == "api"
    assert voices.cache_path().is_file()


def test_stale_cache_is_used_when_api_fails(monkeypatch, tmp_path):
    isolated_storage(monkeypatch, tmp_path)
    old = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    storage.write_json(voices.CACHE_FILENAME, {"updated_at": old, "source": "api", "voices": [{"voice_id": "old", "name": "Old"}]})
    result, metadata = voices.fetch_personal_voices({"elevenlabs_api_key": "secret"}, request_get=lambda *args, **kwargs: (_ for _ in ()).throw(voices.requests.Timeout()))
    assert result[0]["voice_id"] == "old"
    assert metadata["stale"] is True


def test_missing_key_is_safe_error(monkeypatch, tmp_path):
    isolated_storage(monkeypatch, tmp_path)
    try:
        voices.fetch_personal_voices({})
    except voices.ElevenLabsVoicesError as exc:
        assert "secret" not in str(exc)
        assert "API Key" in str(exc)
    else:
        raise AssertionError("era esperada uma mensagem de configuração")
