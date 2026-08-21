import json
from pathlib import Path

import pytest

from hermes_ui import cuts


def test_validate_cut_request_requires_rights_and_valid_manual_interval(tmp_path: Path):
    source = tmp_path / "source.mp4"
    source.write_bytes(b"video")
    with pytest.raises(cuts.CutsError, match="direitos"):
        cuts.validate_cut_request(
            source=source,
            output_format="9:16",
            strategy="manual",
            max_clips=1,
            min_duration=10,
            max_duration=30,
            rights_confirmed=False,
            manual_start=10,
            manual_end=5,
        )
    with pytest.raises(cuts.CutsError, match="fim"):
        cuts.validate_cut_request(
            source=source,
            output_format="9:16",
            strategy="manual",
            max_clips=1,
            min_duration=10,
            max_duration=30,
            rights_confirmed=True,
            manual_start=10,
            manual_end=5,
        )


def test_plan_segments_manual_and_automatic():
    manual = cuts.plan_segments(120, strategy="manual", max_clips=3, min_duration=10, max_duration=30, manual_start=12, manual_end=42)
    assert manual == [{"index": 1, "start": 12.0, "end": 42.0, "duration": 30.0}]

    automatic = cuts.plan_segments(120, strategy="automatic", max_clips=3, min_duration=15, max_duration=40)
    assert len(automatic) == 3
    assert all(item["duration"] <= 40 for item in automatic)
    assert automatic[0]["start"] == 0.0
    assert automatic[-1]["end"] == 120.0


def test_build_clip_command_contains_format_filter_and_no_shell_interpolation(tmp_path: Path):
    source = tmp_path / "source.mp4"
    output = tmp_path / "clip.mp4"
    command = cuts.build_clip_command(source, output, {"start": 1.5, "duration": 20.0}, "9:16", ffmpeg_path="/usr/bin/ffmpeg")
    assert command[0] == "/usr/bin/ffmpeg"
    assert "-ss" in command and "1.500" in command
    assert "-t" in command and "20.000" in command
    assert "scale=1080:1920" in command[command.index("-vf") + 1]
    assert "-i" in command


def test_generate_clips_persists_manifest_and_zip(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.mp4"
    source.write_bytes(b"video")
    monkeypatch.setattr(cuts.storage, "STORAGE", tmp_path / "storage")
    monkeypatch.setattr(cuts, "probe_duration", lambda *_args, **_kwargs: 60.0)
    monkeypatch.setattr(cuts, "resolve_ffmpeg", lambda *_args, **_kwargs: "/usr/bin/ffmpeg")

    def fake_run(command, output, *, source, segment):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"clip")
        return {"source": str(source), "output": str(output), "command": command, "segment": segment, "created_at": "now"}

    monkeypatch.setattr(cuts, "_run_ffmpeg", fake_run)
    record = cuts.generate_clips(
        source,
        output_format="1:1",
        strategy="automatic",
        max_clips=2,
        min_duration=10,
        max_duration=30,
        rights_confirmed=True,
    )
    assert record["status"] == "complete"
    assert len(record["clips"]) == 2
    manifest = cuts._runs_root() / record["id"] / "manifest.json"
    assert json.loads(manifest.read_text(encoding="utf-8"))["output_format"] == "1:1"
    runs = cuts.list_runs()
    assert runs[0]["id"] == record["id"]
    archive, archive_bytes = cuts.zip_run(record)
    assert archive.is_file()
    assert archive_bytes


def test_store_uploaded_video_is_deduplicated(tmp_path, monkeypatch):
    monkeypatch.setattr(cuts.storage, "STORAGE", tmp_path / "storage")
    first = cuts.store_uploaded_video("Meu vídeo.mp4", b"same")
    second = cuts.store_uploaded_video("outro.mp4", b"same")
    assert first == second
    assert first.parent.name == "inputs"
