"""Postiz Public API adapter used as the final upload fallback."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

import requests

from .platforms import IntegrationResult


DEFAULT_POSTIZ_BASE_URL = "https://api.postiz.com/public/v1"
DEFAULT_POSTIZ_MCP_URL = "https://api.postiz.com/mcp"


class PostizAdapter:
    def __init__(self, settings: dict[str, Any] | None = None):
        self.settings = settings or {}
        self.api_key = str(self.settings.get("postiz_api_key") or "").strip()
        self.base_url = str(self.settings.get("postiz_base_url") or DEFAULT_POSTIZ_BASE_URL).strip().rstrip("/")
        self.mcp_url = str(self.settings.get("postiz_mcp_url") or DEFAULT_POSTIZ_MCP_URL).strip().rstrip("/")

    def _headers(self, *, json_body: bool = False) -> dict[str, str]:
        headers = {"Authorization": self.api_key}
        if json_body:
            headers["Content-Type"] = "application/json"
        return headers

    def _error(self, message: str, data: dict[str, Any] | None = None) -> IntegrationResult:
        return IntegrationResult(False, message, data or {})

    def status(self) -> IntegrationResult:
        if not self.api_key:
            return self._error("Postiz não configurado: adicione a API key em Configurações Técnicas.")
        return IntegrationResult(True, f"Postiz configurado em {self.base_url}.", {"base_url": self.base_url, "mcp_url": self.mcp_url})

    def list_integrations(self) -> IntegrationResult:
        status = self.status()
        if not status.ok:
            return status
        try:
            response = requests.get(f"{self.base_url}/integrations", headers=self._headers(), timeout=30)
        except requests.RequestException as exc:
            return self._error(f"Não foi possível contactar o Postiz: {exc}")
        if response.status_code >= 400:
            return self._error(f"Postiz devolveu HTTP {response.status_code}: {response.text[:500]}")
        try:
            payload = response.json()
        except ValueError:
            return self._error("Postiz devolveu uma resposta que não é JSON.")
        if isinstance(payload, dict):
            integrations = payload.get("integrations") or payload.get("data") or payload.get("items") or []
        else:
            integrations = payload
        if not isinstance(integrations, list):
            return self._error("A resposta de integrações do Postiz não tem uma lista válida.", {"payload": payload})
        normalized = [item for item in integrations if isinstance(item, dict) and item.get("id")]
        return IntegrationResult(True, f"{len(normalized)} integração(ões) Postiz carregada(s).", {"integrations": normalized, "payload": payload})

    def upload_file(self, video_path: str | Path, *, mime_type: str | None = None) -> IntegrationResult:
        status = self.status()
        if not status.ok:
            return status
        path = Path(video_path)
        if not path.is_file():
            return self._error(f"Vídeo não encontrado para o Postiz: {path}")
        content_type = mime_type or mimetypes.guess_type(path.name)[0] or "video/mp4"
        try:
            with path.open("rb") as handle:
                response = requests.post(
                    f"{self.base_url}/upload",
                    headers=self._headers(),
                    files={"file": (path.name, handle, content_type)},
                    timeout=180,
                )
        except requests.RequestException as exc:
            return self._error(f"Não foi possível enviar o vídeo para o Postiz: {exc}")
        if response.status_code >= 400:
            return self._error(f"Postiz rejeitou o upload (HTTP {response.status_code}): {response.text[:500]}")
        try:
            payload = response.json()
        except ValueError:
            return self._error("Postiz devolveu uma resposta de upload que não é JSON.")
        asset_id = str(payload.get("id") or "").strip() if isinstance(payload, dict) else ""
        asset_path = str(payload.get("path") or "").strip() if isinstance(payload, dict) else ""
        if not asset_id or not asset_path:
            return self._error("O upload Postiz não devolveu id e path do asset.", {"payload": payload})
        return IntegrationResult(True, "Vídeo carregado no Postiz.", {"asset": {"id": asset_id, "path": asset_path}, "payload": payload})

    def create_youtube_post(
        self,
        integration_id: str,
        *,
        asset: dict[str, str],
        title: str,
        description: str = "",
        visibility: str = "private",
        tags: list[str] | None = None,
        thumbnail: dict[str, str] | None = None,
        post_type: str = "now",
        date: str | None = None,
    ) -> IntegrationResult:
        status = self.status()
        if not status.ok:
            return status
        integration_id = str(integration_id or "").strip()
        if not integration_id:
            return self._error("Seleccione uma integração YouTube do Postiz antes de publicar.")
        normalized_visibility = visibility if visibility in {"public", "unlisted", "private"} else "private"
        tag_values = [str(tag).strip() for tag in (tags or []) if str(tag).strip()]
        body: dict[str, Any] = {
            "type": post_type if post_type in {"now", "schedule", "draft"} else "now",
            "shortLink": False,
            "tags": [],
            "posts": [
                {
                    "integration": {"id": integration_id},
                    "value": [{"content": description, "image": [asset]}],
                    "settings": {
                        "__type": "youtube",
                        "title": title.strip()[:100] or "Vídeo Thunderbolt",
                        "type": normalized_visibility,
                        "selfDeclaredMadeForKids": "no",
                        "thumbnail": thumbnail,
                        "tags": [{"value": value, "label": value} for value in tag_values],
                    },
                }
            ],
        }
        if post_type == "schedule" and date:
            body["date"] = date
        try:
            response = requests.post(f"{self.base_url}/posts", headers=self._headers(json_body=True), json=body, timeout=60)
        except requests.RequestException as exc:
            return self._error(f"Não foi possível criar o post no Postiz: {exc}")
        if response.status_code >= 400:
            return self._error(f"Postiz rejeitou a publicação (HTTP {response.status_code}): {response.text[:500]}", {"request": body})
        try:
            payload = response.json()
        except ValueError:
            return self._error("Postiz devolveu uma resposta de publicação que não é JSON.", {"request": body})
        return IntegrationResult(True, "Post criado no Postiz.", {"payload": payload, "request": body, "asset": asset, "integration_id": integration_id})

    def publish_video(
        self,
        video_path: str | Path,
        *,
        integration_id: str,
        title: str,
        description: str = "",
        visibility: str = "private",
        tags: list[str] | None = None,
        thumbnail_path: str | Path | None = None,
    ) -> IntegrationResult:
        upload = self.upload_file(video_path)
        if not upload.ok:
            return upload
        thumbnail_asset = None
        if thumbnail_path and Path(thumbnail_path).is_file():
            thumb_upload = self.upload_file(thumbnail_path, mime_type=mimetypes.guess_type(str(thumbnail_path))[0] or "image/jpeg")
            if thumb_upload.ok:
                thumbnail_asset = thumb_upload.data.get("asset")
        return self.create_youtube_post(
            integration_id,
            asset=upload.data["asset"],
            title=title,
            description=description,
            visibility=visibility,
            tags=tags,
            thumbnail=thumbnail_asset,
        )
