from __future__ import annotations

import re
import json
import logging
import os
import platform
import sys
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

import requests

try:
    import streamlit as st
except ImportError:  # pragma: no cover - Streamlit is a runtime dependency
    st = None


LOGGER = logging.getLogger(__name__)
_WINDOWS_PLAYWRIGHT_CHECKED = False


ABOUT_ACCOUNT_URL = 'https://i.instagram.com/api/v1/bloks/apps/com.instagram.interactions.about_this_account/'
ABOUT_ACCOUNT_BLOKS_VERSION = '8ca96ca267e30c02cf90888d91eeff09627f0e3fd2bd9df472278c9a6c022cbb'


def _load_dotenv_compat() -> None:
    """Load .env when python-dotenv exists, otherwise parse simple KEY=VALUE lines."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        return
    except ImportError:
        LOGGER.debug('python-dotenv não está instalado; será usado o parser .env compatível.')
    env_path = Path(__file__).resolve().parents[1] / '.env'
    if not env_path.is_file():
        return
    try:
        for raw_line in env_path.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key.strip(), value)
    except OSError as exc:
        LOGGER.warning('Não foi possível ler %s: %s', env_path, exc)


def _streamlit_message(level: str, message: str, key: str) -> None:
    """Show a runtime diagnostic once when Streamlit is available."""
    if st is None:
        return
    try:
        shown_key = f'_instagram_debug_{key}'
        if st.session_state.get(shown_key):
            return
        st.session_state[shown_key] = True
        getattr(st, level)(message)
    except Exception as exc:  # Streamlit may be imported outside an active app context.
        LOGGER.debug('Não foi possível mostrar diagnóstico Streamlit: %s', exc)


def _ensure_windows_playwright() -> None:
    """Ensure Chromium exists on Windows before using the Playwright fallback."""
    global _WINDOWS_PLAYWRIGHT_CHECKED
    if os.name != 'nt' or _WINDOWS_PLAYWRIGHT_CHECKED:
        return
    _WINDOWS_PLAYWRIGHT_CHECKED = True
    _load_dotenv_compat()
    try:
        completed = subprocess.run(
            [sys.executable, '-m', 'playwright', 'install', 'chromium'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=180,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or 'sem detalhes').strip()[-1000:]
            message = f'Não foi possível instalar o Chromium do Playwright no Windows: {detail}'
            LOGGER.warning(message)
            _streamlit_message('error', message + ' Execute: python -m playwright install chromium', 'playwright_install_error')
        else:
            LOGGER.info('Chromium do Playwright verificado/instalado no Windows.')
    except (OSError, subprocess.SubprocessError) as exc:
        message = f'Falha ao executar a instalação do Chromium no Windows: {exc}'
        LOGGER.warning(message)
        _streamlit_message('error', message + ' Execute: python -m playwright install chromium', 'playwright_install_exception')


_load_dotenv_compat()
if os.name == 'nt':
    _ensure_windows_playwright()


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


def _instagram_playwright_headless() -> bool:
    """Use headless mode by default; set INSTAGRAM_PLAYWRIGHT_HEADLESS=false for debug."""
    value = os.getenv('INSTAGRAM_PLAYWRIGHT_HEADLESS', 'true').strip().casefold()
    return value not in {'0', 'false', 'no', 'off'}


def _save_instagram_debug_html(username: str, document: str) -> None:
    storage_dir = Path(__file__).resolve().parents[1] / 'storage'
    path = Path(os.getenv('INSTAGRAM_DEBUG_PROFILE_HTML', str(storage_dir / 'debug_instagram.html')))
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(document, encoding='utf-8')
        LOGGER.info('HTML salvo em %s', path)
    except OSError as exc:
        LOGGER.warning('Não foi possível salvar o HTML de diagnóstico Instagram: %s', exc)


@dataclass
class IntegrationResult:
    ok: bool
    message: str
    data: dict[str, Any]


def normalize_instagram_bio(value: Any) -> str:
    """Keep the complete public biography exactly as returned by Instagram."""
    bio = str(value or '').strip()
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


def _profile_quality(user: Mapping[str, Any]) -> int:
    groups = (
        ('biography', 'bio', 'description'),
        ('edge_follow', 'following', 'following_count', 'followingCount', 'follows'),
        ('edge_followed_by', 'followers', 'follower_count', 'followers_count', 'followerCount'),
        ('edge_owner_to_timeline_media', 'posts', 'post_count', 'media_count'),
        ('username', 'user_name', 'handle'),
    )
    return sum(any(user.get(key) not in (None, '', {}, []) for key in group) for group in groups)


def _merge_profile(base: dict[str, Any] | None, candidate: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(base or {})
    for key, value in candidate.items():
        if value not in (None, '', [], {}):
            if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value
    return merged


def _extract_profile_user(payload: Any) -> Mapping[str, Any] | None:
    if not isinstance(payload, Mapping):
        return None
    candidates = [
        payload.get('user'),
        (payload.get('data') or {}).get('user') if isinstance(payload.get('data'), Mapping) else None,
        (payload.get('graphql') or {}).get('user') if isinstance(payload.get('graphql'), Mapping) else None,
        (payload.get('data') or {}).get('profile') if isinstance(payload.get('data'), Mapping) else None,
        (payload.get('xdt_api__v1__users__web_profile_info') or {}).get('user') if isinstance(payload.get('xdt_api__v1__users__web_profile_info'), Mapping) else None,
    ]
    direct = next((candidate for candidate in candidates if isinstance(candidate, Mapping)), None)
    if direct is not None:
        return direct
    for node in _walk_json(payload):
        if not isinstance(node, Mapping) or not node.get('username'):
            continue
        if any(key in node for key in ('biography', 'edge_follow', 'edge_followed_by', 'follower_count', 'following_count', 'full_name')):
            return node
    return None


def _shared_data_documents(document: str) -> list[Any]:
    """Extract JSON assigned to window._sharedData from the rendered profile HTML."""
    decoder = json.JSONDecoder()
    documents: list[Any] = []
    patterns = (
        r'window\s*\.\s*_sharedData\s*=\s*',
        r'window\s*\[\s*["\']_sharedData["\']\s*\]\s*=\s*',
    )
    for pattern in patterns:
        for match in re.finditer(pattern, document, flags=re.IGNORECASE):
            start = document.find('{', match.end())
            if start < 0:
                continue
            try:
                parsed, _ = decoder.raw_decode(document[start:])
            except json.JSONDecodeError:
                continue
            documents.append(parsed)
    return documents


def _profile_users_from_document(document: str) -> list[Mapping[str, Any]]:
    """Return users found in legacy _sharedData and current embedded profile payloads."""
    users: list[Mapping[str, Any]] = []
    documents = _shared_data_documents(document) + _embedded_json_documents(document)
    for payload in documents:
        direct = _extract_profile_user(payload)
        if isinstance(direct, Mapping):
            users.append(direct)
        for node in _walk_json(payload):
            if not isinstance(node, Mapping):
                continue
            candidate = node.get('user')
            if isinstance(candidate, Mapping) and any(key in candidate for key in ('biography', 'edge_follow', 'edge_followed_by', 'username')):
                users.append(candidate)
    unique: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for user in users:
        marker = str(user.get('id') or user.get('pk') or user.get('username') or id(user))
        if marker not in seen:
            seen.add(marker)
            unique.append(user)
    return unique


def _extract_posts_from_documents(documents: list[Any], limit: int) -> list[dict[str, Any]]:
    posts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for document in documents:
        for node in _walk_json(document):
            if not isinstance(node, Mapping):
                continue
            post = _post_from_node(dict(node))
            if not post or post['id'] in seen:
                continue
            seen.add(post['id'])
            posts.append(post)
            if len(posts) >= max(1, int(limit)):
                return posts
    return posts


def _extract_profile_from_html(html_content: str) -> dict[str, Any]:
    """Extract the public profile and available posts from rendered Instagram HTML."""
    html = str(html_content or '')
    documents = _shared_data_documents(html) + _embedded_json_documents(html)
    users = _profile_users_from_document(html)
    user = max(users, key=_profile_quality, default={})
    posts = _extract_posts_from_documents(documents, limit=10)
    result = {'user': dict(user) if isinstance(user, Mapping) else {}, 'posts': posts}
    LOGGER.info('Instagram HTML extraction profile=%s posts=%s', bool(result['user']), len(posts))
    print(f"Playwright usado no Windows, dados extraídos com {'sucesso' if result['user'] or posts else 'falha'}")
    return result


def _extract_posts_from_html(html_content: str, limit: int = 10) -> list[dict[str, Any]]:
    """Extract public posts from _sharedData and JSON scripts in rendered HTML."""
    html = str(html_content or '')
    documents = _shared_data_documents(html) + _embedded_json_documents(html)
    posts = _extract_posts_from_documents(documents, limit=max(1, int(limit)))
    LOGGER.info('Instagram HTML post extraction posts=%s limit=%s', len(posts), limit)
    print(f"Playwright usado no Windows, posts extraídos: {len(posts)}")
    return posts


def _fetch_profile_with_playwright(username: str) -> dict[str, Any]:
    """Load a public profile page and extract only its rendered HTML."""
    url = f'https://www.instagram.com/{username}/'
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=_instagram_playwright_headless())
            try:
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36',
                    extra_http_headers={'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'},
                )
                page = context.new_page()
                response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
                status = response.status if response else None
                LOGGER.info('Instagram Playwright HTML profile URL=%s status=%s', url, status)
                print(f'Playwright usado no Windows para o perfil @{username}')
                page.wait_for_timeout(5000)
                try:
                    page.wait_for_load_state('networkidle', timeout=10000)
                except (PlaywrightTimeoutError, TimeoutError):
                    LOGGER.debug('Instagram Playwright networkidle excedido; usando HTML já carregado.')
                html_content = page.content()
                _save_instagram_debug_html(username, html_content)
                extracted = _extract_profile_from_html(html_content)
                user = extracted.get('user') if isinstance(extracted, Mapping) else {}
                if isinstance(user, Mapping) and user:
                    LOGGER.info('Instagram Playwright HTML profile extracted URL=%s status=%s', url, status)
                    return dict(user)
                return {}
            finally:
                browser.close()
    except Exception as exc:
        LOGGER.warning('Falha no Playwright HTML do perfil Instagram URL=%s: %s', url, exc, exc_info=True)
        print(f'Playwright falhou no Windows para o perfil @{username}: {exc}')
        _streamlit_message('error', f'Playwright não conseguiu consultar o perfil Instagram: {exc}', 'profile_playwright_error')
        return {}


def _fetch_web_profile_user(username: str) -> dict[str, Any] | None:
    _ensure_windows_playwright()
    headers = _instagram_headers()
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36'
    if platform.system() == 'Windows':
        LOGGER.debug('Windows detectado: perfil Instagram exclusivamente via HTML Playwright sem cookies manuais.')
        return _fetch_profile_with_playwright(username)

    cookies = _instagram_cookies()
    endpoints = (
        f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}',
        f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}',
    )

    request_headers = [
        headers,
        {**headers, 'User-Agent': 'Instagram 390.0.0.0.50 Android', 'Accept': 'application/json, text/plain, */*'},
        {**headers, 'Referer': f'https://www.instagram.com/{username}/', 'Origin': 'https://www.instagram.com', 'X-Requested-With': 'XMLHttpRequest'},
    ]
    best_user: dict[str, Any] | None = None
    for request_header in request_headers:
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, headers=request_header, cookies=cookies or None, timeout=15)
                LOGGER.debug('Instagram profile URL=%s status=%s content_type=%s', endpoint, response.status_code, response.headers.get('content-type', ''))
                if response.status_code >= 400:
                    continue
                payload = response.json()
                LOGGER.debug('Instagram profile URL=%s response=JSON', endpoint)
            except (requests.RequestException, ValueError, AttributeError, StopIteration):
                LOGGER.warning('Falha na requisição JSON do perfil Instagram URL=%s', endpoint, exc_info=True)
                if best_user:
                    return best_user
                continue
            user = _extract_profile_user(payload)
            if isinstance(user, dict):
                best_user = _merge_profile(best_user, user)
                if _profile_quality(best_user) >= 4:
                    return best_user

    curl = shutil.which('curl')
    if curl:
        LOGGER.debug('Fallback curl disponível em %s', curl)
        for endpoint in endpoints:
            try:
                completed = subprocess.run(
                    [curl, '-L', '--max-time', '20', '-sS', '-A', headers['User-Agent'], '-H', f"x-ig-app-id: {headers['x-ig-app-id']}", '-H', 'Accept', 'application/json, text/plain, */*', endpoint],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=25,
                    check=False,
                )
                payload = json.loads(completed.stdout) if completed.returncode == 0 and completed.stdout else None
                LOGGER.debug('Instagram curl URL=%s returncode=%s stdout_bytes=%s stderr=%s', endpoint, completed.returncode, len(completed.stdout or ''), (completed.stderr or '').strip()[-500:])
                user = _extract_profile_user(payload)
                if isinstance(user, dict):
                    best_user = _merge_profile(best_user, user)
                    if _profile_quality(best_user) >= 4:
                        return best_user
            except (OSError, subprocess.SubprocessError, ValueError):
                LOGGER.warning('Falha no fallback curl do perfil Instagram URL=%s', endpoint, exc_info=True)
                continue
    else:
        LOGGER.warning('curl não está disponível no PATH; a tentar Playwright.')
        _streamlit_message('warning', 'curl não foi encontrado no PATH do Windows; será tentado o fallback Playwright.', 'curl_missing')

    return _fetch_profile_with_playwright(username) or best_user


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
        LOGGER.debug('Instagram about-account URL=%s status=%s content_type=%s', ABOUT_ACCOUNT_URL, response.status_code, response.headers.get('content-type', ''))
        if response.status_code >= 400:
            return ''
        country = _country_from_bloks(response.json())
        LOGGER.debug('Instagram about-account country_found=%s', bool(country))
        return country
    except (requests.RequestException, ValueError, TypeError) as exc:
        LOGGER.warning('Falha ao consultar país público do Instagram: %s', exc, exc_info=True)
        return ''


def _country_from_bio_fallback(bio: str) -> str:
    patterns = (
        r'\b(?:from|based in|located in|living in)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ .-]{1,60})',
        r'\b(?:de|baseado em|morando em|localizado em)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ .-]{1,60})',
    )
    for pattern in patterns:
        match = re.search(pattern, bio or '', flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(' .,!;:')
    return ''


def _profile_post_nodes(user: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Return post nodes from both legacy GraphQL edges and current items payloads."""
    containers: list[Any] = [
        user.get('edge_owner_to_timeline_media'),
        user.get('timeline_media'),
        user.get('media'),
        user,
    ]
    nodes: list[Mapping[str, Any]] = []
    for container in containers:
        if not isinstance(container, Mapping):
            continue
        raw_items = container.get('edges') or container.get('items') or container.get('data') or []
        if isinstance(raw_items, Mapping):
            raw_items = raw_items.get('items') or raw_items.get('edges') or []
        if not isinstance(raw_items, list):
            continue
        for item in raw_items:
            node = item.get('node') if isinstance(item, Mapping) and isinstance(item.get('node'), Mapping) else item
            if isinstance(node, Mapping):
                nodes.append(node)
    return nodes


def _profile_data_from_api(user: Mapping[str, Any], reference: Mapping[str, str]) -> dict[str, Any]:
    followers = _profile_metric(user, 'edge_followed_by', 'followers', 'follower_count', 'followerCount')
    following_node = user.get('edge_follow')
    following = normalize_instagram_metric(following_node) if isinstance(following_node, Mapping) else None
    following = following if following is not None else _profile_metric(user, 'follows', 'following', 'following_count', 'followingCount')
    followers = followers if followers is not None else _structured_metric_from_json(json.dumps(user), 'edge_followed_by', 'followers', 'follower_count', 'followerCount')
    following = following if following is not None else _structured_metric_from_json(json.dumps(user), 'edge_follow', 'follows', 'following', 'following_count', 'followingCount')
    media_node = user.get('edge_owner_to_timeline_media') or user.get('media')
    media = (media_node.get('count') if isinstance(media_node, Mapping) else None)
    media = media if media is not None else _profile_metric(user, 'posts', 'post_count', 'media_count')
    biography = str(user.get('biography') or user.get('bio') or user.get('description') or '').strip()
    direct_country = _country_value(user.get('country') or user.get('country_code'))
    country = direct_country or extract_public_instagram_country(user)
    if platform.system() != 'Windows':
        country = country or _fetch_instagram_about_country(user.get('id') or user.get('pk'))
    country = country or _country_from_bio_fallback(biography)
    LOGGER.debug('Instagram profile extracted keys=%s edge_follow=%r bio=%s followers=%s following=%s posts=%s country=%s', sorted(str(key) for key in user.keys()), following_node, bool(biography), followers, following, media, country or '—')
    return {
        'id': f"instagram_{reference['username']}",
        **reference,
        'name': str(user.get('full_name') or user.get('name') or user.get('username') or reference['username']).strip(),
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
        '_api_posts': [dict(node) for node in _profile_post_nodes(user)],
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
    'about_this_account_country', 'account_based_in', 'account_country',
    'country_name', 'country_of_origin', 'country_of_registration', 'location_country',
    'transparency_country',
}
PUBLIC_TRANSPARENCY_KEYS = {
    'about', 'about_account', 'about_this_account', 'about_this_account_data',
    'account_transparency', 'transparency', 'account_info', 'profile_context',
}


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
    LOGGER.debug('fetch_public_instagram_profile source=%s', source)
    try:
        reference = normalize_instagram_reference(source)
    except ValueError as exc:
        return IntegrationResult(False, str(exc), {})
    api_user = _fetch_web_profile_user(reference['username'])
    if api_user:
        data = _profile_data_from_api(api_user, reference)
        return IntegrationResult(True, 'Perfil Instagram encontrado publicamente.', data)
    if platform.system() == 'Windows':
        return IntegrationResult(False, 'Não foi possível obter os dados do Instagram. Verifique sua conexão ou tente novamente mais tarde.', reference)
    try:
        response = requests.get(reference['url'], headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'}, timeout=12)
    except requests.RequestException as exc:
        LOGGER.warning('Falha HTTP no perfil Instagram URL=%s: %s', reference['url'], exc, exc_info=True)
        return IntegrationResult(False, f'Não foi possível consultar o perfil público do Instagram: {exc}', reference)
    LOGGER.debug('Instagram HTML profile URL=%s status=%s content_type=%s response=HTML', reference['url'], response.status_code, response.headers.get('content-type', ''))
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
    embedded_country = embedded_country or _country_from_bio_fallback(description)
    LOGGER.debug('Instagram HTML profile extracted bio=%s followers=%s following=%s posts=%s country=%s', bool(description), followers, following, posts, embedded_country or '—')
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


def _fetch_posts_with_playwright(reference: Mapping[str, str], limit: int) -> list[dict[str, Any]]:
    """Load a public profile page and extract posts only from its rendered HTML."""
    url = str(reference.get('url') or '')
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=_instagram_playwright_headless())
            try:
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36',
                    extra_http_headers={'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'},
                )
                page = context.new_page()
                response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
                status = response.status if response else None
                LOGGER.info('Instagram Playwright HTML posts URL=%s status=%s', url, status)
                print(f'Playwright usado no Windows para os posts de @{reference.get("username", "")}'.strip())
                page.wait_for_timeout(5000)
                try:
                    page.wait_for_load_state('networkidle', timeout=10000)
                except (PlaywrightTimeoutError, TimeoutError):
                    LOGGER.debug('Instagram Playwright networkidle excedido; usando HTML já carregado para posts.')
                html_content = page.content()
                _save_instagram_debug_html(reference.get('username', 'instagram'), html_content)
                if status is not None and status >= 400:
                    return []
                return _extract_posts_from_html(html_content, limit)
            finally:
                browser.close()
    except Exception as exc:
        LOGGER.warning('Falha no Playwright HTML dos posts Instagram URL=%s: %s', url, exc, exc_info=True)
        print(f'Playwright falhou no Windows para os posts: {exc}')
        _streamlit_message('error', f'Playwright não conseguiu consultar os posts Instagram: {exc}', 'posts_playwright_error')
        return []


def fetch_public_instagram_posts(source: str, limit: int = 10) -> IntegrationResult:
    LOGGER.debug('fetch_public_instagram_posts source=%s limit=%s', source, limit)
    _ensure_windows_playwright()
    try:
        reference = normalize_instagram_reference(source)
    except ValueError as exc:
        return IntegrationResult(False, str(exc), {})
    if platform.system() == 'Windows':
        LOGGER.debug('Windows detectado: posts Instagram exclusivamente via HTML Playwright.')
        posts = _fetch_posts_with_playwright(reference, limit)
        if not posts:
            _streamlit_message('error', 'Não foi possível obter os dados do Instagram. Verifique sua conexão ou tente novamente mais tarde.', 'posts_instagram_failed')
        return IntegrationResult(bool(posts), 'Posts públicos encontrados.' if posts else 'Não foi possível obter os dados do Instagram. Verifique sua conexão ou tente novamente mais tarde.', reference | {'posts': posts[:max(1, int(limit))]})
    api_user = _fetch_web_profile_user(reference['username'])
    if api_user:
        api_posts: list[dict[str, Any]] = []
        for node in _profile_post_nodes(api_user):
            post = _post_from_node(dict(node))
            if post:
                api_posts.append(post)
        if api_posts:
            LOGGER.debug('Instagram API posts extracted=%s response=JSON', len(api_posts))
            return IntegrationResult(True, 'Posts públicos encontrados.', reference | {'posts': api_posts[:max(1, int(limit))]})
        if api_user.get('is_private'):
            return IntegrationResult(False, 'Esta conta é privada. O Instagram não disponibiliza posts sem uma sessão autenticada.', reference | {'posts': [], 'is_private': True})
    try:
        response = requests.get(reference['url'], headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'}, cookies=_instagram_cookies() or None, timeout=15)
    except requests.RequestException as exc:
        LOGGER.warning('Falha HTTP nos posts Instagram URL=%s: %s', reference['url'], exc, exc_info=True)
        return IntegrationResult(False, f'Não foi possível consultar os posts públicos do Instagram: {exc}', reference)
    LOGGER.debug('Instagram HTML posts URL=%s status=%s content_type=%s response=HTML', reference['url'], response.status_code, response.headers.get('content-type', ''))
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
    if not posts:
        posts = _fetch_posts_with_playwright(reference, limit)
    LOGGER.debug('Instagram posts extracted=%s limit=%s', len(posts), limit)
    return IntegrationResult(bool(posts), 'Posts públicos encontrados.' if posts else 'Não foi possível obter os dados do Instagram. Verifique sua conexão ou tente novamente mais tarde.', reference | {'posts': posts[:max(1, int(limit))]})


__all__ = ['IntegrationResult', 'extract_public_instagram_country', 'fetch_public_instagram_posts', 'fetch_public_instagram_profile', 'normalize_instagram_bio', 'normalize_instagram_metric', 'normalize_instagram_reference']
