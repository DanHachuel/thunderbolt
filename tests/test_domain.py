from __future__ import annotations

import json
from pathlib import Path


def test_storage_and_batch_modes(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STORAGE_DIR", str(tmp_path / "storage"))
    from hermes_ui import storage
    from hermes_ui.domain import create_batch, create_channel, create_tasks_for_batch, transition_task

    storage.STORAGE = tmp_path / "storage"
    storage.STATE = storage.STORAGE / "state"
    storage.BLUEPRINTS = storage.STORAGE / "blueprints"
    channel_a = create_channel("Canal A")
    channel_b = create_channel("Canal B")

    single = create_batch("single", [channel_a["id"]], "Tema A", 1, {})
    assert len(create_tasks_for_batch(single)) == 1

    same = create_batch("same_channel", [channel_a["id"]], "Tema B", 3, {})
    assert len(create_tasks_for_batch(same)) == 3

    general = create_batch("general", [channel_a["id"], channel_b["id"]], "Tema C", 99, {})
    assert len(create_tasks_for_batch(general)) == 2

    task_id = storage.read_json("tasks.json")[0]["id"]
    assert transition_task(task_id, "doing")["state"] == "doing"
    assert transition_task(task_id, "blocked")["state"] == "blocked"


def test_blueprint_json_is_readable(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STORAGE_DIR", str(tmp_path / "storage"))
    from hermes_ui import storage
    storage.STORAGE = tmp_path / "storage"
    storage.STATE = storage.STORAGE / "state"
    storage.BLUEPRINTS = storage.STORAGE / "blueprints"
    storage.ensure_storage()
    target = storage.BLUEPRINTS / "importados" / "blueprint.json"
    target.write_text(json.dumps({"name": "Teste", "unknown_field": {"keep": True}}), encoding="utf-8")
    assert storage.load_blueprint_file(target)["unknown_field"]["keep"] is True
