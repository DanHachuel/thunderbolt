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


def test_oauth_uses_fixed_loopback_redirect_uri(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("THUNDERBOLT_OAUTH_LOOPBACK_HOST", raising=False)
    monkeypatch.delenv("THUNDERBOLT_OAUTH_LOOPBACK_PORT", raising=False)
    uploader = YouTubeAutomationAgentUploader(
        {"youtube_client_id": "oauth-client-id", "youtube_client_secret": "oauth-client-secret"},
        tmp_path,
    )
    assert uploader._client_config()["installed"]["redirect_uris"] == ["http://127.0.0.1:8765/"]


def test_oauth_uses_client_pair_without_data_api_key(tmp_path: Path):
    uploader = YouTubeAutomationAgentUploader(
        {"youtube_client_id": "oauth-client-id", "youtube_client_secret": "oauth-client-secret"},
        tmp_path,
    )
    assert uploader.configured
    assert uploader.client_id == "oauth-client-id"
    assert uploader.client_secret == "oauth-client-secret"


def test_selected_account_uses_batch_token_path(tmp_path: Path):
    account = {"id": "account-1", "email": "channel@example.com", "client_id": "account-client", "client_secret": "account-secret"}
    uploader = YouTubeAutomationAgentUploader({}, tmp_path, account=account)
    assert uploader.client_id == "account-client"
    assert uploader.client_secret == "account-secret"
    assert any("youtube_batch_tokens" in str(path) for path in uploader._token_candidates())


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
