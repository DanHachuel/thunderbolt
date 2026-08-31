from pathlib import Path

from integrations.platforms import IntegrationResult
from integrations.upload_routing import upload_with_default_route


def _settings():
    return {
        "composio_enabled": True,
        "composio_auto_upload": True,
        "composio_api_key": "composio-test-key",
        "composio_user_id": "user-1",
        "composio_tool_slug": "VIDEO_UPLOAD",
        "composio_file_field": "file",
        "composio_arguments_json": "{}",
        "postiz_enabled": False,
    }


def test_composio_is_first_route_when_configured(tmp_path: Path):
    calls = []

    def composio(settings, **kwargs):
        calls.append(("composio", kwargs["video_path"]))
        return IntegrationResult(True, "Composio ok", {"provider_id": "123"})

    def official(*args, **kwargs):
        calls.append(("official", ""))
        return IntegrationResult(True, "Official ok", {})

    result = upload_with_default_route(
        _settings(),
        storage_root=tmp_path,
        channel={"id": "channel-1"},
        account=None,
        video_path=str(tmp_path / "video.mp4"),
        title="Demo",
        composio_publisher=composio,
        official_uploader=official,
    )
    assert result.ok
    assert result.data["route"] == "Composio"
    assert calls == [("composio", str(tmp_path / "video.mp4"))]


def test_composio_failure_falls_back_to_official(tmp_path: Path):
    calls = []

    def composio(settings, **kwargs):
        calls.append("composio")
        return IntegrationResult(False, "Composio unavailable", {})

    def official(*args, **kwargs):
        calls.append("official")
        return IntegrationResult(True, "Official ok", {})

    result = upload_with_default_route(
        _settings(),
        storage_root=tmp_path,
        channel={"id": "channel-1"},
        account=None,
        video_path=str(tmp_path / "video.mp4"),
        title="Demo",
        composio_publisher=composio,
        official_uploader=official,
    )
    assert result.ok
    assert result.data["route"] == "API Oficial"
    assert calls == ["composio", "official"]


def test_automation_worker_requires_configured_composio_or_another_route():
    source = Path(__file__).parents[1].joinpath("hermes_ui", "pipeline_worker.py").read_text(encoding="utf-8")
    assert "configured_composio" in source
    assert "configured_composio or configured_account_id" in source
