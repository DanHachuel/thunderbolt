from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Mapping

from hermes_ui.thumbnail_blueprints import thumbnail_blueprint_for_channel


class CanvaThumbnailWorkflowError(RuntimeError):
    """Raised when a Canva thumbnail workflow cannot complete safely."""


def _keywords(text: str) -> list[str]:
    words = re.findall(r"[\wÀ-ÿ]{3,}", str(text or "").lower(), flags=re.UNICODE)
    stopwords = {"para", "com", "uma", "the", "and", "from", "this", "that"}
    return list(dict.fromkeys(word for word in words if word not in stopwords))[:8]


def load_local_thumbnail_blueprint(channel: Mapping[str, Any] | None = None, blueprint_id: str = "") -> dict[str, Any]:
    """Resolve the Thunderbolt-local Thumbnail Blueprint; Canva is never queried for it."""
    context = dict(channel or {})
    if blueprint_id:
        context["thumbnail_blueprint_id"] = blueprint_id
    blueprint = thumbnail_blueprint_for_channel(context)
    content = str(blueprint.get("content") or "").strip()
    if not content:
        raise CanvaThumbnailWorkflowError(
            "Nenhum Thumbnail Blueprint local foi encontrado no Thunderbolt."
        )
    return blueprint


def build_search_query(title: str, topic: str = "", blueprint: Mapping[str, Any] | None = None) -> str:
    """Build Canva search terms from the video context, not from a Canva template search."""
    base = _keywords(f"{title} {topic}")
    niche = _keywords(str((blueprint or {}).get("niche") or ""))
    return " ".join((base + niche)[:10])


def select_design(candidates: list[Mapping[str, Any]], width: int, height: int) -> dict[str, Any]:
    """Choose an existing Canva design with the requested thumbnail dimensions."""
    if not candidates:
        raise CanvaThumbnailWorkflowError("A pesquisa Canva não encontrou designs para a thumbnail.")

    def score(item: Mapping[str, Any]) -> tuple[int, int]:
        thumbnail = item.get("thumbnail") if isinstance(item.get("thumbnail"), Mapping) else {}
        item_width = int(thumbnail.get("width") or 0)
        item_height = int(thumbnail.get("height") or 0)
        exact = int(item_width == width and item_height == height)
        ratio_delta = abs((item_width / item_height) - (width / height)) if item_width and item_height else 99
        return exact, -int(ratio_delta * 1000)

    return dict(max(candidates, key=score))


def run_thumbnail_workflow(
    *,
    title: str,
    topic: str,
    channel: Mapping[str, Any] | None,
    blueprint_id: str = "",
    width: int = 1280,
    height: int = 720,
    search_designs: Callable[[str], list[Mapping[str, Any]]],
    edit_design: Callable[[str, Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]],
    export_design: Callable[[str, str, str, int, int], Path],
) -> Path:
    """Run local Blueprint -> search -> edit -> export with injected Canva operations.

    The injected operations are the official Canva connector boundary. This keeps
    local Blueprint files private and prevents the REST-only blank-design fallback.
    """
    blueprint = load_local_thumbnail_blueprint(channel, blueprint_id)
    query = build_search_query(title, topic, blueprint)
    candidates = search_designs(query)
    selected = select_design(candidates, width, height)
    design_id = str(selected.get("id") or "").strip()
    if not design_id:
        raise CanvaThumbnailWorkflowError("A pesquisa Canva devolveu um design sem design_id.")
    changes = {
        "title": title,
        "topic": topic,
        "blueprint_id": str(blueprint.get("id") or ""),
        "blueprint_content": str(blueprint.get("content") or ""),
        "search_query": query,
        "lettering": title,
        "width": width,
        "height": height,
    }
    edited = dict(edit_design(design_id, changes, blueprint))
    edited_id = str(edited.get("design_id") or design_id).strip()
    if not edited_id or edited.get("status") in {"pending_approval", "manual_action_required"}:
        raise CanvaThumbnailWorkflowError(
            "A edição Canva não foi confirmada; a thumbnail não será exportada."
        )
    return export_design(edited_id, "png", "medium", width, height)


__all__ = [
    "CanvaThumbnailWorkflowError",
    "build_search_query",
    "load_local_thumbnail_blueprint",
    "run_thumbnail_workflow",
    "select_design",
]
