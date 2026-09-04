from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Mapping

from .youtube_batch import account_status, token_path

ANALYTICS_SCOPE = "https://www.googleapis.com/auth/yt-analytics.readonly"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _accounts(settings: Mapping[str, Any]) -> list[dict[str, Any]]:
    value = settings.get("youtube_batch_accounts", [])
    return [dict(item) for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def find_account_for_channel(channel: Mapping[str, Any], settings: Mapping[str, Any]) -> dict[str, Any] | None:
    channel_id = _text(channel.get("youtube_channel_id") or channel.get("id"))
    account_id = _text(channel.get("google_account_id"))
    accounts = _accounts(settings)
    for account in accounts:
        if account_id and _text(account.get("id")) == account_id:
            return account
        known_channels = account.get("channels", [])
        if isinstance(known_channels, list) and any(_text(item.get("youtube_channel_id") or item.get("id")) == channel_id for item in known_channels if isinstance(item, Mapping)):
            return account
    return None


def _load_credentials(account: Mapping[str, Any], storage_root: Path) -> tuple[Any | None, str]:
    path = token_path(storage_root, dict(account))
    status = account_status(dict(account), storage_root)
    if not status.ok:
        return None, str(status.message)
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        raw = json.loads(path.read_text(encoding="utf-8"))
        scopes = list(raw.get("scopes") or []) if isinstance(raw, dict) else []
        if ANALYTICS_SCOPE not in scopes:
            return None, "OAuth autorizado sem o scope YouTube Analytics; é necessária uma nova autorização condicional."
        credentials = Credentials.from_authorized_user_info(raw, scopes)
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            path.write_text(credentials.to_json(), encoding="utf-8")
        return credentials, "ready"
    except ImportError:
        return None, "Dependências Google OAuth/API não instaladas."
    except (OSError, ValueError, TypeError) as exc:
        return None, f"Token OAuth inválido: {exc}"


def query_channel_analytics(channel: Mapping[str, Any], settings: Mapping[str, Any], storage_root: Path, *, days: int = 28) -> dict[str, Any]:
    account = find_account_for_channel(channel, settings)
    if not account:
        return {"status": "not_connected", "message": "Nenhuma conta Google OAuth compatível com este canal."}
    credentials, message = _load_credentials(account, storage_root)
    if credentials is None:
        return {"status": "requires_authorization", "message": message, "email": _text(account.get("email"))}
    channel_id = _text(channel.get("youtube_channel_id") or channel.get("id"))
    if not channel_id:
        return {"status": "unavailable", "message": "O canal não tem YouTube channel ID."}
    try:
        from googleapiclient.discovery import build
        analytics = build("youtubeAnalytics", "v2", credentials=credentials, cache_discovery=False)
        end_date = date.today()
        start_date = end_date - timedelta(days=max(1, days) - 1)
        response = analytics.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start_date.isoformat(),
            endDate=end_date.isoformat(),
            metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost",
        ).execute()
        rows = response.get("rows", [])
        headers = [item.get("name") for item in response.get("columnHeaders", [])]
        values = dict(zip(headers, rows[0])) if rows else {}
        return {"status": "ready", "source": "youtube_analytics_oauth", "window_days": days, "values": values, "email": _text(account.get("email"))}
    except ImportError:
        return {"status": "missing_dependencies", "message": "A biblioteca Google API Client ainda não está instalada."}
    except Exception as exc:
        return {"status": "query_failed", "message": str(exc)[:300], "email": _text(account.get("email"))}


__all__ = ["ANALYTICS_SCOPE", "find_account_for_channel", "query_channel_analytics"]
