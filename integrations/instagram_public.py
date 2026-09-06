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
_INSTALOADER_INSTALL_ATTEMPTED = False


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
    """Use headed mode for Windows diagnostics unless explicitly overridden."""
    value = os.getenv('INSTAGRAM_PLAYWRIGHT_HEADLESS', 'false').strip().casefold()
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


def _instagram_instaloader():
    """Load the anonymous fallback, installing it once when the requirement is missing."""
    global _INSTALOADER_INSTALL_ATTEMPTED
    try:
        import instaloader
        return instaloader
    except ImportError:
        if _INSTALOADER_INSTALL_ATTEMPTED:
            LOGGER.warning('Fallback instaloader indisponível; instale com: python -m pip install instaloader')
            return None
        _INSTALOADER_INSTALL_ATTEMPTED = True
        try:
            LOGGER.info('Instaloader ausente; a tentar instalar a dependência automaticamente.')
            completed = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'instaloader>=4.14,<5'],
                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180, check=False,
            )
            if completed.returncode == 0:
                import importlib
                importlib.invalidate_caches()
                try:
                    import instaloader
                    return instaloader
                except ImportError:
                    LOGGER.warning('Instaloader foi instalado, mas não ficou disponível neste interpretador.')
            LOGGER.warning('Instalação automática do instaloader falhou: %s', (completed.stderr or completed.stdout)[-1000:])
        except (OSError, subprocess.SubprocessError) as exc:
            LOGGER.warning('Não foi possível instalar instaloader automaticamente: %s', exc)
        _streamlit_message('error', 'O fallback instaloader não está disponível. Instale com: python -m pip install instaloader', 'instaloader_missing')
        return None


def _fetch_profile_instaloader(username: str) -> dict[str, Any] | None:
    """Fetch a public profile anonymously through Instaloader when Playwright fails."""
    instaloader = _instagram_instaloader()
    if instaloader is None:
        return None
    try:
        loader = instaloader.Instaloader(
            quiet=True,
            request_timeout=30,
            max_connection_attempts=1,
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            save_metadata=False,
        )
        profile = instaloader.Profile.from_username(loader.context, username)
        LOGGER.info('Fallback instaloader activado para o perfil @%s', username)
        return {
            'id': str(getattr(profile, 'userid', '') or ''),
            'username': str(getattr(profile, 'username', '') or username),
            'full_name': str(getattr(profile, 'full_name', '') or ''),
            'biography': str(getattr(profile, 'biography', '') or ''),
            'follower_count': getattr(profile, 'follower_count', getattr(profile, 'followers', None)),
            'following_count': getattr(profile, 'following_count', getattr(profile, 'followees', None)),
            'edge_owner_to_timeline_media': {'count': getattr(profile, 'mediacount', None)},
            'is_private': bool(getattr(profile, 'is_private', False)),
            '_instagram_source': 'instaloader',
        }
    except Exception as exc:
        LOGGER.warning('Fallback instaloader falhou para @%s: %s', username, exc, exc_info=True)
        return None


def _fetch_posts_instaloader(username: str, limit: int = 10) -> list[dict[str, Any]]:
    """Fetch public posts anonymously through Instaloader when Playwright fails."""
    instaloader = _instagram_instaloader()
    if instaloader is None:
        return []
    posts: list[dict[str, Any]] = []
    try:
        loader = instaloader.Instaloader(
            quiet=True,
            request_timeout=30,
            max_connection_attempts=1,
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            save_metadata=False,
        )
        profile = instaloader.Profile.from_username(loader.context, username)
        for post in profile.get_posts():
            shortcode = str(getattr(post, 'shortcode', '') or '')
            if not shortcode:
                continue
            image_url = str(getattr(post, 'url', '') or '')
            timestamp = getattr(post, 'date_utc', '') or ''
            posts.append({
                'id': str(getattr(post, 'mediaid', '') or shortcode),
                'shortcode': shortcode,
                'url': f'https://www.instagram.com/p/{shortcode}/',
                'image_url': image_url,
                'display_url': image_url,
                'caption': str(getattr(post, 'caption', '') or '').strip(),
                'published_at': timestamp,
                'timestamp': timestamp,
                'is_video': bool(getattr(post, 'is_video', False)),
            })
            if len(posts) >= max(1, int(limit)):
                break
        LOGGER.info('Fallback instaloader carregou %s posts para @%s', len(posts), username)
    except Exception as exc:
        LOGGER.warning('Fallback instaloader falhou nos posts de @%s: %s', username, exc, exc_info=True)
    return posts


def fetch_profile_instaloader(username: str) -> dict[str, Any] | None:
    return _fetch_profile_instaloader(username)


def fetch_posts_instaloader(username: str, limit: int = 10) -> list[dict[str, Any]]:
    return _fetch_posts_instaloader(username, limit)


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
    ]
    return next((candidate for candidate in candidates if isinstance(candidate, Mapping)), None)


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
    seen: set[int] = set()
    for user in users:
        marker = id(user)
        if marker not in seen:
            seen.add(marker)
            unique.append(user)
    return unique


def _fetch_profile_with_playwright(username: str, headers: Mapping[str, str] | None = None, cookies: Mapping[str, str] | None = None) -> dict[str, Any] | None:
    """Fetch the structured profile JSON requested by the public Instagram page."""
    headers = headers or _instagram_headers()
    cookies = cookies or _instagram_cookies()
    captured_user: dict[str, Any] | None = None
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=_instagram_playwright_headless())
            try:
                headers_for_context = {'x-ig-app-id': headers['x-ig-app-id'], 'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7', 'Accept': 'application/json, text/plain, */*', 'Origin': 'https://www.instagram.com', 'Referer': 'https://www.instagram.com/'}
                state_path = Path(__file__).resolve().parents[1] / 'storage' / 'instagram_storage_state.json'
                context_kwargs = {'user_agent': headers['User-Agent'], 'extra_http_headers': headers_for_context}
                if state_path.is_file():
                    context_kwargs['storage_state'] = str(state_path)
                context = browser.new_context(**context_kwargs)
                if cookies:
                    context.add_cookies([{'name': name, 'value': value, 'domain': '.instagram.com', 'path': '/'} for name, value in cookies.items()])
                page = context.new_page()

                def capture_profile_response(response: Any) -> None:
                    nonlocal captured_user
                    if '/api/v1/users/web_profile_info/' not in response.url:
                        return
                    try:
                        payload = response.json()
                        user = ((payload.get('data') or {}).get('user') if isinstance(payload, Mapping) else None)
                        if isinstance(user, Mapping):
                            captured_user = _merge_profile(captured_user, user)
                            LOGGER.debug('Instagram Playwright API profile captured user=%s', username)
                    except (ValueError, TypeError, AttributeError) as exc:
                        LOGGER.debug('Não foi possível interpretar resposta web_profile_info: %s', exc)

                page.on('response', capture_profile_response)
                try:
                    page.goto('https://www.instagram.com/', wait_until='domcontentloaded', timeout=30000)
                    state_path.parent.mkdir(parents=True, exist_ok=True)
                    context.storage_state(path=str(state_path))
                    LOGGER.debug('Instagram Playwright página inicial carregada; storage_state salvo em %s.', state_path)
                except Exception as exc:
                    LOGGER.debug('Instagram Playwright não carregou a página inicial: %s', exc)
                url = f'https://www.instagram.com/{username}/'
                response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
                LOGGER.debug('Instagram Playwright profile URL=%s status=%s', url, response.status if response else None)
                if response is None or response.status >= 400:
                    LOGGER.warning('Instagram Playwright perfil HTTP status=%s URL=%s', response.status if response else None, url)
                    return captured_user
                try:
                    _save_instagram_debug_html(username, page.content())
                except Exception as exc:
                    LOGGER.debug('Não foi possível guardar HTML de diagnóstico: %s', exc)
                page.wait_for_timeout(5000)
                try:
                    page.wait_for_load_state('networkidle', timeout=10000)
                except (PlaywrightTimeoutError, TimeoutError):
                    LOGGER.debug('Instagram Playwright networkidle excedido; usando resposta API já capturada.')
                LOGGER.info('Instagram Playwright API profile captured=%s quality=%s URL=%s', bool(captured_user), _profile_quality(captured_user or {}), url)
            finally:
                browser.close()
    except Exception as exc:
        LOGGER.warning('Falha no Playwright do perfil Instagram: %s', exc, exc_info=True)
        _streamlit_message('error', f'Playwright não conseguiu consultar o perfil Instagram: {exc}', 'profile_playwright_error')
    return captured_user


def _fetch_web_profile_user(username: str) -> dict[str, Any] | None:
    _ensure_windows_playwright()
    cookies = _instagram_cookies()
    headers = _instagram_headers()
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36'
    if platform.system() == 'Windows':
        LOGGER.debug('Windows detectado: perfil Instagram exclusivamente via Playwright.')
        playwright_user = _fetch_profile_with_playwright(username, headers, cookies)
        if playwright_user:
            return playwright_user
        LOGGER.warning('Fallback para instaloader activado no perfil @%s.', username)
        fallback_user = fetch_profile_instaloader(username)
        if fallback_user:
            _streamlit_message('info', 'Dados obtidos via fallback (instaloader). O país pode não estar disponível.', 'profile_instaloader_fallback')
        else:
            _streamlit_message('error', 'Não foi possível obter os dados do Instagram. Verifique sua conexão ou tente novamente mais tarde.', 'profile_instagram_failed')
        return fallback_user

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

    return _fetch_profile_with_playwright(username, headers, cookies) or best_user


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


def _profile_data_from_api(user: Mapping[str, Any], reference: Mapping[str, str]) -> dict[str, Any]:
    followers = _profile_metric(user, 'edge_followed_by', 'followers', 'follower_count', 'followerCount')
    following_node = user.get('edge_follow')
    following = normalize_instagram_metric(following_node) if isinstance(following_node, Mapping) else None
    following = following if following is not None else _profile_metric(user, 'follows', 'following', 'following_count', 'followingCount')
    followers = followers if followers is not None else _structured_metric_from_json(json.dumps(user), 'edge_followed_by', 'followers', 'follower_count', 'followerCount')
    following = following if following is not None else _structured_metric_from_json(json.dumps(user), 'edge_follow', 'follows', 'following', 'following_count', 'followingCount')
    media = ((user.get('edge_owner_to_timeline_media') or {}).get('count') if isinstance(user.get('edge_owner_to_timeline_media'), dict) else None)
    media = media if media is not None else _profile_metric(user, 'posts', 'post_count', 'media_count')
    biography = str(user.get('biography') or user.get('bio') or user.get('description') or '').strip()
    country = extract_public_instagram_country(user) or _fetch_instagram_about_country(user.get('id') or user.get('pk'))
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
        '_api_posts': (((user.get('edge_owner_to_timeline_media') or {}).get('edges') or []) if isinstance(user.get('edge_owner_to_timeline_media'), dict) else (user.get('posts') if isinstance(user.get('posts'), list) else [])),
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
    LOGGER.debug('fetch_public_instagram_profile source=%s', source)
    try:
        reference = normalize_instagram_reference(source)
    except ValueError as exc:
        return IntegrationResult(False, str(exc), {})
    api_user = _fetch_web_profile_user(reference['username'])
    if api_user:
        data = _profile_data_from_api(api_user, reference)
        if api_user.get('_instagram_source') == 'instaloader':
            return IntegrationResult(True, 'Perfil encontrado via fallback instaloader. O país pode não estar disponível.', data)
        return IntegrationResult(True, 'Perfil Instagram encontrado publicamente.', data)
    if platform.system() == 'Windows':
        return IntegrationResult(False, 'Não foi possível extrair os dados públicos do Instagram com o Playwright.', reference)
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


def _fetch_posts_with_playwright(reference: Mapping[str, str], limit: int, cookies: Mapping[str, str] | None = None) -> list[dict[str, Any]]:
    # CORREÇÃO WINDOWS: posts são extraídos exclusivamente da resposta API capturada pelo Playwright.
    posts: list[dict[str, Any]] = []
    seen: set[str] = set()
    cookies = cookies or _instagram_cookies()
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=_instagram_playwright_headless())
            try:
                state_path = Path(__file__).resolve().parents[1] / 'storage' / 'instagram_storage_state.json'
                headers_for_context = {'x-ig-app-id': '936619743392459', 'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7', 'Accept': 'application/json, text/plain, */*', 'Origin': 'https://www.instagram.com', 'Referer': 'https://www.instagram.com/'}
                context_kwargs = {'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36', 'extra_http_headers': headers_for_context}
                if state_path.is_file():
                    context_kwargs['storage_state'] = str(state_path)
                context = browser.new_context(**context_kwargs)
                if cookies:
                    context.add_cookies([{'name': name, 'value': value, 'domain': '.instagram.com', 'path': '/'} for name, value in cookies.items()])
                page = context.new_page()

                def capture_profile_posts(response: Any) -> None:
                    if '/api/v1/users/web_profile_info/' not in response.url:
                        return
                    try:
                        payload = response.json()
                        user = ((payload.get('data') or {}).get('user') if isinstance(payload, Mapping) else None)
                        media = user.get('edge_owner_to_timeline_media') if isinstance(user, Mapping) else None
                        edges = media.get('edges') if isinstance(media, Mapping) else []
                        for edge in edges or []:
                            node = edge.get('node') if isinstance(edge, Mapping) else None
                            if not isinstance(node, dict):
                                continue
                            post = _post_from_node(node)
                            if post and post['id'] not in seen:
                                seen.add(post['id'])
                                posts.append(post)
                    except (ValueError, TypeError, AttributeError) as exc:
                        LOGGER.debug('Não foi possível interpretar posts web_profile_info: %s', exc)

                page.on('response', capture_profile_posts)
                try:
                    page.goto('https://www.instagram.com/', wait_until='domcontentloaded', timeout=30000)
                    state_path.parent.mkdir(parents=True, exist_ok=True)
                    context.storage_state(path=str(state_path))
                except Exception as exc:
                    LOGGER.debug('Instagram Playwright não carregou a página inicial para posts: %s', exc)
                response = page.goto(reference['url'], wait_until='domcontentloaded', timeout=30000)
                LOGGER.debug('Instagram Playwright posts URL=%s status=%s', reference['url'], response.status if response else None)
                if response is None or response.status >= 400:
                    return []
                page.wait_for_timeout(5000)
                try:
                    page.wait_for_load_state('networkidle', timeout=10000)
                except (PlaywrightTimeoutError, TimeoutError):
                    LOGGER.debug('Instagram Playwright networkidle excedido; usando posts API já capturados.')
                LOGGER.debug('Instagram Playwright API posts extracted=%s limit=%s', len(posts), limit)
                return posts[:max(1, int(limit))]
            finally:
                browser.close()
    except Exception as exc:
        LOGGER.warning('Falha no Playwright dos posts Instagram: %s', exc, exc_info=True)
        _streamlit_message('error', f'Playwright não conseguiu consultar os posts Instagram: {exc}', 'posts_playwright_error')
    return posts


def fetch_public_instagram_posts(source: str, limit: int = 10) -> IntegrationResult:
    LOGGER.debug('fetch_public_instagram_posts source=%s limit=%s', source, limit)
    _ensure_windows_playwright()
    try:
        reference = normalize_instagram_reference(source)
    except ValueError as exc:
        return IntegrationResult(False, str(exc), {})
    if platform.system() == 'Windows':
        LOGGER.debug('Windows detectado: posts Instagram exclusivamente via Playwright.')
        posts = _fetch_posts_with_playwright(reference, limit, _instagram_cookies())
        if not posts:
            LOGGER.warning('Fallback para instaloader activado nos posts de @%s.', reference['username'])
            posts = fetch_posts_instaloader(reference['username'], limit)
            if posts:
                _streamlit_message('info', 'Dados obtidos via fallback (instaloader). O país pode não estar disponível.', 'posts_instaloader_fallback')
            else:
                _streamlit_message('error', 'Não foi possível obter os dados do Instagram. Verifique sua conexão ou tente novamente mais tarde.', 'posts_instagram_failed')
        return IntegrationResult(bool(posts), 'Posts públicos encontrados.' if posts else 'Não foi possível encontrar posts públicos nesta página do Instagram.', reference | {'posts': posts[:max(1, int(limit))]})
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
        posts = _fetch_posts_with_playwright(reference, limit, _instagram_cookies())
    LOGGER.debug('Instagram posts extracted=%s limit=%s', len(posts), limit)
    return IntegrationResult(bool(posts), 'Posts públicos encontrados.' if posts else 'Não foi possível encontrar posts públicos nesta página do Instagram.', reference | {'posts': posts[:max(1, int(limit))]})


__all__ = ['IntegrationResult', 'extract_public_instagram_country', 'fetch_posts_instaloader', 'fetch_profile_instaloader', 'fetch_public_instagram_posts', 'fetch_public_instagram_profile', 'normalize_instagram_bio', 'normalize_instagram_metric', 'normalize_instagram_reference']
