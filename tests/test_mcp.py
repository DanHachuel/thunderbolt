import json
from pathlib import Path

from hermes_ui import mcp, storage


def _use_temp_storage(monkeypatch, tmp_path):
    storage_root = tmp_path / "storage"
    monkeypatch.setattr(storage, "STORAGE", storage_root)
    monkeypatch.setattr(storage, "STATE", storage_root / "state")
    monkeypatch.setattr(storage, "BLUEPRINTS", storage_root / "blueprints")
    storage.ensure_storage()
    return storage_root


def test_catalog_has_four_external_integrations_and_documented_ports():
    catalog = mcp._merge_defaults([])
    assert [item["id"] for item in catalog] == [
        "short-video-maker",
        "autovio",
        "openmontage",
        "opencut",
    ]
    assert [item["port"] for item in catalog] == [3123, 3001, 8000, 8787]
    assert all(item["active"] is False for item in catalog)
    assert all(item["repository"].startswith("https://github.com/") for item in catalog)


def test_catalog_update_persists_port_and_active(monkeypatch, tmp_path):
    _use_temp_storage(monkeypatch, tmp_path)
    updated = mcp.update_integration("autovio", port=3999, active=True)
    saved = next(item for item in updated if item["id"] == "autovio")
    assert saved["port"] == 3999
    assert saved["active"] is True
    on_disk = json.loads((storage.STATE / "mcp_integrations.json").read_text(encoding="utf-8"))
    assert next(item for item in on_disk if item["id"] == "autovio")["port"] == 3999


def test_skill_install_is_local_and_overwrites_destination(monkeypatch, tmp_path):
    storage_root = _use_temp_storage(monkeypatch, tmp_path)
    packaged = tmp_path / "packaged-skill.md"
    packaged.write_text("# local skill\n", encoding="utf-8")
    monkeypatch.setattr(mcp, "skill_source_path", lambda: packaged)

    destination = mcp.install_skill_locally()
    assert destination == storage_root / "skills" / mcp.SKILL_FILENAME
    assert destination.read_text(encoding="utf-8") == "# local skill\n"
    assert destination.parent == storage_root / "skills"
