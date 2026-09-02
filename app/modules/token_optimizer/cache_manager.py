"""Reversible local cache management for jusTokenMax-derived contexts."""

from __future__ import annotations

import shutil
from pathlib import Path

from hermes_ui import storage



def cache_directory() -> Path:
    return storage.STATE / "token_optimizer_originals"


def clear_derived_cache() -> int:
    directory = cache_directory()
    if not directory.exists():
        return 0
    count = sum(1 for item in directory.iterdir() if item.is_file())
    shutil.rmtree(directory, ignore_errors=True)
    return count
