from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, tzinfo
from pathlib import Path
from typing import Any

from . import storage
from .creative_generation import generate_creative_package, generate_topic_for_channel
from .domain import create_batch, create_tasks_for_batch

WORKER_STATE_FILE = "automation_worker.json"
LOCK_FILENAME = "automation_worker.lock"
DEFAULT_INTERVAL_SECONDS = 10
DEFAULT_STATE: dict[str, Any] = {
    "worker_started_at": None,
    "worker_pid": None,
    "last_heartbeat_local": None,
    "last_tick_local": None,
    "last_error": "",
    "last_runs": {},
}


def _local_now() -> datetime:
    """Return the local wall-clock time of the computer running Thunderbolt."""
    return datetime.now().astimezone()


def _local_iso(value: datetime) -> str:
    return value.astimezone().isoformat(timespec="seconds")


def _state() -> dict[str, Any]:
    saved = storage.read_json(WORKER_STATE_FILE, DEFAULT_STATE)
    if not isinstance(saved, dict):
        saved = {}
    merged = {**DEFAULT_STATE, **saved}
    if not isinstance(merged.get("last_runs"), dict):
        merged["last_runs"] = {}
    return merged


def load_worker_status() -> dict[str, Any]:
    """Read status displayed by the Automação page without starting a worker."""
    status = _state()
    heartbeat = str(status.get("last_heartbeat_local") or "")
    status["alive"] = False
    if heartbeat:
        try:
            heartbeat_at = datetime.fromisoformat(heartbeat)
            status["alive"] = (datetime.now().astimezone() - heartbeat_at.astimezone()).total_seconds() <= 30
        except ValueError:
            status["alive"] = False
    return status


def _write_status(status: dict[str, Any]) -> None:
    storage.write_json(WORKER_STATE_FILE, {**DEFAULT_STATE, **status})


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _acquire_lock() -> Path | None:
    lock_path = storage.STORAGE / LOCK_FILENAME
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            old_pid = int(lock_path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            old_pid = 0
        if _pid_alive(old_pid):
            return None
        try:
            lock_path.unlink()
        except OSError:
            return None
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return None
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
    finally:
        os.close(descriptor)
    return lock_path


def _release_lock(lock_path: Path | None) -> None:
    if lock_path is not None:
        try:
            lock_path.unlink()
        except OSError:
            pass


def _valid_schedule(value: Any) -> bool:
    text = str(value or "").strip()
    if len(text) != 5 or text[2] != ":":
        return False
    try:
        hour, minute = (int(part) for part in text.split(":"))
    except ValueError:
        return False
    return 0 <= hour <= 23 and 0 <= minute <= 59


def _daily_quantity(channel: dict[str, Any]) -> int:
    try:
        return max(1, min(100, int(channel.get("daily_limit", 1))))
    except (TypeError, ValueError):
        return 1


def _blueprint_for_channel(channel: dict[str, Any]) -> dict[str, Any]:
    blueprint_id = str(channel.get("default_blueprint_id") or channel.get("blueprint_id") or "").strip()
    if not blueprint_id:
        return {}
    for path in storage.list_blueprint_files():
        try:
            data = storage.load_blueprint_file(path)
        except (OSError, ValueError):
            continue
        identifiers = {str(data.get("id") or ""), path.stem, str(data.get("name") or "")}
        if blueprint_id in identifiers:
            return data
    return {}


def _creative_payload(channel: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    settings = storage.read_json("settings.json", {})
    blueprint = _blueprint_for_channel(channel)
    user_context = str(channel.get("automation_topic") or "").strip()
    topic_package = generate_topic_for_channel(settings, channel, blueprint, user_context=user_context)
    creative = generate_creative_package(
        settings,
        channel,
        topic_package["topic"],
        blueprint,
        language=str(channel.get("language") or "Português"),
    )
    variant = creative["thumbnail_variant"]
    payload = {
        "topic": topic_package["topic"],
        "topic_source": "llm",
        "title": creative["title"],
        "title_candidates": creative["title_candidates"],
        "thumbnail_variant": variant,
        "thumbnail_variants": creative["thumbnail_variants"],
        "thumbnail_prompt": variant.get("image_prompt", ""),
        "thumbnail_text": variant.get("overlay_text", ""),
        "thumbnail_status": creative.get("thumbnail_status", "prompt_ready"),
        "blueprint_id": str(channel.get("default_blueprint_id") or channel.get("blueprint_id") or ""),
        "blueprint_name": str(blueprint.get("name") or "SEM BLUEPRINT CONFIGURADO"),
        "voice": str(channel.get("default_voice") or channel.get("voice") or ""),
        "ai_generation": {"topic": topic_package, "creative": creative},
    }
    return topic_package["topic"], payload


def _batch_for_day(channel_id: str, day: str) -> dict[str, Any] | None:
    batches = storage.read_json("batches.json", [])
    if not isinstance(batches, list):
        return None
    for batch in reversed(batches):
        if not isinstance(batch, dict) or channel_id not in (batch.get("channel_ids") or []):
            continue
        options = batch.get("options") or {}
        if options.get("automation_worker") is True and options.get("automation_date") == day:
            return batch
    return None


def _tasks_for_batch(batch_id: str) -> list[dict[str, Any]]:
    tasks = storage.read_json("tasks.json", [])
    return [task for task in tasks if isinstance(task, dict) and task.get("batch_id") == batch_id]


def _create_channel_batch(channel: dict[str, Any], when: datetime) -> dict[str, Any]:
    channel_id = str(channel["id"])
    date_key = when.date().isoformat()
    style_wide = str(channel.get("style_wide") or "pexels")
    music_mode = style_wide == "music"
    topic, payload = _creative_payload(channel)
    options = {
        "language": channel.get("language") or "Português",
        "format": "wide",
        "style_wide": style_wide,
        "style_ia": channel.get("style_ia") or "",
        "music_mode": music_mode,
        "background_mode": "none" if music_mode else ("ai" if style_wide == "full_ia" else "stock"),
        "music_path": channel.get("music_path") or "",
        "music_source": channel.get("music_source") or "",
        "topic_source": "llm",
        "channel_payloads": {channel_id: payload},
        "automation_worker": True,
        "automation_date": date_key,
        "automation_scheduled_at": _local_iso(when),
    }
    batch = create_batch("single", [channel_id], topic, _daily_quantity(channel), options)
    tasks = create_tasks_for_batch(batch)
    return {"batch": batch, "tasks": tasks, "channel_id": channel_id}


def run_once(when: datetime | None = None) -> dict[str, Any]:
    """Run one deterministic local-time tick; safe to call from tests or a worker loop."""
    current = when.astimezone() if when is not None and when.tzinfo else (when or _local_now())
    current_minute = current.strftime("%H:%M")
    day = current.date().isoformat()
    status = _state()
    status["last_tick_local"] = _local_iso(current)
    status["last_heartbeat_local"] = _local_iso(current)
    status["last_error"] = ""
    created: list[dict[str, Any]] = []
    skipped: list[str] = []
    channels = storage.read_json("channels.json", [])
    if not isinstance(channels, list):
        channels = []
    try:
        for channel in channels:
            if not isinstance(channel, dict):
                continue
            channel_id = str(channel.get("id") or "")
            if not channel_id or not bool(channel.get("active", True)) or not bool(channel.get("automation_on", False)):
                continue
            if not _valid_schedule(channel.get("automation_time")) or str(channel.get("automation_time")).strip() != current_minute:
                continue
            existing = _batch_for_day(channel_id, day)
            if existing:
                existing_tasks = _tasks_for_batch(str(existing.get("id") or ""))
                if not existing_tasks:
                    existing_tasks = create_tasks_for_batch(existing)
                skipped.append(channel_id)
                continue
            created.append(_create_channel_batch(channel, current))
        for item in created:
            batch = item["batch"]
            status["last_runs"][item["channel_id"]] = {
                "date": day,
                "time": current_minute,
                "batch_id": batch["id"],
                "task_ids": [task["id"] for task in item["tasks"]],
            }
        _write_status(status)
        return {
            "ok": True,
            "local_time": _local_iso(current),
            "scheduled_time": current_minute,
            "created": created,
            "skipped": skipped,
        }
    except Exception as exc:
        status["last_error"] = str(exc)
        _write_status(status)
        return {"ok": False, "local_time": _local_iso(current), "error": str(exc), "created": created}


def run_worker(interval_seconds: int = DEFAULT_INTERVAL_SECONDS) -> None:
    storage.ensure_storage()
    lock_path = _acquire_lock()
    if lock_path is None:
        raise RuntimeError("Já existe um worker de automação activo para este storage do Thunderbolt.")
    started = _local_now()
    status = _state()
    status.update({"worker_started_at": _local_iso(started), "worker_pid": os.getpid(), "last_error": ""})
    _write_status(status)
    try:
        while True:
            result = run_once()
            if not result.get("ok"):
                print(f"Thunderbolt worker: erro: {result.get('error')}", flush=True)
            elif result.get("created"):
                print(f"Thunderbolt worker: {len(result['created'])} canal(is) agendado(s) às {result['scheduled_time']}.", flush=True)
            time.sleep(max(2, int(interval_seconds)))
    finally:
        current = _state()
        current["worker_pid"] = None
        current["last_heartbeat_local"] = None
        _write_status(current)
        _release_lock(lock_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Worker local de automação diária do Thunderbolt")
    parser.add_argument("--once", action="store_true", help="Executa apenas um tick usando o relógio local")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SECONDS, help="Intervalo de verificação em segundos")
    args = parser.parse_args()
    if args.once:
        storage.ensure_storage()
        print(run_once(), flush=True)
        return
    run_worker(args.interval)


if __name__ == "__main__":
    main()
