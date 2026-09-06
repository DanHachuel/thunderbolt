from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from typing import Any
from urllib.parse import urlparse

import requests


@dataclass
class IntegrationResult:
    ok: bool
    message: str
    data: dict[str, Any]


def normalize_instagram_reference(source: str) -> dict[str, str]:
    value = str(source or '').strip()
    if not value:
        raise ValueError('Informe um @handle ou URL pública do Instagram.')
    if value.startswith('@'):
        username = value[1:]
    elif value.startswith(('http://', 'https://')):
        parsed = urlparse(value)
        if (parsed.hostname or '').lower().removeprefix('www.') != 'instagram.com':
            raise ValueError('Use uma URL pública do Instagram, por exemplo https://www.instagram.com/conta/.')
        username = next((part for part in parsed.path.split('/') if part and not part.startswith(('p', 'reel', 'tv'))), '')
    else:
        username = value
    username = username.strip().lstrip('@').split('/', 1)[0]
    if not re.fullmatch(r'[A-Za-z0-9._]{1,64}', username):
        raise ValueError('O @handle Instagram contém caracteres inválidos.')
    return {'username': username, 'handle': f'@{username}', 'url': f'https://www.instagram.com/{username}/'}


def _meta(document: str, name: str) -> str:
    patterns = (
        rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']*)',
        rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:name|property)=["\']{re.escape(name)}["\']',
    )
    for pattern in patterns:
        match = re.search(pattern, document, flags=re.IGNORECASE)
        if match:
            return unescape(match.group(1)).strip()
    return ''


def fetch_public_instagram_profile(source: str) -> IntegrationResult:
    try:
        reference = normalize_instagram_reference(source)
    except ValueError as exc:
        return IntegrationResult(False, str(exc), {})
    try:
        response = requests.get(reference['url'], headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'}, timeout=12)
    except requests.RequestException as exc:
        return IntegrationResult(False, f'Não foi possível consultar o perfil público do Instagram: {exc}', reference)
    if response.status_code >= 400:
        return IntegrationResult(False, f'O Instagram devolveu HTTP {response.status_code}. Confirme o @handle ou use o cadastro manual.', reference | {'status_code': response.status_code})
    title = _meta(response.text, 'og:title') or reference['username']
    description = _meta(response.text, 'og:description')
    avatar_url = _meta(response.text, 'og:image')
    def metric(patterns: tuple[str, ...]) -> int | None:
        for pattern in patterns:
            found = re.search(pattern, description, flags=re.IGNORECASE)
            if not found:
                continue
            try:
                return int(re.sub(r'[^0-9]', '', found.group(1)))
            except ValueError:
                continue
        return None

    followers = metric((r'([\d,.]+)\s*(?:mil\s+)?(?:followers|seguidores)',))
    following = metric((r'([\d,.]+)\s*(?:mil\s+)?(?:following|seguindo)',))
    posts = metric((r'([\d,.]+)\s*(?:mil\s+)?(?:posts|publicações|publications)',))
    data = {'id': f"instagram_{reference['username']}", **reference, 'name': title.split('(')[0].strip() or reference['username'], 'bio': description, 'avatar_url': avatar_url, 'subscriber_count': followers, 'following_count': following, 'post_count': posts, 'public_lookup': True, 'metrics_source': 'instagram_public_page', 'last_public_lookup_at': datetime.now(timezone.utc).isoformat()}
    return IntegrationResult(True, 'Perfil Instagram encontrado publicamente.', data)


__all__ = ['IntegrationResult', 'fetch_public_instagram_profile', 'normalize_instagram_reference']
