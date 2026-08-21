from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from integrations.youtube_direct_credentials import COOKIE_KEYS, delegated_session_id, load_credentials_document
from urllib.parse import quote

import requests


CHUNK_GRANULARITY = 262144
SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".webm", ".avi", ".mpeg", ".mpg", ".flv", ".wmv", ".3gpp"}


@dataclass
class DirectUploadResult:
    ok: bool
    message: str
    data: dict[str, Any]


def _direct_document(settings: dict[str, Any], channel: dict[str, Any], account: dict[str, Any] | None, storage_root: Path | None) -> dict[str, Any]:
    if account is not None and storage_root is not None:
        return load_credentials_document(storage_root, account, settings, [channel], create=True)
    return {
        "cookies": {key: str(settings.get(f"direct_cookie_{key.lower()}", "") or "").strip() for key in COOKIE_KEYS},
        "sessionInfo": str(settings.get("direct_session_info", "") or "").strip(),
        "INNERTUBE_API_KEY": str(settings.get("direct_innertube_api_key", "") or "").strip(),
        "chunk_size": int(settings.get("direct_chunk_size", CHUNK_GRANULARITY) or CHUNK_GRANULARITY),
        "delegated_session_ids": {str(channel.get("id") or ""): str(channel.get("delegated_session_id") or "").strip()},
    }


def _cookie_settings(settings: dict[str, Any], channel: dict[str, Any], account: dict[str, Any] | None = None, storage_root: Path | None = None) -> dict[str, str]:
    document = _direct_document(settings, channel, account, storage_root)
    cookies = document.get("cookies", {})
    return {key: str(cookies.get(key, "") or "").strip() for key in COOKIE_KEYS}


def _session_info(settings: dict[str, Any], channel: dict[str, Any], account: dict[str, Any] | None = None, storage_root: Path | None = None) -> str:
    return str(_direct_document(settings, channel, account, storage_root).get("sessionInfo", "") or "").strip()


def _innertube_api_key(settings: dict[str, Any], channel: dict[str, Any], account: dict[str, Any] | None = None, storage_root: Path | None = None) -> str:
    return str(_direct_document(settings, channel, account, storage_root).get("INNERTUBE_API_KEY", "") or "").strip()


def _delegated_session(settings: dict[str, Any], channel: dict[str, Any], account: dict[str, Any] | None = None, storage_root: Path | None = None) -> str:
    document = _direct_document(settings, channel, account, storage_root)
    if account is not None and storage_root is not None:
        return delegated_session_id(document, channel) or str(channel.get("delegated_session_id") or "").strip()
    return str(channel.get("delegated_session_id") or "").strip()


def _cookie_header(cookies: dict[str, str]) -> str:
    return ";".join(["CONSENT=YES+cb"] + [f"{key}={value}" for key, value in cookies.items() if value])


def _sapishash(sapisid: str, origin: str = "https://studio.youtube.com") -> str:
    timestamp = int(time.time())
    digest = hashlib.sha1(f"{timestamp} {sapisid} {origin}".encode("utf-8")).hexdigest()
    return f"{timestamp}_{digest}"


def _innertube_id() -> str:
    return f"innertube_studio:{secrets.token_hex(18)}:0"


def _header(response: requests.Response, name: str) -> str:
    wanted = name.lower()
    for key, value in response.headers.items():
        if key.lower() == wanted:
            return str(value)
    return ""


def validate_direct_upload(video_path: str | Path, channel: dict[str, Any], settings: dict[str, Any], account: dict[str, Any] | None = None, storage_root: Path | None = None) -> str | None:
    path = Path(video_path)
    if not path.exists() or not path.is_file():
        return "Ficheiro de vídeo não encontrado."
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return "Formato de vídeo não suportado pelo upload directo."
    if path.stat().st_size <= 0:
        return "O ficheiro de vídeo está vazio."
    cookies = _cookie_settings(settings, channel, account, storage_root)
    missing_cookies = [key for key, value in cookies.items() if not value]
    if missing_cookies:
        return f"Faltam cookies no documento de credenciais da conta: {', '.join(missing_cookies)}."
    if not _session_info(settings, channel, account, storage_root):
        return "Falta sessionInfo no documento de credenciais da conta."
    if not _innertube_api_key(settings, channel, account, storage_root):
        return "Falta INNERTUBE_API_KEY no documento de credenciais da conta."
    if not _delegated_session(settings, channel, account, storage_root):
        return "Falta DELEGATED_SESSION_ID deste canal no documento de credenciais da conta."
    return None


class YouTubeDirectUploader:
    def __init__(self, settings: dict[str, Any], channel: dict[str, Any], *, account: dict[str, Any] | None = None, storage_root: Path | None = None, session: requests.Session | None = None):
        self.settings = settings
        self.channel = channel
        self.account = account
        self.storage_root = storage_root
        self.session = session or requests.Session()
        self.document = _direct_document(settings, channel, account, storage_root)
        self.cookies = _cookie_settings(settings, channel, account, storage_root)
        self.session_info = _session_info(settings, channel, account, storage_root)
        self.delegated_session_id = _delegated_session(settings, channel, account, storage_root)
        self.innertube_api_key = _innertube_api_key(settings, channel, account, storage_root)
        self.cookie_header = _cookie_header(self.cookies)
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
        self.inner_tube = _innertube_id()
        self.google_upload: dict[str, str] = {}
        self.video_id = ""

    def _base_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Origin": "https://studio.youtube.com",
            "Referer": "https://studio.youtube.com/",
            "Cookie": self.cookie_header,
        }

    def describe_file(self, path: Path) -> None:
        headers = {
            **self._base_headers(),
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "X-Goog-Upload-File-Name": path.name,
            "X-Goog-Upload-Header-Content-Length": str(path.stat().st_size),
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Protocol": "resumable",
        }
        response = self.session.post("https://upload.youtube.com/upload/studio?authuser=0", headers=headers, data={"frontendUploadId": self.inner_tube}, timeout=60)
        response.raise_for_status()
        self.google_upload = {
            "resource_id": _header(response, "x-goog-upload-header-scotty-resource-id"),
            "upload_url": _header(response, "x-goog-upload-url"),
            "upload_id": _header(response, "x-guploader-uploadid"),
        }
        if not self.google_upload["upload_url"] or not self.google_upload["resource_id"]:
            raise RuntimeError("O YouTube não devolveu uma sessão de upload directo válida.")

    def create_video(self, title: str, description: str, visibility: str) -> None:
        payload = {
            "resourceId": {"scottyResourceId": {"id": self.google_upload["resource_id"]}},
            "frontendUploadId": self.inner_tube,
            "initialMetadata": {
                "title": {"newTitle": title},
                "description": {"newDescription": description},
                "privacy": {"newPrivacy": visibility},
                "draftState": {"isDraft": False},
                "targetedAudience": {"operation": "MDE_TARGETED_AUDIENCE_UPDATE_OPERATION_SET", "newTargetedAudience": "MDE_TARGETED_AUDIENCE_TYPE_ALL"},
            },
            "botguardClientResponse": f"${hashlib.sha1(os.urandom(16)).hexdigest()}",
            "context": {
                "client": {"clientName": 62, "clientVersion": "1.20210806.02.00", "hl": "pt-BR", "gl": "BR", "experimentsToken": "", "utcOffsetMinutes": 0},
                "request": {"sessionInfo": {"token": self.session_info}},
                "user": {"onBehalfOfUser": self.delegated_session_id},
            },
        }
        endpoint = f"https://studio.youtube.com/youtubei/v1/upload/createvideo?alt=json&key={quote(self.innertube_api_key)}"
        headers = {**self._base_headers(), "Content-Type": "application/json", "X-Youtube-Client-Name": "62", "X-Youtube-Client-Version": "1.20210806.02.00", "X-Goog-PageId": self.delegated_session_id, "Authorization": f"SAPISIDHASH {_sapishash(self.cookies['SAPISID'])}"}
        response = self.session.post(endpoint, headers=headers, data=json.dumps(payload), timeout=60)
        response.raise_for_status()
        body = response.json() if response.content else {}
        self.video_id = str(body.get("videoId") or body.get("video_id") or "")
        if not self.video_id:
            raise RuntimeError("O YouTube não devolveu o videoId após createvideo.")

    def upload_chunks(self, path: Path, chunk_size: int = CHUNK_GRANULARITY) -> None:
        chunk_size = max(CHUNK_GRANULARITY, int(chunk_size))
        chunk_size -= chunk_size % CHUNK_GRANULARITY
        if chunk_size == 0:
            chunk_size = CHUNK_GRANULARITY
        offset = 0
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(chunk_size)
                if not chunk:
                    break
                last = offset + len(chunk) >= path.stat().st_size
                headers = {**self._base_headers(), "Content-Type": "application/x-www-form-urlencoded;charset=utf-8", "X-Goog-Upload-Command": "upload, finalize" if last else "upload", "X-Goog-Upload-Offset": str(offset), "X-Goog-Upload-File-Name": quote(path.name)}
                response = self.session.post(self.google_upload["upload_url"], headers=headers, data=chunk, timeout=180)
                response.raise_for_status()
                offset += len(chunk)

    def upload(self, video_path: str | Path, *, title: str, description: str = "", visibility: str = "private", chunk_size: int | None = None) -> DirectUploadResult:
        path = Path(video_path)
        validation_error = validate_direct_upload(path, self.channel, self.settings, self.account, self.storage_root)
        if validation_error:
            return DirectUploadResult(False, validation_error, {"mechanism": "youtube-frontend-direct"})
        try:
            self.describe_file(path)
            self.create_video(title, description, visibility)
            configured_chunk_size = int(chunk_size or self.document.get("chunk_size") or CHUNK_GRANULARITY)
            self.upload_chunks(path, configured_chunk_size)
            return DirectUploadResult(True, f"Upload directo concluído: {self.video_id}", {"mechanism": "youtube-frontend-direct", "video_id": self.video_id, "page_id": self.channel.get("delegated_session_id", ""), "google_account_id": (self.account or {}).get("id", "")})
        except (requests.RequestException, OSError, ValueError, RuntimeError) as exc:
            return DirectUploadResult(False, f"Upload directo falhou: {exc}", {"mechanism": "youtube-frontend-direct", "video_id": self.video_id})
