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
    history = read_json(SCRIPT_HISTORY_FILE, [])
    if not isinstance(history, list):
        history = []
    history.insert(0, {key: value for key, value in record.items() if key != "content"})
    write_json(SCRIPT_HISTORY_FILE, history[:200])
    return record


def list_script_documents() -> list[dict[str, Any]]:
    history = read_json(SCRIPT_HISTORY_FILE, [])
    return [item for item in history if isinstance(item, dict)] if isinstance(history, list) else []


def read_script_document(record: dict[str, Any]) -> str:
    path = Path(str(record.get("path") or ""))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")
