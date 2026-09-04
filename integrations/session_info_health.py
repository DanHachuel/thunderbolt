"""Health check read-only para sessões do Upload directo YouTube.

O token ``sessionInfo`` não é interpretado nem devolvido. O módulo controla a
idade de captura persistida no documento de credenciais, aplica uma janela
conservadora de expiração e permite que a UI/worker alerte antes de iniciar um
upload. A renovação continua manual: o utilizador deve substituir o token na
conta Google/YouTube.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from integrations.youtube_direct_credentials import credentials_document_path, load_credentials_document

DEFAULT_SESSION_INFO_TTL_HOURS = 19
DEFAULT_SESSION_INFO_ALERT_HOURS = 6
MIN_SESSION_INFO_TTL_HOURS = 1
MAX_SESSION_INFO_TTL_HOURS = 72


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def parse_timestamp(value: Any) -> datetime | None:
    """Parse ISO-8601 timestamps used in local credential documents."""
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (TypeError, ValueError, OSError, OverflowError):
            return None
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _clamp_hours(value: Any, default: int) -> int:
    try:
        hours = int(value)
    except (TypeError, ValueError):
        hours = default
    return max(MIN_SESSION_INFO_TTL_HOURS, min(MAX_SESSION_INFO_TTL_HOURS, hours))


@dataclass(frozen=True)
class SessionInfoHealth:
    """Safe, serialisable status of one account's sessionInfo token."""

    status: str
    message: str
    age_hours: float | None
    remaining_hours: float | None
    expires_at: str | None
    captured_at: str | None
    account_id: str
    account_label: str
    credential_file: str
    has_session_info: bool
    needs_manual_renewal: bool

    @property
    def ok(self) -> bool:
        """Whether the token is usable without a preventive warning."""
        return self.status == "healthy"

    @property
    def warning(self) -> bool:
        """Whether the account is usable but close to the configured TTL."""
        return self.status == "expiring"

    def as_dict(self) -> dict[str, Any]:
        """Return public health fields without secrets or token material."""
        return {
            "status": self.status,
            "message": self.message,
            "age_hours": round(self.age_hours, 2) if self.age_hours is not None else None,
            "remaining_hours": round(self.remaining_hours, 2) if self.remaining_hours is not None else None,
            "expires_at": self.expires_at,
            "captured_at": self.captured_at,
            "account_id": self.account_id,
            "account_label": self.account_label,
            "credential_file": self.credential_file,
            "has_session_info": self.has_session_info,
            "needs_manual_renewal": self.needs_manual_renewal,
        }


def health_check_session_info(
    account: dict[str, Any],
    document: dict[str, Any] | None,
    *,
    now: datetime | None = None,
    ttl_hours: Any = DEFAULT_SESSION_INFO_TTL_HOURS,
    alert_hours: Any = DEFAULT_SESSION_INFO_ALERT_HOURS,
    credential_file: str | Path = "",
) -> SessionInfoHealth:
    """Check a sessionInfo document without making a network request.

    A new or legacy document without ``sessionInfoCapturedAt`` is reported as
    ``unknown`` rather than silently trusted. The next manual save records the
    capture time; this avoids claiming that an old token is fresh.
    """
    current = now or utc_now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    ttl = _clamp_hours(ttl_hours, DEFAULT_SESSION_INFO_TTL_HOURS)
    alert = max(1, min(ttl - 1, _clamp_hours(alert_hours, DEFAULT_SESSION_INFO_ALERT_HOURS)))
    document = document if isinstance(document, dict) else {}
    session_info = str(document.get("sessionInfo") or document.get("session_info") or "").strip()
    captured_value = document.get("sessionInfoCapturedAt") or document.get("session_info_captured_at")
    captured = parse_timestamp(captured_value)
    account_id = str(account.get("id") or document.get("account_id") or "").strip()
    account_label = str(account.get("label") or account.get("name") or account.get("email") or account_id or "Conta Google").strip()
    file_text = str(credential_file or "")
    if not session_info:
        return SessionInfoHealth("missing", "Falta sessionInfo nesta conta Google/YouTube.", None, None, None, None, account_id, account_label, file_text, False, True)
    if str(document.get("sessionInfoHealthStatus") or "").strip() == "blocked_by_google":
        return SessionInfoHealth("blocked_by_google", "Sessão bloqueada pelo Google; é necessário login manual.", None, None, None, captured.isoformat() if captured else None, account_id, account_label, file_text, True, True)
    if str(document.get("sessionInfoHealthStatus") or "").strip() == "invalid_format":
        return SessionInfoHealth("invalid_format", "sessionInfo capturado, mas o formato foi rejeitado.", None, None, None, captured.isoformat() if captured else None, account_id, account_label, file_text, True, True)
    if captured is None:
        # Legacy documents without a capture date remain compatible with the
        # existing uploader, while the UI still asks for a manual renewal.
        return SessionInfoHealth("unknown", "sessionInfo existe, mas a data de captura não é conhecida; renove a sessão para activar o alerta de expiração.", None, None, None, None, account_id, account_label, file_text, True, True)
    age = max(0.0, (current - captured.astimezone(timezone.utc)).total_seconds() / 3600)
    expires = parse_timestamp(document.get("expires_at")) or (captured.astimezone(timezone.utc) + timedelta(hours=ttl))
    remaining = (expires - current.astimezone(timezone.utc)).total_seconds() / 3600
    if remaining <= 0:
        return SessionInfoHealth("expired", f"sessionInfo expirou há {abs(remaining):.1f} horas; renove-o manualmente antes de criar ou enviar conteúdos.", age, remaining, expires.isoformat(), captured.isoformat(), account_id, account_label, file_text, True, True)
    if remaining <= alert:
        return SessionInfoHealth("expiring", f"sessionInfo expira em aproximadamente {remaining:.1f} horas; renove-o manualmente preventivamente.", age, remaining, expires.isoformat(), captured.isoformat(), account_id, account_label, file_text, True, True)
    return SessionInfoHealth("healthy", f"sessionInfo válido por aproximadamente mais {remaining:.1f} horas.", age, remaining, expires.isoformat(), captured.isoformat(), account_id, account_label, file_text, True, False)


def session_info_health_from_settings(
    account: dict[str, Any],
    document: dict[str, Any] | None,
    settings: dict[str, Any] | None = None,
    *,
    now: datetime | None = None,
    credential_file: str | Path = "",
) -> SessionInfoHealth:
    """Apply local settings while keeping the 24–48 hour TTL bounded."""
    settings = settings or {}
    return health_check_session_info(
        account,
        document,
        now=now,
        ttl_hours=settings.get("session_info_ttl_hours", DEFAULT_SESSION_INFO_TTL_HOURS),
        alert_hours=settings.get("session_info_alert_hours", DEFAULT_SESSION_INFO_ALERT_HOURS),
        credential_file=credential_file,
    )


def check_account_session_info_health(
    storage_root: Path,
    account: dict[str, Any],
    settings: dict[str, Any] | None = None,
    *,
    now: datetime | None = None,
) -> SessionInfoHealth:
    """Load one account document and return its safe SessionInfo health state."""
    settings = settings or {}
    document = load_credentials_document(storage_root, account, settings, create=False)
    state_path = credentials_document_path(storage_root, account).with_name("renewal_state.json")
    try:
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    except (OSError, json.JSONDecodeError):
        state = {}
    if isinstance(state, dict) and state.get("status") in {"blocked_by_google", "invalid_format"}:
        document = dict(document)
        document["sessionInfoHealthStatus"] = state["status"]
    return session_info_health_from_settings(
        account,
        document,
        settings,
        now=now,
        credential_file=credentials_document_path(storage_root, account),
    )


def check_all_accounts_session_info_health(
    storage_root: Path,
    settings: dict[str, Any] | None = None,
    *,
    now: datetime | None = None,
) -> list[SessionInfoHealth]:
    """Return health states for all configured Google/YouTube accounts."""
    settings = settings or {}
    accounts = settings.get("youtube_batch_accounts", [])
    if not isinstance(accounts, list):
        return []
    result: list[SessionInfoHealth] = []
    for account in accounts:
        if not isinstance(account, dict) or not str(account.get("id") or "").strip():
            continue
        result.append(check_account_session_info_health(storage_root, account, settings, now=now))
    return result


def emit_session_info_health_alerts(
    health_items: list[SessionInfoHealth],
    *,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Persist one deduplicated local notification per account and state."""
    from hermes_ui.notifications import record_notification

    current = now or utc_now()
    day = current.astimezone(timezone.utc).date().isoformat()
    created: list[dict[str, Any]] = []
    for health in health_items:
        if health.status not in {"unknown", "expiring", "expired"}:
            continue
        event_type = "session_info_expired" if health.status == "expired" else "session_info_expiring"
        state_label = "expirado" if health.status == "expired" else "a expirar"
        title = f"SessionInfo {state_label}: {health.account_label}"
        entry = record_notification(
            event_type,
            title,
            health.message,
            metadata={
                "account_id": health.account_id,
                "account_label": health.account_label,
                "status": health.status,
                "captured_at": health.captured_at or "",
                "expires_at": health.expires_at or "",
            },
            dedupe_key=f"session-info:{health.account_id}:{health.status}:{day}",
        )
        if entry:
            created.append(entry)
    return created


__all__ = [
    "DEFAULT_SESSION_INFO_ALERT_HOURS",
    "DEFAULT_SESSION_INFO_TTL_HOURS",
    "MAX_SESSION_INFO_TTL_HOURS",
    "MIN_SESSION_INFO_TTL_HOURS",
    "SessionInfoHealth",
    "check_account_session_info_health",
    "check_all_accounts_session_info_health",
    "emit_session_info_health_alerts",
    "health_check_session_info",
    "parse_timestamp",
    "session_info_health_from_settings",
]
