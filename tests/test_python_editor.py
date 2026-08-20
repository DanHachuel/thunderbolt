from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from hermes_ui import python_editor
from hermes_ui.python_editor import PythonEditorError


def test_video_extensions_and_list_video_files(tmp_path):
    first = tmp_path / "first.mp4"
    second = tmp_path / "second.mov"
    ignored = tmp_path / "notes.txt"
    first.write_bytes(b"video")
    second.write_bytes(b"video")
    ignored.write_text("ignore", encoding="utf-8")

    result = python_editor.list_video_files(tmp_path)
    assert {path.name for path in result} == {"first.mp4", "second.mov"}


def test_list_generated_videos_only_returns_existing_video_artifacts(tmp_path):
    video = tmp_path / "generated.mp4"
    video.write_bytes(b"video")
    tasks = [
        {"artifacts": {"video": str(video)}},
        {"artifacts": {"video": str(tmp_path / "missing.mp4")}},
        {"artifacts": {"video": str(tmp_path / "not-video.txt")}},
    ]
    assert python_editor.list_generated_videos(tasks) == [video.resolve()]


def test_save_script_stays_inside_editor_scripts(tmp_path, monkeypatch):
    monkeypatch.setattr(python_editor, "_scripts", lambda: tmp_path)
    saved = python_editor.save_script("my script", "print('safe')")
    assert saved == (tmp_path / "my-script.py").resolve()
    assert saved.read_text(encoding="utf-8") == "print('safe')"
    with pytest.raises(PythonEditorError, match="não pode ficar vazio"):
        python_editor.save_script("empty.py", " ")


def test_store_uploaded_asset_hashes_and_reuses_file(tmp_path, monkeypatch):
    monkeypatch.setattr(python_editor, "_root", lambda: tmp_path)
    first = python_editor.store_uploaded_asset("clip.mp4", b"content")
    second = python_editor.store_uploaded_asset("clip.mp4", b"content")
    assert first == second
    assert first.read_bytes() == b"content"
    with pytest.raises(PythonEditorError, match="extensão"):
        python_editor.store_uploaded_asset("clip.txt", b"content")


def test_trim_video_builds_controlled_ffmpeg_command(tmp_path, monkeypatch):
    source = tmp_path / "source.mp4"
    source.write_bytes(b"source")
    output = tmp_path / "output.mp4"
    calls = []

    monkeypatch.setattr(python_editor, "_ffmpeg", lambda *_args, **_kwargs: "/usr/bin/ffmpeg")
    monkeypatch.setattr(python_editor, "_output_path", lambda *_args, **_kwargs: output)

    def fake_run(command, **kwargs):
        calls.append(command)
        output.write_bytes(b"result")
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(python_editor.subprocess, "run", fake_run)
    result, info = python_editor.trim_video(source, 1, 5)
    assert result == output
    assert info["operation"] == "corte"
    assert calls[0][0] == "/usr/bin/ffmpeg"
    assert "-ss" in calls[0]
    assert "-to" in calls[0]
    assert str(source) in calls[0]


def test_save_edit_record_uses_dedicated_history(tmp_path, monkeypatch):
    writes = []
    monkeypatch.setattr(python_editor.storage, "append_json", lambda name, record: writes.append((name, record)) or record)
    source = tmp_path / "source.mp4"
    output = tmp_path / "output.mp4"
    record = python_editor.save_edit_record(source, output, {"operation": "corte", "start_seconds": 1, "created_at": "now"})
    assert writes[0][0] == "python_editor_edits.json"
    assert record["operation"] == "corte"
    assert record["parameters"]["start_seconds"] == 1
