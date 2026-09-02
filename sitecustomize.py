"""Process-wide UTF-8 protection for Windows terminals and MobaXterm."""
from __future__ import annotations

import os
import sys
import io

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

for stream_name in ("stdin", "stdout", "stderr"):
    stream = getattr(sys, stream_name, None)
    buffer = getattr(stream, "buffer", None) if stream is not None else None
    encoding = str(getattr(stream, "encoding", "") or "").lower().replace("-", "_") if stream is not None else ""
    if buffer is not None and encoding != "utf_8":
        try:
            replacement = io.TextIOWrapper(buffer, encoding="utf-8", errors="replace", line_buffering=True)
            setattr(sys, stream_name, replacement)
        except (OSError, ValueError):
            pass
    elif stream is not None and hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass
