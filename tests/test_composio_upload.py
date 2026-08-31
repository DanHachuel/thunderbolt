import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from integrations import composio_upload


def test_parse_arguments_requires_object():
    assert composio_upload.parse_arguments('{"title": "Demo"}') == {"title": "Demo"}
    with pytest.raises(composio_upload.ComposioUploadError):
        composio_upload.parse_arguments("[]")
    with pytest.raises(composio_upload.ComposioUploadError):
        composio_upload.parse_arguments("not-json")


def test_execute_upload_injects_selected_file_field(monkeypatch, tmp_path):
    video = tmp_path / "demo.mp4"
    video.write_bytes(b"video")
    captured = {}

    class FakeTools:
        def execute(self, slug, **kwargs):
            captured.update(slug=slug, kwargs=kwargs)
            return SimpleNamespace(data={"remote_id": "123"}, error=None, log_id="log-123")

    class FakeClient:
        tools = FakeTools()

    monkeypatch.setattr(composio_upload, "_client", lambda *args, **kwargs: FakeClient())
    result = composio_upload.execute_upload("ak_123456789", "user-1", "DRIVE_UPLOAD_FILE", str(video), "file", '{"title":"Demo"}')
    assert result["successful"] is True
    assert result["log_id"] == "log-123"
    assert captured["slug"] == "DRIVE_UPLOAD_FILE"
    assert captured["kwargs"]["arguments"]["file"] == str(video.resolve())
    assert captured["kwargs"]["arguments"]["title"] == "Demo"
    assert "ak_123456789" not in json.dumps(result)


def test_execute_upload_rejects_existing_file_value(tmp_path):
    video = tmp_path / "demo.mp4"
    video.write_bytes(b"video")
    with pytest.raises(composio_upload.ComposioUploadError, match="já contém"):
        composio_upload.execute_upload("ak_123456789", "user-1", "TOOL", str(video), "file", '{"file":"other.mp4"}')


def test_discover_tools_normalises_sdk_items(monkeypatch):
    class FakeTools:
        def get(self, user_id, **kwargs):
            assert user_id == "user-1"
            assert kwargs["search"] == "upload video"
            return [SimpleNamespace(slug="DRIVE_UPLOAD_FILE", name="Upload file", description="Upload", toolkit=SimpleNamespace(slug="drive"), input_parameters={"type": "object"})]

    class FakeClient:
        tools = FakeTools()

    monkeypatch.setattr(composio_upload, "_client", lambda *args, **kwargs: FakeClient())
    result = composio_upload.discover_tools("ak_123456789", "user-1", "upload video")
    assert result[0]["slug"] == "DRIVE_UPLOAD_FILE"
    assert result[0]["toolkit"] == "drive"
    assert result[0]["schema"] == {"type": "object"}


def test_source_contains_composio_ui_contract():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert "Upload via Composio" in source
    assert "upload_composio_api_key" in source
    assert "test_configuration" in source
    assert "Secção reservada para uma futura integração Composio" not in source
