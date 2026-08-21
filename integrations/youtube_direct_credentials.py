from __future__ import annotations

import json
import os
import re
import secrets
from pathlib import Path
from typing import Any

COOKIE_KEYS = ("SID", "SSID", "HSID", "APISID", "SAPISID")
DIRECT_DOCUMENT_NAME = "credentials.json"
DEFAULT_CHUNK_SIZE = 262144


def account_key(account: dict[str, Any]) -> str:
    raw = str(account.get("id") or "").strip()
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip(".-")
    return safe[:80] or "google-account"


def account_directory(storage_root: Path, account: dict[str, Any]) -> Path:
    return Path(storage_root) / "youtube_direct_accounts" / account_key(account)


def credentials_document_path(storage_root: Path, account: dict[str, Any]) -> Path:
    return account_directory(storage_root, account) / DIRECT_DOCUMENT_NAME


def cookie_file_path(storage_root: Path, account: dict[str, Any]) -> Path:
    """Legacy path retained only to migrate pre-document installations."""
    return account_directory(storage_root, account) / "cookies.json"


def _normalise_pairs(value: Any) -> dict[str, str]:
    pairs: dict[str, str] = {}
    if isinstance(value, dict):
        if isinstance(value.get("cookies"), list):
            return _normalise_pairs(value["cookies"])
        for key, item in value.items():
            key_text = str(key).strip()
            if key_text in COOKIE_KEYS:
                pairs[key_text] = str(item or "").strip()
        return pairs
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                name = str(item.get("name") or item.get("key") or "").strip()
                content = str(item.get("value") or "").strip()
                if name in COOKIE_KEYS:
                    pairs[name] = content
        return pairs
    return pairs


def parse_cookie_file(content: bytes, filename: str = "cookies.json") -> dict[str, str]:
    text = content.decode("utf-8-sig", errors="replace").strip()
    pairs: dict[str, str] = {}
    try:
        parsed = json.loads(text)
        pairs.update(_normalise_pairs(parsed))
    except json.JSONDecodeError:
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) >= 7 and fields[5].strip() in COOKIE_KEYS:
                pairs[fields[5].strip()] = fields[6].strip()
                continue
            if "=" in line:
                name, value = line.split("=", 1)
                name = name.strip()
                if name in COOKIE_KEYS:
                    pairs[name] = value.strip().rstrip(";")
    missing = [key for key in COOKIE_KEYS if not pairs.get(key)]
    if missing:
        raise ValueError(f"Faltam cookies obrigatórios no ficheiro {filename}: {', '.join(missing)}.")
    return {key: pairs[key] for key in COOKIE_KEYS}


def parse_credentials_document(content: bytes, filename: str = DIRECT_DOCUMENT_NAME) -> dict[str, Any]:
    try:
        raw = json.loads(content.decode("utf-8-sig", errors="replace"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"O documento de credenciais {filename} deve ser JSON válido.") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"O documento de credenciais {filename} deve conter um objecto JSON.")
    document = _normalise_document(raw, {"id": raw.get("account_id", ""), "email": raw.get("email", "")})
    missing = [key for key in COOKIE_KEYS if not document["cookies"].get(key)]
    if missing:
        raise ValueError(f"Faltam cookies obrigatórios no documento {filename}: {', '.join(missing)}.")
    if not document["sessionInfo"]:
        raise ValueError(f"Falta sessionInfo no documento {filename}.")
    if not document["INNERTUBE_API_KEY"]:
        raise ValueError(f"Falta INNERTUBE_API_KEY no documento {filename}.")
    return document


def _safe_chunk_size(value: Any) -> int:
    try:
        chunk = max(DEFAULT_CHUNK_SIZE, int(value))
    except (TypeError, ValueError):
        chunk = DEFAULT_CHUNK_SIZE
    chunk -= chunk % DEFAULT_CHUNK_SIZE
    return chunk or DEFAULT_CHUNK_SIZE


def _channel_keys(channel: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    for field in ("id", "youtube_channel_id"):
        value = str(channel.get(field) or "").strip()
        if value and value not in keys:
            keys.append(value)
    return keys


def _normalise_document(raw: Any, account: dict[str, Any]) -> dict[str, Any]:
    raw = raw if isinstance(raw, dict) else {}
    cookies = _normalise_pairs(raw.get("cookies", raw))
    delegated_raw = raw.get("delegated_session_ids", {})
    delegated: dict[str, str] = {}
    if isinstance(delegated_raw, dict):
        for key, value in delegated_raw.items():
            if isinstance(value, dict):
                value = value.get("DELEGATED_SESSION_ID") or value.get("delegated_session_id") or ""
            value = str(value or "").strip()
            if value:
                delegated[str(key)] = value
    return {
        "account_id": str(raw.get("account_id") or account.get("id") or "").strip(),
        "email": str(raw.get("email") or account.get("email") or "").strip(),
        "sessionInfo": str(raw.get("sessionInfo") or raw.get("session_info") or raw.get("direct_session_info") or "").strip(),
        "cookies": {key: cookies.get(key, "") for key in COOKIE_KEYS},
        "INNERTUBE_API_KEY": str(raw.get("INNERTUBE_API_KEY") or raw.get("innertube_api_key") or raw.get("direct_innertube_api_key") or "").strip(),
        "chunk_size": _safe_chunk_size(raw.get("chunk_size", raw.get("direct_chunk_size", DEFAULT_CHUNK_SIZE))),
        "delegated_session_ids": delegated,
    }


def _legacy_document(storage_root: Path, account: dict[str, Any], settings: dict[str, Any] | None, channels: list[dict[str, Any]] | None) -> dict[str, Any]:
    settings = settings or {}
    legacy_cookies = load_cookie_file(storage_root, account)
    if not legacy_cookies:
        legacy_cookies = {
            key: str(settings.get(f"direct_cookie_{key.lower()}") or "").strip()
            for key in COOKIE_KEYS
        }
    delegated: dict[str, str] = {}
    for channel in channels or []:
        if str(channel.get("google_account_id") or "") != str(account.get("id") or ""):
            continue
        delegated_value = str(channel.get("delegated_session_id") or "").strip()
        if delegated_value:
            for key in _channel_keys(channel)[:1]:
                delegated[key] = delegated_value
    return _normalise_document({
        "account_id": account.get("id"),
        "email": account.get("email"),
        "sessionInfo": account.get("direct_session_info") or settings.get("direct_session_info"),
        "cookies": legacy_cookies,
        "INNERTUBE_API_KEY": settings.get("direct_innertube_api_key"),
        "chunk_size": settings.get("direct_chunk_size", DEFAULT_CHUNK_SIZE),
        "delegated_session_ids": delegated,
    }, account)


def save_credentials_document(storage_root: Path, account: dict[str, Any], document: dict[str, Any]) -> Path:
    normalised = _normalise_document(document, account)
    destination = credentials_document_path(storage_root, account)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "account_id": normalised["account_id"],
        "email": normalised["email"],
        "sessionInfo": normalised["sessionInfo"],
        "cookies": normalised["cookies"],
        "INNERTUBE_API_KEY": normalised["INNERTUBE_API_KEY"],
        "chunk_size": normalised["chunk_size"],
        "delegated_session_ids": normalised["delegated_session_ids"],
    }
    temporary = destination.with_name(f".{destination.name}.{secrets.token_hex(6)}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass
    temporary.replace(destination)
    try:
        os.chmod(destination, 0o600)
    except OSError:
        pass
    return destination


def _read_json_document(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def load_credentials_document(storage_root: Path, account: dict[str, Any], settings: dict[str, Any] | None = None, channels: list[dict[str, Any]] | None = None, *, create: bool = True) -> dict[str, Any]:
    path = credentials_document_path(storage_root, account)
    raw = _read_json_document(path) if path.exists() else None
    if raw is None:
        document = _legacy_document(storage_root, account, settings, channels)
        if create:
            save_credentials_document(storage_root, account, document)
        return document
    document = _normalise_document(raw, account)
    changed = False
    for channel in channels or []:
        if str(channel.get("google_account_id") or "") != str(account.get("id") or ""):
            continue
        keys = _channel_keys(channel)
        if keys and keys[0] not in document["delegated_session_ids"]:
            document["delegated_session_ids"][keys[0]] = ""
            changed = True
    if changed and create:
        save_credentials_document(storage_root, account, document)
    return document


def ensure_credentials_document(storage_root: Path, account: dict[str, Any], settings: dict[str, Any] | None = None, channels: list[dict[str, Any]] | None = None) -> Path:
    load_credentials_document(storage_root, account, settings, channels, create=True)
    return credentials_document_path(storage_root, account)


def delegated_session_id(document: dict[str, Any], channel: dict[str, Any]) -> str:
    mapping = document.get("delegated_session_ids", {}) if isinstance(document, dict) else {}
    if not isinstance(mapping, dict):
        return ""
    for key in _channel_keys(channel):
        value = mapping.get(key, "")
        if isinstance(value, dict):
            value = value.get("DELEGATED_SESSION_ID") or value.get("delegated_session_id") or ""
        if str(value or "").strip():
            return str(value).strip()
    return ""


def document_status(storage_root: Path, account: dict[str, Any], channel: dict[str, Any] | None = None, settings: dict[str, Any] | None = None, channels: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    path = credentials_document_path(storage_root, account)
    document = load_credentials_document(storage_root, account, settings, channels, create=True)
    missing_cookies = [key for key in COOKIE_KEYS if not document["cookies"].get(key)]
    delegated = delegated_session_id(document, channel or {}) if channel else ""
    return {
        "document_file": str(path),
        "document_exists": path.exists(),
        "missing_cookies": missing_cookies,
        "has_session_info": bool(document.get("sessionInfo")),
        "has_innertube_api_key": bool(document.get("INNERTUBE_API_KEY")),
        "has_delegated_session_id": bool(delegated) if channel is not None else None,
        "ready": not missing_cookies and bool(document.get("sessionInfo")) and bool(document.get("INNERTUBE_API_KEY")) and (channel is None or bool(delegated)),
    }


def load_cookie_file(storage_root: Path, account: dict[str, Any]) -> dict[str, str]:
    """Load cookies from the legacy cookies.json file for migration only."""
    path = cookie_file_path(storage_root, account)
    if not path.exists():
        return {}
    raw = _read_json_document(path)
    return _normalise_pairs(raw or {})


def save_cookie_file(storage_root: Path, account: dict[str, Any], content: bytes, filename: str = "cookies.json") -> Path:
    """Legacy helper retained for migration tests; new writes must use credentials.json."""
    cookies = parse_cookie_file(content, filename)
    destination = cookie_file_path(storage_root, account)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{secrets.token_hex(6)}.tmp")
    temporary.write_text(json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass
    temporary.replace(destination)
    try:
        os.chmod(destination, 0o600)
    except OSError:
        pass
    return destination


def direct_account_status(storage_root: Path, account: dict[str, Any]) -> dict[str, Any]:
    """Backward-compatible account status; the source of truth is credentials.json."""
    status = document_status(storage_root, account)
    return {
        "cookie_file": status["document_file"],
        "document_exists": status["document_exists"],
        "cookie_file_exists": status["document_exists"],
        "missing_cookies": status["missing_cookies"],
        "has_session_info": status["has_session_info"],
        "has_innertube_api_key": status["has_innertube_api_key"],
        "ready": status["ready"],
        "document_file": status["document_file"],
    }
