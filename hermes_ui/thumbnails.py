from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any

from .storage import STORAGE, now, read_json, write_json
from .thumbnail_generation import ThumbnailGenerationError, generate_thumbnail_image


def _as_path(value: Any) -> Path | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    candidates = [Path(raw)]
    path = Path(raw)
    if not path.is_absolute():
        candidates.extend([STORAGE / path, STORAGE.parent / path])
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return Path(raw)


def _variant_index(task: dict[str, Any], variant: dict[str, Any], variants: list[Any]) -> int:
    for key in ("variant_index", "index"):
        try:
            value = int(variant.get(key))
        except (TypeError, ValueError):
            continue
        if 0 <= value < len(variants):
            return value
    for index, candidate in enumerate(variants):
        if isinstance(candidate, dict) and candidate is variant:
            return index
        if isinstance(candidate, dict) and variant and candidate.get("image_prompt") == variant.get("image_prompt"):
            return index
    return 0


def normalize_thumbnail_task(task: dict[str, Any]) -> dict[str, Any]:
    variants = task.get("thumbnail_variants") if isinstance(task.get("thumbnail_variants"), list) else []
    variant = task.get("thumbnail_variant") if isinstance(task.get("thumbnail_variant"), dict) else {}
    artifacts = task.get("artifacts") if isinstance(task.get("artifacts"), dict) else {}
    image_path = variant.get("image_path") or task.get("thumbnail_path") or artifacts.get("thumbnail")
    prompt = variant.get("image_prompt") or task.get("thumbnail_prompt") or ""
    title = str(task.get("title") or task.get("topic") or "Vídeo sem título").strip()
    return {
        "task": task,
        "task_id": str(task.get("id") or ""),
        "title": title,
        "topic": str(task.get("topic") or "").strip(),
        "channel_name": str(task.get("channel_name") or "Canal sem nome").strip(),
        "status": str(task.get("thumbnail_status") or "not_generated"),
        "prompt": str(prompt or "").strip(),
        "image_path": _as_path(image_path),
        "variant": variant,
        "variants": variants,
        "variant_index": _variant_index(task, variant, variants),
    }


def list_thumbnail_tasks() -> list[dict[str, Any]]:
    tasks = read_json("tasks.json", [])
    if not isinstance(tasks, list):
        return []
    records = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        record = normalize_thumbnail_task(task)
        has_thumbnail_signal = bool(
            record["image_path"]
            or record["prompt"]
            or task.get("thumbnail_status")
            or task.get("thumbnail_variant")
            or task.get("thumbnail_variants")
        )
        if record["task_id"] and has_thumbnail_signal:
            records.append(record)
    return records


def regenerate_thumbnail(task_id: str, settings: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    tasks = read_json("tasks.json", [])
    if not isinstance(tasks, list):
        raise ThumbnailGenerationError("O índice de tarefas não está disponível.")
    for task in tasks:
        if not isinstance(task, dict) or str(task.get("id") or "") != str(task_id):
            continue
        record = normalize_thumbnail_task(task)
        if not record["prompt"]:
            raise ThumbnailGenerationError("Esta tarefa não tem um prompt de imagem para refazer a thumbnail.")
        previous_image = record.get("image_path")
        if previous_image and previous_image.is_file():
            history_dir = STORAGE / "thumbnails" / "history"
            history_dir.mkdir(parents=True, exist_ok=True)
            history_path = history_dir / f"{task_id}-{uuid.uuid4().hex[:10]}-{previous_image.name}"
            shutil.copy2(previous_image, history_path)
        image_path = generate_thumbnail_image(
            settings,
            record["prompt"],
            topic=record["title"] or record["topic"],
            variant_index=record["variant_index"],
        )
        artifacts = dict(task.get("artifacts") or {})
        artifacts["thumbnail"] = str(image_path)
        task["artifacts"] = artifacts
        task["thumbnail_path"] = str(image_path)
        task["thumbnail_status"] = "generated"
        variant = dict(record["variant"])
        if variant:
            variant["image_path"] = str(image_path)
            task["thumbnail_variant"] = variant
        variants = task.get("thumbnail_variants")
        if isinstance(variants, list) and 0 <= record["variant_index"] < len(variants) and isinstance(variants[record["variant_index"]], dict):
            variants[record["variant_index"]] = {**variants[record["variant_index"]], "image_path": str(image_path)}
            task["thumbnail_variants"] = variants
        task["updated_at"] = now()
        write_json("tasks.json", tasks)
        return task, image_path
    raise ThumbnailGenerationError(f"A tarefa {task_id} não foi encontrada.")


__all__ = ["list_thumbnail_tasks", "normalize_thumbnail_task", "regenerate_thumbnail"]

