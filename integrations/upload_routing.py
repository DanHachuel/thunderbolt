"""Ordered YouTube upload routing for Thunderbolt.

The route is intentionally deterministic:
1. Official YouTube API, up to five successful sends per Google account/day.
2. Internal browser-session upload, when the account document is complete.
3. Postiz, when configured with an API key and integration ID.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Callable

from integrations.platforms import IntegrationResult, YouTubeAdapter
from integrations.postiz import PostizAdapter
from integrations.youtube_direct_credentials import document_status
from integrations.youtube_direct_upload import YouTubeDirectUploader
from hermes_ui.storage import read_json, write_json

OFFICIAL_DAILY_LIMIT = 5
QUOTA_FILENAME = "official_upload_quota.json"


def _attempt_record(name: str, result: IntegrationResult, *, skipped: bool = False) -> dict[str, Any]:
    return {
        "route": name,
        "status": "skipped" if skipped else ("success" if result.ok else "failed"),
        "message": result.message,
        "data": result.data,
    }


def _quota_key(channel: dict[str, Any], account: dict[str, Any] | None) -> str:
    if account and account.get("id"):
        return f"account:{account['id']}"
    if channel.get("google_account_id"):
        return f"account:{channel['google_account_id']}"
    return f"channel:{channel.get('id', 'unknown')}"


def official_upload_count(channel: dict[str, Any], account: dict[str, Any] | None, *, today: str | None = None) -> int:
    today = today or date.today().isoformat()
    state = read_json(QUOTA_FILENAME, {})
    if not isinstance(state, dict):
        return 0
    entry = state.get(_quota_key(channel, account), {})
    if not isinstance(entry, dict) or entry.get("date") != today:
        return 0
    try:
        return max(0, int(entry.get("count", 0)))
    except (TypeError, ValueError):
        return 0


def record_official_upload(channel: dict[str, Any], account: dict[str, Any] | None, *, today: str | None = None) -> int:
    today = today or date.today().isoformat()
    state = read_json(QUOTA_FILENAME, {})
    if not isinstance(state, dict):
        state = {}
    key = _quota_key(channel, account)
    current = official_upload_count(channel, account, today=today)
    state[key] = {"date": today, "count": current + 1}
    write_json(QUOTA_FILENAME, state)
    return current + 1


def _result_with_attempts(result: IntegrationResult, attempts: list[dict[str, Any]], route: str) -> IntegrationResult:
    data = dict(result.data or {})
    data["route"] = route
    data["attempts"] = attempts
    return IntegrationResult(result.ok, result.message, data)


def upload_with_default_route(
    settings: dict[str, Any],
    *,
    storage_root: Path,
    channel: dict[str, Any],
    account: dict[str, Any] | None,
    video_path: str,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    category_id: str = "22",
    language: str = "pt-BR",
    privacy_status: str = "unlisted",
    thumbnail_path: str = "",
    captions_path: str = "",
    official_uploader: Callable[..., IntegrationResult] | None = None,
    direct_uploader: Callable[..., IntegrationResult] | None = None,
    postiz_publisher: Callable[..., IntegrationResult] | None = None,
) -> IntegrationResult:
    attempts: list[dict[str, Any]] = []
    quota_count = official_upload_count(channel, account)
    if quota_count >= OFFICIAL_DAILY_LIMIT:
        quota_result = IntegrationResult(False, f"Limite local de {OFFICIAL_DAILY_LIMIT} envios oficiais por conta Google atingido hoje; a tentar o próximo método.", {"count": quota_count, "limit": OFFICIAL_DAILY_LIMIT})
        attempts.append(_attempt_record("API Oficial", quota_result, skipped=True))
    else:
        official_uploader = official_uploader or YouTubeAdapter(settings).upload_video
        try:
            official_result = official_uploader(
                video_path,
                title=title,
                description=description,
                tags=tags or [],
                category_id=category_id,
                language=language,
                privacy_status=privacy_status,
                thumbnail_path=thumbnail_path,
                captions_path=captions_path,
            )
        except Exception as exc:  # Keep fallback actionable and deterministic.
            official_result = IntegrationResult(False, f"API Oficial falhou: {exc}", {})
        attempts.append(_attempt_record("API Oficial", official_result))
        if official_result.ok:
            used = record_official_upload(channel, account)
            data = dict(official_result.data or {})
            data["official_daily_count"] = used
            data["official_daily_limit"] = OFFICIAL_DAILY_LIMIT
            data["route"] = "API Oficial"
            data["attempts"] = attempts
            return IntegrationResult(True, official_result.message, data)

    direct_ready = False
    if account:
        try:
            status = document_status(storage_root, account, channel, settings, [channel])
            direct_ready = bool(status.get("ready"))
            if not direct_ready:
                missing = list(status.get("missing_cookies", []))
                if not status.get("has_session_info"):
                    missing.append("sessionInfo")
                if not status.get("has_innertube_api_key"):
                    missing.append("INNERTUBE_API_KEY")
                if not status.get("has_delegated_session_id"):
                    missing.append("DELEGATED_SESSION_ID")
                direct_result = IntegrationResult(False, f"Upload directo indisponível: {', '.join(missing)}.", {"missing": missing})
            else:
                direct_result = None
        except Exception as exc:
            direct_result = IntegrationResult(False, f"Não foi possível validar o documento do Upload directo: {exc}", {})
    else:
        direct_result = IntegrationResult(False, "Upload directo indisponível: o canal não tem uma conta Google associada.", {})
    if direct_ready:
        direct_uploader = direct_uploader or YouTubeDirectUploader(settings, channel, account=account, storage_root=storage_root).upload
        try:
            direct_result = direct_uploader(video_path, title=title, description=description, visibility=privacy_status)
        except Exception as exc:
            direct_result = IntegrationResult(False, f"Upload directo falhou: {exc}", {})
    attempts.append(_attempt_record("Upload directo", direct_result))
    if direct_result.ok:
        return _result_with_attempts(direct_result, attempts, "Upload directo")

    postiz = PostizAdapter(settings)
    if not bool(settings.get("postiz_enabled", False)):
        postiz_result = IntegrationResult(False, "Postiz está desactivado em Configuração API > API Keys > Serviços e modelos.", {})
        attempts.append(_attempt_record("Postiz", postiz_result, skipped=True))
    else:
        postiz_publisher = postiz_publisher or postiz.publish_video
        try:
            postiz_result = postiz_publisher(
                video_path,
                integration_id=str(settings.get("postiz_integration_id", "") or ""),
                title=title,
                description=description,
                visibility=privacy_status,
                tags=tags or [],
                thumbnail_path=thumbnail_path,
            )
        except Exception as exc:
            postiz_result = IntegrationResult(False, f"Postiz falhou: {exc}", {})
        attempts.append(_attempt_record("Postiz", postiz_result))
        if postiz_result.ok:
            return _result_with_attempts(postiz_result, attempts, "Postiz")

    return IntegrationResult(False, "Nenhum método de envio conseguiu publicar o vídeo.", {"attempts": attempts, "route": "none"})
