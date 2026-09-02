from __future__ import annotations

from typing import Any, Mapping

from hermes_ui.canva_client import CanvaClient


class CanvaSkillsClient(CanvaClient):
    """REST client shared by the adapted Canva Skills."""

    def get(self, endpoint: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return self.request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return self.request("POST", endpoint, json=data or {})

    def delete(self, endpoint: str) -> dict[str, Any]:
        return self.request("DELETE", endpoint)


def client_from_card(card: Mapping[str, Any], token_saver=None) -> CanvaSkillsClient:
    return CanvaSkillsClient(card, token_saver=token_saver)
