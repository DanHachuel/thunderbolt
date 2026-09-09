"""Local Markdown storage for Thunderbolt scripts and music lyrics."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import STORAGE, append_json, ensure_storage, read_json, write_json

SCRIPT_HISTORY_FILE = "scripts.json"


def _slug(value: str, fallback: str = "documento") -> str:
    normalized = re.sub(r"[^a-zA-Z0-9À-ÿ]+", "-", str(value or "").strip(), flags=re.UNICODE).strip("-").lower()
    return (normalized or fallback)[:90]


def script_storage_path() -> Path:
    ensure_storage()
    path = STORAGE / "scripts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _history_records() -> list[dict[str, Any]]:
    history = read_json(SCRIPT_HISTORY_FILE, [])
    return [item for item in history if isinstance(item, dict)] if isinstance(history, list) else []


def _record_index(history: list[dict[str, Any]], document_id: str) -> int:
    return next((index for index, item in enumerate(history) if str(item.get("id") or "") == document_id), -1)


def _front_matter_values(markdown: str) -> dict[str, str]:
    text = str(markdown or "")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) != 3:
        return {}
    values: dict[str, str] = {}
    for line in parts[1].splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip()
    return values


def _with_front_matter(markdown: str, updates: dict[str, Any]) -> str:
    text = str(markdown or "")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            lines = parts[1].splitlines()
            update_keys = {str(key): str(value or "") for key, value in updates.items()}
            seen: set[str] = set()
            output: list[str] = []
            for line in lines:
                key, separator, _value = line.partition(":")
                normalized_key = key.strip()
                if separator and normalized_key in update_keys:
                    output.append(f"{normalized_key}: {update_keys[normalized_key]}")
                    seen.add(normalized_key)
                else:
                    output.append(line)
            for key, value in update_keys.items():
                if key not in seen:
                    output.append(f"{key}: {value}")
            return "---\n" + "\n".join(output) + "\n---" + parts[2]
    front_matter = ["---", *[f"{key}: {str(value or '')}" for key, value in updates.items()], "---", ""]
    return "\n".join(front_matter) + text.lstrip("\r\n")


def _merge_record_front_matter(record: dict[str, Any], values: dict[str, str]) -> dict[str, Any]:
    merged = dict(record)
    field_mapping = {
        "id": "id",
        "type": "document_type",
        "title": "title",
        "language": "language",
        "channel": "channel_name",
        "blueprint_id": "blueprint_id",
        "blueprint": "blueprint_name",
        "created_at": "created_at",
    }
    for source, target in field_mapping.items():
        if source in values:
            merged[target] = values[source]
    return merged


def save_script_document(document: dict[str, Any]) -> dict[str, Any]:
    content = str(document.get("content") or "").strip()
    if not content:
        raise ValueError("O documento não pode ser guardado vazio.")
    created_at = datetime.now(timezone.utc).isoformat()
    document_id = str(document.get("id") or uuid.uuid4().hex[:12])
    title = str(document.get("title") or "Documento").strip()
    document_type = str(document.get("document_type") or "video_script").strip()
    prefix = "roteiro" if document_type == "video_script" else "letra"
    filename = f"{prefix}-{_slug(title)}-{document_id}.md"
    path = script_storage_path() / filename
    front_matter = [
        "---",
        f"id: {document_id}",
        f"type: {document_type}",
        f"title: {title}",
        f"language: {str(document.get('language') or '')}",
        f"channel: {str(document.get('channel_name') or '')}",
        f"blueprint_id: {str(document.get('blueprint_id') or '')}",
        f"blueprint: {str(document.get('blueprint_name') or document.get('blueprint_id') or '')}",
        f"created_at: {created_at}",
        "---",
        "",
    ]
    summary = str(document.get("summary") or "").strip()
    if summary:
        front_matter.extend([f"> {summary}", ""])
    path.write_text("\n".join(front_matter) + content.rstrip() + "\n", encoding="utf-8")
    record = {
        **document,
        "id": document_id,
        "title": title,
        "document_type": document_type,
        "path": str(path),
        "filename": filename,
        "created_at": created_at,
        "content": content,
    }
    history = _history_records()
    history.insert(0, {key: value for key, value in record.items() if key != "content"})
    write_json(SCRIPT_HISTORY_FILE, history[:200])
    return record


def list_script_documents() -> list[dict[str, Any]]:
    return _history_records()


def read_script_document(record: dict[str, Any]) -> str:
    path = Path(str(record.get("path") or ""))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def update_script_document(document_id: str, content: str) -> dict[str, Any]:
    """Replace one saved Markdown document and refresh its indexed front matter."""
    if not str(content or "").strip():
        raise ValueError("O documento não pode ser guardado vazio.")
    history = _history_records()
    index = _record_index(history, str(document_id))
    if index < 0:
        raise ValueError("O roteiro já não existe no histórico.")
    record = history[index]
    path = Path(str(record.get("path") or ""))
    if not path.is_file():
        raise FileNotFoundError("O ficheiro do roteiro já não está disponível no storage.")
    normalized = str(content).rstrip() + "\n"
    path.write_text(normalized, encoding="utf-8")
    history[index] = _merge_record_front_matter(record, _front_matter_values(normalized))
    write_json(SCRIPT_HISTORY_FILE, history)
    return history[index]


def update_script_document_metadata(document_id: str, metadata: dict[str, Any]) -> dict[str, Any]:
    """Update front-matter fields in place without changing the Markdown body."""
    history = _history_records()
    index = _record_index(history, str(document_id))
    if index < 0:
        raise ValueError("O roteiro já não existe no histórico.")
    record = history[index]
    path = Path(str(record.get("path") or ""))
    if not path.is_file():
        raise FileNotFoundError("O ficheiro do roteiro já não está disponível no storage.")
    updated_markdown = _with_front_matter(path.read_text(encoding="utf-8"), metadata)
    path.write_text(updated_markdown.rstrip() + "\n", encoding="utf-8")
    history[index] = _merge_record_front_matter(record, _front_matter_values(updated_markdown))
    write_json(SCRIPT_HISTORY_FILE, history)
    return history[index]


def delete_script_document(document_id: str) -> bool:
    """Remove a saved document from the history index and its Markdown file."""
    history = _history_records()
    index = _record_index(history, str(document_id))
    if index < 0:
        return False
    record = history.pop(index)
    path = Path(str(record.get("path") or ""))
    try:
        if path.is_file():
            path.unlink()
    finally:
        write_json(SCRIPT_HISTORY_FILE, history)
    return True
