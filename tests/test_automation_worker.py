from __future__ import annotations

from datetime import datetime


def _use_temp_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("THUNDERBOLT_STORAGE_DIR", str(tmp_path / "storage"))
    from hermes_ui import storage

    storage.STORAGE = tmp_path / "storage"
    storage.STATE = storage.STORAGE / "state"
    storage.BLUEPRINTS = storage.STORAGE / "blueprints"
    storage.ensure_storage()
    return storage


def test_worker_uses_local_clock_and_creates_daily_batch(tmp_path, monkeypatch):
    storage = _use_temp_storage(tmp_path, monkeypatch)
    from hermes_ui import automation_worker
    from hermes_ui.automation_worker import run_once
    from hermes_ui.domain import create_channel

    monkeypatch.setattr(automation_worker, "_creative_payload", lambda channel: (_ for _ in ()).throw(AssertionError("a criação agendada não deve bloquear no LLM")))
    local_now = datetime.now().astimezone().replace(hour=8, minute=30, second=0, microsecond=0)
    channel = create_channel(
        "Canal worker",
        metadata={
            "active": True,
            "automation_on": True,
            "automation_time": "08:30",
            "daily_limit": 2,
            "default_blueprint_id": "bp_worker",
            "default_voice": "pt-BR-FranciscaNeural-Female",
        },
    )

    result = run_once(local_now)

    assert result["ok"] is True
    assert len(result["created"]) == 1
    batch = result["created"][0]["batch"]
    assert batch["options"]["automation_worker"] is True
    assert batch["options"]["automation_date"] == local_now.date().isoformat()
    tasks = storage.read_json("tasks.json", [])
    assert len(tasks) == 2
    assert all(task["blueprint_id"] == "bp_worker" for task in tasks)
    assert all(task["voice"] == "pt-BR-FranciscaNeural-Female" for task in tasks)
    assert all(task["automation_time"] == "08:30" for task in tasks)
    assert all(task["topic_source"] == "llm_pending" for task in tasks)
    assert all(task["stage"] == "topic" for task in tasks)
    assert all(task["title"] == "" for task in tasks)
    assert all(task["language"] == "pt" for task in tasks)
    assert all(task["thumbnail_variant"] == {} for task in tasks)
    assert all(task["thumbnail_prompt"] == "" for task in tasks)


def test_worker_catches_up_a_missed_schedule_after_its_minute(tmp_path, monkeypatch):
    storage = _use_temp_storage(tmp_path, monkeypatch)
    from hermes_ui.automation_worker import run_once
    from hermes_ui.domain import create_channel

    local_now = datetime.now().astimezone().replace(hour=9, minute=17, second=30, microsecond=0)
    channel = create_channel("Canal atrasado", metadata={"automation_on": True, "automation_time": "09:05", "language": "en"})

    result = run_once(local_now)

    assert result["ok"] is True
    assert len(result["created"]) == 1
    batch = result["created"][0]["batch"]
    assert batch["options"]["automation_scheduled_at"].startswith(local_now.date().isoformat() + "T09:05")
    task = storage.read_json("tasks.json", [])[0]
    assert task["channel_id"] == channel["id"]
    assert task["language"] == "en"
    assert task["stage"] == "topic"


def test_worker_does_not_duplicate_same_channel_on_same_day(tmp_path, monkeypatch):
    storage = _use_temp_storage(tmp_path, monkeypatch)
    from hermes_ui import automation_worker
    from hermes_ui.automation_worker import run_once
    from hermes_ui.domain import create_channel

    monkeypatch.setattr(automation_worker, "_creative_payload", lambda channel: ("Tema específico sem duplicados", {"topic": "Tema específico sem duplicados", "topic_source": "llm", "title": "Título diário", "thumbnail_status": "prompt_ready"}))
    local_now = datetime.now().astimezone().replace(hour=9, minute=5, second=0, microsecond=0)
    channel = create_channel("Canal sem duplicados", metadata={"automation_on": True, "automation_time": "09:05"})

    first = run_once(local_now)
    second = run_once(local_now)

    assert len(first["created"]) == 1
    assert second["created"] == []
    assert second["skipped"] == [channel["id"]]
    assert len(storage.read_json("batches.json", [])) == 1
    assert len(storage.read_json("tasks.json", [])) == 1


def test_worker_does_not_create_before_scheduled_time(tmp_path, monkeypatch):
    storage = _use_temp_storage(tmp_path, monkeypatch)
    from hermes_ui.automation_worker import run_once
    from hermes_ui.domain import create_channel

    local_now = datetime.now().astimezone().replace(hour=10, minute=0, second=0, microsecond=0)
    create_channel("Canal desligado", metadata={"active": False, "automation_on": True, "automation_time": "10:00"})
    create_channel("Canal fora de hora", metadata={"active": True, "automation_on": True, "automation_time": "10:01"})

    result = run_once(local_now)

    assert result["ok"] is True
    assert result["created"] == []
    assert storage.read_json("batches.json", []) == []
    assert storage.read_json("tasks.json", []) == []


def test_worker_creates_pending_card_without_waiting_for_creative_generation(tmp_path, monkeypatch):
    storage = _use_temp_storage(tmp_path, monkeypatch)
    from hermes_ui.automation_worker import run_once
    from hermes_ui.domain import create_channel

    local_now = datetime.now().astimezone().replace(hour=11, minute=0, second=0, microsecond=0)
    create_channel("Canal sem provider", metadata={"automation_on": True, "automation_time": "11:00", "language": "en"})

    result = run_once(local_now)

    assert result["ok"] is True
    assert result["created"]
    tasks = storage.read_json("tasks.json", [])
    assert len(tasks) == 1
    assert tasks[0]["state"] == "to_do"
    assert tasks[0]["stage"] == "topic"
    assert tasks[0]["topic_source"] == "llm_pending"
    assert tasks[0]["language"] == "en"
