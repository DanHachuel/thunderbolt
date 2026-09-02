from __future__ import annotations

import io
import os
import sys

# Este ficheiro é o primeiro módulo Python executado pelo launcher. As
# variáveis e os streams precisam de ser corrigidos antes de qualquer import
# de streamlit/click, pois o erro utf-16-le acontece durante essa inicialização.
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "1"
os.environ["CLICK_NO_WIN_CONSOLE"] = "1"


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

from streamlit.web.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
