import json
from pathlib import Path

from integrations import upload_routing
from integrations.platforms import IntegrationResult


def _settings(arguments="{}"):
    return {
        "composio_enabled": True,
        "composio_auto_upload": True,
        "composio_api_key": "composio-test-key",
        "composio_user_id": "user-1",
        "composio_tool_slug": "YOUTUBE_UPLOAD",
        "composio_file_field": "video",
        "composio_channel_field": "channel_id",
        "composio_arguments_json": arguments,
        "postiz_enabled": False,
    }


def test_default_composio_route_injects_task_youtube_channel_id(monkeypatch, tmp_path: Path):
    captured = {}

    def fake_execute(api_key, user_id, slug, video_path, file_field, arguments_json):
        captured.update(api_key=api_key, user_id=user_id, slug=slug, video_path=video_path, file_field=file_field, arguments=json.loads(arguments_json))
        return {"successful": True, "data": {"remote_id": "abc"}, "error": "", "log_id": "log-1"}

    monkeypatch.setattr(upload_routing, "execute_upload", fake_execute)
    result = upload_routing.upload_with_default_route(
        _settings('{"title":"Demo"}'),
        storage_root=tmp_path,
        channel={"id": "local-1", "youtube_channel_id": "UC-CORRECT"},
        account=None,
        video_path=str(tmp_path / "video.mp4"),
        title="Demo",
    )
    assert result.ok
    assert result.data["route"] == "Composio"
    assert captured["arguments"] == {
        "title": "Demo",
        "channel_id": "UC-CORRECT",
        "privacy_status": "unlisted",
        "category_id": "22",
        "language": "pt-BR",
    }
    assert captured["file_field"] == "videoFilePath"


def test_default_composio_route_blocks_conflicting_channel(monkeypatch, tmp_path: Path):
    called = []

    def fake_execute(*args):
        called.append(args)
        return {"successful": True, "data": {}, "error": "", "log_id": ""}

    monkeypatch.setattr(upload_routing, "execute_upload", fake_execute)
    result = upload_routing._composio_upload(
        _settings('{"channel_id":"UC-WRONG"}'),
        channel={"id": "local-1", "youtube_channel_id": "UC-CORRECT"},
        video_path=str(tmp_path / "video.mp4"),
    )
    assert not result.ok
    assert "outro canal" in result.message
    assert called == []


def test_automation_source_keeps_channel_field_internal():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert "composio_channel_field = str(settings.get(\"composio_channel_field\") or \"\")" in source
    assert "composio_channel_field" in source
