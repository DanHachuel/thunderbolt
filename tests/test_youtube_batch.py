from __future__ import annotations

import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

from integrations import youtube_batch
from integrations.platforms import IntegrationResult


def test_loopback_redirect_uri_is_deterministic_and_configurable(monkeypatch):
    monkeypatch.delenv("THUNDERBOLT_OAUTH_LOOPBACK_HOST", raising=False)
    monkeypatch.delenv("THUNDERBOLT_OAUTH_LOOPBACK_PORT", raising=False)
    assert youtube_batch.loopback_redirect_uri() == "http://127.0.0.1:8765/"
    monkeypatch.setenv("THUNDERBOLT_OAUTH_LOOPBACK_HOST", "localhost")
    monkeypatch.setenv("THUNDERBOLT_OAUTH_LOOPBACK_PORT", "9876")
    assert youtube_batch.loopback_redirect_uri() == "http://localhost:9876/"
    assert youtube_batch._client_config({"client_id": "id", "client_secret": "secret"})["installed"]["redirect_uris"] == ["http://localhost:9876/"]


def test_redirect_uri_mismatch_message_is_actionable():
    result = youtube_batch._authorization_error_message("one@example.com", RuntimeError("Error 400: redirect_uri_mismatch"))
    assert "redirect_uri_mismatch" in result
    assert "Desktop app" in result
    assert "http://127.0.0.1:8765/" in result


def test_authorize_retries_with_dynamic_port_when_loopback_port_is_busy(tmp_path, monkeypatch):
    calls = []

    class AddressInUseError(OSError):
        winerror = 10048

    class Credentials:
        def to_json(self):
            return '{"refresh_token":"refresh-token"}'

    class Flow:
        @classmethod
        def from_client_config(cls, config, scopes):
            assert config["installed"]["redirect_uris"] == ["http://127.0.0.1:8765/"]
            assert scopes == youtube_batch.BATCH_SCOPES
            return cls()

        def run_local_server(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise AddressInUseError("[WinError 10048] socket already in use")
            return Credentials()

    fake_flow = types.ModuleType("google_auth_oauthlib.flow")
    fake_flow.InstalledAppFlow = Flow
    monkeypatch.setitem(sys.modules, "google_auth_oauthlib.flow", fake_flow)

    result = youtube_batch.authorize_account(
        {"id": "google-one", "email": "one@example.com", "client_id": "client", "client_secret": "secret"},
        tmp_path,
        open_browser=False,
    )

    assert result.ok
    assert [call["port"] for call in calls] == [8765, 0]
    assert youtube_batch.token_path(tmp_path, {"id": "google-one", "email": "one@example.com"}).exists()


def test_account_key_and_token_path_are_separate_per_account(tmp_path):
    first = {"id": "google_batch_one", "email": "one@example.com"}
    second = {"id": "google_batch_two", "email": "two@example.com"}
    assert youtube_batch.account_key(first) != youtube_batch.account_key(second)
    assert youtube_batch.token_path(tmp_path, first).parent == tmp_path / "state" / "youtube_batch_tokens"
    assert youtube_batch.token_path(tmp_path, first) != youtube_batch.token_path(tmp_path, second)


def test_account_status_rejects_incomplete_configuration(tmp_path):
    result = youtube_batch.account_status({"id": "account", "email": "one@example.com"}, tmp_path)
    assert not result.ok
    assert result.data["status"] == "not_configured"


def test_account_status_is_passive_and_does_not_load_token(tmp_path, monkeypatch):
    account = {"id": "google_batch_one", "email": "one@example.com", "client_id": "client", "client_secret": "secret"}
    path = youtube_batch.token_path(tmp_path, account)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"refresh_token":"refresh"}', encoding="utf-8")
    monkeypatch.setattr(youtube_batch, "_load_credentials", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("status não deve renovar token")))
    result = youtube_batch.account_status(account, tmp_path)
    assert result.ok
    assert result.data["refresh_on_use"] is True


def test_channel_record_normalizes_metadata_and_missing_statistics():
    record = youtube_batch._channel_record({
        "id": "UC123",
        "snippet": {
            "title": "Canal Exemplo",
            "customUrl": "@exemplo",
            "description": "Descrição",
            "publishedAt": "2026-01-01T00:00:00Z",
            "thumbnails": {"default": {"url": "https://img.example/thumb.jpg"}},
        },
        "statistics": {"videoCount": "12", "viewCount": "900"},
    })
    assert record["youtube_channel_id"] == "UC123"
    assert record["name"] == "Canal Exemplo"
    assert record["handle"] == "@exemplo"
    assert record["url"] == "https://www.youtube.com/@exemplo"
    assert record["subscriber_count"] is None
    assert record["video_count"] == 12
    assert record["metrics_source"] == "youtube_data_api_oauth_mine"


def test_list_my_channels_uses_mine_true_and_follows_pagination(tmp_path, monkeypatch):
    account = {"id": "google_batch_one", "email": "one@example.com", "client_id": "client", "client_secret": "secret"}
    token = youtube_batch.token_path(tmp_path, account)
    token.parent.mkdir(parents=True, exist_ok=True)
    token.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(youtube_batch, "account_status", lambda *_args, **_kwargs: IntegrationResult(True, "ready", {"status": "ready"}))
    monkeypatch.setattr(youtube_batch, "_load_credentials", lambda *_args, **_kwargs: object())

    requests = []

    class FakeRequest:
        def __init__(self, payload):
            self.payload = payload

        def execute(self):
            return self.payload

    class FakeChannels:
        def list(self, **kwargs):
            requests.append(kwargs)
            if kwargs.get("pageToken"):
                return FakeRequest({"items": [{"id": "UC2", "snippet": {"title": "Dois"}, "statistics": {}}]})
            return FakeRequest({
                "items": [{"id": "UC1", "snippet": {"title": "Um"}, "statistics": {}}],
                "nextPageToken": "page-2",
            })

    class FakeService:
        def channels(self):
            return FakeChannels()

    fake_discovery = types.ModuleType("googleapiclient.discovery")
    fake_discovery.build = lambda *args, **kwargs: FakeService()
    fake_googleapiclient = types.ModuleType("googleapiclient")
    fake_googleapiclient.discovery = fake_discovery
    monkeypatch.setitem(sys.modules, "googleapiclient", fake_googleapiclient)
    monkeypatch.setitem(sys.modules, "googleapiclient.discovery", fake_discovery)

    result = youtube_batch.list_my_channels(account, tmp_path)
    assert result.ok
    assert result.data["count"] == 2
    assert [item["youtube_channel_id"] for item in result.data["channels"]] == ["UC1", "UC2"]
    assert requests[0]["mine"] is True
    assert requests[0]["maxResults"] == 50
    assert requests[0]["part"] == "snippet,contentDetails,statistics"
    assert requests[1]["pageToken"] == "page-2"


def test_delete_account_token_removes_only_batch_token(tmp_path):
    account = {"id": "google_batch_one", "email": "one@example.com"}
    path = youtube_batch.token_path(tmp_path, account)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("token", encoding="utf-8")
    youtube_batch.delete_account_token(account, tmp_path)
    assert not path.exists()
