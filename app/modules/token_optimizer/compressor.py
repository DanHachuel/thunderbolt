"""Safe adapter around the official jusTokenMax Python package."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from hermes_ui import storage


@dataclass(frozen=True)
class TokenOptimizationResult:
    content: str
    original_hash: str
    before_chars: int
    after_chars: int
    kind: str
    applied: bool
    fallback: bool = False
    note: str = ""


def _settings() -> dict[str, Any]:
    value = storage.read_json("settings.json", {})
    return value if isinstance(value, dict) else {}


def _enabled(settings: Mapping[str, Any], kind: str) -> bool:
    if not bool(settings.get("token_optimizer_enabled", True)):
        return False
    return bool(settings.get(f"token_optimizer_{kind}_enabled", True))


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _record(result: TokenOptimizationResult) -> None:
    path = storage.STATE / "token_optimizer_metrics.json"
    current = storage.read_json("token_optimizer_metrics.json", {"calls": 0, "applied": 0, "fallbacks": 0, "before_chars": 0, "after_chars": 0})
    if not isinstance(current, dict):
        current = {"calls": 0, "applied": 0, "fallbacks": 0, "before_chars": 0, "after_chars": 0}
    current["calls"] = int(current.get("calls", 0)) + 1
    current["applied"] = int(current.get("applied", 0)) + int(result.applied)
    current["fallbacks"] = int(current.get("fallbacks", 0)) + int(result.fallback)
    current["before_chars"] = int(current.get("before_chars", 0)) + result.before_chars
    current["after_chars"] = int(current.get("after_chars", 0)) + result.after_chars
    storage.write_json(path.name, current)


def _cache_original(content: str, digest: str) -> None:
    directory = storage.STATE / "token_optimizer_originals"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{digest}.txt"
    if not target.exists():
        target.write_text(content, encoding="utf-8")


def _compress_with_jus_token_max(content: str, kind: str) -> str:
    from justokenmax.jsoncompress import compress_json
    from justokenmax.logs import compress_log
    from justokenmax.redact import mask_secrets

    redacted, _ = mask_secrets(content)
    redacted = re.sub(
        r'(["\'](?:api[_-]?key|token|password|secret)["\']\s*:\s*["\'])([^"\']+)(["\'])',
        r'\1****\3', redacted, flags=re.IGNORECASE,
    )
    if kind == "json":
        compressed, _stats = compress_json(redacted)
        return compressed
    if kind == "log":
        compressed, _stats = compress_log(redacted)
        return compressed
    return redacted


def compress_text(text: str, content_type: str = "auto", *, settings: Mapping[str, Any] | None = None) -> TokenOptimizationResult:
    raw = str(text or "")
    kind = str(content_type or "auto").strip().casefold()
    if kind == "auto":
        try:
            json.loads(raw)
            kind = "json"
        except (TypeError, ValueError):
            kind = "text"
    if kind not in {"json", "log"} or not _enabled(settings or _settings(), kind):
        result = TokenOptimizationResult(raw, _hash(raw), len(raw), len(raw), kind, False, note="disabled_or_unsupported")
        _record(result)
        return result
    if len(raw) < 8000:
        result = TokenOptimizationResult(raw, _hash(raw), len(raw), len(raw), kind, False, note="below_minimum_size")
        _record(result)
        return result
    digest = _hash(raw)
    try:
        optimized = _compress_with_jus_token_max(raw, kind)
        if not optimized or len(optimized) >= len(raw):
            result = TokenOptimizationResult(raw, digest, len(raw), len(raw), kind, False, note="no_reduction")
        else:
            _cache_original(raw, digest)
            result = TokenOptimizationResult(optimized, digest, len(raw), len(optimized), kind, True)
    except (ImportError, OSError, RuntimeError, TypeError, ValueError) as exc:
        result = TokenOptimizationResult(raw, digest, len(raw), len(raw), kind, False, True, f"jusTokenMax indisponível: {type(exc).__name__}")
    _record(result)
    return result


def compress_payload(payload: Any, *, settings: Mapping[str, Any] | None = None) -> TokenOptimizationResult:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    result = compress_text(raw, "json", settings=settings)
    if result.applied:
        return result
    return result


def retrieve_original(original_hash: str) -> str | None:
    digest = str(original_hash or "").strip().lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        return None
    path = storage.STATE / "token_optimizer_originals" / f"{digest}.txt"
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def check_installation() -> dict[str, Any]:
    try:
        import importlib.metadata
        return {"installed": True, "version": importlib.metadata.version("justokenmax")}
    except (ImportError, importlib.metadata.PackageNotFoundError):
        return {"installed": False, "version": "", "message": "Instale o jusTokenMax para activar a compressão nativa."}
