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
SEED_BLUEPRINTS = ROOT / "seed" / "blueprints"

DEFAULTS: dict[str, Any] = {
    "channels.json": [],
    "tasks.json": [],
    "queues.json": {"niche": [], "clone": [], "script": [], "title": [], "thumb": [], "video": [], "upload": []},
    "batches.json": [],
    "uploads.json": [],
    "metadata_edits.json": [],
    "settings.json": {
        "port": 3030,
        "moneyprinter_path": "",
        "script_interval_minutes": 10,
        "llm_rpm_limit": 40,
        "video_concurrency": 3,
        "upload_concurrency": 2,
        "youtube_api_key": "",
        "llm_provider": "moonshot",
        "moonshot_api_key": "",
        "moonshot_base_url": "",
        "moonshot_model_name": "",
        "shengsuanyun_api_key": "",
        "shengsuanyun_base_url": "",
        "shengsuanyun_model_name": "",
        "openai_api_key": "",
        "openai_base_url": "",
        "openai_model_name": "",
        "gemini_api_key": "",
        "gemini_model_name": "",
        "deepseek_api_key": "",
        "deepseek_base_url": "",
        "deepseek_model_name": "",
        "qwen_api_key": "",
        "qwen_model_name": "",
        "azure_api_key": "",
        "azure_base_url": "",
        "azure_model_name": "",
        "azure_api_version": "2024-02-15-preview",
        "volcengine_api_key": "",
        "volcengine_base_url": "",
        "volcengine_model_name": "",
        "grok_api_key": "",
        "grok_base_url": "",
        "grok_model_name": "",
        "minimax_api_key": "",
        "minimax_base_url": "",
        "minimax_model_name": "",
        "mimo_api_key": "",
        "mimo_base_url": "",
        "mimo_model_name": "",
        "cloudflare_api_key": "",
        "cloudflare_account_id": "",
        "cloudflare_gateway_id": "",
        "cloudflare_model_name": "",
        "modelscope_api_key": "",
        "modelscope_base_url": "",
        "modelscope_model_name": "",
        "aihubmix_api_key": "",
        "aihubmix_base_url": "",
        "aihubmix_model_name": "",
        "aimlapi_api_key": "",
        "aimlapi_base_url": "",
        "aimlapi_model_name": "",
        "evolink_api_key": "",
        "evolink_base_url": "",
        "evolink_model_name": "",
        "ollama_base_url": "",
        "ollama_model_name": "",
        "oneapi_api_key": "",
        "oneapi_base_url": "",
        "oneapi_model_name": "",
        "litellm_model_name": "",
        "groq_api_key": "",
        "groq_base_url": "",
        "groq_model_name": "",
        "pollinations_api_key": "",
        "pollinations_base_url": "",
        "pollinations_model_name": "",
        "log_level": "DEBUG",
        "listen_host": "127.0.0.1",
        "listen_port": 8080,
        "video_source": "pexels",
        "match_materials_to_script": False,
        "endpoint": "",
        "proxy_http": "",
        "proxy_https": "",
        "pexels_api_keys": "",
        "pixabay_api_keys": "",
        "coverr_api_keys": "",
        "twelvelabs_api_keys": "",
        "sonilo_api_key": "",
        "subtitle_provider": "edge",
        "ffmpeg_path": "",
        "video_codec": "",
        "material_directory": "",
        "whisper_model_size": "large-v3",
        "whisper_device": "cpu",
        "whisper_compute_type": "int8",
        "azure_speech_key": "",
        "azure_speech_region": "",
        "siliconflow_tts_api_key": "",
        "minimax_tts_api_key": "",
        "minimax_tts_base_url": "",
        "minimax_tts_model_id": "speech-2.8-hd",
        "minimax_tts_voice_id": "English_expressive_narrator",
        "elevenlabs_api_key": "",
        "elevenlabs_model_id": "eleven_multilingual_v2",
        "chatterbox_base_url": "http://127.0.0.1:4123/v1",
        "chatterbox_api_key": "",
        "chatterbox_model_id": "chatterbox",
        "upload_post_enabled": False,
        "upload_post_api_key": "",
        "upload_post_username": "",
        "upload_post_platforms": "tiktok,instagram",
        "upload_post_auto_upload": False,
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


def seed_blueprints() -> None:
    """Copy packaged seed Blueprints without overwriting local user files."""
    if not SEED_BLUEPRINTS.exists():
        return
    destination = BLUEPRINTS / "importados"
    destination.mkdir(parents=True, exist_ok=True)
    for source in sorted(SEED_BLUEPRINTS.glob("*.json")):
        target = destination / source.name
        if not target.exists():
            shutil.copy2(source, target)


def ensure_storage() -> None:
    for path in [STATE, BLUEPRINTS / "canais", BLUEPRINTS / "nichos", BLUEPRINTS / "importados", BLUEPRINTS / "brandings", STORAGE / "brand", STORAGE / "scripts", STORAGE / "thumbnails", STORAGE / "videos", STORAGE / "artifacts", STORAGE / "metadata_cleaner", STORAGE / "metadata_cleaner" / "outputs"]:
        path.mkdir(parents=True, exist_ok=True)
    seed_blueprints()
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
