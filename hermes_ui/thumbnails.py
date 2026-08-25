from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any

from .creative_generation import generate_thumbnail_prompt
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
        "channel_id": str(task.get("channel_id") or "").strip(),
        "channel_name": str(task.get("channel_name") or "Canal sem nome").strip(),
        "blueprint_id": str(task.get("blueprint_id") or "").strip(),
        "blueprint_name": str(task.get("blueprint_name") or "").strip(),
        "status": str(task.get("thumbnail_status") or "not_generated"),
        "prompt": str(prompt or "").strip(),
        "image_path": _as_path(image_path),
        "variant": variant,
        "variants": variants,
        "variant_index": _variant_index(task, variant, variants),
        "thumbnail_text": str(variant.get("overlay_text") or task.get("thumbnail_text") or "").strip(),
        "lettering_prompt": str(variant.get("lettering_prompt") or task.get("thumbnail_lettering_prompt") or "").strip(),
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


def _archive_image(task_id: str, image_path: Path | None) -> Path | None:
    if not image_path or not image_path.is_file():
        return None
    history_dir = STORAGE / "thumbnails" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    history_path = history_dir / f"{task_id}-{uuid.uuid4().hex[:10]}-{image_path.name}"
    shutil.copy2(image_path, history_path)
    return history_path


def _variant_for_record(record: dict[str, Any]) -> dict[str, Any]:
    variant = dict(record.get("variant") or {})
    variants = record.get("variants") if isinstance(record.get("variants"), list) else []
    index = int(record.get("variant_index") or 0)
    if not variant and 0 <= index < len(variants) and isinstance(variants[index], dict):
        variant = dict(variants[index])
    return variant


def _persist_thumbnail_result(
    tasks: list[dict[str, Any]],
    task: dict[str, Any],
    record: dict[str, Any],
    image_path: Path,
    *,
    variant: dict[str, Any] | None = None,
    source: str = "generated",
    lettering_prompt: str = "",
) -> dict[str, Any]:
    selected_variant = _variant_for_record(record)
    if variant:
        selected_variant.update({key: value for key, value in variant.items() if value is not None})
    selected_variant["image_path"] = str(image_path)
    selected_variant["status"] = "generated"
    selected_variant.setdefault("image_prompt", record.get("prompt") or "")
    task["thumbnail_variant"] = selected_variant
    variants = task.get("thumbnail_variants")
    if not isinstance(variants, list):
        variants = []
    variants = list(variants)
    index = int(record.get("variant_index") or 0)
    while len(variants) <= index:
        variants.append({})
    variants[index] = {**(variants[index] if isinstance(variants[index], dict) else {}), **selected_variant}
    task["thumbnail_variants"] = variants
    task["thumbnail_prompt"] = str(selected_variant.get("image_prompt") or record.get("prompt") or "")
    task["thumbnail_text"] = str(selected_variant.get("overlay_text") or task.get("thumbnail_text") or "")
    if lettering_prompt:
        task["thumbnail_lettering_prompt"] = lettering_prompt
    task["thumbnail_source"] = source
    task["thumbnail_status"] = "generated"
    artifacts = dict(task.get("artifacts") or {})
    artifacts["thumbnail"] = str(image_path)
    task["artifacts"] = artifacts
    task["thumbnail_path"] = str(image_path)
    task["updated_at"] = now()
    return task


def _persist_thumbnail_prompt_result(
    task: dict[str, Any],
    record: dict[str, Any],
    variant: dict[str, Any],
) -> dict[str, Any]:
    """Persist a prompt-only update while leaving the active image and artifacts untouched."""
    selected_variant = _variant_for_record(record)
    selected_variant.update({key: value for key, value in variant.items() if value is not None})
    if record.get("image_path"):
        selected_variant.setdefault("image_path", str(record["image_path"]))
    selected_variant["status"] = "prompt_ready"
    variants = task.get("thumbnail_variants")
    if not isinstance(variants, list):
        variants = []
    variants = list(variants)
    index = int(record.get("variant_index") or 0)
    while len(variants) <= index:
        variants.append({})
    variants[index] = {
        **(variants[index] if isinstance(variants[index], dict) else {}),
        **selected_variant,
    }
    task["thumbnail_variant"] = selected_variant
    task["thumbnail_variants"] = variants
    task["thumbnail_prompt"] = str(selected_variant.get("image_prompt") or "")
    task["thumbnail_text"] = str(selected_variant.get("overlay_text") or task.get("thumbnail_text") or "")
    task["thumbnail_lettering_prompt"] = str(
        selected_variant.get("lettering_prompt") or task.get("thumbnail_lettering_prompt") or ""
    )
    task["thumbnail_source"] = "prompt_regenerated"
    task["thumbnail_status"] = "prompt_ready"
    task["updated_at"] = now()
    return task


def _find_task(tasks: list[Any], task_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    for task in tasks:
        if isinstance(task, dict) and str(task.get("id") or "") == str(task_id):
            return task, normalize_thumbnail_task(task)
    raise ThumbnailGenerationError(f"A tarefa {task_id} não foi encontrada.")


def generate_thumbnail_for_task(task_id: str, settings: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    """Generate an image from the task's current prompt and persist it on the task."""
    tasks = read_json("tasks.json", [])
    if not isinstance(tasks, list):
        raise ThumbnailGenerationError("O índice de tarefas não está disponível.")
    task, record = _find_task(tasks, task_id)
    if not record["prompt"]:
        raise ThumbnailGenerationError("A thumbnail não tem um prompt de imagem para gerar.")
    _archive_image(str(task_id), record.get("image_path"))
    image_path = generate_thumbnail_image(
        settings,
        record["prompt"],
        topic=record["title"] or record["topic"],
        variant_index=record["variant_index"],
        lettering_text=record.get("thumbnail_text") or "",
        lettering_prompt=record.get("lettering_prompt") or "",
    )
    _persist_thumbnail_result(tasks, task, record, image_path)
    write_json("tasks.json", tasks)
    return task, image_path


def regenerate_thumbnail_prompt(
    task_id: str,
    settings: dict[str, Any],
    channel: dict[str, Any],
    blueprint: dict[str, Any] | None = None,
    language: str = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Regenerate and persist only the thumbnail prompt, keeping the existing image unchanged."""
    tasks = read_json("tasks.json", [])
    if not isinstance(tasks, list):
        raise ThumbnailGenerationError("O índice de tarefas não está disponível.")
    task, record = _find_task(tasks, task_id)
    topic = record["topic"] or record["title"]
    if not topic:
        raise ThumbnailGenerationError("A tarefa não tem tópico para refazer o prompt da thumbnail.")
    variant = generate_thumbnail_prompt(
        settings,
        channel or {},
        topic,
        current_prompt=record["prompt"],
        blueprint=blueprint,
        language=language,
    )
    _persist_thumbnail_prompt_result(task, record, variant)
    write_json("tasks.json", tasks)
    return task, variant


def regenerate_thumbnail_prompt_and_image(
    task_id: str,
    settings: dict[str, Any],
    variant: dict[str, Any],
) -> tuple[dict[str, Any], Path]:
    """Persist a newly generated prompt and render its image as one atomic task update."""
    tasks = read_json("tasks.json", [])
    if not isinstance(tasks, list):
        raise ThumbnailGenerationError("O índice de tarefas não está disponível.")
    task, record = _find_task(tasks, task_id)
    prompt = str((variant or {}).get("image_prompt") or "").strip()
    if not prompt:
        raise ThumbnailGenerationError("O provider não devolveu um prompt de imagem válido.")
    _archive_image(str(task_id), record.get("image_path"))
    image_path = generate_thumbnail_image(
        settings,
        prompt,
        topic=record["title"] or record["topic"],
        variant_index=record["variant_index"],
        lettering_text=str((variant or {}).get("overlay_text") or ""),
        lettering_prompt=str((variant or {}).get("lettering_prompt") or ""),
    )
    _persist_thumbnail_result(tasks, task, record, image_path, variant=variant, source="prompt_regenerated")
    write_json("tasks.json", tasks)
    return task, image_path


def regenerate_thumbnail_lettering(
    task_id: str,
    settings: dict[str, Any],
    lettering_prompt: str = "",
) -> tuple[dict[str, Any], Path]:
    """Edit only the lettering while sending the existing image as a Nano Banana reference."""
    tasks = read_json("tasks.json", [])
    if not isinstance(tasks, list):
        raise ThumbnailGenerationError("O índice de tarefas não está disponível.")
    task, record = _find_task(tasks, task_id)
    previous_image = record.get("image_path")
    if not previous_image or not previous_image.is_file():
        raise ThumbnailGenerationError("A thumbnail precisa de uma imagem existente para refazer o lettering.")
    base_prompt = record["prompt"] or "Cria uma thumbnail de YouTube cinematográfica e de alto contraste."
    edit_prompt = str(lettering_prompt or "").strip() or (
        f"Refaz apenas o lettering da thumbnail para o vídeo {record['title']!r}. "
        "Escolhe uma frase curta e forte, com no máximo quatro palavras, relacionada com o título."
    )
    combined_prompt = (
        "BASE IMAGE LAYER — preserva exactamente a composição, enquadramento, sujeitos, fundo, iluminação, "
        "cores, objectos e estilo da imagem de referência. Não recries nem movas nenhum elemento.\n"
        f"{base_prompt}\n\n"
        "LETTERING EDIT LAYER — altera exclusivamente o texto/lettering visível da thumbnail. "
        "Mantém tudo o que pertence à BASE IMAGE LAYER pixelmente tão próximo quanto possível, sem mudar a imagem.\n"
        f"{edit_prompt}\n"
        "Não adicionar logótipos, marcas de água ou outros elementos."
    )
    _archive_image(str(task_id), previous_image)
    image_path = generate_thumbnail_image(
        settings,
        combined_prompt,
        topic=record["title"] or record["topic"],
        variant_index=record["variant_index"],
        reference_image=previous_image,
        lettering_prompt=edit_prompt,
    )
    variant = _variant_for_record(record)
    variant["image_prompt"] = base_prompt
    variant["lettering_prompt"] = edit_prompt
    _persist_thumbnail_result(tasks, task, record, image_path, variant=variant, source="lettering_regenerated", lettering_prompt=edit_prompt)
    write_json("tasks.json", tasks)
    return task, image_path


def upload_thumbnail_image(
    task_id: str,
    image_bytes: bytes,
    filename: str,
    content_type: str = "",
) -> tuple[dict[str, Any], Path]:
    """Store a user-provided image, preserve the old one, and attach it to the task."""
    if not isinstance(image_bytes, (bytes, bytearray)) or not image_bytes:
        raise ThumbnailGenerationError("O ficheiro de imagem está vazio.")
    if len(image_bytes) > 20 * 1024 * 1024:
        raise ThumbnailGenerationError("A imagem excede o limite de 20 MB.")
    suffix = Path(str(filename or "")).suffix.lower()
    allowed = {".png", ".jpg", ".jpeg", ".webp"}
    if suffix not in allowed:
        raise ThumbnailGenerationError("Use uma imagem PNG, JPG, JPEG ou WEBP.")
    if content_type and not str(content_type).lower().startswith("image/"):
        raise ThumbnailGenerationError("O ficheiro enviado não é uma imagem válida.")
    tasks = read_json("tasks.json", [])
    if not isinstance(tasks, list):
        raise ThumbnailGenerationError("O índice de tarefas não está disponível.")
    task, record = _find_task(tasks, task_id)
    _archive_image(str(task_id), record.get("image_path"))
    output_dir = STORAGE / "thumbnails" / "uploads"
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"uploaded-{task_id}-{uuid.uuid4().hex[:12]}{suffix}"
    fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=output_dir)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(bytes(image_bytes))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, destination)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    variant = _variant_for_record(record)
    _persist_thumbnail_result(tasks, task, record, destination, variant=variant, source="uploaded")
    write_json("tasks.json", tasks)
    return task, destination


def regenerate_thumbnail(task_id: str, settings: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    """Backward-compatible alias for regenerating from the current prompt."""
    return generate_thumbnail_for_task(task_id, settings)


__all__ = [
    "generate_thumbnail_for_task",
    "list_thumbnail_tasks",
    "normalize_thumbnail_task",
    "regenerate_thumbnail",
    "regenerate_thumbnail_lettering",
    "regenerate_thumbnail_prompt",
    "regenerate_thumbnail_prompt_and_image",
    "upload_thumbnail_image",
]

