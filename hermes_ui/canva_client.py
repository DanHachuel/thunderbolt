from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Mapping

import requests

from .canva_auth import refresh_access_token, token_is_expiring

API_ROOT = "https://api.canva.com/rest/v1"


class CanvaClient:
    def __init__(self, card: Mapping[str, Any], *, token_saver=None) -> None:
        self.card = dict(card)
        self.token_saver = token_saver
        self.client_id = str(card.get("client_id") or "").strip()
        self.client_secret = str(card.get("client_secret") or "").strip()
        self.token = dict(card.get("oauth_token") or {})
        self.base_url = str(card.get("base_url") or API_ROOT).rstrip("/")

    def _save_token(self, token: Mapping[str, Any]) -> None:
        self.token = dict(token)
        if self.token_saver:
            self.token_saver(self.token)

    def _access_token(self) -> str:
        if not self.token.get("access_token"):
            raise RuntimeError("Canva não está autorizada. Autorize a integração em Configuração API > Imagem e Video IA.")
        if token_is_expiring(self.token):
            refresh = str(self.token.get("refresh_token") or "").strip()
            if not refresh:
                raise RuntimeError("O token Canva expirou e não existe refresh token. Autorize novamente.")
            self._save_token(refresh_access_token(self.client_id, self.client_secret, refresh))
        return str(self.token["access_token"])

    def request(self, method: str, path: str, *, json: Mapping[str, Any] | None = None, params: Mapping[str, Any] | None = None, timeout: int = 60) -> dict[str, Any]:
        refreshed = False
        for attempt in range(4):
            try:
                token = self._access_token()
                response = requests.request(method, f"{self.base_url}/{path.lstrip('/')}", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}, json=json, params=params, timeout=timeout)
            except requests.RequestException as exc:
                if attempt == 3:
                    raise RuntimeError(f"Falha de rede na Canva: {str(exc)[:200]}") from exc
                time.sleep(2 ** attempt)
                continue
            if response.status_code == 401 and not refreshed and self.token.get("refresh_token"):
                self._save_token(refresh_access_token(self.client_id, self.client_secret, str(self.token["refresh_token"])))
                refreshed = True
                continue
            if response.status_code == 429:
                if attempt == 3:
                    raise RuntimeError("Canva devolveu HTTP 429: limite de pedidos atingido.")
                time.sleep(2 ** attempt)
                continue
            if response.status_code >= 400:
                raise RuntimeError(f"Canva devolveu HTTP {response.status_code}: {response.text[:240]}")
            return response.json()
        raise RuntimeError("Canva não respondeu após as tentativas disponíveis.")

    def create_design(self, width: int = 1280, height: int = 720, *, title: str = "Thunderbolt thumbnail") -> dict[str, Any]:
        if not (40 <= width <= 8000 and 40 <= height <= 8000 and width * height <= 25_000_000):
            raise ValueError("Dimensões Canva inválidas: cada dimensão deve estar entre 40 e 8000 e a área não pode exceder 25.000.000 px².")
        return self.request("POST", "designs", json={"type": "type_and_asset", "design_type": {"type": "custom", "width": width, "height": height}, "title": title})

    def export_design(self, design_id: str, *, file_type: str = "png", quality: str = "regular") -> str:
        if file_type not in {"png", "jpg"}:
            raise ValueError("A Canva thumbnail só suporta PNG ou JPG.")
        if quality not in {"regular", "pro"}:
            raise ValueError("A qualidade Canva deve ser regular ou pro.")
        payload = self.request("POST", "exports", json={"design_id": design_id, "format": {"type": file_type, "export_quality": quality}})
        job = payload.get("job") or payload
        job_id = str(job.get("id") or "").strip()
        if not job_id:
            raise RuntimeError("Canva não devolveu o ID do job de exportação.")
        return job_id

    def get_export_job_status(self, job_id: str) -> dict[str, Any]:
        return self.request("GET", f"exports/{job_id}", json=None)

    def wait_export(self, job_id: str, *, attempts: int = 30, interval: float = 2.0) -> str:
        for _ in range(attempts):
            payload = self.get_export_job_status(job_id)
            job = payload.get("job") or payload
            status = str(job.get("status") or "").lower()
            if status == "success" and job.get("urls"):
                return str(job["urls"][0])
            if status == "failed":
                error = job.get("error") or {}
                raise RuntimeError(f"Exportação Canva falhou: {error.get('code') or error}")
            time.sleep(interval)
        raise RuntimeError("A exportação Canva excedeu o tempo de espera.")

    def download_export(self, url: str, destination: Path) -> Path:
        try:
            response = requests.get(url, timeout=90)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f"Não foi possível descarregar a thumbnail Canva: {str(exc)[:200]}") from exc
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)
        return destination

    def create_and_export_thumbnail(self, *, title: str, width: int = 1280, height: int = 720) -> Path:
        design = self.create_design(width, height, title=title)
        design_id = str((design.get("design") or design).get("id") or "")
        if not design_id:
            raise RuntimeError("Canva não devolveu o ID do design.")
        job_id = self.export_design(design_id, file_type=str(self.card.get("export_format") or "png"), quality=str(self.card.get("export_quality") or "regular"))
        url = self.wait_export(job_id)
        destination = Path(str(self.card.get("output_path") or "thumbnail-canva.png"))
        return self.download_export(url, destination)
