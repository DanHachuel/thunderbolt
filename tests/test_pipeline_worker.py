from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from hermes_ui.thumbnail_generation import ThumbnailGenerationError

from hermes_ui import storage
from hermes_ui import pipeline_worker


def _isolate_storage(tmp_path, monkeypatch):
    root = tmp_path / "storage"
    monkeypatch.setattr(storage, "STORAGE", root)
    monkeypatch.setattr(storage, "STATE", root / "state")
    monkeypatch.setattr(storage, "BLUEPRINTS", root / "blueprints")
    monkeypatch.setattr(storage, "TIKTOK_PROMPT_MASTERS", root / "tiktok" / "prompts_master")
    monkeypatch.setattr(storage, "MEDIA_DOWNLOADS", root / "downloads")
    monkeypatch.setattr(pipeline_worker, "STORAGE", root)
    storage.ensure_storage()
    return root


def test_pipeline_lock_recovers_after_dead_process(tmp_path, monkeypatch):
    root = _isolate_storage(tmp_path, monkeypatch)
    lock_path = root / "state" / pipeline_worker.PIPELINE_LOCK_FILENAME
    lock_path.write_text("999999999", encoding="utf-8")

    acquired = pipeline_worker._acquire_lock()

    assert acquired == lock_path
    assert lock_path.read_text(encoding="utf-8") == str(__import__("os").getpid())
    lock_path.unlink()


def test_recover_stale_task_marks_it_failed(tmp_path, monkeypatch):
    _isolate_storage(tmp_path, monkeypatch)
    old_timestamp = (datetime.now(timezone.utc) - timedelta(seconds=pipeline_worker.STALE_TASK_SECONDS + 10)).isoformat()
    storage.write_json(
        "tasks.json",
        [{
            "id": "video_stale",
            "state": "doing",
            "stage": "video",
            "progress": 72,
            "title": "Vídeo preso",
            "channel_name": "Canal",
            "updated_at": old_timestamp,
        }],
    )

    recovered = pipeline_worker.recover_stale_tasks()

    task = storage.read_json("tasks.json")[0]
    assert recovered == ["video_stale"]
    assert task["state"] == "failed"
    assert task["failed_stage"] == "video"
    assert "heartbeat" in task["error"]


def test_run_task_reuses_prepared_title_and_thumbnail_without_full_creative_generation(tmp_path, monkeypatch):
    _isolate_storage(tmp_path, monkeypatch)
    video_path = tmp_path / "prepared.mp4"
    video_path.write_bytes(b"mp4")
    task = {
        "id": "video_prepared",
        "state": "to_do",
        "stage": "script",
        "progress": 0,
        "topic": "Tema preparado",
        "topic_source": "manual",
        "title": "Título preparado",
        "thumbnail_variant": {
            "concept": "Conceito preparado",
            "image_prompt": "prompt preparado",
            "overlay_text": "TEMA REAL",
            "lettering_prompt": "texto grande",
        },
        "thumbnail_variants": [{"concept": "Conceito preparado", "image_prompt": "prompt preparado", "overlay_text": "TEMA REAL", "lettering_prompt": "texto grande"}],
        "generation_settings": {"video_script": "Roteiro preparado", "video_keywords": "alpha, beta"},
        "channel_id": "channel-1",
        "language": "pt-BR",
    }
    channel = {"id": "channel-1", "name": "Canal teste", "language": "pt-BR", "niche": "Teste"}
    blueprint = {"id": "blueprint-1", "name": "Blueprint teste"}
    updates = []

    monkeypatch.setattr(pipeline_worker, "_settings", lambda: {"youtube_batch_accounts": []})
    monkeypatch.setattr(pipeline_worker, "_channel_for_task", lambda value: channel)
    monkeypatch.setattr(pipeline_worker, "_blueprint_for_channel", lambda value: blueprint)
    monkeypatch.setattr(pipeline_worker, "_update", lambda task_id, **changes: updates.append(changes) or {**task, **changes})
    monkeypatch.setattr(pipeline_worker, "save_script_document", lambda script: {"path": "prepared-script.md"})
    monkeypatch.setattr(pipeline_worker, "_save_json_artifact", lambda task_id, name, payload: f"{name}.json")
    monkeypatch.setattr(pipeline_worker, "generate_thumbnail_image", lambda *args, **kwargs: tmp_path / "prepared.jpg")
    monkeypatch.setattr(pipeline_worker, "_run_video_helper", lambda value: video_path)
    monkeypatch.setattr(pipeline_worker, "upload_with_default_route", lambda *args, **kwargs: SimpleNamespace(ok=True, message="", data={"uploaded": True}))
    monkeypatch.setattr(pipeline_worker, "generate_creative_package", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("não deve regenerar o pacote criativo")))

    result = pipeline_worker._run_task(task)

    assert result["state"] == "done"
    assert result["title"] == "Título preparado"
    assert any(update.get("thumbnail_prompt") == "prompt preparado" and update.get("thumbnail_text") == "TEMA REAL" for update in updates)
    assert any(update.get("stage") == "upload" and update.get("state") == "done" for update in updates)


def test_run_task_resumes_from_persisted_artifacts_without_regenerating_previous_stages(tmp_path, monkeypatch):
    _isolate_storage(tmp_path, monkeypatch)
    script_path = tmp_path / "roteiro-pronto.md"
    script_path.write_text("---\nid: script-ready\ntype: video_script\n---\n\nRoteiro persistido", encoding="utf-8")
    video_path = tmp_path / "video-pronto.mp4"
    video_path.write_bytes(b"mp4")
    thumbnail_path = tmp_path / "thumbnail-pronta.jpg"
    thumbnail_path.write_bytes(b"jpg")
    prompt_path = tmp_path / "thumbnail-prompt.json"
    prompt_path.write_text('{"thumbnail": {"image_prompt": "prompt persistido", "overlay_text": "PRONTO"}}', encoding="utf-8")
    task = {
        "id": "video_resume",
        "state": "failed",
        "stage": "thumbnail",
        "progress": 86,
        "topic": "Tema retomado",
        "topic_source": "manual",
        "title": "Título persistido",
        "tags": ["tema", "retomado"],
        "channel_id": "channel-resume",
        "language": "pt-BR",
        "artifacts": {
            "script": str(script_path),
            "video": str(video_path),
            "thumbnail": str(thumbnail_path),
            "thumbnail_prompt_json": str(prompt_path),
        },
        "thumbnail_variant": {"image_prompt": "prompt persistido", "overlay_text": "PRONTO"},
        "thumbnail_prompt": "prompt persistido",
        "thumbnail_text": "PRONTO",
    }
    channel = {"id": "channel-resume", "name": "Canal retomado", "language": "pt-BR", "niche": "Teste"}
    storage.write_json("channels.json", [channel])
    storage.write_json("tasks.json", [task])
    calls = {"upload": 0}

    monkeypatch.setattr(pipeline_worker, "_settings", lambda: {"youtube_batch_accounts": []})
    monkeypatch.setattr(pipeline_worker, "_channel_for_task", lambda value: channel)
    monkeypatch.setattr(pipeline_worker, "_blueprint_for_channel", lambda value: {})
    monkeypatch.setattr(pipeline_worker, "save_script_document", lambda *args, **kwargs: pytest.fail("não deve guardar novamente o roteiro"))
    monkeypatch.setattr(pipeline_worker, "generate_script_document", lambda *args, **kwargs: pytest.fail("não deve regenerar o roteiro"))
    monkeypatch.setattr(pipeline_worker, "generate_title_and_keywords", lambda *args, **kwargs: pytest.fail("não deve regenerar título e keywords"))
    monkeypatch.setattr(pipeline_worker, "_run_video_helper", lambda *args, **kwargs: pytest.fail("não deve regenerar o vídeo"))
    monkeypatch.setattr(pipeline_worker, "generate_video_from_pool", lambda *args, **kwargs: pytest.fail("não deve chamar o pool de vídeo"))
    monkeypatch.setattr(pipeline_worker, "generate_thumbnail_prompt", lambda *args, **kwargs: pytest.fail("não deve regenerar o prompt da thumbnail"))
    monkeypatch.setattr(pipeline_worker, "_generate_pipeline_thumbnail", lambda *args, **kwargs: pytest.fail("não deve regenerar a thumbnail pronta"))

    def fake_upload(*args, **kwargs):
        calls["upload"] += 1
        assert kwargs["video_path"] == str(video_path)
        assert kwargs["thumbnail_path"] == str(thumbnail_path)
        return SimpleNamespace(ok=True, message="", data={"uploaded": True})

    monkeypatch.setattr(pipeline_worker, "upload_with_default_route", fake_upload)

    result = pipeline_worker._run_task(task)

    persisted = storage.read_json("tasks.json")[0]
    assert result["state"] == "done"
    assert persisted["stage"] == "upload"
    assert persisted["state"] == "done"
    assert persisted["artifacts"]["video"] == str(video_path)
    assert persisted["artifacts"]["thumbnail"] == str(thumbnail_path)
    assert calls["upload"] == 1


def test_run_once_marks_unexpected_pipeline_error_terminal(tmp_path, monkeypatch):
    _isolate_storage(tmp_path, monkeypatch)
    storage.write_json("tasks.json", [{"id": "video_error", "state": "to_do", "stage": "script", "progress": 0, "title": "Erro", "channel_name": "Canal"}])
    monkeypatch.setattr(pipeline_worker, "_run_task", lambda task: (_ for _ in ()).throw(RuntimeError("falha simulada")))

    result = pipeline_worker.run_once()

    assert result["ok"] is False
    task = storage.read_json("tasks.json")[0]
    assert task["state"] == "failed"
    assert task["error"] == "falha simulada"
    assert storage.read_json(pipeline_worker.PIPELINE_LOG_FILENAME)["status"] == "failed"


def test_run_once_persists_idle_heartbeat(tmp_path, monkeypatch):
    _isolate_storage(tmp_path, monkeypatch)

    result = pipeline_worker.run_once()
    status = pipeline_worker.load_pipeline_worker_status()

    assert result["status"] == "idle"
    assert status["status"] == "idle"
    assert status["alive"] is True
    assert status["last_heartbeat_at"]


def test_backlog_has_live_progress_and_stale_recovery_ui():
    source = Path(__file__).resolve().parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")

    assert "@st.fragment(run_every=5.0)" in source
    assert "st.progress(progress, text=f\"{label} · {_pipeline_stage_label(task)} · {progress}%\")" in source
    assert "recover_stale_tasks()" in source
    assert "_render_pipeline_progress_panel()" in source
    assert "Worker de vídeo sem heartbeat recente" in source


class _FakeStdout:
    def __init__(self, lines):
        self._lines = iter(lines)

    def readline(self):
        return next(self._lines, "")

    def close(self):
        return None


class _FakePopen:
    def __init__(self, lines, returncode=0, stays_alive=False):
        self.stdout = _FakeStdout(lines)
        self.returncode = None if stays_alive else returncode
        self._stays_alive = stays_alive

    def poll(self):
        return self.returncode

    def kill(self):
        self.returncode = -9
        self._stays_alive = False

    def wait(self, timeout=None):
        return self.returncode


def test_video_helper_uses_configured_root_and_persists_helper_diagnostics(tmp_path, monkeypatch):
    _isolate_storage(tmp_path, monkeypatch)
    root = tmp_path / "MoneyPrinterTurbo"
    root.mkdir()
    (root / "cli.py").write_text("# fake", encoding="utf-8")
    (root / "config.toml").write_text("[app]\n", encoding="utf-8")
    video_path = tmp_path / "generated.mp4"
    video_path.write_bytes(b"mp4")
    storage.write_json("settings.json", {"moneyprinter_path": str(root)})
    storage.write_json("tasks.json", [{"id": "video_root", "state": "doing", "stage": "video", "progress": 68, "topic": "Tema"}])
    captured = {}

    def fake_popen(command, **kwargs):
        captured["command"] = command
        return _FakePopen([
            f"VIDEO_FILE={video_path}\n",
            "LOG_FILE=/tmp/mpt-video.log\n",
            "RESULT_FILE=/tmp/mpt-result.json\n",
        ])

    monkeypatch.setattr(pipeline_worker.subprocess, "Popen", fake_popen)

    result = pipeline_worker._run_video_helper({"id": "video_root", "topic": "Tema"})

    assert result == video_path
    assert captured["command"][captured["command"].index("--root") + 1] == str(root.resolve())
    task = storage.read_json("tasks.json")[0]
    diagnostics_path = Path(task["artifacts"]["video_diagnostics"])
    diagnostics = __import__("json").loads(diagnostics_path.read_text(encoding="utf-8"))
    assert diagnostics["log_file"] == "/tmp/mpt-video.log"
    assert task["video_log"] == "/tmp/mpt-video.log"
    assert task["video_result"] == "/tmp/mpt-result.json"
    assert "VIDEO_FILE=" in diagnostics["output_tail"]


def test_video_helper_passes_uploaded_voiceover_to_moneyprinterturbo(tmp_path, monkeypatch):
    _isolate_storage(tmp_path, monkeypatch)
    root = tmp_path / "MoneyPrinterTurbo"
    root.mkdir()
    (root / "cli.py").write_text("# fake", encoding="utf-8")
    (root / "config.toml").write_text("[app]\n", encoding="utf-8")
    voiceover = tmp_path / "narracao.wav"
    voiceover.write_bytes(b"audio")
    video_path = tmp_path / "generated.mp4"
    video_path.write_bytes(b"mp4")
    storage.write_json("settings.json", {"moneyprinter_path": str(root)})
    storage.write_json("tasks.json", [{"id": "video_voiceover", "state": "doing", "stage": "video", "progress": 68, "topic": "Tema"}])
    captured = {}

    def fake_popen(command, **kwargs):
        captured["command"] = command
        return _FakePopen([f"VIDEO_FILE={video_path}\n"])

    monkeypatch.setattr(pipeline_worker.subprocess, "Popen", fake_popen)
    result = pipeline_worker._run_video_helper(
        {
            "id": "video_voiceover",
            "topic": "Tema",
            "generation_settings": {"voiceover_mode": "Upload", "voiceover_file": str(voiceover)},
        }
    )

    assert result == video_path
    assert captured["command"][captured["command"].index("--custom-audio-file") + 1] == str(voiceover.resolve())


def test_video_helper_rejects_upload_mode_without_audio_file(tmp_path, monkeypatch):
    _isolate_storage(tmp_path, monkeypatch)
    with pytest.raises(pipeline_worker.PipelineError, match="ficheiro de narração válido"):
        pipeline_worker._run_video_helper(
            {
                "id": "video_missing_voiceover",
                "topic": "Tema",
                "generation_settings": {"voiceover_mode": "Upload", "voiceover_file": ""},
            }
        )


def test_video_helper_timeout_kills_subprocess_and_returns_pipeline_error(tmp_path, monkeypatch):
    _isolate_storage(tmp_path, monkeypatch)
    storage.write_json("tasks.json", [{"id": "video_timeout", "state": "doing", "stage": "video", "progress": 68, "topic": "Tema"}])
    process = _FakePopen([], stays_alive=True)
    monkeypatch.setattr(pipeline_worker.subprocess, "Popen", lambda *args, **kwargs: process)
    monkeypatch.setattr(pipeline_worker, "VIDEO_TIMEOUT_SECONDS", 0)

    with pytest.raises(pipeline_worker.PipelineError, match="excedeu o limite"):
        pipeline_worker._run_video_helper({"id": "video_timeout", "topic": "Tema"})

    assert process.returncode == -9


def test_run_once_preserves_blocked_state_when_pipeline_is_stopped(tmp_path, monkeypatch):
    _isolate_storage(tmp_path, monkeypatch)
    storage.write_json("tasks.json", [{"id": "video_stopped", "state": "to_do", "stage": "video", "progress": 68, "topic": "Tema"}])
    monkeypatch.setattr(pipeline_worker, "_run_task", lambda task: (_ for _ in ()).throw(pipeline_worker.PipelineStopped("A tarefa foi parada pelo utilizador.")))

    result = pipeline_worker.run_once()

    assert result["ok"] is True
    assert result["status"] == "stopped"
    assert storage.read_json("tasks.json")[0]["state"] == "blocked"
    assert storage.read_json(pipeline_worker.PIPELINE_LOG_FILENAME)["status"] == "stopped"


def test_thumbnail_failure_keeps_video_artifact_ready_after_video_stage(tmp_path, monkeypatch):
    _isolate_storage(tmp_path, monkeypatch)
    video_path = tmp_path / "video-pronto.mp4"
    video_path.write_bytes(b"mp4")
    channel = {"id": "channel-1", "name": "Canal teste", "language": "pt-BR", "niche": "Teste"}
    task = {
        "id": "video_thumbnail_quota",
        "state": "to_do",
        "stage": "script",
        "progress": 0,
        "topic": "Tema com quota esgotada",
        "topic_source": "manual",
        "title": "Título pronto",
        "thumbnail_variant": {},
        "thumbnail_variants": [],
        "generation_settings": {"video_script": "Roteiro pronto", "video_keywords": "video, teste"},
        "channel_id": "channel-1",
        "language": "pt-BR",
        "artifacts": {},
    }
    storage.write_json("channels.json", [channel])
    storage.write_json("tasks.json", [task])

    monkeypatch.setattr(pipeline_worker, "_settings", lambda: {"youtube_batch_accounts": []})
    monkeypatch.setattr(pipeline_worker, "_channel_for_task", lambda value: channel)
    monkeypatch.setattr(pipeline_worker, "_blueprint_for_channel", lambda value: {})
    monkeypatch.setattr(pipeline_worker, "save_script_document", lambda script: {"path": "script.md"})
    monkeypatch.setattr(pipeline_worker, "_run_video_helper", lambda value: video_path)
    monkeypatch.setattr(pipeline_worker, "generate_thumbnail_prompt", lambda *args, **kwargs: {"image_prompt": "prompt depois do vídeo", "overlay_text": "THUMB DEPOIS"})
    monkeypatch.setattr(
        pipeline_worker,
        "_generate_pipeline_thumbnail",
        lambda *args, **kwargs: (_ for _ in ()).throw(ThumbnailGenerationError("HTTP 429 quota")),
    )
    monkeypatch.setattr(pipeline_worker, "upload_with_default_route", lambda *args, **kwargs: pytest.fail("upload não deve ocorrer sem thumbnail"))

    result = pipeline_worker.run_once()

    assert result["ok"] is False
    persisted = storage.read_json("tasks.json")[0]
    assert persisted["state"] == "failed"
    assert persisted["stage"] == "thumbnail"
    assert persisted["progress"] == 86
    assert persisted["video_ready"] is True
    assert persisted["artifacts"]["video"] == str(video_path)
    assert "vídeo já está disponível" in persisted["error"]
    assert result["task_id"] == task["id"]


def test_pipeline_stage_order_places_video_before_thumbnail_prompt():
    from hermes_ui.domain import STAGES

    assert STAGES.index("video") < STAGES.index("thumbnail_prompt") < STAGES.index("thumbnail") < STAGES.index("upload")
