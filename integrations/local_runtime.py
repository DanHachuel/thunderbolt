from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class MoneyPrinterRuntime:
    """Detecta apenas a instalação local do MoneyPrinterTurbo."""

    def __init__(self, settings: dict[str, Any]):
        self.settings = settings
        self.moneyprinter_path = Path(settings.get("moneyprinter_path", "") or os.getenv("MONEYPRINTER_PATH", ""))

    def moneyprinter_available(self) -> bool:
        return bool(self.moneyprinter_path and self.moneyprinter_path.exists())

    def status(self) -> dict[str, Any]:
        available = self.moneyprinter_available()
        return {
            "moneyprinter": available,
            "mode": "moneyprinter" if available else "not_configured",
            "moneyprinter_path": str(self.moneyprinter_path) if self.moneyprinter_path else "",
        }
