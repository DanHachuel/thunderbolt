from __future__ import annotations

from typing import Any, Mapping

from .client import CanvaSkillsClient


def edit_design(design_id: str, changes: Mapping[str, Any], *, client: CanvaSkillsClient, auto_commit: bool = False) -> dict[str, Any]:
    """Prepare a safe edit request; REST Connect has no public edit transaction endpoint."""
    if not auto_commit:
        return {"status": "pending_approval", "design_id": design_id, "changes": dict(changes)}
    return {"status": "manual_action_required", "design_id": design_id, "changes": dict(changes), "message": "A Canva Connect REST API não expõe start/perform/commit editing transactions; abra o edit_url no Canva para aplicar estas alterações manualmente."}
