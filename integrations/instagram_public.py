from __future__ import annotations

import re
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from typing import Any, Mapping
from urllib.parse import urlparse

import requests


@dataclass
class IntegrationResult:
    ok: bool
    message: str
    data: dict[str, Any]


def normalize_instagram_bio(value: Any) -> str:
    """Keep the profile biography, never Instagram's metrics summary."""
    bio = str(value or '').strip()
    if not bio:
        return ''
    if re.search(r'\b(?:followers|following|seguidores|seguindo|posts|publicações)\b', bio, flags=re.IGNORECASE) and re.search(r'\d', bio):
        return ''
    return bio


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


def _structured_metric(document: str, *keys: str) -> int | None:
    """Read numeric Instagram counters embedded in the public HTML payload."""
    document = unescape(document)
    for key in keys:
        patterns = (
            rf'\\?["\']{re.escape(key)}\\?["\']\s*:\s*\{{[^}}]{{0,240}}?\\?["\']count\\?["\']\s*:\s*(\d+)',
            rf'\\?["\']{re.escape(key)}\\?["\']\s*:\s*(\d+)',
        )
        for pattern in patterns:
            found = re.search(pattern, document, flags=re.IGNORECASE)
            if found:
                try:
                    return int(found.group(1))
                except ValueError:
                    continue
    return None


def _structured_metric_from_json(document: str, *keys: str) -> int | None:
    wanted = {key.casefold() for key in keys}
    for parsed in _embedded_json_documents(document):
        for node in _walk_json(parsed):
            if not isinstance(node, dict):
                continue
            for key, value in node.items():
                if str(key).casefold() not in wanted:
                    continue
                if isinstance(value, dict):
                    value = value.get('count') or value.get('value')
                try:
                    return int(value)
                except (TypeError, ValueError):
                    continue
    return None


def _fetch_web_profile_user(username: str) -> dict[str, Any] | None:
    headers = {
        'x-ig-app-id': '936619743392459',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    # The www host is the current public web endpoint. The legacy i host is
    # retained as a fallback because Instagram rate-limits the two hosts
    # independently and their availability can vary by region.
    endpoints = (
        f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}',
        f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}',
    )
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, headers=headers, timeout=15)
            if response.status_code >= 400:
                continue
            payload = response.json()
        except (requests.RequestException, ValueError, AttributeError):
            continue
        user = ((payload.get('data') or {}).get('user') if isinstance(payload, dict) else None)
        if isinstance(user, dict):
            return user
    curl = shutil.which('curl')
    if curl:
        try:
            completed = subprocess.run(
                [curl, '-L', '--max-time', '20', '-sS', '-A', headers['User-Agent'], '-H', f"x-ig-app-id: {headers['x-ig-app-id']}", endpoint],
                capture_output=True,
                text=True,
                timeout=25,
                check=False,
            )
            payload = json.loads(completed.stdout) if completed.returncode == 0 and completed.stdout else None
            user = ((payload.get('data') or {}).get('user') if isinstance(payload, dict) else None)
            if isinstance(user, dict):
                return user
        except (OSError, subprocess.SubprocessError, ValueError):
            pass
    return None


def _profile_data_from_api(user: Mapping[str, Any], reference: Mapping[str, str]) -> dict[str, Any]:
    followers = _profile_metric(user, 'edge_followed_by', 'followers', 'follower_count', 'followerCount')
    following = _profile_metric(user, 'edge_follow', 'follows', 'following', 'following_count', 'followingCount')
    followers = followers if followers is not None else _structured_metric_from_json(json.dumps(user), 'edge_followed_by', 'followers', 'follower_count', 'followerCount')
    following = following if following is not None else _structured_metric_from_json(json.dumps(user), 'edge_follow', 'follows', 'following', 'following_count', 'followingCount')
    media = ((user.get('edge_owner_to_timeline_media') or {}).get('count') if isinstance(user.get('edge_owner_to_timeline_media'), dict) else None)
    return {
        'id': f"instagram_{reference['username']}",
        **reference,
        'name': str(user.get('full_name') or user.get('username') or reference['username']).strip(),
        'bio': normalize_instagram_bio(user.get('biography')),
        'avatar_url': str(user.get('profile_pic_url_hd') or user.get('profile_pic_url') or '').strip(),
        'subscriber_count': followers,
        'following_count': following,
        'post_count': media,
        'is_private': bool(user.get('is_private')),
        'public_lookup': True,
        'metrics_source': 'instagram_web_profile_info',
        'last_public_lookup_at': datetime.now(timezone.utc).isoformat(),
        '_api_posts': (((user.get('edge_owner_to_timeline_media') or {}).get('edges') or []) if isinstance(user.get('edge_owner_to_timeline_media'), dict) else []),
    }


def normalize_instagram_metric(value: Any) -> int | None:
    """Normalize an Instagram counter without turning an unknown value into zero."""
    if isinstance(value, Mapping):
        value = value.get('count') or value.get('value')
    if value in (None, ''):
        return None
    digits = re.sub(r'[^0-9]', '', str(value))
    return int(digits) if digits else None


def _profile_metric(user: Mapping[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = normalize_instagram_metric(user.get(key))
        if value is not None:
            return value
    return None


def fetch_public_instagram_profile(source: str) -> IntegrationResult:
    try:
        reference = normalize_instagram_reference(source)
    except ValueError as exc:
        return IntegrationResult(False, str(exc), {})
    api_user = _fetch_web_profile_user(reference['username'])
    if api_user:
        return IntegrationResult(True, 'Perfil Instagram encontrado publicamente.', _profile_data_from_api(api_user, reference))
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

    followers = metric((r'([\d,.]+)\s*(?:mil\s+)?(?:followers|seguidores)',)) or _structured_metric(response.text, 'edge_followed_by', 'followers', 'follower_count') or _structured_metric_from_json(response.text, 'edge_followed_by', 'followers', 'follower_count', 'followerCount')
    following = metric((r'([\d,.]+)\s*(?:mil\s+)?(?:following|seguindo)',)) or _structured_metric(response.text, 'edge_follow', 'follows', 'following', 'following_count', 'followingCount') or _structured_metric_from_json(response.text, 'edge_follow', 'follows', 'following', 'following_count', 'followingCount')
    posts = metric((r'([\d,.]+)\s*(?:mil\s+)?(?:posts|publicações|publications)',)) or _structured_metric(response.text, 'edge_owner_to_timeline_media', 'posts', 'post_count')
    data = {'id': f"instagram_{reference['username']}", **reference, 'name': title.split('(')[0].strip() or reference['username'], 'bio': normalize_instagram_bio(description), 'avatar_url': avatar_url, 'subscriber_count': followers, 'following_count': following, 'post_count': posts, 'public_lookup': True, 'metrics_source': 'instagram_public_page', 'last_public_lookup_at': datetime.now(timezone.utc).isoformat()}
    return IntegrationResult(True, 'Perfil Instagram encontrado publicamente.', data)


def _walk_json(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _embedded_json_documents(document: str) -> list[Any]:
    decoder = json.JSONDecoder()
    documents: list[Any] = []
    for script in re.findall(r'<script[^>]*>(.*?)</script>', document, flags=re.IGNORECASE | re.DOTALL):
        candidate = script.strip()
        if not candidate:
            continue
        for start in [0] + [match.start() for match in re.finditer(r'[\[{]', candidate)][:20]:
            try:
                parsed, _ = decoder.raw_decode(candidate[start:])
            except (json.JSONDecodeError, TypeError):
                continue
            documents.append(parsed)
            break
    return documents


def _post_from_node(node: dict[str, Any]) -> dict[str, Any] | None:
    shortcode = str(node.get('shortcode') or node.get('code') or '').strip()
    media_id = str(node.get('id') or '').strip()
    image_url = str(node.get('display_url') or node.get('thumbnail_src') or node.get('image') or '').strip()
    if not shortcode and not media_id:
        return None
    if not image_url and not node.get('is_video'):
        return None
    caption_value = node.get('caption') or node.get('title') or ''
    if isinstance(caption_value, dict):
        caption_value = caption_value.get('text') or ''
    edges = node.get('edge_media_to_caption')
    if isinstance(edges, dict):
        edge_list = edges.get('edges') or []
        if edge_list and isinstance(edge_list[0], dict):
            caption_value = ((edge_list[0].get('node') or {}).get('text') or caption_value)
    url = str(node.get('permalink') or node.get('url') or '').strip()
    if not url and shortcode:
        url = f'https://www.instagram.com/p/{shortcode}/'
    return {
        'id': media_id or shortcode,
        'shortcode': shortcode,
        'url': url,
        'image_url': image_url,
        'caption': str(caption_value or '').strip(),
        'published_at': node.get('taken_at_timestamp') or node.get('taken_at') or '',
        'is_video': bool(node.get('is_video') or node.get('video_url')),
    }


def fetch_public_instagram_posts(source: str, limit: int = 10) -> IntegrationResult:
    try:
        reference = normalize_instagram_reference(source)
    except ValueError as exc:
        return IntegrationResult(False, str(exc), {})
    api_user = _fetch_web_profile_user(reference['username'])
    if api_user:
        api_posts: list[dict[str, Any]] = []
        for edge in ((api_user.get('edge_owner_to_timeline_media') or {}).get('edges') or []):
            node = edge.get('node') if isinstance(edge, dict) else None
            if isinstance(node, dict):
                post = _post_from_node(node)
                if post:
                    api_posts.append(post)
        if api_posts:
            return IntegrationResult(True, 'Posts públicos encontrados.', reference | {'posts': api_posts[:max(1, int(limit))]})
        if api_user.get('is_private'):
            return IntegrationResult(False, 'Esta conta é privada. O Instagram não disponibiliza posts sem uma sessão autenticada.', reference | {'posts': [], 'is_private': True})
    try:
        response = requests.get(reference['url'], headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'}, timeout=15)
    except requests.RequestException as exc:
        return IntegrationResult(False, f'Não foi possível consultar os posts públicos do Instagram: {exc}', reference)
    if response.status_code >= 400:
        return IntegrationResult(False, f'O Instagram devolveu HTTP {response.status_code} ao consultar os posts.', reference | {'status_code': response.status_code})
    posts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for document in _embedded_json_documents(response.text):
        for node in _walk_json(document):
            post = _post_from_node(node)
            if not post or post['id'] in seen:
                continue
            seen.add(post['id'])
            posts.append(post)
            if len(posts) >= max(1, int(limit)):
                break
        if len(posts) >= max(1, int(limit)):
            break
    return IntegrationResult(bool(posts), 'Posts públicos encontrados.' if posts else 'Não foi possível encontrar posts públicos nesta página do Instagram.', reference | {'posts': posts[:max(1, int(limit))]})


__all__ = ['IntegrationResult', 'fetch_public_instagram_posts', 'fetch_public_instagram_profile', 'normalize_instagram_bio', 'normalize_instagram_metric', 'normalize_instagram_reference']
