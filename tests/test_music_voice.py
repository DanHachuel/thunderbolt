from pathlib import Path

import pytest

from hermes_ui import music, storage
from hermes_ui.voice_preview import load_preview_file, synthesize_preview


def _use_temp_storage(monkeypatch, tmp_path):
    root = tmp_path / "storage"
    monkeypatch.setattr(storage, "STORAGE", root)
    monkeypatch.setattr(storage, "STATE", root / "state")
    monkeypatch.setattr(storage, "BLUEPRINTS", root / "blueprints")
    storage.ensure_storage()
    return root


def test_music_file_is_stored_and_listed(monkeypatch, tmp_path):
    root = _use_temp_storage(monkeypatch, tmp_path)
    saved = music.store_music_file("faixa teste.mp3", b"audio")
    assert saved.parent == root / "music"
    assert saved in music.list_music_files()


def test_suno_requires_explicit_configured_endpoint():
    result = music.request_suno_generation({}, "instrumental")
    assert result["ok"] is False
    assert "Suno API" in result["message"]


def test_voice_preview_rejects_empty_text(tmp_path, monkeypatch):
    _use_temp_storage(monkeypatch, tmp_path)
    with pytest.raises(ValueError, match="texto"):
        synthesize_preview("", "edge", "en-US-AriaNeural-Female", {})


def test_voice_preview_loader_rejects_empty_directory_and_zero_byte_file(tmp_path):
    assert load_preview_file("") is None
    assert load_preview_file(tmp_path) is None
    empty_file = tmp_path / "empty.mp3"
    empty_file.write_bytes(b"")
    assert load_preview_file(empty_file) is None


def test_voice_preview_loader_reads_non_empty_audio_file(tmp_path):
    audio_file = tmp_path / "preview.mp3"
    audio_file.write_bytes(b"fake-mp3")
    loaded = load_preview_file(str(audio_file))
    assert loaded is not None
    path, data = loaded
    assert path == audio_file
    assert data == b"fake-mp3"


def test_voice_preview_rejects_unknown_provider(tmp_path, monkeypatch):
    _use_temp_storage(monkeypatch, tmp_path)
    with pytest.raises(ValueError, match="não suportado"):
        synthesize_preview("teste", "unknown", "", {})
