from __future__ import annotations

import json
import os
import re
import secrets
from pathlib import Path
from typing import Any

COOKIE_KEYS = ("SID", "SSID", "HSID", "APISID", "SAPISID")


def account_key(account: dict[str, Any]) -> str:
    raw = str(account.get("id") or "").strip()
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip(".-")
    return safe[:80] or "google-account"


def account_directory(storage_root: Path, account: dict[str, Any]) -> Path:
    return Path(storage_root) / "youtube_direct_accounts" / account_key(account)


def cookie_file_path(storage_root: Path, account: dict[str, Any]) -> Path:
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


def save_cookie_file(storage_root: Path, account: dict[str, Any], content: bytes, filename: str = "cookies.json") -> Path:
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


def load_cookie_file(storage_root: Path, account: dict[str, Any]) -> dict[str, str]:
    path = cookie_file_path(storage_root, account)
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return _normalise_pairs(raw)


def direct_account_status(storage_root: Path, account: dict[str, Any]) -> dict[str, Any]:
    cookies = load_cookie_file(storage_root, account)
    missing = [key for key in COOKIE_KEYS if not cookies.get(key)]
    session_info = str(account.get("direct_session_info") or "").strip()
    return {
        "cookie_file": str(cookie_file_path(storage_root, account)),
        "cookie_file_exists": cookie_file_path(storage_root, account).exists(),
        "missing_cookies": missing,
        "has_session_info": bool(session_info),
        "ready": not missing and bool(session_info),
    }
