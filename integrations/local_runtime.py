from __future__ import annotations

import os
import socket
from pathlib import Path
from typing import Any


class LocalRuntime:
    """Detecta serviços locais sem fazer a UI depender deles para arrancar."""

    def __init__(self, settings: dict[str, Any]):
        self.settings = settings
        self.moneyprinter_path = Path(settings.get("moneyprinter_path", "") or os.getenv("MONEYPRINTER_PATH", ""))
        self.hermes_url = settings.get("hermes_url", "http://localhost:8765")

    def moneyprinter_available(self) -> bool:
        return bool(self.moneyprinter_path and self.moneyprinter_path.exists())

    def hermes_available(self) -> bool:
        try:
            host = self.hermes_url.split("//", 1)[-1].split(":", 1)[0].split("/", 1)[0]
            port = int(self.hermes_url.rsplit(":", 1)[-1].split("/", 1)[0]) if ":" in self.hermes_url else 80
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except (OSError, ValueError):
            return False

    def status(self) -> dict[str, Any]:
        hermes = self.hermes_available() if self.settings.get("hermes_enabled", True) else False
        mpt = self.moneyprinter_available()
        return {"hermes": hermes, "moneyprinter": mpt, "mode": "hermes" if hermes else "local_fallback"}
