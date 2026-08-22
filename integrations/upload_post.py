"""Upload-Post API adapter for publishing local video artefacts."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

import requests

from .platforms import IntegrationResult


DEFAULT_UPLOAD_POST_BASE_URL = "https://api.upload-post.com/api"
UPLOAD_POST_PLATFORM_OPTIONS = (
    "tiktok",
    "instagram",
    "youtube",
    "facebook",
    "linkedin",
    "x",
    "threads",
    "pinterest",
    "reddit",
    "bluesky",
    "discord",
    "telegram",
)
_PLATFORM_ALIASES = {
    "facebook pages": "facebook",
    "facebook_pages": "facebook",
    "twitter": "x",
    "x (twitter)": "x",
}


def normalize_upload_post_platforms(value: Any) -> list[str]:
    """Return stable Upload-Post platform slugs without duplicates."""
    values = value if isinstance(value, (list, tuple, set)) else str(value or "").replace("\n", ",").split(",")
    result: list[str] = []
    seen: set[str] = set()
    supported = set(UPLOAD_POST_PLATFORM_OPTIONS)
    for item in values:
        platform = str(item or "").strip().lower()
        platform = _PLATFORM_ALIASES.get(platform, platform)
        if platform in supported and platform not in seen:
            result.append(platform)
            seen.add(platform)
    return result


class UploadPostAdapter:
    """Small deterministic client for Upload-Post's ``POST /upload`` endpoint."""

    def __init__(self, settings: dict[str, Any] | None = None):
        self.settings = settings or {}
        self.api_key = str(self.settings.get("upload_post_api_key") or "").strip()
        self.enabled = bool(self.settings.get("upload_post_enabled", False))
        self.username = str(self.settings.get("upload_post_username") or "").strip()
        self.platforms = normalize_upload_post_platforms(self.settings.get("upload_post_platforms", ""))
        self.base_url = str(self.settings.get("upload_post_base_url") or DEFAULT_UPLOAD_POST_BASE_URL).strip().rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Apikey {self.api_key}"}

    def _error(self, message: str, data: dict[str, Any] | None = None) -> IntegrationResult:
        return IntegrationResult(False, message, data or {})

    def status(self) -> IntegrationResult:
        if not self.enabled:
            return self._error("Upload-Post está desactivado em Configuração API.")
        if not self.api_key:
            return self._error("Upload-Post não configurado: adicione a API key em Configuração API > API Keys > Serviços e modelos.")
        if not self.username:
            return self._error("Upload-Post não configurado: adicione o username/perfil em Configuração API.")
        if not self.platforms:
            return self._error("Upload-Post não configurado: indique pelo menos uma plataforma em Configuração API.")
        return IntegrationResult(
            True,
            f"Upload-Post configurado para {self.username} ({', '.join(self.platforms)}).",
            {"base_url": self.base_url, "username": self.username, "platforms": self.platforms},
        )

    def upload_video(
        self,
        video_path: str | Path,
        *,
        title: str,
        description: str = "",
        user: str | None = None,
        platforms: list[str] | None = None,
        async_upload: bool = False,
    ) -> IntegrationResult:
        """Upload a local video to one or more connected Upload-Post platforms."""
        if not self.enabled:
            return self._error("Upload-Post está desactivado em Configuração API.")
        if not self.api_key:
            return self._error("Upload-Post não configurado: adicione a API key em Configuração API.")
        path = Path(video_path)
        if not path.is_file():
            return self._error(f"Vídeo não encontrado para o Upload-Post: {path}")
        selected_user = str(user or self.username).strip()
        selected_platforms = normalize_upload_post_platforms(platforms or self.platforms)
        if not selected_user:
            return self._error("Indique o username/perfil ligado ao Upload-Post antes de publicar.")
        if not selected_platforms:
            return self._error("Seleccione pelo menos uma plataforma do Upload-Post antes de publicar.")

        form_data: list[tuple[str, str]] = [
            ("user", selected_user),
            *[("platform[]", platform) for platform in selected_platforms],
            ("title", str(title or "Vídeo Thunderbolt").strip()[:500] or "Vídeo Thunderbolt"),
            ("description", str(description or "").strip()),
            ("async_upload", "true" if async_upload else "false"),
        ]
        content_type = mimetypes.guess_type(path.name)[0] or "video/mp4"
        try:
            with path.open("rb") as handle:
                response = requests.post(
                    f"{self.base_url}/upload",
                    headers=self._headers(),
                    data=form_data,
                    files={"video": (path.name, handle, content_type)},
                    timeout=240,
                )
        except requests.RequestException as exc:
            return self._error(f"Não foi possível contactar o Upload-Post: {exc}", {"platforms": selected_platforms, "user": selected_user})
        if response.status_code >= 400:
            return self._error(
                f"Upload-Post rejeitou o vídeo (HTTP {response.status_code}): {response.text[:500]}",
                {"platforms": selected_platforms, "user": selected_user},
            )
        try:
            payload: Any = response.json()
        except ValueError:
            return self._error("Upload-Post devolveu uma resposta que não é JSON.", {"response": response.text[:2000]})
        payload_dict = payload if isinstance(payload, dict) else {"response": payload}
        request_id = str(payload_dict.get("request_id") or payload_dict.get("requestId") or "").strip()
        message = "Upload-Post aceitou o vídeo para publicação."
        if request_id:
            message += f" Request ID: {request_id}."
        return IntegrationResult(
            True,
            message,
            {
                "payload": payload_dict,
                "request_id": request_id,
                "user": selected_user,
                "platforms": selected_platforms,
                "async_upload": bool(async_upload),
            },
        )
