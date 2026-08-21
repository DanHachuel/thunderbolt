import json
from pathlib import Path

from integrations.platforms import IntegrationResult
from integrations.postiz import PostizAdapter
from integrations import upload_routing


class _Response:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload, ensure_ascii=False)

    def json(self):
        return self._payload


def _settings():
    return {
        "postiz_enabled": True,
        "postiz_api_key": "postiz-test-key",
        "postiz_base_url": "https://postiz.example/public/v1",
        "postiz_integration_id": "yt-integration",
    }


def test_postiz_list_integrations_uses_raw_authorization(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "integrations.postiz.requests.get",
        lambda url, **kwargs: captured.update({"url": url, "kwargs": kwargs}) or _Response([{"id": "yt-1", "name": "YouTube"}]),
    )
    result = PostizAdapter(_settings()).list_integrations()
    assert result.ok
    assert result.data["integrations"][0]["id"] == "yt-1"
    assert captured["url"].endswith("/integrations")
    assert captured["kwargs"]["headers"]["Authorization"] == "postiz-test-key"


def test_postiz_publish_uploads_mp4_then_creates_youtube_post(tmp_path, monkeypatch):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"fake-mp4")
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        if url.endswith("/upload"):
            return _Response({"id": "asset-1", "path": "https://uploads.example/video.mp4"})
        return _Response({"postId": "post-1"})

    monkeypatch.setattr("integrations.postiz.requests.post", fake_post)
    result = PostizAdapter(_settings()).publish_video(video, integration_id="yt-1", title="Título", description="Descrição", visibility="public", tags=["história"])
    assert result.ok
    assert calls[0][0].endswith("/upload")
    assert calls[0][1]["headers"]["Authorization"] == "postiz-test-key"
    payload = calls[1][1]["json"]
    assert payload["posts"][0]["integration"]["id"] == "yt-1"
    assert payload["posts"][0]["value"][0]["image"][0]["id"] == "asset-1"
    assert payload["posts"][0]["settings"]["__type"] == "youtube"
    assert payload["posts"][0]["settings"]["type"] == "public"


def test_ordered_route_stops_after_official_success(tmp_path, monkeypatch):
    monkeypatch.setenv("THUNDERBOLT_STORAGE_DIR", str(tmp_path / "storage"))
    # Rebind storage functions used by the routing module to an isolated fake state.
    quota = {}
    monkeypatch.setattr(upload_routing, "read_json", lambda _name, _default=None: quota)
    monkeypatch.setattr(upload_routing, "write_json", lambda _name, value: quota.update(value))
    calls = []
    result = upload_routing.upload_with_default_route(
        {},
        storage_root=tmp_path / "storage",
        channel={"id": "channel-1", "google_account_id": "account-1"},
        account={"id": "account-1"},
        video_path="video.mp4",
        title="Título",
        official_uploader=lambda *args, **kwargs: calls.append("official") or IntegrationResult(True, "ok", {"video_id": "yt-1"}),
        direct_uploader=lambda *args, **kwargs: calls.append("direct") or IntegrationResult(True, "should-not-run", {}),
        postiz_publisher=lambda *args, **kwargs: calls.append("postiz") or IntegrationResult(True, "should-not-run", {}),
    )
    assert result.ok
    assert result.data["route"] == "API Oficial"
    assert calls == ["official"]
    assert quota["account:account-1"]["count"] == 1


def test_ordered_route_uses_direct_then_postiz_after_official_failure(tmp_path, monkeypatch):
    quota = {"account:account-1": {"date": "2099-01-01", "count": 5}}
    monkeypatch.setattr(upload_routing, "read_json", lambda _name, _default=None: quota)
    monkeypatch.setattr(upload_routing, "write_json", lambda _name, value: quota.update(value))
    monkeypatch.setattr(upload_routing, "document_status", lambda *args, **kwargs: {"ready": True, "missing_cookies": [], "has_session_info": True, "has_innertube_api_key": True, "has_delegated_session_id": True})
    calls = []
    result = upload_routing.upload_with_default_route(
        {"postiz_enabled": True, "postiz_api_key": "key"},
        storage_root=tmp_path / "storage",
        channel={"id": "channel-1", "google_account_id": "account-1"},
        account={"id": "account-1"},
        video_path="video.mp4",
        title="Título",
        official_uploader=lambda *args, **kwargs: calls.append("official") or IntegrationResult(False, "failed", {}),
        direct_uploader=lambda *args, **kwargs: calls.append("direct") or IntegrationResult(False, "failed", {}),
        postiz_publisher=lambda *args, **kwargs: calls.append("postiz") or IntegrationResult(True, "posted", {"post_id": "p-1"}),
    )
    assert result.ok
    assert result.data["route"] == "Postiz"
    assert calls == ["official", "direct", "postiz"]
    assert [attempt["route"] for attempt in result.data["attempts"]] == ["API Oficial", "Upload directo", "Postiz"]
