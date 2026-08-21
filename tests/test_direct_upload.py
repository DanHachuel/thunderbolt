import json
from pathlib import Path

from integrations.youtube_direct_credentials import credentials_document_path, delete_credentials_document, direct_account_status, document_status, load_credentials_document, merge_credentials_document, parse_cookie_file, parse_credentials_document, save_cookie_file, save_credentials_document, update_credentials_document_session_info
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


def test_cookie_file_parser_accepts_json_and_netscape(tmp_path: Path):
    json_content = b'{"SID":"sid-a","SSID":"ssid-a","HSID":"hsid-a","APISID":"apisid-a","SAPISID":"sapisid-a"}'
    assert parse_cookie_file(json_content)["SID"] == "sid-a"
    netscape = b".youtube.com\tTRUE\t/\tTRUE\t0\tSID\tsid-n\n.youtube.com\tTRUE\t/\tTRUE\t0\tSSID\tssid-n\n.youtube.com\tTRUE\t/\tTRUE\t0\tHSID\thsid-n\n.youtube.com\tTRUE\t/\tTRUE\t0\tAPISID\tapisid-n\n.youtube.com\tTRUE\t/\tTRUE\t0\tSAPISID\tsapisid-n\n"
    assert parse_cookie_file(netscape, "cookies.txt")["SAPISID"] == "sapisid-n"


def test_cookie_file_is_saved_per_google_account(tmp_path: Path):
    account = {"id": "google-one", "email": "one@example.com", "direct_session_info": "session-one"}
    path = save_cookie_file(tmp_path, account, b'{"SID":"sid","SSID":"ssid","HSID":"hsid","APISID":"apisid","SAPISID":"sapisid"}')
    assert path == tmp_path / "youtube_direct_accounts" / "google-one" / "cookies.json"
    status = direct_account_status(tmp_path, account)
    assert status["cookie_file_exists"] is True
    assert status["missing_cookies"] == []
    assert status["ready"] is False


def test_direct_upload_uses_account_credentials_and_channel_page_id(tmp_path: Path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")
    account = {"id": "google-one", "email": "one@example.com", "direct_session_info": "session-from-account"}
    save_cookie_file(tmp_path, account, b'{"SID":"sid-account","SSID":"ssid-account","HSID":"hsid-account","APISID":"apisid-account","SAPISID":"sapisid-account"}')
    settings = {"direct_innertube_api_key": "innertube-key", "direct_session_info": "wrong-global-session"}
    session = FakeSession()
    result = YouTubeDirectUploader(settings, {"delegated_session_id": "channel-page"}, account=account, storage_root=tmp_path, session=session).upload(str(video), title="Título")
    assert result.ok
    create_call = next(call for call in session.calls if "createvideo" in call[0])
    assert '"token": "session-from-account"' in create_call[1]["data"]
    assert create_call[1]["headers"]["Cookie"].find("sid-account") >= 0



def test_credentials_document_keeps_all_direct_data_per_google_account(tmp_path: Path):
    account = {"id": "google-doc", "email": "doc@example.com", "innertube_api_key": "innertube-account"}
    channel = {"id": "channel-doc", "google_account_id": "google-doc"}
    raw = {
        "account_id": "google-doc",
        "email": "doc@example.com",
        "sessionInfo": "session-document",
        "cookies": {"SID": "sid", "SSID": "ssid", "HSID": "hsid", "APISID": "apisid", "SAPISID": "sapisid"},
        "INNERTUBE_API_KEY": "legacy-document-value",
        "chunk_size": 524288,
        "delegated_session_ids": {"channel-doc": "delegated-document"},
    }
    parsed = parse_credentials_document(json.dumps(raw).encode("utf-8"), "credentials.json")
    save_credentials_document(tmp_path, account, parsed)
    loaded = load_credentials_document(tmp_path, account, channels=[channel])
    status = document_status(tmp_path, account, channel, channels=[channel])
    assert credentials_document_path(tmp_path, account).name == "credentials.json"
    assert loaded["cookies"]["SID"] == "sid"
    assert loaded["sessionInfo"] == "session-document"
    assert "INNERTUBE_API_KEY" not in json.loads(credentials_document_path(tmp_path, account).read_text(encoding="utf-8"))
    assert loaded.get("INNERTUBE_API_KEY", "") == ""
    assert loaded["chunk_size"] == 524288
    assert loaded["delegated_session_ids"]["channel-doc"] == "delegated-document"
    assert status["ready"] is True


def test_session_info_override_is_saved_in_credentials_document(tmp_path: Path):
    account = {"id": "google-session", "email": "session@example.com"}
    raw = {
        "account_id": "google-session",
        "email": "session@example.com",
        "cookies": {"SID": "sid", "SSID": "ssid", "HSID": "hsid", "APISID": "apisid", "SAPISID": "sapisid"},
        "INNERTUBE_API_KEY": "innertube",
        "delegated_session_ids": {},
    }
    parsed = parse_credentials_document(json.dumps(raw).encode("utf-8"), "credentials.json", session_info_override="session-from-ui")
    save_credentials_document(tmp_path, account, parsed)
    assert load_credentials_document(tmp_path, account)["sessionInfo"] == "session-from-ui"
    update_credentials_document_session_info(tmp_path, account, "session-updated")
    assert load_credentials_document(tmp_path, account)["sessionInfo"] == "session-updated"


def test_delete_credentials_document_removes_only_selected_account(tmp_path: Path):
    first = {"id": "google-first", "email": "first@example.com"}
    second = {"id": "google-second", "email": "second@example.com"}
    for account in (first, second):
        save_credentials_document(tmp_path, account, {
            "account_id": account["id"],
            "email": account["email"],
            "sessionInfo": "session",
            "cookies": {"SID": "sid", "SSID": "ssid", "HSID": "hsid", "APISID": "apisid", "SAPISID": "sapisid"},
            "INNERTUBE_API_KEY": "innertube",
            "delegated_session_ids": {},
        })
    delete_credentials_document(tmp_path, first)
    assert not credentials_document_path(tmp_path, first).exists()
    assert credentials_document_path(tmp_path, second).exists()


def test_merge_credentials_document_preserves_existing_fields_and_strips_placeholders(tmp_path: Path):
    account = {"id": "google-merge", "email": "merge@example.com", "innertube_api_key": "innertube-account"}
    existing = {
        "account_id": "google-merge",
        "email": "merge@example.com",
        "sessionInfo": "session-existing",
        "cookies": {"SID": "sid-existing", "SSID": "ssid-existing", "HSID": "hsid-existing", "APISID": "apisid-existing", "SAPISID": "sapisid-existing"},
        "INNERTUBE_API_KEY": "innertube-existing",
        "chunk_size": 524288,
        "delegated_session_ids": {"channel-merge": "delegated-existing"},
    }
    save_credentials_document(tmp_path, account, existing)
    partial_upload = {
        "account_id": "google-merge",
        "email": "merge@example.com",
        "sessionInfo": "...",
        "cookies": {"SID": "sid-new", "SSID": "...", "HSID": "hsid-new", "APISID": "apisid-new", "SAPISID": "sapisid-new"},
        "INNERTUBE_API_KEY": "...",
    }

    merged_path = merge_credentials_document(tmp_path, account, json.dumps(partial_upload).encode("utf-8"), "cookies-only.json")
    assert merged_path == credentials_document_path(tmp_path, account)
    merged = load_credentials_document(tmp_path, account)
    assert merged["sessionInfo"] == "session-existing"
    assert merged.get("INNERTUBE_API_KEY", "") == ""
    assert merged["cookies"]["SID"] == "sid-new"
    assert merged["cookies"]["SSID"] == "ssid-existing"
    assert merged["delegated_session_ids"]["channel-merge"] == "delegated-existing"

    saved = load_credentials_document(tmp_path, account)
    assert saved["sessionInfo"] == "session-existing"
    assert saved.get("INNERTUBE_API_KEY", "") == ""
    assert saved["cookies"]["SSID"] == "ssid-existing"


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
