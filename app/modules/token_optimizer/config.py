"""Persistent token optimizer settings."""

from __future__ import annotations

from typing import Any

from hermes_ui import storage


DEFAULTS = {
    "token_optimizer_enabled": True,
    "token_optimizer_json_enabled": True,
    "token_optimizer_log_enabled": True,
    "token_optimizer_pdf_enabled": True,
    "token_optimizer_csv_enabled": True,
    "token_optimizer_diff_enabled": True,
    "token_optimizer_code_enabled": True,
    "token_optimizer_redact_enabled": True,
}


def load(settings: dict[str, Any] | None = None) -> dict[str, Any]:
    result = dict(DEFAULTS)
    source = settings if isinstance(settings, dict) else storage.read_json("settings.json", {})
    if isinstance(source, dict):
        result.update({key: source.get(key, value) for key, value in DEFAULTS.items()})
    return result


def save(values: dict[str, Any]) -> dict[str, Any]:
    current = storage.read_json("settings.json", {})
    if not isinstance(current, dict):
        current = {}
    current.update({key: bool(values.get(key, default)) for key, default in DEFAULTS.items()})
    storage.write_json("settings.json", current)
    return current
