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


def test_seed_blueprints_are_initialized_without_overwrite(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STORAGE_DIR", str(tmp_path / "storage"))
    from hermes_ui import storage

    storage.STORAGE = tmp_path / "storage"
    storage.STATE = storage.STORAGE / "state"
    storage.BLUEPRINTS = storage.STORAGE / "blueprints"
    storage.ensure_storage()
    imported = sorted((storage.BLUEPRINTS / "importados").glob("*.json"))
    assert len(imported) == 13

    preserved = imported[0]
    preserved.write_text('{"name": "personalizado"}\n', encoding="utf-8")
    storage.ensure_storage()
    assert storage.load_blueprint_file(preserved)["name"] == "personalizado"


def test_blueprint_creation_modes(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STORAGE_DIR", str(tmp_path / "storage"))
    from hermes_ui import blueprints, storage
    storage.STORAGE = tmp_path / "storage"
    storage.STATE = storage.STORAGE / "state"
    storage.BLUEPRINTS = storage.STORAGE / "blueprints"
    storage.ensure_storage()

    blueprint, branding = blueprints.create_blueprint_from_link("https://youtu.be/abc123", "história", "Português (pt-BR)", False)
    assert blueprint["metadata"]["input_type"] == "video"
    assert branding is None
    blueprint_path, branding_path = blueprints.save_generated_blueprint(blueprint)
    assert blueprint_path.exists()
    assert branding_path is None

    blueprint2, branding2 = blueprints.create_blueprint_from_link("https://www.youtube.com/@canal", "filosofia", "Português (pt-BR)", True)
    assert branding2 is not None
    _, branding_path2 = blueprints.save_generated_blueprint(blueprint2, branding2)
    assert branding_path2 is not None and branding_path2.exists()
    assert len(blueprints.list_branding_files()) == 1


def test_automation_defaults_are_carried_into_created_tasks(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STORAGE_DIR", str(tmp_path / "storage"))
    from hermes_ui import storage
    from hermes_ui.domain import create_batch, create_channel, create_tasks_for_batch, update_channel

    storage.STORAGE = tmp_path / "storage"
    storage.STATE = storage.STORAGE / "state"
    storage.BLUEPRINTS = storage.STORAGE / "blueprints"
    channel = create_channel("Canal automático", metadata={
        "default_blueprint_id": "bp_default",
        "default_voice": "pt-BR-FranciscaNeural-Female",
        "automation_on": True,
        "automation_time": "08:30",
    })
    update_channel(channel["id"], {"automation_on": True, "automation_time": "08:30"})
    batch = create_batch("single", [channel["id"]], "Tema automático", 1, {"language": "36 – Português (Brasil)"})
    task = create_tasks_for_batch(batch)[0]

    assert task["automation_on"] is True
    assert task["automation_time"] == "08:30"
    assert task["blueprint_id"] == "bp_default"
    assert task["voice"] == "pt-BR-FranciscaNeural-Female"


def test_set_channel_defaults_syncs_aliases_and_tasks(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STORAGE_DIR", str(tmp_path / "storage"))
    from hermes_ui import storage
    from hermes_ui.domain import create_batch, create_channel, create_tasks_for_batch, set_channel_defaults

    storage.STORAGE = tmp_path / "storage"
    storage.STATE = storage.STORAGE / "state"
    storage.BLUEPRINTS = storage.STORAGE / "blueprints"
    channel = create_channel("Canal com defaults")
    updated = set_channel_defaults(channel["id"], "BlueprintCocomelon", "pt-BR-FranciscaNeural-Female")

    assert updated["blueprint_id"] == "BlueprintCocomelon"
    assert updated["default_blueprint_id"] == "BlueprintCocomelon"
    assert updated["voice"] == "pt-BR-FranciscaNeural-Female"
    assert updated["default_voice"] == "pt-BR-FranciscaNeural-Female"

    batch = create_batch("single", [channel["id"]], "Tema", 1, {})
    task = create_tasks_for_batch(batch)[0]
    assert task["blueprint_id"] == "BlueprintCocomelon"
    assert task["voice"] == "pt-BR-FranciscaNeural-Female"


def test_delete_channel_removes_only_selected_channel(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_STORAGE_DIR", str(tmp_path / "storage"))
    from hermes_ui import storage
    from hermes_ui.domain import create_channel, delete_channel

    storage.STORAGE = tmp_path / "storage"
    storage.STATE = storage.STORAGE / "state"
    storage.BLUEPRINTS = storage.STORAGE / "blueprints"
    first = create_channel("Canal para apagar")
    second = create_channel("Canal preservado")
    storage.write_json("tasks.json", [{"id": "video_1", "channel_id": first["id"]}])

    removed = delete_channel(first["id"])

    assert removed["id"] == first["id"]
    assert [item["id"] for item in storage.read_json("channels.json")] == [second["id"]]
    assert storage.read_json("tasks.json")[0]["channel_id"] == first["id"]
    assert delete_channel("channel_inexistente") is None
