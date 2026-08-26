"""Outbound Telegram Gateway integration for persisted Thunderbolt notifications."""

from __future__ import annotations

import os
from typing import Any, Callable

import requests

from .platforms import IntegrationResult

DEFAULT_TELEGRAM_API_BASE_URL = "https://api.telegram.org"
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
DEFAULT_TELEGRAM_TIMEOUT = 15


class TelegramGatewayAdapter:
    """Send Thunderbolt notifications through the Telegram Bot API.

    The adapter deliberately implements outbound delivery only. It does not
    poll Telegram or receive messages, which keeps notification delivery
    isolated from the production and upload flows.
    """

    def __init__(self, settings: dict[str, Any] | None = None, *, request_client: Any = requests) -> None:
        self.settings = settings or {}
        self.enabled = bool(self.settings.get("telegram_enabled", False))
        self.bot_token = str(self.settings.get("telegram_bot_token") or os.getenv("TELEGRAM_BOT_TOKEN", "")).strip()
        self.chat_id = str(self.settings.get("telegram_chat_id") or os.getenv("TELEGRAM_CHAT_ID", "")).strip()
        self.proxy_url = str(self.settings.get("telegram_proxy_url") or os.getenv("TELEGRAM_PROXY_URL", "")).strip()
        self.timeout = max(1, int(self.settings.get("telegram_timeout_seconds", DEFAULT_TELEGRAM_TIMEOUT) or DEFAULT_TELEGRAM_TIMEOUT))
        self._request_client = request_client

    def _error(self, message: str, *, status_code: int | None = None, error_type: str = "") -> IntegrationResult:
        data: dict[str, Any] = {}
        if status_code is not None:
            data["status_code"] = status_code
        if error_type:
            data["error_type"] = error_type
        return IntegrationResult(False, message, data)

    def status(self) -> IntegrationResult:
        if not self.enabled:
            return self._error("Telegram está desactivado nas notificações.", error_type="disabled")
        if not self.bot_token or not self.chat_id:
            return self._error("Telegram não está configurado: indique o Bot Token e o Chat ID.", error_type="missing_configuration")
        return IntegrationResult(True, "Telegram configurado para notificações.", {"chat_id_configured": True})

    def _url(self, method: str) -> str:
        return f"{DEFAULT_TELEGRAM_API_BASE_URL}/bot{self.bot_token}/{method}"

    def _request_kwargs(self, payload: dict[str, Any]) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"json": payload, "timeout": self.timeout}
        if self.proxy_url:
            kwargs["proxies"] = {"http": self.proxy_url, "https": self.proxy_url}
        return kwargs

    def _post(self, method: str, payload: dict[str, Any]) -> IntegrationResult:
        try:
            response = self._request_client.post(self._url(method), **self._request_kwargs(payload))
        except requests.RequestException as exc:
            return self._error("Não foi possível contactar o Telegram.", error_type=type(exc).__name__)
        except Exception as exc:
            return self._error("A chamada ao Telegram falhou.", error_type=type(exc).__name__)

        status_code = int(getattr(response, "status_code", 0) or 0)
        if status_code == 429:
            return self._error("O Telegram limitou a chamada de notificação; tente novamente mais tarde.", status_code=status_code, error_type="rate_limited")
        if status_code in {401, 403}:
            return self._error("O Telegram rejeitou o Bot Token ou não permite o envio para este Chat ID.", status_code=status_code, error_type="unauthorized")
        if status_code < 200 or status_code >= 300:
            return self._error("O Telegram rejeitou a notificação.", status_code=status_code or None, error_type="http_error")
        try:
            payload_response = response.json()
        except (TypeError, ValueError):
            return self._error("O Telegram devolveu uma resposta inválida.", status_code=status_code, error_type="invalid_json")
        if not isinstance(payload_response, dict) or payload_response.get("ok") is not True:
            return self._error("O Telegram não aceitou a notificação.", status_code=status_code, error_type="api_error")
        return IntegrationResult(True, "Notificação enviada pelo Telegram.", {"status_code": status_code, "result": payload_response.get("result")})

    @staticmethod
    def split_message(text: str, *, max_length: int = TELEGRAM_MAX_MESSAGE_LENGTH) -> list[str]:
        """Split a message at line boundaries while respecting Telegram's limit."""
        normalized = str(text or "").strip()
        if not normalized:
            return []
        chunks: list[str] = []
        remaining = normalized
        while len(remaining) > max_length:
            cut = remaining.rfind("\n", 0, max_length + 1)
            if cut < max_length // 2:
                cut = max_length
            chunks.append(remaining[:cut].rstrip())
            remaining = remaining[cut:].lstrip()
        if remaining:
            chunks.append(remaining)
        return chunks

    @staticmethod
    def format_notification(notification: dict[str, Any]) -> str:
        """Format an already-redacted local notification for Telegram."""
        title = str(notification.get("title") or notification.get("label") or "Notificação").strip()
        message = str(notification.get("message") or "").strip()
        category = str(notification.get("category") or "Sistema").strip()
        created_at = str(notification.get("created_at") or "").strip()
        lines = [title]
        if message:
            lines.append(message)
        details: list[str] = []
        if category:
            details.append(f"Categoria: {category}")
        if created_at:
            details.append(f"Data: {created_at}")
        metadata = notification.get("metadata")
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                if value in (None, "", [], {}):
                    continue
                details.append(f"{key}: {value}")
        if details:
            lines.extend(["", *details])
        return "\n".join(lines)

    def send_message(self, text: str) -> IntegrationResult:
        """Send plain text to the configured chat, splitting oversized messages."""
        status = self.status()
        if not status.ok:
            return status
        chunks = self.split_message(text)
        if not chunks:
            return self._error("A notificação Telegram está vazia.", error_type="empty_message")
        message_ids: list[str] = []
        for chunk in chunks:
            result = self._post("sendMessage", {"chat_id": self.chat_id, "text": chunk})
            if not result.ok:
                return result
            message_result = result.data.get("result") if isinstance(result.data, dict) else None
            if isinstance(message_result, dict) and message_result.get("message_id") is not None:
                message_ids.append(str(message_result["message_id"]))
        return IntegrationResult(True, "Notificação enviada pelo Telegram.", {"message_ids": message_ids, "chunks": len(chunks)})

    def send_notification(self, notification: dict[str, Any]) -> IntegrationResult:
        """Format and send one persisted Thunderbolt notification."""
        return self.send_message(self.format_notification(notification))


def send_notification_to_telegram(notification: dict[str, Any], settings: dict[str, Any] | None = None) -> IntegrationResult:
    """Convenience function used by the notification persistence layer."""
    return TelegramGatewayAdapter(settings).send_notification(notification)


__all__ = [
    "DEFAULT_TELEGRAM_API_BASE_URL",
    "DEFAULT_TELEGRAM_TIMEOUT",
    "TELEGRAM_MAX_MESSAGE_LENGTH",
    "TelegramGatewayAdapter",
    "send_notification_to_telegram",
]
