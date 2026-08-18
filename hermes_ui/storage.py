from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STORAGE = Path(os.getenv("HERMES_STORAGE_DIR", ROOT / "storage"))
STATE = STORAGE / "state"
BLUEPRINTS = STORAGE / "blueprints"

DEFAULTS: dict[str, Any] = {
    "channels.json": [],
    "tasks.json": [],
    "queues.json": {"niche": [], "clone": [], "script": [], "title": [], "thumb": [], "video": [], "upload": []},
    "batches.json": [],
    "uploads.json": [],
    "settings.json": {
        "port": 3030,
        "hermes_url": "http://localhost:8765",
        "hermes_enabled": True,
        "moneyprinter_path": "",
        "script_interval_minutes": 10,
        "llm_rpm_limit": 40,
        "video_concurrency": 3,
        "upload_concurrency": 2,
        "youtube_api_key": "",
        "tiktok_client_key": "",
        "tiktok_client_secret": "",
        "tiktok_redirect_uri": "http://localhost:3030/oauth/tiktok/callback",
        "tiktok_scopes": "user.info.basic,video.publish,video.upload",
        "tiktok_access_token": "",
        "tiktok_connection_status": "not_configured",
    },
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_storage() -> None:
    for path in [STATE, BLUEPRINTS / "canais", BLUEPRINTS / "nichos", BLUEPRINTS / "importados", STORAGE / "brand", STORAGE / "scripts", STORAGE / "thumbnails", STORAGE / "videos", STORAGE / "artifacts"]:
        path.mkdir(parents=True, exist_ok=True)
    for filename, default in DEFAULTS.items():
        target = STATE / filename
        if not target.exists():
            atomic_write(target, default)


def atomic_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def read_json(name: str, default: Any | None = None) -> Any:
    ensure_storage()
    path = STATE / name
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        backup = path.with_suffix(path.suffix + f".corrupt-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        if path.exists():
            shutil.copy2(path, backup)
        fallback = DEFAULTS.get(name, [] if default is None else default)
        atomic_write(path, fallback)
        return fallback


def write_json(name: str, data: Any) -> None:
    ensure_storage()
    atomic_write(STATE / name, data)


def append_json(name: str, item: dict[str, Any]) -> dict[str, Any]:
    entries = read_json(name, [])
    if not isinstance(entries, list):
        entries = []
    entries.append(item)
    write_json(name, entries)
    return item


def list_blueprint_files() -> list[Path]:
    ensure_storage()
    return sorted(BLUEPRINTS.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def load_blueprint_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("O blueprint deve ser um objecto JSON.")
    return data
