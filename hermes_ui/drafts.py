from __future__ import annotations

import uuid
from typing import Any

from .storage import now, read_json, write_json

DRAFTS_FILE = "drafts.json"
MAX_DRAFTS = 200


def list_drafts() -> list[dict[str, Any]]:
    """Return locally persisted drafts, newest first."""
    records = read_json(DRAFTS_FILE, [])
    return [record for record in records if isinstance(record, dict)] if isinstance(records, list) else []


def save_draft(draft: dict[str, Any]) -> dict[str, Any]:
    """Persist one editable pipeline draft without advancing any pipeline task."""
    record = {
        **draft,
        "id": str(draft.get("id") or f"draft_{uuid.uuid4().hex[:12]}"),
        "created_at": str(draft.get("created_at") or now()),
        "updated_at": now(),
    }
    drafts = list_drafts()
    drafts.insert(0, record)
    write_json(DRAFTS_FILE, drafts[:MAX_DRAFTS])
    return record


__all__ = ["DRAFTS_FILE", "list_drafts", "save_draft"]

