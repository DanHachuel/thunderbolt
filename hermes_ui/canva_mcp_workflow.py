from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import requests

from .canva_mcp_client import CanvaMCPClient, CanvaMCPError


def _payload(result: Mapping[str, Any]) -> Any:
    if isinstance(result.get("structuredContent"), Mapping):
        return result["structuredContent"]
    content = result.get("content")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, Mapping) and isinstance(item.get("json"), (dict, list)):
                return item["json"]
            if isinstance(item, Mapping) and item.get("text"):
                try:
                    return json.loads(str(item["text"]))
                except (TypeError, ValueError):
                    continue
    return result


def _items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        for key in ("items", "designs", "results"):
            if isinstance(value.get(key), list):
                return [dict(item) for item in value[key] if isinstance(item, Mapping)]
    return []


def _first_id(value: Any, keys: tuple[str, ...]) -> str:
    if isinstance(value, Mapping):
        for key in keys:
            candidate = str(value.get(key) or "").strip()
            if candidate:
                return candidate
        for child in value.values():
            found = _first_id(child, keys)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _first_id(child, keys)
            if found:
                return found
    return ""


def _first_text_element(value: Any) -> str:
    if isinstance(value, Mapping):
        for key in ("element_id", "id"):
            candidate = str(value.get(key) or "").strip()
            if candidate and any(token in str(value).lower() for token in ("text", "richtext", "content")):
                return candidate
        for child in value.values():
            found = _first_text_element(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _first_text_element(child)
            if found:
                return found
    return ""


def _first_page(value: Any) -> tuple[str, list[dict[str, Any]]]:
    pages: list[dict[str, Any]] = []
    if isinstance(value, Mapping) and isinstance(value.get("pages"), list):
        pages = [dict(page) for page in value["pages"] if isinstance(page, Mapping)]
    page_id = str((pages[0] if pages else {}).get("page_id") or "").strip()
    return page_id, pages


def run_direct_canva_thumbnail(
    *,
    title: str,
    topic: str,
    prompt: str,
    blueprint: Mapping[str, Any],
    destination: Path,
    width: int,
    height: int,
    quality: str = "medium",
) -> Path:
    """Run the user-triggered Canva MCP flow in the local Thunderbolt process."""
    with CanvaMCPClient() as client:
        available = {str(item.get("name")) for item in client.tools()}
        search_name = "search-designs" if "search-designs" in available else "search_designs"
        result = _payload(client.call(search_name, {
            "query": " ".join(word for word in f"{title} {topic}".split() if len(word) >= 3)[:255],
            "sort_by": "relevance",
            "ownership": "any",
            "limit": 25,
            "user_intent": "Find an existing Canva design to edit as a Thunderbolt thumbnail.",
        }))
        candidates = _items(result)
        if not candidates:
            raise CanvaMCPError("Canva não encontrou designs para as palavras-chave da thumbnail.")
        selected = candidates[0]
        design_id = str(selected.get("id") or "").strip()
        if not design_id:
            raise CanvaMCPError("A pesquisa Canva devolveu um design sem ID.")

        get_name = "get-design-content" if "get-design-content" in available else "get_design_content"
        content = _payload(client.call(get_name, {
            "design_id": design_id,
            "user_intent": "Inspect the selected Canva design before applying the thumbnail edit.",
        }))
        start_name = "start-editing-transaction" if "start-editing-transaction" in available else "start_editing_transaction"
        started = _payload(client.call(start_name, {
            "design_id": design_id,
            "user_intent": "Edit the selected design according to the local Thunderbolt Thumbnail Blueprint.",
        }))
        transaction_id = _first_id(started, ("transaction_id",))
        if not transaction_id:
            raise CanvaMCPError("Canva não devolveu uma transacção de edição.")
        page_id, pages = _first_page(started)
        element_id = _first_text_element(started) or _first_text_element(content)
        if not element_id:
            raise CanvaMCPError("O design Canva não devolveu um elemento de texto editável.")
        perform_name = "perform-editing-operations" if "perform-editing-operations" in available else "perform_editing_operations"
        operations = [{"type": "replace_text", "element_id": element_id, "text": title[:255]}]
        performed = _payload(client.call(perform_name, {
            "transaction_id": transaction_id,
            "operations": operations,
            "page_index": 1,
            "pages": pages,
            "user_intent": f"Apply this local Thumbnail Blueprint to the thumbnail: {blueprint.get('id', '')}. Prompt: {prompt[:1000]}",
        }))
        commit_name = "commit-editing-transaction" if "commit-editing-transaction" in available else "commit_editing_transaction"
        client.call(commit_name, {
            "transaction_id": transaction_id,
            "user_intent": "Save the approved thumbnail lettering edit before export.",
        })
        formats_name = "get-export-formats" if "get-export-formats" in available else "get_export_formats"
        formats = _payload(client.call(formats_name, {
            "design_id": design_id,
            "user_intent": "Verify PNG export support before exporting the finished thumbnail.",
        }))
        format_text = json.dumps(formats, ensure_ascii=False).lower()
        if '"png"' not in format_text:
            raise CanvaMCPError("O design Canva seleccionado não suporta exportação PNG.")
        export_name = "export-design" if "export-design" in available else "export_design"
        exported = _payload(client.call(export_name, {
            "design_id": design_id,
            "format": {
                "type": "png",
                "width": width,
                "height": height,
                "export_quality": "pro" if quality == "high" else "regular",
                "lossless": True,
                "pages": [1],
            },
            "user_intent": "Export the finished Thunderbolt thumbnail as PNG.",
        }))
        url = _first_id(exported, ("url", "download_url"))
        if not url:
            raise CanvaMCPError("Canva não devolveu URL de download do PNG.")
        response = requests.get(url, timeout=90)
        response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)
        return destination


__all__ = ["run_direct_canva_thumbnail"]
