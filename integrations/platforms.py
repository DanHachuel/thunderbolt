from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


@dataclass
class IntegrationResult:
    ok: bool
    message: str
    data: dict[str, Any]


class YouTubeAdapter:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY", "")

    @staticmethod
    def extract_channel_ref(value: str) -> str:
        value = value.strip()
        match = re.search(r"(?:channel/|@)([A-Za-z0-9_.-]+)", value)
        return match.group(1) if match else value

    def fetch_channel(self, value: str) -> IntegrationResult:
        ref = self.extract_channel_ref(value)
        if not self.api_key:
            return IntegrationResult(False, "YOUTUBE_API_KEY não configurada; preencha os dados manualmente.", {"url": value, "handle": ref})
        try:
            params = {"part": "snippet,statistics", "key": self.api_key}
            if ref.startswith("UC"):
                params["id"] = ref
            else:
                params["forHandle"] = ref if ref.startswith("@") else f"@{ref}"
            response = requests.get("https://www.googleapis.com/youtube/v3/channels", params=params, timeout=15)
            response.raise_for_status()
            items = response.json().get("items", [])
            if not items:
                return IntegrationResult(False, "Canal não encontrado pela API do YouTube.", {})
            item = items[0]
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            data = {
                "youtube_id": item.get("id", ""),
                "name": snippet.get("title", ""),
                "handle": snippet.get("customUrl", ""),
                "description": snippet.get("description", ""),
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                "subscriber_count": int(stats["subscriberCount"]) if stats.get("subscriberCount") else None,
                "video_count": int(stats["videoCount"]) if stats.get("videoCount") else None,
                "view_count": int(stats["viewCount"]) if stats.get("viewCount") else None,
                "metrics_source": "youtube_data_api",
            }
            return IntegrationResult(True, "Canal importado do YouTube.", data)
        except requests.RequestException as exc:
            return IntegrationResult(False, f"Falha ao consultar o YouTube: {exc}", {})


class TikTokAdapter:
    def __init__(self, settings: dict[str, Any]):
        self.client_key = settings.get("tiktok_client_key", "")
        self.client_secret = settings.get("tiktok_client_secret", "")
        self.redirect_uri = settings.get("tiktok_redirect_uri", "")
        self.scopes = settings.get("tiktok_scopes", "user.info.basic,video.publish,video.upload")
        self.access_token = settings.get("tiktok_access_token", "") or os.getenv("TIKTOK_ACCESS_TOKEN", "")

    @property
    def configured(self) -> bool:
        return bool(self.client_key and self.client_secret and self.redirect_uri)

    def status(self) -> IntegrationResult:
        if not self.configured:
            return IntegrationResult(False, "TikTok ainda não configurado.", {"status": "not_configured"})
        return IntegrationResult(True, "Credenciais TikTok configuradas; OAuth ainda deve ser autorizado.", {"status": "configured"})

    def authorization_url(self, state: str) -> str:
        from urllib.parse import urlencode
        params = urlencode({"client_key": self.client_key, "scope": self.scopes, "response_type": "code", "redirect_uri": self.redirect_uri, "state": state})
        return f"https://www.tiktok.com/v2/auth/authorize/?{params}"

    def upload_video(self, video_path: str, title: str = "", privacy_level: str = "SELF_ONLY") -> IntegrationResult:
        path = Path(video_path)
        if not path.exists():
            return IntegrationResult(False, "Ficheiro de vídeo não encontrado.", {"path": video_path})
        if not self.configured:
            return IntegrationResult(False, "Configure Client Key, Client Secret e Redirect URI antes do upload.", {"path": video_path})
        if not self.access_token:
            return IntegrationResult(False, "Conclua o OAuth TikTok ou configure TIKTOK_ACCESS_TOKEN localmente.", {"path": str(path), "status": "requires_oauth"})
        try:
            size = path.stat().st_size
            payload = {"post_info": {"title": title[:2200], "privacy_level": privacy_level, "disable_duet": False, "disable_comment": False, "disable_stitch": False}, "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}}
            response = requests.post("https://open.tiktokapis.com/v2/post/publish/video/init/", headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json; charset=UTF-8"}, json=payload, timeout=30)
            response.raise_for_status()
            body = response.json()
            error = body.get("error", {})
            if error.get("code") not in (None, "ok"):
                return IntegrationResult(False, f"TikTok rejeitou a inicialização: {error.get('message', error.get('code'))}", {"error": error})
            data = body.get("data", {})
            publish_id = data.get("publish_id", "")
            upload_url = data.get("upload_url", "")
            if not upload_url or not publish_id:
                return IntegrationResult(False, "TikTok não devolveu upload_url e publish_id.", {"response": body})
            with path.open("rb") as handle:
                upload = requests.put(upload_url, headers={"Content-Type": "video/mp4", "Content-Length": str(size), "Content-Range": f"bytes 0-{size - 1}/{size}"}, data=handle, timeout=300)
            upload.raise_for_status()
            return IntegrationResult(True, "Vídeo enviado para processamento no TikTok.", {"publish_id": publish_id, "status": "processing"})
        except requests.RequestException as exc:
            return IntegrationResult(False, f"Falha no upload TikTok: {exc}", {"status": "failed"})
