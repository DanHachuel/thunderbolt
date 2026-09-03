from __future__ import annotations

import io
import sys
from pathlib import Path

import click

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from windows_encoding_compat import install, wrap_stream  # noqa: E402


class Utf16Console:
    encoding = "utf-16-le"

    def __init__(self) -> None:
        self.buffer = io.BytesIO()

    def flush(self) -> None:
        self.buffer.flush()


def test_click_echo_never_uses_utf16_console_codec() -> None:
    original_echo = click.echo
    original_stdout = sys.stdout
    console = Utf16Console()
    try:
        sys.stdout = console  # type: ignore[assignment]
        install(force=True)
        click.echo("Stopping...")
        assert console.buffer.getvalue() == b"Stopping...\n"
    finally:
        click.echo = original_echo
        if getattr(click, "_thunderbolt_utf8_echo", False):
            delattr(click, "_thunderbolt_utf8_echo")
        sys.stdout = original_stdout


def test_wrap_stream_replaces_utf16_stream_with_utf8() -> None:
    stream = Utf16Console()
    wrapped = wrap_stream(stream)
    assert wrapped is not stream
    assert wrapped.encoding == "utf-8"
    wrapped.write("Stopping...")
    wrapped.flush()
    assert stream.buffer.getvalue() == b"Stopping..."


def test_bootstrap_installs_compatibility_before_streamlit_import() -> None:
    source = (SCRIPTS / "streamlit_bootstrap.py").read_text(encoding="utf-8")
    assert source.index("install_windows_encoding()") < source.index("from streamlit.web.cli import main")
    assert source.index("os.environ[\"CLICK_NO_WIN_CONSOLE\"]") < source.index("from streamlit.web.cli import main")


def test_bootstrap_registers_custom_sigint_before_streamlit_main() -> None:
    source = (SCRIPTS / "streamlit_bootstrap.py").read_text(encoding="utf-8")
    handler = source.index("def custom_sigint_handler")
    registration = source.index("signal.signal(signal.SIGINT, custom_sigint_handler)")
    streamlit_main = source.index("from streamlit.web.cli import main")
    assert handler > streamlit_main
    assert registration > handler
    assert "raise SystemExit(0)" in source
    assert "Encerrando servidor..." in source
