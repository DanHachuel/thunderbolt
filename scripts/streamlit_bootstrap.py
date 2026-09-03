from __future__ import annotations

import os
import sys
from windows_encoding_compat import install as install_windows_encoding, wrap_stream

# Este ficheiro é o primeiro módulo Python executado pelo launcher. As
# variáveis e os streams precisam de ser corrigidos antes de qualquer import
# de streamlit/click, pois o erro utf-16-le acontece durante essa inicialização.
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "1"
os.environ["CLICK_NO_WIN_CONSOLE"] = "1"
install_windows_encoding()


def _utf8_stream(stream: object) -> object:
    if os.name != "nt":
        return stream
    buffer = getattr(stream, "buffer", None)
    if buffer is None:
        return stream
    try:
        return wrap_stream(stream)
    except (AttributeError, OSError, ValueError):
        return stream


sys.stdout = _utf8_stream(sys.stdout)
sys.stderr = _utf8_stream(sys.stderr)

from streamlit.web.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
