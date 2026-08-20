import json
from pathlib import Path

from hermes_ui import mcp, storage
from hermes_ui.mcp_server import _MCPDispatcher, _tool_definitions


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


def test_server_config_persists_safe_defaults_and_updates(monkeypatch, tmp_path):
    _use_temp_storage(monkeypatch, tmp_path)
    config = mcp.load_server_config()
    assert config["enabled"] is False
    assert config["host"] == "127.0.0.1"
    assert config["port"] == 3031
    saved = mcp.save_server_config(enabled=True, port=3998, write_enabled=True)
    assert saved["enabled"] is True
    assert saved["port"] == 3998
    assert saved["write_enabled"] is True
    loaded = mcp.load_server_config()
    assert loaded["port"] == 3998
    assert loaded["write_enabled"] is True
    assert "auth_token" in json.loads((storage.STATE / "mcp_server.json").read_text(encoding="utf-8"))


def test_server_tools_hide_write_tool_by_default():
    read_only = _tool_definitions(False)
    writable = _tool_definitions(True)
    assert "thunderbolt_create_video_batch" not in {tool["name"] for tool in read_only}
    assert "thunderbolt_create_video_batch" in {tool["name"] for tool in writable}


def test_server_dispatcher_supports_initialize_list_and_status(monkeypatch, tmp_path):
    _use_temp_storage(monkeypatch, tmp_path)
    dispatcher = _MCPDispatcher()
    initialized = dispatcher.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
    assert initialized["result"]["capabilities"]["tools"]["listChanged"] is False
    listed = dispatcher.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    names = {tool["name"] for tool in listed["result"]["tools"]}
    assert "thunderbolt_get_status" in names
    status = dispatcher.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "thunderbolt_get_status", "arguments": {}}})
    assert status["result"]["isError"] is False
    assert status["result"]["structuredContent"]["channels"] == 0


def test_skill_install_is_local_and_overwrites_destination(monkeypatch, tmp_path):
    storage_root = _use_temp_storage(monkeypatch, tmp_path)
    packaged = tmp_path / "packaged-skill.md"
    packaged.write_text("# local skill\n", encoding="utf-8")
    monkeypatch.setattr(mcp, "skill_source_path", lambda: packaged)

    destination = mcp.install_skill_locally()
    assert destination == storage_root / "skills" / mcp.SKILL_FILENAME
    assert destination.read_text(encoding="utf-8") == "# local skill\n"
    assert destination.parent == storage_root / "skills"
