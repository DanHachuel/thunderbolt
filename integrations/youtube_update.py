from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from integrations.platforms import IntegrationResult
from integrations.youtube_upload import AGENT_SCOPES, YouTubeAutomationAgentUploader, _path_value

YOUTUBE_UPDATE_VIDEO = "YOUTUBE_UPDATE_VIDEO"


def _channel_id(channel: dict[str, Any]) -> str:
    value = str(channel.get("youtube_channel_id") or channel.get("youtube_id") or "").strip()
    if value.startswith("UC"):
        return value
    match = re.search(r"(?:/channel/)(UC[A-Za-z0-9_-]+)", str(channel.get("url") or ""))
    return match.group(1) if match else ""


class YouTubeVideoUpdater(YouTubeAutomationAgentUploader):
    """Official OAuth adapter for metadata-only YouTube updates."""

    def list_videos(self, channel: dict[str, Any], *, page_token: str = "", max_results: int = 25) -> IntegrationResult:
        channel_id = _channel_id(channel)
        if not channel_id:
            return IntegrationResult(False, "Este canal não tem um YouTube channel ID. Actualize o cadastro do canal antes de listar vídeos.", {"operation": YOUTUBE_UPDATE_VIDEO, "videos": []})
        try:
            credentials = self._load_credentials()
            if credentials is None:
                return IntegrationResult(False, "Autorize primeiro a conta YouTube para listar vídeos.", {"operation": YOUTUBE_UPDATE_VIDEO, "videos": []})
            youtube = self._build_client(credentials)
            channel_response = youtube.channels().list(part="contentDetails", id=channel_id).execute()
            items = channel_response.get("items") or []
            if not items:
                return IntegrationResult(False, "O canal YouTube não foi encontrado para esta conta autorizada.", {"operation": YOUTUBE_UPDATE_VIDEO, "videos": []})
            uploads_id = ((items[0].get("contentDetails") or {}).get("relatedPlaylists") or {}).get("uploads")
            if not uploads_id:
                return IntegrationResult(False, "Não foi possível localizar a playlist de uploads do canal.", {"operation": YOUTUBE_UPDATE_VIDEO, "videos": []})
            ids: list[str] = []
            next_token = page_token or ""
            while True:
                playlist = youtube.playlistItems().list(part="snippet,contentDetails", playlistId=uploads_id, maxResults=max(1, min(50, int(max_results))), pageToken=next_token).execute()
                ids.extend(str((item.get("contentDetails") or {}).get("videoId") or "") for item in playlist.get("items", []))
                next_token = str(playlist.get("nextPageToken") or "")
                if not next_token:
                    break
            ids = [item for item in ids if item]
            if not ids:
                return IntegrationResult(True, "Nenhum vídeo encontrado neste canal.", {"operation": YOUTUBE_UPDATE_VIDEO, "videos": [], "next_page_token": ""})
            details = youtube.videos().list(part="snippet,status,contentDetails", id=",".join(ids)).execute()
            videos = []
            for item in details.get("items", []):
                snippet = item.get("snippet") or {}
                videos.append({
                    "id": item.get("id", ""),
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "category_id": snippet.get("categoryId", "22"),
                    "default_language": snippet.get("defaultLanguage") or snippet.get("defaultAudioLanguage") or channel.get("language") or "pt",
                    "published_at": snippet.get("publishedAt", ""),
                    "channel_id": snippet.get("channelId", channel_id),
                    "thumbnail_url": ((snippet.get("thumbnails") or {}).get("high") or (snippet.get("thumbnails") or {}).get("default") or {}).get("url", ""),
                    "privacy_status": (item.get("status") or {}).get("privacyStatus", ""),
                    "url": f"https://www.youtube.com/watch?v={item.get('id', '')}",
                })
            return IntegrationResult(True, f"{len(videos)} vídeo(s) carregado(s).", {"operation": YOUTUBE_UPDATE_VIDEO, "videos": videos, "next_page_token": ""})
        except Exception as exc:
            return IntegrationResult(False, f"Falha ao listar vídeos YouTube: {exc}", {"operation": YOUTUBE_UPDATE_VIDEO, "videos": []})

    def update_video(self, video: dict[str, Any], *, title: str, description: str, thumbnail_path: str | Path | None = None) -> IntegrationResult:
        video_id = str(video.get("id") or "").strip()
        if not video_id:
            return IntegrationResult(False, "Vídeo sem videoId; a actualização foi recusada.", {"operation": YOUTUBE_UPDATE_VIDEO})
        title = str(title or "").strip()
        description = str(description or "")
        if not title:
            return IntegrationResult(False, "O título não pode ficar vazio.", {"operation": YOUTUBE_UPDATE_VIDEO, "video_id": video_id})
        changed: list[str] = []
        try:
            credentials = self._load_credentials()
            if credentials is None:
                return IntegrationResult(False, "Autorize primeiro a conta YouTube.", {"operation": YOUTUBE_UPDATE_VIDEO, "video_id": video_id})
            youtube = self._build_client(credentials)
            current_category = str(video.get("category_id") or "22")
            body = {"id": video_id, "snippet": {"title": title[:100], "description": description, "categoryId": current_category}}
            if title != str(video.get("title") or "") or description != str(video.get("description") or ""):
                youtube.videos().update(part="snippet", body=body).execute()
                if title != str(video.get("title") or ""):
                    changed.append("title")
                if description != str(video.get("description") or ""):
                    changed.append("description")
            thumbnail = _path_value(thumbnail_path)
            if thumbnail:
                if not thumbnail.exists() or not thumbnail.is_file():
                    return IntegrationResult(False, "A thumbnail seleccionada não existe.", {"operation": YOUTUBE_UPDATE_VIDEO, "video_id": video_id, "changed": changed})
                with thumbnail.open("rb") as handle:
                    youtube.thumbnails().set(videoId=video_id, media_body=handle).execute()
                changed.append("thumbnail")
            return IntegrationResult(True, "Vídeo actualizado sem alterar o ficheiro de vídeo.", {"operation": YOUTUBE_UPDATE_VIDEO, "video_id": video_id, "changed": changed, "url": f"https://www.youtube.com/watch?v={video_id}"})
        except Exception as exc:
            return IntegrationResult(False, f"Falha ao actualizar o vídeo YouTube: {exc}", {"operation": YOUTUBE_UPDATE_VIDEO, "video_id": video_id, "changed": changed})


def update_youtube_video(settings: dict[str, Any], channel: dict[str, Any], video: dict[str, Any], *, title: str, description: str, thumbnail_path: str | Path | None = None) -> IntegrationResult:
    updater = YouTubeVideoUpdater(settings, Path(__file__).resolve().parents[1] / "storage")
    return updater.update_video(video, title=title, description=description, thumbnail_path=thumbnail_path)
