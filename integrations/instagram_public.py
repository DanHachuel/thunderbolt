from __future__ import annotations

import re
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from typing import Any, Mapping
from urllib.parse import urlparse

import requests


ABOUT_ACCOUNT_URL = 'https://i.instagram.com/api/v1/bloks/apps/com.instagram.interactions.about_this_account/'
ABOUT_ACCOUNT_BLOKS_VERSION = '8ca96ca267e30c02cf90888d91eeff09627f0e3fd2bd9df472278c9a6c022cbb'


def _instagram_cookies() -> dict[str, str]:
    cookies = {}
    sessionid = os.getenv('INSTAGRAM_SESSIONID') or os.getenv('IG_SESSIONID')
    if sessionid:
        cookies['sessionid'] = sessionid.strip()
    for name in ('csrftoken', 'ds_user_id', 'mid', 'ig_did'):
        value = os.getenv(f'INSTAGRAM_{name.upper()}') or os.getenv(f'IG_{name.upper()}')
        if value:
            cookies[name] = value.strip()
    return cookies


def _instagram_headers() -> dict[str, str]:
    return {
        'x-ig-app-id': '936619743392459',
        'User-Agent': 'Instagram 390.0.0.0.50 Android',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }


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
    metric_words = r'followers|following|seguidores|seguindo|posts|publicações|publications'
    metric_hits = re.findall(
        rf'(?:\d[\d.,]*\s*(?:{metric_words})\b|\b(?:{metric_words})\s*\d[\d.,]*)',
        bio,
        flags=re.IGNORECASE,
    )
    if len(metric_hits) >= 2:
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
    headers = _instagram_headers()
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36'
    # The www host is the current public web endpoint. The legacy i host is
    # retained as a fallback because Instagram rate-limits the two hosts
    # independently and their availability can vary by region.
    endpoints = (
        f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}',
        f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}',
    )
    curl = shutil.which('curl')
    if curl:
        for endpoint in endpoints:
            try:
                completed = subprocess.run(
                    [curl, '-L', '--max-time', '20', '-sS', '-A', headers['User-Agent'], '-H', f"x-ig-app-id: {headers['x-ig-app-id']}", '-H', 'Accept: application/json, text/plain, */*', endpoint],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=25,
                    check=False,
                )
                payload = json.loads(completed.stdout) if completed.returncode == 0 and completed.stdout else None
                user = ((payload.get('data') or {}).get('user') if isinstance(payload, dict) else None)
                if isinstance(user, dict):
                    return user
            except (OSError, subprocess.SubprocessError, ValueError):
                continue
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
    return None


def _country_from_bloks(value: Any) -> str:
    if isinstance(value, Mapping):
        data_key = str(value.get('key') or '').casefold()
        if data_key in PUBLIC_COUNTRY_KEYS:
            serialized = value.get('initial_lispy') or value.get('value')
            if isinstance(serialized, str) and 'bk.action.array.Make' in serialized:
                country = _country_value(serialized.rsplit('bk.action.array.Make,', 1)[-1].split(')', 1)[0].replace('\\"', '"').replace('"', '').strip())
            else:
                country = _country_value(serialized)
            if country:
                return country
        for key, candidate in value.items():
            if str(key).casefold() in PUBLIC_COUNTRY_KEYS:
                if isinstance(candidate, str) and 'bk.action.array.Make' in candidate:
                    country = _country_value(candidate.rsplit('bk.action.array.Make,', 1)[-1].split(')', 1)[0].replace('\\"', '"').replace('"', '').strip())
                else:
                    country = _country_value(candidate)
                if country:
                    return country
            country = _country_from_bloks(candidate)
            if country:
                return country
    elif isinstance(value, list):
        for candidate in value:
            country = _country_from_bloks(candidate)
            if country:
                return country
    elif isinstance(value, str) and 'about_this_account_country' in value:
        marker = 'bk.action.array.Make,'
        if marker in value:
            country = value.rsplit(marker, 1)[-1].split(')', 1)[0].replace('\\"', '"').replace('"', '').strip()
            return _country_value(country)
    return ''


def _fetch_instagram_about_country(user_id: Any) -> str:
    cookies = _instagram_cookies()
    if not cookies or not str(user_id or '').strip():
        return ''
    payload = {
        'referer_type': 'ProfileUsername',
        'target_user_id': str(user_id),
        'bk_client_context': json.dumps({'bloks_version': ABOUT_ACCOUNT_BLOKS_VERSION, 'style_id': 'instagram'}, separators=(',', ':')),
        'bloks_versioning_id': ABOUT_ACCOUNT_BLOKS_VERSION,
    }
    try:
        response = requests.post(ABOUT_ACCOUNT_URL, data=payload, headers=_instagram_headers(), cookies=cookies, timeout=20)
        if response.status_code >= 400:
            return ''
        return _country_from_bloks(response.json())
    except (requests.RequestException, ValueError, TypeError):
        return ''


def _profile_data_from_api(user: Mapping[str, Any], reference: Mapping[str, str]) -> dict[str, Any]:
    followers = _profile_metric(user, 'edge_followed_by', 'followers', 'follower_count', 'followerCount')
    following = _profile_metric(user, 'edge_follow', 'follows', 'following', 'following_count', 'followingCount')
    followers = followers if followers is not None else _structured_metric_from_json(json.dumps(user), 'edge_followed_by', 'followers', 'follower_count', 'followerCount')
    following = following if following is not None else _structured_metric_from_json(json.dumps(user), 'edge_follow', 'follows', 'following', 'following_count', 'followingCount')
    media = ((user.get('edge_owner_to_timeline_media') or {}).get('count') if isinstance(user.get('edge_owner_to_timeline_media'), dict) else None)
    biography = str(user.get('biography') or '').strip()
    country = extract_public_instagram_country(user) or _fetch_instagram_about_country(user.get('id') or user.get('pk'))
    return {
        'id': f"instagram_{reference['username']}",
        **reference,
        'name': str(user.get('full_name') or user.get('username') or reference['username']).strip(),
        'bio': normalize_instagram_bio(biography),
        'bio_raw': biography,
        'country': country,
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


PUBLIC_COUNTRY_KEYS = {
    'about_this_account_country', 'account_based_in', 'account_country', 'country_name',
    'country_of_origin', 'country_of_registration', 'location_country', 'transparency_country',
}
PUBLIC_TRANSPARENCY_KEYS = {'about', 'about_account', 'account_transparency', 'transparency', 'account_info'}


def _country_value(value: Any) -> str:
    if isinstance(value, Mapping):
        for key in ('name', 'label', 'display_name', 'country', 'country_name', 'code'):
            candidate = str(value.get(key) or '').strip()
            if candidate and not candidate.isdigit() and len(candidate) <= 80:
                return candidate
        return ''
    candidate = str(value or '').strip()
    return candidate if candidate and not candidate.isdigit() and len(candidate) <= 80 else ''


def extract_public_instagram_country(value: Any) -> str:
    """Read only the account-country field exposed by Instagram transparency data."""
    if isinstance(value, Mapping):
        for key, candidate in value.items():
            if str(key).casefold() in PUBLIC_COUNTRY_KEYS:
                country = _country_value(candidate)
                if country:
                    return country
        for key, candidate in value.items():
            if str(key).casefold() in PUBLIC_TRANSPARENCY_KEYS:
                country = extract_public_instagram_country(candidate)
                if country:
                    return country
    elif isinstance(value, list):
        for candidate in value:
            country = extract_public_instagram_country(candidate)
            if country:
                return country
    return ''


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
    embedded_country = ''
    for document in _embedded_json_documents(response.text):
        embedded_country = extract_public_instagram_country(document)
        if embedded_country:
            break
    data = {'id': f"instagram_{reference['username']}", **reference, 'name': title.split('(')[0].strip() or reference['username'], 'bio': normalize_instagram_bio(description), 'bio_raw': description, 'country': embedded_country, 'avatar_url': avatar_url, 'subscriber_count': followers, 'following_count': following, 'post_count': posts, 'public_lookup': True, 'metrics_source': 'instagram_public_page', 'last_public_lookup_at': datetime.now(timezone.utc).isoformat()}
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


__all__ = ['IntegrationResult', 'extract_public_instagram_country', 'fetch_public_instagram_posts', 'fetch_public_instagram_profile', 'normalize_instagram_bio', 'normalize_instagram_metric', 'normalize_instagram_reference']
