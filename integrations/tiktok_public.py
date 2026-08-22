import json
import re
from datetime import datetime, timezone
from html import unescape
from hashlib import sha256
from typing import Any
from urllib.parse import urlparse

import requests

from integrations.platforms import IntegrationResult


TIKTOK_PUBLIC_HOSTS = {"tiktok.com", "www.tiktok.com", "m.tiktok.com"}
TIKTOK_PUBLIC_URL = "https://www.tiktok.com"
PUBLIC_USER_AGENT = "Thunderbolt/0.2 TikTok public profile lookup; manual user initiated request"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, dict):
        for key in ("text", "content", "simpleText", "name", "title", "value"):
            text = _text(value.get(key))
            if text:
                return text
    return ""


def _first(value: Any, keys: set[str]) -> Any:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in keys and child not in (None, "", [], {}):
                return child
        for child in value.values():
            found = _first(child, keys)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _first(child, keys)
            if found is not None:
                return found
    return None


def _number(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = _text(value).lower().replace(" ", "")
    match = re.search(r"([0-9][0-9.,]*)(k|m|b|mil|milhões|mi|bi)?", text)
    if not match:
        return None
    raw = match.group(1)
    suffix = match.group(2) or ""
    try:
        if suffix in {"k", "mil"}:
            return int(float(raw.replace(",", ".")) * 1_000)
        if suffix in {"m", "mi", "milhões"}:
            return int(float(raw.replace(",", ".")) * 1_000_000)
        if suffix in {"b", "bi"}:
            return int(float(raw.replace(",", ".")) * 1_000_000_000)
        return int(re.sub(r"[^0-9]", "", raw))
    except ValueError:
        return None


def _meta(document: str, *names: str) -> str:
    for name in names:
        patterns = (
            rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']*)["\']',
            rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:name|property)=["\']{re.escape(name)}["\']',
        )
        for pattern in patterns:
            match = re.search(pattern, document, flags=re.IGNORECASE)
            if match:
                return unescape(match.group(1)).strip()
    return ""


def _json_scripts(document: str) -> list[Any]:
    values: list[Any] = []
    for match in re.finditer(r"<script[^>]*>(.*?)</script>", document, flags=re.IGNORECASE | re.DOTALL):
        body = match.group(1).strip()
        if not body or not (body.startswith("{") or body.startswith("[")):
            continue
        try:
            values.append(json.loads(unescape(body)))
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
    return values


def _username_from_reference(source: str) -> str:
    value = str(source or "").strip()
    if not value:
        return ""
    if not value.startswith(("http://", "https://")):
        value = value if value.startswith("@") else f"@{value}"
        return value[1:].strip("/ ")
    parsed = urlparse(value)
    for part in parsed.path.split("/"):
        if part.startswith("@") and len(part) > 1:
            return part[1:].strip()
    return ""


def normalize_tiktok_reference(source: str) -> dict[str, str]:
    value = str(source or "").strip()
    if not value:
        raise ValueError("Informe um @handle ou URL pública do TikTok.")
    if value.startswith("@"):
        username = value[1:].strip()
    elif value.startswith(("http://", "https://")):
        parsed = urlparse(value)
        if parsed.netloc.lower().split(":", 1)[0] not in TIKTOK_PUBLIC_HOSTS:
            raise ValueError("Use uma URL pública do TikTok, por exemplo https://www.tiktok.com/@conta.")
        username = _username_from_reference(value)
    else:
        username = value
    username = username.strip().lstrip("@").split("/", 1)[0]
    if not re.fullmatch(r"[A-Za-z0-9._-]{2,64}", username):
        raise ValueError("O @handle TikTok deve conter apenas letras, números, ponto, sublinhado ou hífen.")
    handle = f"@{username}"
    url = f"{TIKTOK_PUBLIC_URL}/{handle}"
    return {
        "id": f"tiktok_{sha256(url.encode('utf-8')).hexdigest()[:20]}",
        "username": username,
        "handle": handle,
        "url": url,
    }


def _canonical_profile_data(source: str, document: str) -> dict[str, Any]:
    reference = normalize_tiktok_reference(source)
    title = _meta(document, "og:title", "twitter:title")
    description = _meta(document, "og:description", "description", "twitter:description")
    avatar_url = _meta(document, "og:image", "twitter:image")
    canonical_url = _meta(document, "og:url") or reference["url"]
    scripts = _json_scripts(document)
    for payload in scripts:
        candidate = payload
        if isinstance(payload, dict) and payload.get("@type") in {"Person", "ProfilePage"}:
            display_name = _text(payload.get("name"))
            description = description or _text(payload.get("description"))
            avatar_url = avatar_url or _text(payload.get("image"))
            canonical_url = _text(payload.get("url")) or canonical_url
            if display_name:
                title = display_name
        username = _first(candidate, {"uniqueId", "unique_id", "username"})
        display_name = _first(candidate, {"nickname", "displayName", "display_name"})
        bio = _first(candidate, {"signature", "bio", "bioDescription", "bio_description"})
        avatar = _first(candidate, {"avatarLarger", "avatarMedium", "avatar_url", "avatarUrl"})
        if username:
            reference["username"] = _text(username).lstrip("@").strip() or reference["username"]
            reference["handle"] = f"@{reference['username']}"
            reference["url"] = f"{TIKTOK_PUBLIC_URL}/{reference['handle']}"
        if display_name and not title:
            title = _text(display_name)
        if bio and not description:
            description = _text(bio)
        if avatar and not avatar_url:
            avatar_url = _text(avatar)

    title = re.sub(r"\s*[|·—-]\s*TikTok\s*$", "", title, flags=re.IGNORECASE).strip()
    if title and "(" in title:
        title = title.split("(", 1)[0].strip()
    if title.startswith("@"):
        title = ""
    follower_count = None
    following_count = None
    likes_count = None
    video_count = None
    for payload in scripts:
        follower_count = follower_count or _number(_first(payload, {"followerCount", "followers", "follower_count"}))
        following_count = following_count or _number(_first(payload, {"followingCount", "following", "following_count"}))
        likes_count = likes_count or _number(_first(payload, {"heartCount", "likes", "likeCount", "likes_count"}))
        video_count = video_count or _number(_first(payload, {"videoCount", "video_count"}))

    return {
        **reference,
        "name": title or reference["username"],
        "bio": description,
        "avatar_url": avatar_url,
        "subscriber_count": follower_count,
        "following_count": following_count,
        "likes_count": likes_count,
        "video_count": video_count,
        "public_url": canonical_url if "tiktok.com" in canonical_url else reference["url"],
        "public_lookup": True,
        "metrics_source": "tiktok_public_page",
        "last_public_lookup_at": _now_iso(),
    }


def fetch_public_tiktok_profile(source: str) -> IntegrationResult:
    try:
        reference = normalize_tiktok_reference(source)
    except ValueError as exc:
        return IntegrationResult(False, str(exc), {})
    headers = {
        "User-Agent": PUBLIC_USER_AGENT,
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    }
    try:
        response = requests.get(reference["url"], headers=headers, timeout=12, allow_redirects=True)
    except requests.RequestException as exc:
        return IntegrationResult(False, f"Não foi possível consultar o perfil público do TikTok: {exc}", reference)
    if response.status_code in {401, 403, 429}:
        return IntegrationResult(False, "O TikTok bloqueou ou limitou a pesquisa pública. Use o cadastro manual com o @handle e a URL.", reference | {"status_code": response.status_code})
    if response.status_code >= 400:
        return IntegrationResult(False, f"O perfil público do TikTok devolveu HTTP {response.status_code}. Confirme o @handle ou use o cadastro manual.", reference | {"status_code": response.status_code})
    data = _canonical_profile_data(source, response.text)
    recognized = bool(data.get("name") or data.get("bio") or data.get("avatar_url") or any(data.get(key) is not None for key in ("subscriber_count", "video_count", "likes_count")))
    if not recognized:
        return IntegrationResult(False, "A página pública não expôs dados estruturados reconhecíveis. Pode cadastrar a conta manualmente.", data)
    return IntegrationResult(True, "Perfil TikTok encontrado publicamente. Reveja os dados antes de cadastrar.", data)


__all__ = ["PUBLIC_USER_AGENT", "fetch_public_tiktok_profile", "normalize_tiktok_reference"]
