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
        for key in ("data", "result", "response"):
            if isinstance(value.get(key), (Mapping, list)):
                nested = _items(value[key])
                if nested:
                    return nested
    return []


def _design_id(value: Any) -> str:
    """Extract a Canva design identifier from REST/MCP result variants."""
    if isinstance(value, Mapping):
        for key in ("design_id", "designId", "id"):
            candidate = str(value.get(key) or "").strip()
            if candidate:
                return candidate
        for key in ("design", "resource", "data"):
            if isinstance(value.get(key), Mapping):
                found = _design_id(value[key])
                if found:
                    return found
    return ""


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


def _first_text_element(value: Any, *, text_context: bool = False) -> str:
    if isinstance(value, Mapping):
        # The MCP returns rich text elements with slightly different ID
        # names depending on the design type/version of the server.
        text_markers = ("text", "richtext", "rich_text", "content", "paragraph")
        mapping_text = str(value).lower()
        is_text_mapping = text_context or any(
            marker in str(key).lower() or marker in mapping_text
            for key in value
            for marker in text_markers
        )
        for key in ("element_id", "elementId", "richtext_id", "richTextId", "text_id", "textId", "id"):
            candidate = str(value.get(key) or "").strip()
            if candidate and is_text_mapping:
                return candidate
        for key, child in value.items():
            child_context = text_context or any(marker in str(key).lower() for marker in text_markers)
            found = _first_text_element(child, text_context=child_context)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _first_text_element(child, text_context=text_context)
            if found:
                return found
    return ""


def _has_richtext(value: Any) -> bool:
    """Return whether a Canva payload contains at least one richtext item."""
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).lower() in {"richtexts", "rich_texts", "text_elements", "textelements"}:
                if isinstance(child, list) and any(isinstance(item, Mapping) for item in child):
                    return True
                if isinstance(child, Mapping) and child:
                    return True
            if _has_richtext(child):
                return True
    elif isinstance(value, list):
        return any(_has_richtext(child) for child in value)
    return False


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
        candidates = [candidate for candidate in candidates if _design_id(candidate)]
        if not candidates:
            raise CanvaMCPError("A pesquisa Canva devolveu um design sem ID.")

        get_name = "get-design-content" if "get-design-content" in available else "get_design_content"
        selected = None
        content: Any = {}
        for candidate in candidates:
            candidate_id = _design_id(candidate)
            candidate_content = _payload(client.call(get_name, {
                "design_id": candidate_id,
                "content_types": ["richtexts"],
                "user_intent": "Inspect the selected Canva design before applying the thumbnail edit.",
            }))
            if _has_richtext(candidate_content):
                selected = candidate
                content = candidate_content
                break
        if selected is None:
            raise CanvaMCPError("Os designs Canva encontrados não têm elementos de texto editáveis.")
        design_id = _design_id(selected)
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
            cancel_name = "cancel-editing-transaction" if "cancel-editing-transaction" in available else "cancel_editing_transaction"
            if cancel_name in available:
                client.call(cancel_name, {
                    "transaction_id": transaction_id,
                    "user_intent": "Discard the Canva editing transaction because no editable text element was returned.",
                })
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
