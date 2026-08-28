from __future__ import annotations

from hermes_ui import music, music_generation


def test_music_generator_returns_structured_original_prompt(monkeypatch):
    monkeypatch.setattr(
        music_generation,
        "_chat_json",
        lambda settings, system, user: {
            "title": "Luzes da Costa",
            "language": "Português",
            "genre": "Fado (Portugal)",
            "vocal": "Feminina",
            "cultural_references": "costa atlântica ao anoitecer",
            "music_prompt": "# 1. Nome da Música\nLuzes da Costa\n\n# 2. Idioma da Música\nPortuguês\n\n# 3. Letra / Lyrics\n[Intro]\nOh-oh\n\n[Verse 1]\nLetra original\n\n[Pre-Chorus]\nLetra\n\n[Chorus]\nLetra\n\n[Verse 2]\nLetra\n\n[Bridge]\nLetra\n\n[Instrumental Solo]\nGuitarra\n\n[Final Chorus]\nLetra\n\n[Outro]\nOh-oh\n\n# 4. Estilo / Style Prompt\nFado contemporâneo, 96 BPM.",
        },
    )

    generated = music_generation.generate_music_fields(
        {}, theme="Uma viagem nocturna", language="pt", genre="Fado (Portugal)", vocal="Feminina", references="costa atlântica",
    )

    assert generated["title"] == "Luzes da Costa"
    assert generated["language"] == "pt"
    assert generated["genre"] == "Fado (Portugal)"
    assert generated["vocal"] == "Feminina"
    assert "# 3. Letra / Lyrics" in generated["prompt"]


def test_create_music_task_persists_music_metadata_without_creating_video_task(monkeypatch, tmp_path):
    monkeypatch.setattr(music.storage, "STATE", tmp_path / "state")
    monkeypatch.setattr(music.storage, "STORAGE", tmp_path / "storage")

    task = music.create_music_task(
        "Suno AI", "prompt original", "Título", language="pt", genre="MPB (Brasil)", vocal="Coral", references="chuva tropical", theme="Cidade à noite",
    )

    assert task["kind"] == "audio_generation"
    assert task["language"] == "pt"
    assert task["genre"] == "MPB (Brasil)"
    assert task["vocal"] == "Coral"
    assert task["duration_seconds"] == 120
    assert music.storage.read_json("tasks.json", []) == []


def test_suno_request_marks_vocal_music_as_not_instrumental(monkeypatch):
    captured = {}

    class Response:
        status_code = 200
        content = b"{}"

        def json(self):
            return {}

    monkeypatch.setattr(music.requests, "post", lambda *args, **kwargs: captured.update(kwargs) or Response())
    result = music.request_suno_generation(
        {"suno_api_key": "configured", "suno_api_base_url": "https://music.example"}, "letra", "canção", make_instrumental=False,
    )

    assert result["ok"] is True
    assert captured["json"]["duration"] == 120
    assert captured["json"]["make_instrumental"] is False
