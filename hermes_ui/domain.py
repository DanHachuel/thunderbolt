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
        "youtube_channel_id": "",
        "google_account_id": "",
        "google_account_email": "",
        "name": name.strip(),
        "url": url.strip(),
        "handle": "",
        "description": "",
        "niche": "",
        "reference_channels": [],
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


def set_channel_defaults(channel_id: str, blueprint_id: str = "", voice: str = "") -> dict[str, Any] | None:
    """Persist the canonical and legacy aliases for a channel's generation defaults."""
    blueprint = str(blueprint_id or "").strip()
    selected_voice = str(voice or "").strip()
    return update_channel(channel_id, {
        "blueprint_id": blueprint,
        "default_blueprint_id": blueprint,
        "voice": selected_voice,
        "default_voice": selected_voice,
    })


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
    """Expand a batch into tasks, allowing independent payloads for each channel."""
    tasks = read_json("tasks.json", [])
    channels = {c["id"]: c for c in read_json("channels.json", [])}
    options = batch.get("options") or {}
    channel_payloads = options.get("channel_payloads") or {}
    target_channels = batch.get("channel_ids") or []
    count = max(1, int(batch.get("quantity") or 1))
    if batch.get("mode") == "general":
        count = 1
    created: list[dict[str, Any]] = []
    for channel_id in target_channels:
        channel = channels.get(channel_id, {})
        payload = channel_payloads.get(channel_id) if isinstance(channel_payloads, dict) else None
        payload = payload if isinstance(payload, dict) else {}
        for index in range(count):
            default_topic = str(batch.get("topic") or "").strip()
            if count == 1:
                topic = str(payload.get("topic") or default_topic).strip()
            else:
                topic = str(payload.get("topic") or f"{default_topic} — variação {index + 1}").strip()
            if not topic:
                topic = f"Vídeo para {channel.get('name', 'Canal')}"
            title = str(payload.get("title") or topic).strip()
            artifacts = dict(payload.get("artifacts") or {})
            thumbnail_path = str(payload.get("thumbnail_path") or "").strip()
            if thumbnail_path:
                artifacts.setdefault("thumbnail", thumbnail_path)
            task = {
                "id": make_id("video"),
                "batch_id": batch["id"],
                "creation_mode": batch.get("mode", "single"),
                "channel_id": channel_id,
                "channel_name": channel.get("name", "Canal"),
                "topic": topic,
                "title": title,
                "topic_source": str(payload.get("topic_source") or options.get("topic_source") or "manual"),
                "language": payload.get("language", options.get("language", channel.get("language", "Português"))),
                "format": payload.get("format", options.get("format", "wide")),
                "style_wide": payload.get("style_wide", options.get("style_wide", channel.get("style_wide", "pexels"))),
                "style_ia": payload.get("style_ia", options.get("style_ia", "")),
                "music_mode": payload.get("music_mode", options.get("music_mode", False)),
                "music_path": payload.get("music_path", options.get("music_path", "")),
                "music_source": payload.get("music_source", options.get("music_source", "")),
                "background_mode": payload.get("background_mode", options.get("background_mode", "stock")),
                "blueprint_id": payload.get("blueprint_id") or channel.get("default_blueprint_id") or channel.get("blueprint_id", ""),
                "blueprint_name": payload.get("blueprint_name", ""),
                "voice": payload.get("voice") or channel.get("default_voice") or channel.get("voice", ""),
                "automation_on": bool(channel.get("automation_on", False)),
                "automation_time": channel.get("automation_time", "00:00"),
                "thumbnail_variant": payload.get("thumbnail_variant", {}),
                "thumbnail_variants": payload.get("thumbnail_variants", []),
                "thumbnail_prompt": payload.get("thumbnail_prompt", ""),
                "thumbnail_text": payload.get("thumbnail_text", ""),
                "thumbnail_status": payload.get("thumbnail_status", "not_generated"),
                "title_candidates": payload.get("title_candidates", []),
                "ai_generation": payload.get("ai_generation", {}),
                "stage": "script",
                "state": "to_do",
                "progress": 0,
                "artifacts": artifacts,
                "error": None,
                "created_at": now(),
                "updated_at": now(),
            }
            tasks.append(task)
            created.append(task)
    write_json("tasks.json", tasks)
    queues = read_json("queues.json", {})
    if not isinstance(queues, dict):
        queues = {}
    queues.setdefault("script", [])
    queues["script"].extend(task["id"] for task in created)
    write_json("queues.json", queues)
    return created


def update_channel_video(video_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    """Actualizar um vídeo remoto sincronizado ou um override local de vídeo do canal."""
    videos = read_json("channel_videos.json", [])
    for video in videos:
        if video.get("id") == video_id:
            video.update(updates)
            video["updated_at"] = now()
            write_json("channel_videos.json", videos)
            return video
    return None


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
