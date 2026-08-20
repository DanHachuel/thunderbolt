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
    from hermes_ui.automation_worker import run_once
    from hermes_ui.domain import create_channel

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


def test_worker_does_not_duplicate_same_channel_on_same_day(tmp_path, monkeypatch):
    storage = _use_temp_storage(tmp_path, monkeypatch)
    from hermes_ui.automation_worker import run_once
    from hermes_ui.domain import create_channel

    local_now = datetime.now().astimezone().replace(hour=9, minute=5, second=0, microsecond=0)
    channel = create_channel("Canal sem duplicados", metadata={"automation_on": True, "automation_time": "09:05"})

    first = run_once(local_now)
    second = run_once(local_now)

    assert len(first["created"]) == 1
    assert second["created"] == []
    assert second["skipped"] == [channel["id"]]
    assert len(storage.read_json("batches.json", [])) == 1
    assert len(storage.read_json("tasks.json", [])) == 1


def test_worker_requires_active_channel_and_exact_local_hhmm(tmp_path, monkeypatch):
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
