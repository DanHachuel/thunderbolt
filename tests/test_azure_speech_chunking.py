from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHUNKED = _load_module(ROOT / "seed" / "skills" / "azure_tts_chunked.py", "azure_tts_chunked_test")
MPT_AGENT = _load_module(ROOT / "seed" / "skills" / "mpt_agent.py", "mpt_agent_test")


def test_split_text_keeps_chunks_below_safe_request_size():
    text = "Parágrafo inicial. " + ("palavra " * 700) + "Fim."
    chunks = CHUNKED.split_text(text, limit=1800)
    assert len(chunks) > 1
    assert all(0 < len(chunk) <= 1800 for chunk in chunks)
    assert "Parágrafo inicial" in chunks[0]
    assert "Fim" in chunks[-1]


def test_split_text_handles_newlines_and_long_unbroken_tokens():
    chunks = CHUNKED.split_text("linha um\nlinha dois\n" + ("x" * 5000), limit=500)
    assert len(chunks) > 2
    assert all(len(chunk) <= 500 for chunk in chunks)
    assert "linha um" in chunks[0]
    assert chunks[-1] == "x" * 500


def test_mpt_agent_prepares_azure_audio_without_logging_credentials(tmp_path, monkeypatch):
    root = tmp_path / "MoneyPrinterTurbo"
    root.mkdir()
    config_path = root / "config.toml"
    config_path.write_text('[azure]\nspeech_key = "azure-secret"\nspeech_region = "eastus"\n', encoding="utf-8")
    task_dir = root / "storage" / "tasks" / "task-1"
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["env"] = kwargs["env"]
        output = Path(command[command.index("--output") + 1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"prepared-audio")
        return SimpleNamespace(returncode=0, stdout="AZURE_CHUNK_COUNT=4\n")

    monkeypatch.setattr(MPT_AGENT.subprocess, "run", fake_run)
    result = MPT_AGENT._prepare_azure_v2_chunked_audio(
        root,
        config_path,
        task_dir,
        [
            "--video-script",
            "Roteiro longo preparado",
            "--voice-name",
            "en-US-BrianMultilingualNeural-V2-Male",
            "--voice-rate",
            "1.25",
        ],
        "/usr/bin/uv",
    )

    assert result == task_dir / "azure-v2-audio.mp3"
    command = captured["command"]
    assert command[command.index("--project") + 1] == str(root)
    assert command[command.index("--voice") + 1] == "en-US-BrianMultilingualNeural"
    assert command[command.index("--rate") + 1] == "1.25"
    environment = captured["env"]
    assert environment["AZURE_SPEECH_KEY"] == "azure-secret"
    assert environment["AZURE_SPEECH_REGION"] == "eastus"
    assert "azure-secret" not in str(captured["command"])


def test_mpt_agent_does_not_prepare_audio_without_azure_v2_voice(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text('[azure]\nspeech_key = "secret"\nspeech_region = "eastus"\n', encoding="utf-8")
    monkeypatch.setattr(MPT_AGENT.subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("não deve chamar Azure")))
    assert MPT_AGENT._prepare_azure_v2_chunked_audio(
        tmp_path,
        config_path,
        tmp_path / "task",
        ["--video-script", "Roteiro", "--voice-name", "en-US-BrianMultilingualNeural-Male"],
        "/usr/bin/uv",
    ) is None


def test_generate_video_injects_chunked_audio_into_moneyprinter_command(tmp_path, monkeypatch):
    root = tmp_path / "MoneyPrinterTurbo"
    root.mkdir()
    (root / "config.toml").write_text("[app]\n", encoding="utf-8")
    prepared_audio = tmp_path / "azure-v2-audio.mp3"
    prepared_audio.write_bytes(b"audio")
    captured: dict[str, object] = {}

    monkeypatch.setattr(MPT_AGENT.shutil, "which", lambda _: "/usr/bin/uv")
    monkeypatch.setattr(MPT_AGENT, "run_checked", lambda *args, **kwargs: None)
    monkeypatch.setattr(MPT_AGENT, "_prepare_azure_v2_chunked_audio", lambda *args, **kwargs: prepared_audio)

    def fake_run(command, **kwargs):
        captured["command"] = command
        task_id = command[command.index("--task-id") + 1]
        output = root / "storage" / "tasks" / task_id / "final-video.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"mp4")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(MPT_AGENT.subprocess, "run", fake_run)
    videos, task_dir, _log_path, _result_path = MPT_AGENT.generate_video(
        root,
        "Tema longo",
        [
            "--video-source",
            "pexels",
            "--video-script",
            "Roteiro preparado",
            "--voice-name",
            "en-US-BrianMultilingualNeural-V2-Male",
        ],
    )

    command = captured["command"]
    assert command[command.index("--custom-audio-file") + 1] == str(prepared_audio)
    assert command[command.index("--voice-name") + 1] == "en-US-BrianMultilingualNeural-V2-Male"
    assert videos == [task_dir / "final-video.mp4"]
