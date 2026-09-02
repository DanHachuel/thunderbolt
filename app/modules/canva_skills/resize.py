from __future__ import annotations

from typing import Any, Mapping

from .client import CanvaSkillsClient
from .config import PLATFORM_DIMENSIONS, SUPPORTED_EXPORT_FORMATS


def resize_for_social_media(design_id: str, platforms: list[str], export_format: str = "png", *, client: CanvaSkillsClient) -> dict[str, dict[str, Any]]:
    """Create platform variants and export them.

    Connect REST currently has no general resize endpoint. The skill therefore
    creates a copy for each platform and records target dimensions; users can
    refine the copy through Canva's edit URL when exact responsive layout is
    required.
    """
    if export_format.lower() not in SUPPORTED_EXPORT_FORMATS:
        raise ValueError("O formato deve ser png ou jpg.")
    results: dict[str, dict[str, Any]] = {}
    for platform in platforms:
        if platform not in PLATFORM_DIMENSIONS:
            continue
        copied = client.post("designs", {"type": "design", "design_id": design_id, "page_numbers": [1]})
        design = copied.get("design") or copied
        variant_id = str(design.get("id") or "")
        if not variant_id:
            raise RuntimeError(f"A Canva não devolveu o design da variante {platform}.")
        job_id = client.export_design(variant_id, file_type=export_format.lower())
        url = client.wait_export(job_id)
        urls = design.get("urls") or {}
        results[platform] = {"design_id": variant_id, "export_url": url, "edit_url": urls.get("edit_url", ""), "width": PLATFORM_DIMENSIONS[platform][0], "height": PLATFORM_DIMENSIONS[platform][1], "resize_note": "A Connect REST não aplica resize responsivo; a dimensão é metadado para edição/exportação."}
    return results
