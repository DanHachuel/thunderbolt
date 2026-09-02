from __future__ import annotations

import base64
import hashlib
import secrets
import time
from typing import Any, Mapping
from urllib.parse import urlencode

import requests

AUTHORIZE_URL = "https://www.canva.com/api/oauth/authorize"
TOKEN_URL = "https://api.canva.com/rest/v1/oauth/token"


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_pkce_pair() -> tuple[str, str]:
    verifier = _b64(secrets.token_bytes(64))
    challenge = _b64(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def create_state() -> str:
    return _b64(secrets.token_bytes(48))


def authorization_url(client_id: str, redirect_uri: str, scope: str, state: str, code_challenge: str) -> str:
    params = {
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "scope": " ".join(str(scope or "").split()),
        "response_type": "code",
        "client_id": str(client_id).strip(),
        "state": str(state).strip(),
        "redirect_uri": str(redirect_uri).strip(),
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code(client_id: str, client_secret: str, code: str, redirect_uri: str, code_verifier: str, *, timeout: int = 30) -> dict[str, Any]:
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": code_verifier,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        },
        headers={"Accept": "application/json"},
        timeout=timeout,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Canva OAuth devolveu HTTP {response.status_code}: {response.text[:240]}")
    payload = response.json()
    if not payload.get("access_token"):
        raise RuntimeError("Canva OAuth não devolveu access_token.")
    return _with_expiry(payload)


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str, *, timeout: int = 30) -> dict[str, Any]:
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Accept": "application/json"},
        timeout=timeout,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Refresh Canva devolveu HTTP {response.status_code}: {response.text[:240]}")
    return _with_expiry(response.json())


def _with_expiry(payload: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    try:
        result["expires_at"] = int(time.time()) + max(0, int(payload.get("expires_in", 0)))
    except (TypeError, ValueError):
        result["expires_at"] = 0
    return result


def token_is_expiring(token: Mapping[str, Any], margin_seconds: int = 90) -> bool:
    try:
        return int(token.get("expires_at", 0)) <= int(time.time()) + margin_seconds
    except (TypeError, ValueError):
        return True
