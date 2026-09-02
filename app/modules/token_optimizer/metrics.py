"""Local metrics for token optimization effectiveness."""

from __future__ import annotations

from typing import Any

from hermes_ui import storage


def get_stats() -> dict[str, Any]:
    value = storage.read_json("token_optimizer_metrics.json", {})
    stats = value if isinstance(value, dict) else {}
    before = int(stats.get("before_chars", 0) or 0)
    after = int(stats.get("after_chars", 0) or 0)
    return {
        "calls": int(stats.get("calls", 0) or 0),
        "applied": int(stats.get("applied", 0) or 0),
        "fallbacks": int(stats.get("fallbacks", 0) or 0),
        "before_chars": before,
        "after_chars": after,
        "reduction_percent": round(max(0, before - after) * 100 / before, 2) if before else 0.0,
    }
