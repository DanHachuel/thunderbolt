from __future__ import annotations

import sys
import types
from pathlib import Path

from integrations import music_uploads
from integrations.music_uploads import JewelMusicAdapter, PushtunesAdapter, YTMusicApiAdapter


class FakeResponse:
    def __init__(self, status_code: int = 200, payload=None, text: str = ""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self._payload



def test_jewelmusic_upload_uses_documented_endpoint_and_metadata(monkeypatch, tmp_path):
    audio = tmp_path / "track.mp3"
    audio.write_bytes(b"fake-audio")
    calls = {}

    def fake_post(url, **kwargs):
        calls.update(url=url, **kwargs)
        return FakeResponse(payload={"id": "track-1", "status": "uploaded"})

    monkeypatch.setattr(music_uploads.requests, "post", fake_post)
    adapter = JewelMusicAdapter(
        {
            "jewelmusic_enabled": True,
            "jewelmusic_api_key": "jml_test_example",
            "jewelmusic_base_url": "https://api.jewelmusic.com",
        }
    )

    result = adapter.upload_track(audio, title="Noite", artist="Artista", album="Álbum", year="2026")

    assert result.ok is True
    assert calls["url"] == "https://api.jewelmusic.com/v1/tracks/upload"
    assert calls["headers"]["Authorization"] == "Bearer jml_test_example"
    assert calls["data"]["title"] == "Noite"
    assert calls["data"]["artist"] == "Artista"
    assert calls["files"]["file"][0] == "track.mp3"



def test_jewelmusic_rejects_missing_key_without_network(monkeypatch):
    called = False

    def fake_get(*args, **kwargs):
        nonlocal called
        called = True
        return FakeResponse()

    monkeypatch.setattr(music_uploads.requests, "get", fake_get)
    result = JewelMusicAdapter(
        {"jewelmusic_enabled": True, "jewelmusic_api_key": ""}
    ).test_connection()

    assert result.ok is False
    assert "API Key" in result.message
    assert called is False



def _install_fake_ytmusicapi(monkeypatch):
    module = types.ModuleType("ytmusicapi")

    class FakeYTMusic:
        def __init__(self, auth, proxies=None):
            self.auth = auth
            self.proxies = proxies

        def get_library_upload_songs(self, limit=1):
            return []

        def upload_song(self, filepath):
            return types.SimpleNamespace(name="SUCCEEDED")

    module.YTMusic = FakeYTMusic
    monkeypatch.setitem(sys.modules, "ytmusicapi", module)


def test_ytmusicapi_validates_browser_auth_and_uploads_supported_file(monkeypatch, tmp_path):
    _install_fake_ytmusicapi(monkeypatch)
    auth = tmp_path / "browser.json"
    auth.write_text('{"cookie": "local-only"}', encoding="utf-8")
    audio = tmp_path / "track.flac"
    audio.write_bytes(b"fake-audio")
    adapter = YTMusicApiAdapter(
        {
            "ytmusicapi_enabled": True,
            "ytmusicapi_auth_file": str(auth),
        }
    )

    assert adapter.test_connection().ok is True
    result = adapter.upload_song(audio)

    assert result.ok is True
    assert result.data["filename"] == "track.flac"



def test_ytmusicapi_rejects_wav_before_client_call(monkeypatch, tmp_path):
    _install_fake_ytmusicapi(monkeypatch)
    auth = tmp_path / "browser.json"
    auth.write_text("{}", encoding="utf-8")
    audio = tmp_path / "track.wav"
    audio.write_bytes(b"fake-audio")
    result = YTMusicApiAdapter(
        {"ytmusicapi_enabled": True, "ytmusicapi_auth_file": str(auth)}
    ).upload_song(audio)

    assert result.ok is False
    assert "não suportado" in result.message



def test_pushtunes_builds_safe_sync_command_and_copies_browser_auth(monkeypatch, tmp_path):
    csv_file = tmp_path / "tracks.csv"
    csv_file.write_text("artist,title\nArtista,Faixa\n", encoding="utf-8")
    auth_file = tmp_path / "browser.json"
    auth_file.write_text('{"cookie": "local-only"}', encoding="utf-8")
    captured = {}

    class Completed:
        returncode = 0
        stdout = "Successfully pushed 1 track"
        stderr = ""

    def fake_run(command, **kwargs):
        captured.update(command=command, **kwargs)
        copied = Path(kwargs["cwd"]) / "browser.json"
        assert copied.is_file()
        assert copied.read_text(encoding="utf-8") == auth_file.read_text(encoding="utf-8")
        return Completed()

    monkeypatch.setattr(music_uploads.subprocess, "run", fake_run)
    adapter = PushtunesAdapter(
        {
            "pushtunes_enabled": True,
            "pushtunes_source": "csv",
            "pushtunes_target": "ytm",
            "pushtunes_operation": "tracks",
            "pushtunes_csv_file": str(csv_file),
            "pushtunes_ytm_auth_file": str(auth_file),
            "pushtunes_spotify_client_secret": "secret-not-in-command",
        }
    )
    monkeypatch.setattr(adapter, "_command_prefix", lambda: ["pushtunes"])

    result = adapter.sync()

    assert result.ok is True
    assert captured["command"][:6] == ["pushtunes", "push", "tracks", "--from", "csv", "--to"]
    assert "secret-not-in-command" not in " ".join(captured["command"])
    assert result.data["returncode"] == 0



def test_pushtunes_requires_csv_for_csv_source(tmp_path):
    result = PushtunesAdapter(
        {
            "pushtunes_enabled": True,
            "pushtunes_source": "csv",
            "pushtunes_target": "ytm",
        }
    )
    result._command_prefix = lambda: ["pushtunes"]

    # No CSV path is allowed at status time; a missing path must be reported by
    # the adapter rather than becoming a subprocess error.
    result.csv_file = str(tmp_path / "missing.csv")
    checked = result.status()

    assert checked.ok is False
    assert "CSV" in checked.message



def test_pushtunes_requires_tidal_session_file(tmp_path):
    csv_file = tmp_path / "tracks.csv"
    csv_file.write_text("artist,title\nArtista,Faixa\n", encoding="utf-8")
    adapter = PushtunesAdapter(
        {
            "pushtunes_enabled": True,
            "pushtunes_source": "csv",
            "pushtunes_target": "tidal",
            "pushtunes_operation": "tracks",
            "pushtunes_csv_file": str(csv_file),
        }
    )
    adapter._command_prefix = lambda: ["pushtunes"]

    result = adapter.status()

    assert result.ok is False
    assert "tidal-session.json" in result.message


def test_distrokid_adapter_is_exported_and_manual_submit_is_documented():
    from integrations.distrokid_upload import DistroKidAdapter
    from pathlib import Path
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert DistroKidAdapter
    assert '"DistroKid"' in source
    assert '_render_distrokid_upload_tab()' in source
    assert 'submissão final fica sempre manual' in source
