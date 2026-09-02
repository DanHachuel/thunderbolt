from __future__ import annotations

import json

from app.modules.token_optimizer import compressor, metrics
from hermes_ui import storage


def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "STORAGE", tmp_path)
    monkeypatch.setattr(storage, "STATE", tmp_path / "state")
    storage.ensure_storage()


def test_json_compression_is_reversible_and_redacts(monkeypatch, tmp_path):
    isolated(monkeypatch, tmp_path)
    payload = {"items": [{"id": i, "name": f"Item {i}"} for i in range(300)], "api_key": "super-secret-value"}
    result = compressor.compress_text(json.dumps(payload), "json")
    assert result.applied is True
    assert "super-secret-value" not in result.content
    assert compressor.retrieve_original(result.original_hash) == json.dumps(payload)
    stats = metrics.get_stats()
    assert stats["calls"] == 1
    assert stats["reduction_percent"] > 0


def test_disabled_lever_returns_original(monkeypatch, tmp_path):
    isolated(monkeypatch, tmp_path)
    raw = json.dumps({"items": list(range(300))})
    result = compressor.compress_text(raw, "json", settings={"token_optimizer_enabled": False})
    assert result.content == raw
    assert result.applied is False


def test_malformed_json_falls_back_without_error(monkeypatch, tmp_path):
    isolated(monkeypatch, tmp_path)
    raw = "not json " * 200
    result = compressor.compress_text(raw, "json")
    assert result.content == raw
    assert result.fallback is False


def test_installation_check():
    status = compressor.check_installation()
    assert status["installed"] is True
    assert status["version"]
