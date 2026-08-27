"""Preparação de uploads DistroKid por browser, inspirada no fluxo do musikai.

O adapter executa apenas a parte de upload/preenchimento do formulário. A
submissão final fica sempre manual no browser para evitar publicação acidental.
"""
from __future__ import annotations

import http.cookies
import os
import re
import uuid
from pathlib import Path
from typing import Any

import requests

from .platforms import IntegrationResult

DISTROKID_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".aac"}
DISTROKID_COVER_EXTENSIONS = {".jpg", ".jpeg", ".png"}
DEFAULT_DISTROKID_URL = "https://distrokid.com/new/"
_LIVE_SESSIONS: dict[str, Any] = {}


def _cookie_header_to_context_cookies(cookie_header: str) -> list[dict[str, str]]:
    jar = http.cookies.SimpleCookie()
    jar.load(str(cookie_header or ""))
    return [
        {"name": morsel.key, "value": morsel.value, "domain": ".distrokid.com", "path": "/"}
        for morsel in jar.values()
        if morsel.key and morsel.value
    ]


def _safe_path(value: str | Path | None, allowed: set[str], label: str) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_file():
        raise ValueError(f"{label} não encontrado: {path}")
    if path.suffix.lower() not in allowed:
        raise ValueError(f"Formato de {label.lower()} não suportado: {path.suffix}")
    return path.resolve()


def _text(value: Any, maximum: int = 500) -> str:
    return str(value or "").strip()[:maximum]


class DistroKidAdapter:
    """Preenche a página de novo lançamento DistroKid e carrega as tracks localmente."""

    def __init__(self, settings: dict[str, Any] | None = None):
        self.settings = settings or {}
        self.enabled = bool(self.settings.get("distrokid_enabled", False))
        self.cookie = str(self.settings.get("distrokid_cookie") or "").strip()
        self.account = _text(self.settings.get("distrokid_account"), 160)
        self.first_name = _text(self.settings.get("distrokid_first_name"), 120)
        self.last_name = _text(self.settings.get("distrokid_last_name"), 120)
        self.record_label = _text(self.settings.get("distrokid_record_label"), 160)
        self.browser_path = str(self.settings.get("distrokid_browser_path") or os.getenv("THUNDERBOLT_CHROME_PATH") or "").strip()
        self.base_url = str(self.settings.get("distrokid_url") or DEFAULT_DISTROKID_URL).strip() or DEFAULT_DISTROKID_URL

    def status(self) -> IntegrationResult:
        if not self.enabled:
            return IntegrationResult(False, "DistroKid está desactivado nesta configuração.", {})
        if not self.cookie:
            return IntegrationResult(False, "Configure o cookie de sessão DistroKid para preencher o formulário de upload.", {"missing_fields": ["distrokid_cookie"]})
        cookies = _cookie_header_to_context_cookies(self.cookie)
        if not cookies:
            return IntegrationResult(False, "O cookie DistroKid não tem um formato válido de cabeçalho Cookie.", {"missing_fields": ["distrokid_cookie"]})
        return IntegrationResult(True, "DistroKid configurado para upload manual assistido.", {"account": self.account or "Conta DistroKid", "cookies": len(cookies), "manual_submit": True})

    def test_connection(self) -> IntegrationResult:
        status = self.status()
        if not status.ok:
            return status
        cookie_header = self.cookie
        try:
            response = requests.get(
                self.base_url,
                headers={"Cookie": cookie_header, "User-Agent": "Mozilla/5.0 Thunderbolt"},
                timeout=30,
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            return IntegrationResult(False, f"Não foi possível contactar o DistroKid: {exc}", {"api": "DistroKid web", "account": self.account or "Conta DistroKid"})
        final_url = str(getattr(response, "url", "") or "")
        authenticated = response.status_code < 400 and "/login" not in final_url.lower() and "login" not in (response.text or "")[:2000].lower()
        if not authenticated:
            return IntegrationResult(False, "A sessão DistroKid foi rejeitada ou expirou. Actualize o cookie no browser e guarde-o novamente.", {"api": "DistroKid web", "status_code": response.status_code, "authenticated": False})
        return IntegrationResult(True, "Chamada DistroKid concluída; a sessão parece válida.", {"api": "DistroKid web", "status_code": response.status_code, "authenticated": True})

    def prepare_upload(
        self,
        tracks: list[dict[str, Any]],
        *,
        artist: str,
        release_title: str,
        record_label: str = "",
        cover_path: str | Path | None = None,
        genre: str = "",
    ) -> IntegrationResult:
        """Open DistroKid's form, fill metadata and upload tracks; never submit automatically."""
        status = self.status()
        if not status.ok:
            return status
        if not tracks:
            return IntegrationResult(False, "Seleccione pelo menos uma faixa para o upload DistroKid.", {})
        clean_artist = _text(artist, 160)
        clean_release_title = _text(release_title, 160)
        clean_label = _text(record_label or self.record_label, 160)
        if not clean_artist or not clean_release_title:
            return IntegrationResult(False, "Artista e título do lançamento são obrigatórios para o upload DistroKid.", {})
        prepared_tracks: list[dict[str, Any]] = []
        try:
            for item in tracks:
                path = _safe_path(item.get("path"), DISTROKID_AUDIO_EXTENSIONS, "ficheiro de áudio")
                if path is None:
                    raise ValueError("Cada faixa DistroKid precisa de um ficheiro de áudio local.")
                prepared_tracks.append({
                    "path": path,
                    "title": _text(item.get("title") or path.stem, 160),
                    "instrumental": bool(item.get("instrumental", False)),
                })
            cover = _safe_path(cover_path, DISTROKID_COVER_EXTENSIONS, "capa")
        except ValueError as exc:
            return IntegrationResult(False, str(exc), {"api": "DistroKid web"})
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            return IntegrationResult(False, "A dependência Playwright não está instalada; actualize o Thunderbolt para activar o browser DistroKid.", {"api": "DistroKid web"})
        session_id = f"distrokid-{uuid.uuid4().hex[:12]}"
        try:
            playwright = sync_playwright().start()
            launch_kwargs: dict[str, Any] = {"headless": False}
            if self.browser_path:
                launch_kwargs["executable_path"] = self.browser_path
            else:
                launch_kwargs["channel"] = "chrome"
            browser = playwright.chromium.launch(**launch_kwargs)
            context = browser.new_context(locale="en-US", accept_downloads=True)
            context.add_cookies(_cookie_header_to_context_cookies(self.cookie))
            page = context.new_page()
            page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("body", state="visible", timeout=30000)
            if "/login" in page.url.lower():
                raise RuntimeError("A sessão DistroKid foi redireccionada para login.")
            self._fill_form(page, prepared_tracks, clean_artist, clean_release_title, clean_label, cover, _text(genre, 120))
            _LIVE_SESSIONS[session_id] = {"playwright": playwright, "browser": browser, "context": context, "page": page}
            return IntegrationResult(True, "Formulário DistroKid aberto e ficheiros carregados. Reveja todos os dados no browser e clique manualmente em Submit.", {"session_id": session_id, "account": self.account or "Conta DistroKid", "tracks": len(prepared_tracks), "manual_submit": True})
        except Exception as exc:
            try:
                playwright.stop()  # type: ignore[name-defined]
            except Exception:
                pass
            if exc.__class__.__name__ == "Error" or "executable" in str(exc).lower() or "browser" in str(exc).lower():
                return IntegrationResult(False, f"Não foi possível abrir o browser DistroKid: {exc}", {"api": "DistroKid web"})
            if "Timeout" in exc.__class__.__name__ or "timeout" in str(exc).lower():
                return IntegrationResult(False, f"O DistroKid não carregou o formulário a tempo: {exc}", {"api": "DistroKid web"})
            return IntegrationResult(False, f"Upload DistroKid falhou: {exc}", {"api": "DistroKid web"})

    @staticmethod
    def _fill_form(page: Any, tracks: list[dict[str, Any]], artist: str, release_title: str, record_label: str, cover: Path | None, genre: str) -> None:
        try:
            page.locator("#sitetran_select").select_option("en", timeout=5000)
        except Exception:
            pass
        page.locator("#artistName").fill(artist)
        if record_label:
            try:
                page.locator("#recordLabel").select_option(label=record_label, timeout=8000)
            except Exception:
                try:
                    page.locator("#recordLabel").select_option(record_label, timeout=5000)
                except Exception:
                    pass
        try:
            page.locator("#howManySongsOnThisAlbum").select_option(str(len(tracks)), timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(1000)
        if cover is not None:
            page.locator("#artwork").set_input_files(str(cover), timeout=15000)
            try:
                page.locator("img.artworkPreview").wait_for(state="visible", timeout=30000)
            except Exception:
                pass
        track_nodes = page.locator("input[name^='tracknum_']")
        count = track_nodes.count()
        if count < len(tracks):
            raise RuntimeError(f"O DistroKid apresentou {count} campos de faixa, mas foram seleccionadas {len(tracks)}.")
        for index, track in enumerate(tracks, start=1):
            track_id = track_nodes.nth(index - 1).get_attribute("id") or ""
            track_id = re.sub(r"^tracknum_", "", track_id)
            if not track_id:
                raise RuntimeError(f"Não foi possível encontrar o identificador da faixa {index}.")
            page.locator(f"#title_{track_id}").fill(track["title"])
            page.locator(f"#js-track-upload-{index}").set_input_files(str(track["path"]), timeout=30000)
            page.locator(f"#showFilename_{index}").wait_for(state="visible", timeout=120000)
        if len(tracks) > 1:
            try:
                page.locator("#albumTitleInput").fill(release_title)
            except Exception:
                pass
        if genre:
            try:
                page.locator("#genrePrimary").select_option(label=genre, timeout=5000)
            except Exception:
                pass


def close_distrokid_session(session_id: str) -> IntegrationResult:
    session = _LIVE_SESSIONS.pop(str(session_id), None)
    if not session:
        return IntegrationResult(False, "Sessão DistroKid não encontrada ou já encerrada.", {})
    try:
        session["context"].close()
        session["browser"].close()
        session["playwright"].stop()
    except Exception as exc:
        return IntegrationResult(False, f"A sessão DistroKid foi fechada com aviso: {exc}", {"session_id": session_id})
    return IntegrationResult(True, "Sessão DistroKid fechada.", {"session_id": session_id})


__all__ = ["DEFAULT_DISTROKID_URL", "DISTROKID_AUDIO_EXTENSIONS", "DISTROKID_COVER_EXTENSIONS", "DistroKidAdapter", "close_distrokid_session"]
