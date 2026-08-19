from __future__ import annotations

import re
import uuid
from typing import Any

from .storage import append_json, now, read_json, write_json

STAGES = ["niche", "blueprint", "brand", "script", "title", "thumbnail", "video", "edit", "upload"]
VALID_STATES = {"to_do", "doing", "blocked", "done", "failed", "cancelled"}


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9À-ÿ]+", "-", value.strip().lower()).strip("-")
    return value or "item"


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def create_channel(name: str, url: str = "", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    channel = {
        "id": make_id("channel"),
        "name": name.strip(),
        "url": url.strip(),
        "handle": "",
        "description": "",
        "thumbnail_url": "",
        "subscriber_count": None,
        "video_count": None,
        "view_count": None,
        "metrics_source": "manual",
        "last_youtube_sync": None,
        "language": "Português",
        "blueprint_id": "",
        "default_blueprint_id": "",
        "style_wide": "pexels",
        "voice": "",
        "default_voice": "",
        "delegated_session_id": "",
        "automation_on": False,
        "automation_time": "00:00",
        "active": True,
        "daily_limit": 1,
        "backlog_total": 0,
        "created_at": now(),
        "updated_at": now(),
    }
    if metadata:
        channel.update({k: v for k, v in metadata.items() if k in channel})
    channels = read_json("channels.json", [])
    channels.append(channel)
    write_json("channels.json", channels)
    return channel


def update_channel(channel_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    channels = read_json("channels.json", [])
    for channel in channels:
        if channel.get("id") == channel_id:
            channel.update(updates)
            channel["updated_at"] = now()
            write_json("channels.json", channels)
            return channel
    return None


def delete_channel(channel_id: str) -> dict[str, Any] | None:
    """Remove apenas o cadastro do canal, preservando tarefas e artefactos."""
    channels = read_json("channels.json", [])
    remaining = [channel for channel in channels if channel.get("id") != channel_id]
    if len(remaining) == len(channels):
        return None
    removed = next(channel for channel in channels if channel.get("id") == channel_id)
    write_json("channels.json", remaining)
    return removed


def create_batch(mode: str, channel_ids: list[str], topic: str, quantity: int, options: dict[str, Any]) -> dict[str, Any]:
    batch = {
        "id": make_id("batch"),
        "mode": mode,
        "channel_ids": channel_ids,
        "topic": topic.strip(),
        "quantity": quantity,
        "status": "to_do",
        "created_at": now(),
        "options": options,
    }
    append_json("batches.json", batch)
    return batch


def create_tasks_for_batch(batch: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = read_json("tasks.json", [])
    channels = {c["id"]: c for c in read_json("channels.json", [])}
    target_channels = batch["channel_ids"]
    count = batch["quantity"]
    if batch["mode"] == "general":
        count = 1
    created: list[dict[str, Any]] = []
    for channel_id in target_channels:
        for index in range(count):
            channel = channels.get(channel_id, {})
            task = {
                "id": make_id("video"),
                "batch_id": batch["id"],
                "creation_mode": batch["mode"],
                "channel_id": channel_id,
                "channel_name": channel.get("name", "Canal"),
                "topic": batch["topic"] if count == 1 else f"{batch['topic']} — variação {index + 1}",
                "language": batch["options"].get("language", channel.get("language", "Português")),
                "format": batch["options"].get("format", "wide"),
                "style_wide": batch["options"].get("style_wide", channel.get("style_wide", "pexels")),
                "style_ia": batch["options"].get("style_ia", ""),
                "music_mode": batch["options"].get("music_mode", False),
                "music_path": batch["options"].get("music_path", ""),
                "music_source": batch["options"].get("music_source", ""),
                "background_mode": batch["options"].get("background_mode", "stock"),
                "blueprint_id": channel.get("default_blueprint_id") or channel.get("blueprint_id", ""),
                "voice": channel.get("default_voice") or channel.get("voice", ""),
                "automation_on": bool(channel.get("automation_on", False)),
                "automation_time": channel.get("automation_time", "00:00"),
                "stage": "script",
                "state": "to_do",
                "progress": 0,
                "artifacts": {},
                "error": None,
                "created_at": now(),
                "updated_at": now(),
            }
            tasks.append(task)
            created.append(task)
    write_json("tasks.json", tasks)
    for task in created:
        queues = read_json("queues.json", {})
        queues.setdefault("script", []).append(task["id"])
        write_json("queues.json", queues)
    return created


def update_task(task_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    tasks = read_json("tasks.json", [])
    for task in tasks:
        if task.get("id") == task_id:
            task.update(updates)
            task["updated_at"] = now()
            write_json("tasks.json", tasks)
            return task
    return None


def transition_task(task_id: str, state: str | None = None, stage: str | None = None, error: str | None = None) -> dict[str, Any] | None:
    if state and state not in VALID_STATES:
        raise ValueError(f"Estado inválido: {state}")
    tasks = read_json("tasks.json", [])
    for task in tasks:
        if task.get("id") == task_id:
            if state:
                task["state"] = state
            if stage:
                if stage not in STAGES:
                    raise ValueError(f"Etapa inválida: {stage}")
                task["stage"] = stage
            if error is not None:
                task["error"] = error
            task["updated_at"] = now()
            write_json("tasks.json", tasks)
            return task
    return None


def pipeline_summary() -> dict[str, Any]:
    tasks = read_json("tasks.json", [])
    channels = read_json("channels.json", [])
    return {
        "channels": len(channels),
        "active_channels": sum(1 for c in channels if c.get("active")),
        "total_tasks": len(tasks),
        "done": sum(1 for t in tasks if t.get("state") == "done"),
        "pending": sum(1 for t in tasks if t.get("state") in {"to_do", "doing", "blocked"}),
        "failed": sum(1 for t in tasks if t.get("state") == "failed"),
        "doing": sum(1 for t in tasks if t.get("state") == "doing"),
    }
