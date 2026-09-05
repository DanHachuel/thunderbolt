from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from integrations.platforms import IntegrationResult
from integrations.youtube_batch import loopback_host, loopback_port, loopback_redirect_uri, token_path as batch_token_path


# Mantemos os mesmos escopos usados pelo youtube-automation-agent.
AGENT_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
FALLBACK_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


@dataclass
class UploadAttempt:
    mechanism: str
    result: IntegrationResult


def _safe_text(value: Any, default: str = "") -> str:
    return str(value if value is not None else default).strip()


def _path_value(value: Any) -> Path | None:
    if isinstance(value, dict):
        value = value.get("path") or value.get("file") or value.get("filepath")
    if not value:
        return None
    return Path(str(value)).expanduser()


def validate_video_file(video_path: str | os.PathLike[str]) -> tuple[bool, str, Path]:
    """Validate the same real-video conditions used by the agent before publishing."""
    path = Path(video_path).expanduser()
    if not path.exists() or not path.is_file():
        return False, "Ficheiro de vídeo não encontrado; o upload foi recusado.", path
    if path.suffix.lower() != ".mp4":
        return False, "O youtube-automation-agent só publica ficheiros MP4 reais.", path
    if path.stat().st_size <= 0:
        return False, "O ficheiro de vídeo está vazio; o upload foi recusado.", path
    return True, "Vídeo válido.", path


def build_agent_video_metadata(
    *,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    category_id: str = "22",
    language: str = "pt-BR",
    privacy_status: str = "unlisted",
    publish_at: str | None = None,
    embeddable: bool = True,
    notify_subscribers: bool = True,
    allow_audio_remixing: bool = True,
    allow_video_remixing: bool = True,
) -> dict[str, Any]:
    """Build the snippet/status payload used by PublishingSchedulingAgent."""
    status: dict[str, Any] = {
        "privacyStatus": privacy_status or "unlisted",
        "selfDeclaredMadeForKids": False,
        "embeddable": bool(embeddable),
        "publicStatsViewable": True,
    }
    if publish_at and status["privacyStatus"] == "private":
        # YouTube requires a future publishAt with privacyStatus=private.
        status["publishAt"] = publish_at
    return {
        "snippet": {
            "title": _safe_text(title)[:100] or "Vídeo Thunderbolt",
            "description": _safe_text(description),
            "tags": [str(tag).strip() for tag in (tags or []) if str(tag).strip()],
            "categoryId": _safe_text(category_id, "22"),
            "defaultLanguage": _safe_text(language, "pt-BR"),
            "defaultAudioLanguage": _safe_text(language, "pt-BR"),
        },
        "status": status,
    }


class _GoogleYouTubeBase:
    def __init__(self, settings: dict[str, Any], token_path: Path, scopes: list[str], alternate_token_path: Path | None = None, account: dict[str, Any] | None = None):
        self.settings = settings
        self.account = account if isinstance(account, dict) else None
        self.client_id = _safe_text((self.account or {}).get("client_id")) or _safe_text(settings.get("youtube_client_id")) or os.getenv("YOUTUBE_CLIENT_ID", "")
        self.client_secret = _safe_text((self.account or {}).get("client_secret")) or _safe_text(settings.get("youtube_client_secret")) or os.getenv("YOUTUBE_CLIENT_SECRET", "")
        self.token_path = token_path
        self.alternate_token_path = alternate_token_path
        self.scopes = scopes

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    @property
    def token_exists(self) -> bool:
        return any(path.exists() and path.stat().st_size > 0 for path in self._token_candidates())

    def _token_candidates(self) -> list[Path]:
        paths = [self.token_path]
        if self.account:
            paths.append(batch_token_path(self.token_path.parents[1], self.account))
        if self.alternate_token_path and self.alternate_token_path not in paths:
            paths.append(self.alternate_token_path)
        return list(dict.fromkeys(paths))

    def _client_config(self) -> dict[str, Any]:
        return {
            "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [loopback_redirect_uri()],
            }
        }

    def _load_credentials(self) -> Any:
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
        except ImportError as exc:
            raise RuntimeError("As dependências Google OAuth ainda não estão instaladas. Execute a instalação do Thunderbolt novamente.") from exc
        token_source = next((path for path in self._token_candidates() if path.exists() and path.stat().st_size > 0), None)
        if token_source is None:
            return None
        raw = json.loads(token_source.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and isinstance(raw.get("youtube"), dict):
            raw = raw["youtube"]
        credentials = Credentials.from_authorized_user_info(raw, self.scopes)
        granted_scopes = {str(scope).strip() for scope in (credentials.scopes or [])}
        if "https://www.googleapis.com/auth/youtube.upload" in self.scopes and granted_scopes and "https://www.googleapis.com/auth/youtube.upload" not in granted_scopes:
            email = _safe_text((self.account or {}).get("email")) or "a conta seleccionada"
            raise RuntimeError(f"{email} está autorizada apenas para leitura/listagem. Autorize novamente esta conta com o escopo de upload YouTube.")
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self._save_credentials(credentials)
        return credentials

    def _save_credentials(self, credentials: Any, *, nested: bool = False) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.loads(credentials.to_json())
        if nested:
            payload = {"youtube": payload}
        temporary = self.token_path.with_name(f".{self.token_path.name}.{secrets.token_hex(6)}.tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        temporary.replace(self.token_path)
        try:
            os.chmod(self.token_path, 0o600)
        except OSError:
            pass

    def _build_client(self, credentials: Any) -> Any:
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise RuntimeError("A biblioteca Google API Client ainda não está instalada. Execute a instalação do Thunderbolt novamente.") from exc
        return build("youtube", "v3", credentials=credentials, cache_discovery=False)

    def authorize(self, *, open_browser: bool = True) -> IntegrationResult:
        if not self.configured:
            return IntegrationResult(False, "Preencha o YouTube OAuth Client ID e Client Secret nas Configurações.", {"status": "not_configured"})
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError as exc:
            return IntegrationResult(False, "As dependências Google OAuth ainda não estão instaladas. Execute a instalação do Thunderbolt novamente.", {"status": "missing_dependencies", "error": str(exc)})
        try:
            flow = InstalledAppFlow.from_client_config(self._client_config(), self.scopes)
            credentials = flow.run_local_server(
                host=loopback_host(),
                port=loopback_port(),
                open_browser=open_browser,
                access_type="offline",
                prompt="consent",
                include_granted_scopes="true",
            )
            self._save_credentials(credentials, nested=self.__class__.__name__ == "YouTubeAutomationAgentUploader")
            return IntegrationResult(True, "Conta YouTube autorizada com sucesso.", {"status": "authorized", "token_path": str(self.token_path)})
        except Exception as exc:
            detail = str(exc)
            if "redirect_uri_mismatch" in detail.lower():
                message = (
                    "A autorização Google foi rejeitada (redirect_uri_mismatch). "
                    f"Use um cliente OAuth do tipo Desktop app ou adicione exactamente {loopback_redirect_uri()} "
                    "em Google Cloud > APIs e serviços > Credenciais > URIs de redireccionamento autorizados. "
                    "Não use uma URI sem a porta, com localhost diferente ou sem a barra final."
                )
            else:
                message = f"A autorização Google falhou: {detail}"
            return IntegrationResult(False, message, {"status": "authorization_failed", "redirect_uri": loopback_redirect_uri()})

    def status(self) -> IntegrationResult:
        if not self.configured:
            return IntegrationResult(False, "YouTube OAuth ainda não configurado.", {"status": "not_configured", "authorized": False})
        if not self.token_exists:
            return IntegrationResult(False, "YouTube OAuth configurado, mas a conta ainda não foi autorizada.", {"status": "requires_authorization", "authorized": False})
        try:
            credentials = self._load_credentials()
            if credentials and credentials.valid:
                return IntegrationResult(True, "YouTube autorizado e pronto para publicar.", {"status": "ready", "authorized": True})
            if credentials and credentials.refresh_token:
                return IntegrationResult(True, "YouTube autorizado; o token será renovado no próximo uso.", {"status": "ready_refreshable", "authorized": True})
        except Exception as exc:
            return IntegrationResult(False, f"Token YouTube inválido ou expirado: {exc}", {"status": "invalid_token", "authorized": False})
        return IntegrationResult(False, "Token YouTube não está pronto para publicar.", {"status": "requires_authorization", "authorized": False})

    def _upload_common(
        self,
        *,
        video_path: str,
        title: str,
        description: str,
        tags: list[str],
        category_id: str,
        language: str,
        privacy_status: str,
        publish_at: str | None,
        thumbnail_path: str | None,
        captions_path: str | None,
    ) -> IntegrationResult:
        valid, message, path = validate_video_file(video_path)
        if not valid:
            return IntegrationResult(False, message, {"status": "invalid_video", "path": str(path)})
        try:
            credentials = self._load_credentials()
            if credentials is None:
                return IntegrationResult(False, "Autorize primeiro a conta YouTube.", {"status": "requires_authorization", "path": str(path)})
            youtube = self._build_client(credentials)
            body = build_agent_video_metadata(
                title=title,
                description=description,
                tags=tags,
                category_id=category_id,
                language=language,
                privacy_status=privacy_status,
                publish_at=publish_at,
                embeddable=True,
                notify_subscribers=True,
                allow_audio_remixing=True,
                allow_video_remixing=True,
            )
            try:
                from googleapiclient.http import MediaFileUpload
            except ImportError as exc:
                raise RuntimeError("A biblioteca de upload Google ainda não está instalada.") from exc
            media = MediaFileUpload(str(path), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media, notifySubscribers=True)
            response = None
            while response is None:
                _, response = request.next_chunk()
            video_id = response.get("id") if isinstance(response, dict) else None
            if not video_id:
                return IntegrationResult(False, "O YouTube não devolveu um ID de vídeo após o upload.", {"status": "upload_failed", "response": response or {}})

            extras: dict[str, Any] = {}
            thumbnail = _path_value(thumbnail_path)
            if thumbnail and thumbnail.exists() and thumbnail.is_file():
                try:
                    with thumbnail.open("rb") as handle:
                        youtube.thumbnails().set(videoId=video_id, media_body=handle).execute()
                    extras["thumbnail_uploaded"] = True
                except Exception as exc:
                    extras["thumbnail_warning"] = str(exc)
            captions = _path_value(captions_path)
            if captions and captions.exists() and captions.is_file():
                try:
                    with captions.open("rb") as handle:
                        youtube.captions().insert(
                            part="snippet",
                            body={"snippet": {"videoId": video_id, "language": language or "pt", "name": "Thunderbolt", "isDraft": False}},
                            media_body=handle,
                        ).execute()
                    extras["captions_uploaded"] = True
                except Exception as exc:
                    extras["captions_warning"] = str(exc)
            return IntegrationResult(
                True,
                f"Vídeo publicado no YouTube: https://www.youtube.com/watch?v={video_id}",
                {"status": "published", "video_id": video_id, "url": f"https://www.youtube.com/watch?v={video_id}", "mechanism": self.__class__.__name__, **extras},
            )
        except Exception as exc:
            return IntegrationResult(False, f"Falha no upload YouTube: {exc}", {"status": "upload_failed", "error": str(exc), "mechanism": self.__class__.__name__})


class YouTubeAutomationAgentUploader(_GoogleYouTubeBase):
    """Adaptation of the source agent's PublishingSchedulingAgent inside Thunderbolt."""

    def __init__(self, settings: dict[str, Any], storage_root: Path, account: dict[str, Any] | None = None):
        super().__init__(settings, storage_root / "state" / "youtube_agent_tokens.json", AGENT_SCOPES, account=account)

    def upload(self, **kwargs: Any) -> IntegrationResult:
        result = self._upload_common(**kwargs)
        result.data.setdefault("mechanism", "youtube-automation-agent-adaptado")
        return result


class DirectYouTubeOAuthUploader(_GoogleYouTubeBase):
    """Independent minimal OAuth upload path used only after the primary path fails."""

    def __init__(self, settings: dict[str, Any], storage_root: Path, account: dict[str, Any] | None = None):
        super().__init__(
            settings,
            storage_root / "state" / "youtube_oauth_fallback_token.json",
            FALLBACK_SCOPES,
            alternate_token_path=storage_root / "state" / "youtube_agent_tokens.json",
            account=account,
        )

    def upload(self, **kwargs: Any) -> IntegrationResult:
        result = self._upload_common(**kwargs)
        result.data.setdefault("mechanism", "oauth-direct-fallback")
        return result


def upload_youtube_with_fallback(
    settings: dict[str, Any],
    storage_root: Path,
    *,
    video_path: str,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    category_id: str = "22",
    language: str = "pt-BR",
    privacy_status: str = "unlisted",
    publish_at: str | None = None,
    thumbnail_path: str | None = None,
    captions_path: str | None = None,
    account: dict[str, Any] | None = None,
    on_attempt: Callable[[UploadAttempt], None] | None = None,
) -> IntegrationResult:
    """Run the adapted agent path first and OAuth direct only as redundancy."""
    kwargs = {
        "video_path": video_path,
        "title": title,
        "description": description,
        "tags": tags or [],
        "category_id": category_id,
        "language": language,
        "privacy_status": privacy_status,
        "publish_at": publish_at,
        "thumbnail_path": thumbnail_path,
        "captions_path": captions_path,
    }
    attempts: list[dict[str, Any]] = []
    primary = YouTubeAutomationAgentUploader(settings, storage_root, account=account)
    primary_result = primary.upload(**kwargs)
    primary_result.data.setdefault("mechanism", "youtube-automation-agent-adaptado")
    primary_attempt = UploadAttempt("youtube-automation-agent-adaptado", primary_result)
    attempts.append({"mechanism": primary_attempt.mechanism, "ok": primary_result.ok, "message": primary_result.message, "data": primary_result.data})
    if on_attempt:
        on_attempt(primary_attempt)
    if primary_result.ok:
        primary_result.data["attempts"] = attempts
        return primary_result

    fallback = DirectYouTubeOAuthUploader(settings, storage_root, account=account)
    fallback_result = fallback.upload(**kwargs)
    fallback_result.data.setdefault("mechanism", "oauth-direct-fallback")
    fallback_attempt = UploadAttempt("oauth-direct-fallback", fallback_result)
    attempts.append({"mechanism": fallback_attempt.mechanism, "ok": fallback_result.ok, "message": fallback_result.message, "data": fallback_result.data})
    if on_attempt:
        on_attempt(fallback_attempt)
    fallback_result.data["attempts"] = attempts
    if fallback_result.ok:
        fallback_result.message = f"Upload concluído pelo fallback OAuth directo após falha do agente: {fallback_result.message}"
        return fallback_result
    return IntegrationResult(False, f"O agente de upload falhou e o fallback OAuth também falhou. Agente: {primary_result.message} Fallback: {fallback_result.message}", {"status": "all_upload_mechanisms_failed", "attempts": attempts})


def authorize_youtube_agent(settings: dict[str, Any], storage_root: Path, *, open_browser: bool = True) -> IntegrationResult:
    return YouTubeAutomationAgentUploader(settings, storage_root).authorize(open_browser=open_browser)


def authorize_youtube_fallback(settings: dict[str, Any], storage_root: Path, *, open_browser: bool = True) -> IntegrationResult:
    return DirectYouTubeOAuthUploader(settings, storage_root).authorize(open_browser=open_browser)


def youtube_upload_status(settings: dict[str, Any], storage_root: Path) -> dict[str, IntegrationResult]:
    return {
        "agent": YouTubeAutomationAgentUploader(settings, storage_root).status(),
        "fallback": DirectYouTubeOAuthUploader(settings, storage_root).status(),
    }
