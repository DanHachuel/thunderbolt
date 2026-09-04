from __future__ import annotations

import asyncio
import io
import logging
import os
import signal
import sys
import time

# Este ficheiro é o primeiro módulo Python executado pelo launcher. As
# variáveis e os streams precisam de ser corrigidos antes de qualquer import
# de streamlit/click, pois o erro utf-16-le acontece durante essa inicialização.
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "1"
os.environ["CLICK_NO_WIN_CONSOLE"] = "1"


# O shutdown do Streamlit pode emitir tracebacks assíncronos depois de SIGINT.
# Estes níveis só afectam a saída de encerramento, não os logs da aplicação.
logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
logging.getLogger("streamlit").setLevel(logging.CRITICAL)


def _utf8_stream(stream: object) -> object:
    if os.name != "nt":
        return stream
    buffer = getattr(stream, "buffer", None)
    if buffer is None:
        return stream
    try:
        return io.TextIOWrapper(buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except (AttributeError, OSError, ValueError):
        return stream


sys.stdout = _utf8_stream(sys.stdout)
sys.stderr = _utf8_stream(sys.stderr)


_shutdown_started = False


def _custom_sigint_handler(signum: int, frame: object) -> None:
    """Parar o loop, dar uma pequena janela de drenagem e sair sem traceback."""
    global _shutdown_started
    if _shutdown_started:
        return
    _shutdown_started = True
    print("\nEncerrando servidor...", file=sys.stderr, flush=True)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None and not loop.is_closed():
        loop.call_soon_threadsafe(loop.stop)
    # O processo pai (cli.mjs) encerra proxy e workers quando o filho termina.
    # os._exit evita que callbacks tardios do Streamlit imprimam tracebacks.
    time.sleep(0.5)
    os._exit(0)


_original_signal = signal.signal


def _protected_signal(signum: signal.Signals, handler: object) -> object:
    """Não permitir que Streamlit substitua o handler seguro de SIGINT."""
    if signum == signal.SIGINT:
        return _original_signal(signal.SIGINT, _custom_sigint_handler)
    return _original_signal(signum, handler)


_original_signal(signal.SIGINT, _custom_sigint_handler)
signal.signal = _protected_signal

from streamlit.web.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
