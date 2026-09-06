from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

import requests


META_GRAPH_BASE_URL = "https://graph.facebook.com/v20.0"


def _result(status: str, message: str, *, status_code: int | None = None, data: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "message": message[:240],
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    if status_code is not None:
        payload["status_code"] = int(status_code)
    if data:
        payload["data"] = dict(data)
    return payload


def _get_graph(identifier: str, access_token: str, fields: str) -> dict[str, Any]:
    identifier = str(identifier or "").strip()
    access_token = str(access_token or "").strip()
    if not access_token:
        return _result("missing", "Informe a API key/token antes do teste.")
    if not identifier:
        return _result("missing", "Informe o identificador da conta antes do teste.")
    try:
        response = requests.get(
            f"{META_GRAPH_BASE_URL}/{identifier}",
            params={"fields": fields, "access_token": access_token},
            timeout=15,
        )
    except requests.RequestException:
        return _result("error", "Não foi possível contactar a Meta Graph API.")
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if response.status_code >= 400 or payload.get("error"):
        error = payload.get("error") if isinstance(payload, dict) else {}
        message = str(error.get("message") or f"A Meta Graph API devolveu HTTP {response.status_code}.")
        return _result("error", message, status_code=response.status_code)
    return _result("success", "Chamada Meta Graph API concluída.", status_code=response.status_code, data={
        "id": payload.get("id"),
        "name": payload.get("name"),
        "username": payload.get("username"),
    })


def test_instagram_api_card(card: Mapping[str, Any]) -> dict[str, Any]:
    """Validate an Instagram Graph API card without persisting its token."""
    return _get_graph(
        str(card.get("account_id") or ""),
        str(card.get("access_token") or ""),
        "id,username,name,profile_picture_url,followers_count,media_count",
    )


def test_facebook_pages_api_card(card: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a Facebook Pages Graph API card without persisting its token."""
    return _get_graph(
        str(card.get("page_id") or ""),
        str(card.get("access_token") or ""),
        "id,name,fan_count,followers_count,link",
    )


__all__ = ["META_GRAPH_BASE_URL", "test_instagram_api_card", "test_facebook_pages_api_card"]
