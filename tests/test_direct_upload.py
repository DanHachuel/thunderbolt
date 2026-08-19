from pathlib import Path

from integrations.youtube_direct_upload import YouTubeDirectUploader, validate_direct_upload


class FakeResponse:
    def __init__(self, headers=None, body=None, content=b"{}", status_code=200):
        self.headers = headers or {}
        self._body = body or {}
        self.content = content
        self.status_code = status_code
        self.text = content.decode("utf-8", errors="ignore")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP error")

    def json(self):
        return self._body


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if "upload/studio" in url:
            return FakeResponse(headers={"x-goog-upload-header-scotty-resource-id": "resource-1", "x-goog-upload-url": "https://upload.test/chunk", "x-guploader-uploadid": "upload-1"})
        if "createvideo" in url:
            return FakeResponse(body={"videoId": "video-123"}, content=b'{"videoId":"video-123"}')
        return FakeResponse(content=b"ok")


def valid_settings():
    return {
        "direct_cookie_sid": "sid", "direct_cookie_ssid": "ssid", "direct_cookie_hsid": "hsid", "direct_cookie_apisid": "apisid", "direct_cookie_sapisid": "sapisid",
        "direct_session_info": "session-info", "direct_innertube_api_key": "innertube-key",
    }


def test_direct_upload_requires_manual_session_values(tmp_path: Path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")
    error = validate_direct_upload(str(video), {"delegated_session_id": ""}, valid_settings())
    assert error and "DELEGATED_SESSION_ID" in error


def test_direct_upload_uses_page_id_and_chunks(tmp_path: Path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"x" * 262144 + b"last")
    session = FakeSession()
    result = YouTubeDirectUploader(valid_settings(), {"delegated_session_id": "123456"}, session=session).upload(str(video), title="Título", description="Descrição", chunk_size=262144)
    assert result.ok
    assert result.data["video_id"] == "video-123"
    create_call = next(call for call in session.calls if "createvideo" in call[0])
    assert '"onBehalfOfUser": "123456"' in create_call[1]["data"]
    chunk_calls = [call for call in session.calls if "chunk" in call[0]]
    assert len(chunk_calls) == 2
    assert chunk_calls[-1][1]["headers"]["X-Goog-Upload-Command"] == "upload, finalize"
