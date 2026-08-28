import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _isolated_storage(tmp_path, monkeypatch):
    storage_root = tmp_path / "storage"
    monkeypatch.setenv("THUNDERBOLT_STORAGE_DIR", str(storage_root))
    from hermes_ui import storage

    storage.STORAGE = storage_root
    storage.STATE = storage_root / "state"
    storage.BLUEPRINTS = storage_root / "blueprints"
    storage.ensure_storage()
    return storage


def test_concurrent_task_mutations_preserve_every_video(tmp_path, monkeypatch):
    storage = _isolated_storage(tmp_path, monkeypatch)
    storage.write_json("tasks.json", [])

    def add_task(index):
        def mutate(tasks):
            tasks.append({"id": f"video-{index}", "state": "to_do"})

        storage.update_json("tasks.json", [], mutate)

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(add_task, range(32)))

    tasks = storage.read_json("tasks.json")
    assert len(tasks) == 32
    assert {task["id"] for task in tasks} == {f"video-{index}" for index in range(32)}


def test_corrupt_protected_task_file_is_not_replaced_by_empty_list(tmp_path, monkeypatch):
    storage = _isolated_storage(tmp_path, monkeypatch)
    task_path = storage.STATE / "tasks.json"
    task_path.write_text("{ dados incompletos", encoding="utf-8")

    with pytest.raises(storage.StorageIntegrityError):
        storage.read_json("tasks.json", [])

    assert task_path.read_text(encoding="utf-8") == "{ dados incompletos"
    assert list(storage.STATE.glob("tasks.json.corrupt-*"))


def test_install_merges_legacy_tasks_when_new_storage_already_exists(tmp_path):
    legacy_state = tmp_path / "Hermes-UI" / "storage" / "state"
    current_state = tmp_path / ".thunderbolt" / "storage" / "state"
    legacy_state.mkdir(parents=True)
    current_state.mkdir(parents=True)
    (legacy_state / "tasks.json").write_text(
        json.dumps([{"id": "legacy-video", "state": "to_do", "topic": "Vídeo antigo"}]),
        encoding="utf-8",
    )
    (legacy_state / "queues.json").write_text(json.dumps({"script": ["legacy-video"]}), encoding="utf-8")
    (current_state / "tasks.json").write_text("[]\n", encoding="utf-8")
    (current_state / "queues.json").write_text(json.dumps({"script": []}), encoding="utf-8")

    environment = os.environ.copy()
    environment["HOME"] = str(tmp_path)
    environment.pop("THUNDERBOLT_HOME", None)
    completed = subprocess.run(
        ["node", str(ROOT / "scripts" / "install.mjs"), "--skip-python-deps", "--skip-moneyprinter"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    tasks = json.loads((current_state / "tasks.json").read_text(encoding="utf-8"))
    queues = json.loads((current_state / "queues.json").read_text(encoding="utf-8"))
    assert [task["id"] for task in tasks] == ["legacy-video"]
    assert queues["script"] == ["legacy-video"]
    assert "não elimina tarefas" in completed.stdout
