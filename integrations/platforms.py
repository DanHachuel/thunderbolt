from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests


def _extract_json_assignment(document: str, variable: str) -> dict[str, Any] | None:
    marker = re.search(rf"(?:var\s+)?{re.escape(variable)}\s*=", document)
    if not marker:
        return None
    start = document.find("{", marker.end())
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(document)):
        character = document[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                try:
                    parsed = json.loads(document[start:index + 1])
                except json.JSONDecodeError:
                    return None
                return parsed if isinstance(parsed, dict) else None
    return None


def _find_first_key(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        if key in value:
            return value[key]
        for child in value.values():
            found = _find_first_key(child, key)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_first_key(child, key)
            if found is not None:
                return found
    return None


def _text_from_node(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("simpleText", "content", "text"):
            if isinstance(value.get(key), str):
                return value[key].strip()
        runs = value.get("runs")
        if isinstance(runs, list):
            return "".join(str(run.get("text", "")) for run in runs if isinstance(run, dict)).strip()
    return ""


def _parse_public_count(value: Any) -> int | None:
    text = _text_from_node(value).lower().replace(" ", "")
    if not text:
        return None
    match = re.search(r"([0-9][0-9.,]*)(mil|milhões|mi|bi|[kmb])?", text)
    if not match:
        return None
    number = match.group(1)
    suffix = match.group(2) or ""
    if suffix == "milhões":
        suffix = "m"
    try:
        if suffix in {"k", "mil"}:
            return int(float(number.replace(",", ".")) * 1_000)
        if suffix in {"m", "mi"}:
            return int(float(number.replace(",", ".")) * 1_000_000)
        if suffix == "b":
            return int(float(number.replace(",", ".")) * 1_000_000_000)
        return int(re.sub(r"[^0-9]", "", number))
    except ValueError:
        return None


def _thumbnail_from_metadata(metadata: dict[str, Any]) -> str:
    thumbnails = metadata.get("avatar", {}).get("thumbnails", []) if isinstance(metadata, dict) else []
    if isinstance(thumbnails, list) and thumbnails:
        last = thumbnails[-1]
        if isinstance(last, dict):
            return str(last.get("url", ""))
    return ""


def _meta_content(document: str, *names: str) -> str:
    for name in names:
        pattern = rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']*)["\']'
        match = re.search(pattern, document, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
        reverse_pattern = rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:name|property)=["\']{re.escape(name)}["\']'
        match = re.search(reverse_pattern, document, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _public_page_candidates(source: str) -> list[str]:
    source = source.strip()
    if source.startswith(("http://", "https://")):
        parsed = urlparse(source)
        base = f"https://{parsed.netloc}{parsed.path}".rstrip("/")
        if parsed.netloc.lower().endswith("youtube.com"):
            base = base.replace("/about", "").replace("/videos", "")
    elif source.startswith("UC"):
        base = f"https://www.youtube.com/channel/{source}"
    else:
        handle = source if source.startswith("@") else f"@{source}"
        base = f"https://www.youtube.com/{handle}"
    return list(dict.fromkeys([
        f"{base}/about?hl=pt-BR&gl=BR",
        f"{base}?hl=pt-BR&gl=BR",
        f"{base}/videos?hl=pt-BR&gl=BR",
    ]))


def _channel_id_from_document(document: str, canonical_url: str = "") -> str:
    patterns = [
        r'"externalId"\s*:\s*"(UC[A-Za-z0-9_-]+)"',
        r'"channelId"\s*:\s*"(UC[A-Za-z0-9_-]+)"',
        r"/channel/(UC[A-Za-z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, document)
        if match:
            return match.group(1)
    match = re.search(r"/channel/(UC[A-Za-z0-9_-]+)", canonical_url)
    return match.group(1) if match else ""


def _public_feed_data(channel_id: str, headers: dict[str, str]) -> dict[str, Any]:
    if not channel_id:
        return {}
    try:
        response = requests.get(
            f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",
            headers=headers,
            timeout=12,
        )
        response.raise_for_status()
        root = ET.fromstring(response.text)
        namespace = {"yt": "http://www.youtube.com/xml/schemas/2015", "atom": "http://www.w3.org/2005/Atom"}
        title = root.findtext("atom:title", default="", namespaces=namespace).strip()
        feed_id = root.findtext("yt:channelId", default=channel_id, namespaces=namespace).strip()
        entries = root.findall("atom:entry", namespace)
        return {"name": title, "youtube_id": feed_id, "video_count": len(entries) if entries else None}
    except (requests.RequestException, ET.ParseError, ValueError):
        return {}


@dataclass
class IntegrationResult:
    ok: bool
    message: str
    data: dict[str, Any]


class YouTubeAdapter:
    def __init__(self, api_key: str = "", settings: dict[str, Any] | None = None):
        self.settings = settings or {}
        self.api_key = api_key or self.settings.get("youtube_api_key", "") or os.getenv("YOUTUBE_API_KEY", "")

    @staticmethod
    def extract_channel_ref(value: str) -> str:
        value = value.strip()
        match = re.search(r"(?:channel/|@)([A-Za-z0-9_.-]+)", value)
        return match.group(1) if match else value

    def fetch_channel_public(self, value: str) -> IntegrationResult:
        """Fetch public channel metadata without requiring a YouTube Data API key."""
        source = (value or "").strip()
        if not source:
            return IntegrationResult(False, "Introduza o nome, handle, URL ou ID do canal.", {})
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        last_url = source
        last_error = ""
        for page_url in _public_page_candidates(source):
            last_url = page_url
            try:
                response = requests.get(page_url, headers=headers, timeout=20)
                response.raise_for_status()
            except requests.RequestException as exc:
                last_error = str(exc)
                continue
            document = response.text or ""
            initial_data = _extract_json_assignment(document, "ytInitialData") or {}
            metadata = _find_first_key(initial_data, "channelMetadataRenderer") or {}
            header = _find_first_key(initial_data, "pageHeaderViewModel") or {}
            canonical_url = _meta_content(document, "og:url", "twitter:url") or page_url.split("?", 1)[0].rstrip("/")
            owner_urls = metadata.get("ownerUrls", []) if isinstance(metadata, dict) else []
            if owner_urls:
                canonical_url = str(owner_urls[0])
            canonical_url = canonical_url.replace("http://", "https://").removesuffix("/about")
            youtube_id = str(metadata.get("externalId", "")) if isinstance(metadata, dict) else ""
            if not youtube_id:
                youtube_id = _channel_id_from_document(document, canonical_url)
            feed = _public_feed_data(youtube_id, headers)
            title = _text_from_node(metadata.get("title")) if isinstance(metadata, dict) else ""
            if not title and isinstance(header, dict):
                title = _text_from_node(header.get("title"))
                if not title:
                    title = _text_from_node(_find_first_key(header, "dynamicTextViewModel"))
            if not title:
                title = _meta_content(document, "og:title", "twitter:title") or feed.get("name", "")
            description = _text_from_node(metadata.get("description")) if isinstance(metadata, dict) else ""
            description = description or _meta_content(document, "description", "og:description")
            thumbnail_url = _thumbnail_from_metadata(metadata) or _meta_content(document, "og:image", "twitter:image")
            handle_match = re.search(r"/@([^/?]+)", canonical_url)
            handle = f"@{handle_match.group(1)}" if handle_match else ""
            if not handle:
                handle_match = re.search(r"/@([^/?]+)", document)
                handle = f"@{handle_match.group(1)}" if handle_match else ""
            subscriber_value = _find_first_key(initial_data, "subscriberCountText")
            video_value = _find_first_key(initial_data, "videoCountText")
            data = {
                "youtube_id": youtube_id or feed.get("youtube_id", ""),
                "name": title,
                "handle": handle,
                "url": canonical_url,
                "description": description,
                "thumbnail_url": thumbnail_url,
                "subscriber_count": _parse_public_count(subscriber_value),
                "video_count": _parse_public_count(video_value) or feed.get("video_count"),
                "view_count": None,
                "metrics_source": "youtube_public_page",
                "public_lookup": True,
            }
            if data["name"] or data["youtube_id"] or data["thumbnail_url"]:
                return IntegrationResult(True, "Canal encontrado publicamente no YouTube, sem API Key. Reveja os dados antes de guardar.", data)
            last_error = "A página respondeu sem metadados reconhecíveis."
        return IntegrationResult(False, f"Não foi possível obter dados públicos do YouTube sem API Key. Confirme o URL/handle ou use Cadastro manual. {last_error}".strip(), {"url": last_url, "public_lookup": True})

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

    def upload_video(self, video_path: str, **kwargs: Any) -> IntegrationResult:
        """Publish through the adapted youtube-automation-agent, then OAuth fallback."""
        from integrations.youtube_upload import upload_youtube_with_fallback
        from hermes_ui.storage import STORAGE

        return upload_youtube_with_fallback(
            self.settings,
            STORAGE,
            video_path=video_path,
            **kwargs,
        )

    def upload_status(self) -> dict[str, IntegrationResult]:
        from integrations.youtube_upload import youtube_upload_status
        from hermes_ui.storage import STORAGE

        return youtube_upload_status(self.settings, STORAGE)

    def authorize_agent(self) -> IntegrationResult:
        from integrations.youtube_upload import authorize_youtube_agent
        from hermes_ui.storage import STORAGE

        return authorize_youtube_agent(self.settings, STORAGE)

    def authorize_fallback(self) -> IntegrationResult:
        from integrations.youtube_upload import authorize_youtube_fallback
        from hermes_ui.storage import STORAGE

        return authorize_youtube_fallback(self.settings, STORAGE)


class TikTokAdapter:
    def __init__(self, settings: dict[str, Any]):
        self.client_key = settings.get("tiktok_client_key", "")
        self.client_secret = settings.get("tiktok_client_secret", "")
        # Redirect URI, scopes, OAuth e access token são geridos no TikTok for Developers Playground.
        # A UI guarda apenas as credenciais da aplicação.
        self.access_token = os.getenv("TIKTOK_ACCESS_TOKEN", "")

    @property
    def configured(self) -> bool:
        return bool(self.client_key and self.client_secret)

    def status(self) -> IntegrationResult:
        if not self.configured:
            return IntegrationResult(False, "TikTok ainda não configurado.", {"status": "not_configured"})
        return IntegrationResult(True, "TikTok Client ID e Client Secret configurados; autorização e publicação são geridas no TikTok for Developers Playground.", {"status": "configured"})

    def upload_video(self, video_path: str, title: str = "", privacy_level: str = "SELF_ONLY") -> IntegrationResult:
        path = Path(video_path)
        if not path.exists():
            return IntegrationResult(False, "Ficheiro de vídeo não encontrado.", {"path": video_path})
        if not self.configured:
            return IntegrationResult(False, "Configure TikTok Client ID e Client Secret.", {"path": video_path})
        if not self.access_token:
            return IntegrationResult(False, "Conclua a autorização no TikTok for Developers Playground; o token de publicação deve ser fornecido pelo ambiente de execução.", {"path": str(path), "status": "requires_playground_authorization"})
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
