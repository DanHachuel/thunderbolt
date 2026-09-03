"""Windows console compatibility for Click/Streamlit shutdown output."""
from __future__ import annotations

import io
import os
import sys
from typing import Any, Callable


_UTF8_ENV = {
    "CLICK_NO_WIN_CONSOLE": "1",
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUTF8": "1",
}


def _safe_click_echo(original: Callable[..., Any]) -> Callable[..., Any]:
    def echo(message: Any = None, file: Any = None, nl: bool = True, err: bool = False, color: Any = None) -> Any:
        target = file if file is not None else (sys.stderr if err else sys.stdout)
        if message is None:
            message = ""
        text = str(message) + ("\n" if nl else "")
        buffer = getattr(target, "buffer", None)
        try:
            if buffer is not None and hasattr(buffer, "write"):
                buffer.write(text.encode("utf-8", "replace"))
                if hasattr(buffer, "flush"):
                    buffer.flush()
            else:
                target.write(text)
                if hasattr(target, "flush"):
                    target.flush()
            return None
        except (AttributeError, OSError, UnicodeError, ValueError, LookupError):
            # Fall back to Click for non-console streams (files, testing runners).
            return original(message, file=file, nl=nl, err=err, color=color)

    echo.__name__ = getattr(original, "__name__", "echo")
    echo.__doc__ = getattr(original, "__doc__", None)
    return echo


def install(*, force: bool = False) -> None:
    """Install the Windows-safe Click output path before Streamlit imports Click."""
    os.environ.update(_UTF8_ENV)
    if not force and os.name != "nt":
        return
    try:
        import click
    except ImportError:
        return
    if getattr(click, "_thunderbolt_utf8_echo", False):
        return
    click.echo = _safe_click_echo(click.echo)
    click._thunderbolt_utf8_echo = True


def wrap_stream(stream: Any) -> Any:
    """Wrap a text stream as UTF-8 without closing its inherited buffer twice."""
    if stream is None or getattr(stream, "buffer", None) is None:
        return stream
    try:
        wrapper = io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        setattr(wrapper, "_thunderbolt_utf8", True)
        return wrapper
    except (AttributeError, OSError, ValueError):
        return stream
