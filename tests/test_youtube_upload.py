from pathlib import Path

from integrations.platforms import IntegrationResult
from integrations.youtube_upload import (
    DirectYouTubeOAuthUploader,
    YouTubeAutomationAgentUploader,
    build_agent_video_metadata,
    upload_youtube_with_fallback,
    validate_video_file,
)


def test_agent_metadata_matches_publishing_shape():
    payload = build_agent_video_metadata(
        title="Título",
        description="Descrição",
        tags=["um", "dois"],
        category_id="24",
        language="pt-BR",
        privacy_status="private",
        publish_at="2030-01-01T12:00:00Z",
    )
    assert payload["snippet"]["title"] == "Título"
    assert payload["snippet"]["tags"] == ["um", "dois"]
    assert payload["snippet"]["categoryId"] == "24"
    assert payload["snippet"]["defaultAudioLanguage"] == "pt-BR"
    assert payload["status"]["selfDeclaredMadeForKids"] is False
    assert payload["status"]["publishAt"].endswith("Z")


def test_invalid_video_is_rejected(tmp_path: Path):
    invalid = tmp_path / "video.mov"
    invalid.write_bytes(b"not-a-video")
    ok, message, path = validate_video_file(invalid)
    assert not ok
    assert "MP4" in message
    assert path.name == "video.mov"


def test_agent_is_primary_and_stops_on_success(monkeypatch, tmp_path: Path):
    calls: list[str] = []

    def primary(self, **kwargs):
        calls.append("agent")
        return IntegrationResult(True, "ok", {"video_id": "primary-id"})

    def fallback(self, **kwargs):
        calls.append("fallback")
        return IntegrationResult(True, "fallback", {"video_id": "fallback-id"})

    monkeypatch.setattr(YouTubeAutomationAgentUploader, "upload", primary)
    monkeypatch.setattr(DirectYouTubeOAuthUploader, "upload", fallback)
    result = upload_youtube_with_fallback({}, tmp_path, video_path="video.mp4", title="Título")
    assert result.ok
    assert calls == ["agent"]
    assert result.data["video_id"] == "primary-id"
    assert result.data["attempts"][0]["mechanism"] == "youtube-automation-agent-adaptado"


def test_fallback_runs_only_after_primary_failure(monkeypatch, tmp_path: Path):
    calls: list[str] = []

    def primary(self, **kwargs):
        calls.append("agent")
        return IntegrationResult(False, "agent failed", {"status": "upload_failed"})

    def fallback(self, **kwargs):
        calls.append("fallback")
        return IntegrationResult(True, "ok", {"video_id": "fallback-id"})

    monkeypatch.setattr(YouTubeAutomationAgentUploader, "upload", primary)
    monkeypatch.setattr(DirectYouTubeOAuthUploader, "upload", fallback)
    result = upload_youtube_with_fallback({}, tmp_path, video_path="video.mp4", title="Título")
    assert result.ok
    assert calls == ["agent", "fallback"]
    assert result.data["video_id"] == "fallback-id"
    assert "fallback" in result.data["mechanism"]
    assert len(result.data["attempts"]) == 2
