from __future__ import annotations

from typing import Any, Mapping

from .client import CanvaSkillsClient


def get_design_feedback(design_id: str, *, client: CanvaSkillsClient) -> dict[str, Any]:
    design_payload = client.get(f"designs/{design_id}")
    design = design_payload.get("design") or design_payload
    findings = []
    title = str(design.get("title") or "").strip()
    if not title:
        findings.append({"category": "readability", "severity": "medium", "message": "O design não tem título identificável na metadata."})
    thumb = design.get("thumbnail") or {}
    if thumb.get("width") and thumb.get("height") and thumb["width"] / thumb["height"] < 1.5:
        findings.append({"category": "layout", "severity": "high", "message": "A proporção da thumbnail parece inadequada para YouTube 16:9."})
    return {"design_id": design_id, "visual_hierarchy": findings, "layout": [], "readability": [], "consistency": [], "accessibility": [], "limitations": ["A Connect REST não expõe uma análise visual completa nem listagem de threads de comentários; os itens não verificáveis ficam explícitos."]}


def implement_feedback(design_id: str, feedback_items: list[Mapping[str, Any]], *, client: CanvaSkillsClient, approved: bool = False) -> dict[str, Any]:
    if not approved:
        return {"status": "pending_approval", "design_id": design_id, "items": [dict(item) for item in feedback_items]}
    return {"status": "manual_action_required", "design_id": design_id, "applied": [], "manual": [dict(item) for item in feedback_items], "message": "A Connect REST pública não fornece transacções de edição; nenhuma alteração foi cometida."}
