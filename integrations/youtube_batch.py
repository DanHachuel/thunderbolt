from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from pathlib import Path
from typing import Any

from integrations.platforms import IntegrationResult

BATCH_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
DEFAULT_LOOPBACK_HOST = "127.0.0.1"
DEFAULT_LOOPBACK_PORT = 8765


def loopback_host() -> str:
    return _text(os.getenv("THUNDERBOLT_OAUTH_LOOPBACK_HOST")) or DEFAULT_LOOPBACK_HOST


def loopback_port() -> int:
    try:
        port = int(os.getenv("THUNDERBOLT_OAUTH_LOOPBACK_PORT", str(DEFAULT_LOOPBACK_PORT)))
    except (TypeError, ValueError):
        port = DEFAULT_LOOPBACK_PORT
    return port if 1024 <= port <= 65535 else DEFAULT_LOOPBACK_PORT


def loopback_redirect_uri() -> str:
    return f"http://{loopback_host()}:{loopback_port()}/"


def _authorization_error_message(email: str, exc: Exception) -> str:
    detail = str(exc)
    if "redirect_uri_mismatch" in detail.lower():
        return (
            f"A autorização da conta {email} foi rejeitada pelo Google (redirect_uri_mismatch). "
            f"Use um cliente OAuth do tipo Desktop app ou adicione exactamente {loopback_redirect_uri()} "
            "em Google Cloud > APIs e serviços > Credenciais > URIs de redireccionamento autorizados. "
            "Não use uma URI sem a porta, com localhost diferente ou sem a barra final."
        )
    return f"A autorização da conta {email} falhou: {detail}"


def _text(value: Any) -> str:
    return str(value or "").strip()


def account_key(account: dict[str, Any]) -> str:
    raw = _text(account.get("id") or account.get("email"))
    digest = hashlib.sha256(raw.lower().encode("utf-8")).hexdigest()[:16]
    slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")[:36] or "google-account"
    return f"{slug}-{digest}"


def token_path(storage_root: Path, account: dict[str, Any]) -> Path:
    return Path(storage_root) / "state" / "youtube_batch_tokens" / f"{account_key(account)}.json"


def _client_config(account: dict[str, Any]) -> dict[str, Any]:
    return {
        "installed": {
            "client_id": _text(account.get("client_id")),
            "client_secret": _text(account.get("client_secret")),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [loopback_redirect_uri()],
        }
    }


def _save_credentials(path: Path, credentials: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(6)}.tmp")
    temporary.write_text(credentials.to_json(), encoding="utf-8")
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass
    temporary.replace(path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _load_credentials(path: Path) -> Any | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError as exc:
        raise RuntimeError("As dependências Google OAuth ainda não estão instaladas. Execute a instalação do Thunderbolt novamente.") from exc
    raw = json.loads(path.read_text(encoding="utf-8"))
    credentials = Credentials.from_authorized_user_info(raw, BATCH_SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        _save_credentials(path, credentials)
    return credentials


def authorize_account(account: dict[str, Any], storage_root: Path, *, open_browser: bool = True) -> IntegrationResult:
    email = _text(account.get("email"))
    if not email or "@" not in email:
        return IntegrationResult(False, "Informe um e-mail Google válido para esta conta.", {"status": "email_not_configured"})
    if not _text(account.get("client_id")) or not _text(account.get("client_secret")):
        return IntegrationResult(False, "Preencha o OAuth Client ID e o OAuth Client Secret desta conta.", {"status": "oauth_not_configured", "email": email})
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        return IntegrationResult(False, "As dependências Google OAuth ainda não estão instaladas. Execute a instalação do Thunderbolt novamente.", {"status": "missing_dependencies", "error": str(exc)})
    try:
        flow = InstalledAppFlow.from_client_config(_client_config(account), BATCH_SCOPES)
        credentials = flow.run_local_server(
            host=loopback_host(),
            port=loopback_port(),
            open_browser=open_browser,
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
        )
        path = token_path(storage_root, account)
        _save_credentials(path, credentials)
        return IntegrationResult(True, f"Conta Google autorizada para listagem de canais: {email}.", {"status": "authorized", "email": email, "token_path": str(path)})
    except Exception as exc:
        return IntegrationResult(False, _authorization_error_message(email, exc), {"status": "authorization_failed", "email": email, "redirect_uri": loopback_redirect_uri()})


def delete_account_token(account: dict[str, Any], storage_root: Path) -> None:
    path = token_path(storage_root, account)
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def account_status(account: dict[str, Any], storage_root: Path) -> IntegrationResult:
    email = _text(account.get("email"))
    if not email or not _text(account.get("client_id")) or not _text(account.get("client_secret")):
        return IntegrationResult(False, "Conta incompleta: informe e-mail, Client ID e Client Secret.", {"status": "not_configured", "email": email})
    path = token_path(storage_root, account)
    if not path.exists():
        return IntegrationResult(False, "Conta configurada, mas ainda não autorizada.", {"status": "requires_authorization", "email": email})
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and (raw.get("refresh_token") or raw.get("access_token")):
            return IntegrationResult(True, f"Conta autorizada: {email}", {"status": "ready", "email": email, "token_path": str(path), "refresh_on_use": bool(raw.get("refresh_token"))})
    except (OSError, ValueError) as exc:
        return IntegrationResult(False, f"Token da conta {email} inválido: {exc}", {"status": "invalid_token", "email": email})
    return IntegrationResult(False, f"Token da conta {email} não está pronto.", {"status": "requires_authorization", "email": email})


def _channel_record(item: dict[str, Any]) -> dict[str, Any]:
    channel_id = _text(item.get("id"))
    snippet = item.get("snippet") or {}
    statistics = item.get("statistics") or {}
    custom_url = _text(snippet.get("customUrl"))
    url = f"https://www.youtube.com/{custom_url.lstrip('/')}" if custom_url else f"https://www.youtube.com/channel/{channel_id}"
    thumbnails = snippet.get("thumbnails") or {}
    thumbnail = (thumbnails.get("high") or thumbnails.get("medium") or thumbnails.get("default") or {}).get("url", "")

    def integer(value: Any) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    return {
        "youtube_channel_id": channel_id,
        "name": _text(snippet.get("title")) or channel_id,
        "url": url,
        "handle": custom_url,
        "description": _text(snippet.get("description")),
        "thumbnail_url": _text(thumbnail),
        "subscriber_count": integer(statistics.get("subscriberCount")),
        "video_count": integer(statistics.get("videoCount")),
        "view_count": integer(statistics.get("viewCount")),
        "metrics_source": "youtube_data_api_oauth_mine",
        "published_at": _text(snippet.get("publishedAt")),
    }


def list_my_channels(account: dict[str, Any], storage_root: Path) -> IntegrationResult:
    status = account_status(account, storage_root)
    if not status.ok:
        return status
    try:
        credentials = _load_credentials(token_path(storage_root, account))
        if credentials is None:
            return IntegrationResult(False, "Autorize primeiro esta conta Google.", {"status": "requires_authorization"})
        from googleapiclient.discovery import build

        youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
        channels: list[dict[str, Any]] = []
        page_token = None
        while True:
            kwargs: dict[str, Any] = {
                "part": "snippet,contentDetails,statistics",
                "mine": True,
                "maxResults": 50,
            }
            if page_token:
                kwargs["pageToken"] = page_token
            response = youtube.channels().list(**kwargs).execute()
            channels.extend(_channel_record(item) for item in response.get("items", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return IntegrationResult(True, f"{len(channels)} canal(is) encontrado(s) na conta {account.get('email')}.", {"status": "listed", "email": account.get("email", ""), "channels": channels, "count": len(channels)})
    except ImportError as exc:
        return IntegrationResult(False, "A biblioteca Google API Client ainda não está instalada. Execute a instalação do Thunderbolt novamente.", {"status": "missing_dependencies", "error": str(exc)})
    except Exception as exc:
        return IntegrationResult(False, f"Não foi possível listar os canais da conta {account.get('email', '')}: {exc}", {"status": "list_failed", "email": account.get("email", ""), "error": str(exc)})
