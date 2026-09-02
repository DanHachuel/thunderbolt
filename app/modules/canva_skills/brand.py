from __future__ import annotations

from typing import Any

from .client import CanvaSkillsClient


def list_brand_kits(*, client: CanvaSkillsClient) -> list[dict[str, Any]]:
    payload = client.get("brand-templates", {"limit": 100})
    return list(payload.get("items") or payload.get("brand_templates") or [])


def check_brand_compliance(design_id: str, brand_kit_id: str, *, client: CanvaSkillsClient) -> dict[str, Any]:
    design = client.get(f"designs/{design_id}").get("design", {})
    templates = list_brand_kits(client=client)
    selected = next((item for item in templates if str(item.get("id")) == brand_kit_id), None)
    if selected is None:
        raise ValueError("Brand Template/kit não encontrado ou sem permissão.")
    return {"design_id": design_id, "brand_kit_id": brand_kit_id, "on_brand": [], "off_brand": [], "cannot_verify": [{"category": "colors", "reason": "A metadata REST não expõe paleta completa."}, {"category": "typography", "reason": "A metadata REST não expõe fontes completas."}, {"category": "logo", "reason": "É necessária inspecção visual no Canva."}], "design_title": design.get("title", ""), "brand_template_title": selected.get("title", "")}
