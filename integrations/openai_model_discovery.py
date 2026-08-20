"""Discovery of models from OpenAI-compatible providers such as NVIDIA NIM."""

from __future__ import annotations

from typing import Any

import requests


DEFAULT_NVIDIA_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_TIMEOUT_SECONDS = 12
MAX_MODEL_IDS = 2000


class ModelDiscoveryError(ValueError):
    """Raised when an OpenAI-compatible model list cannot be loaded safely."""


def models_endpoint(base_url: str) -> str:
    """Return the ``/models`` endpoint for an OpenAI-compatible base URL."""
    value = str(base_url or "").strip().rstrip("/")
    if not value:
        raise ModelDiscoveryError("Informe a Base URL antes de consultar os modelos.")
    if value.endswith("/models"):
        return value
    return f"{value}/models"


def normalize_model_ids(payload: Any) -> list[str]:
    """Extract unique model IDs from the standard OpenAI response shape."""
    if isinstance(payload, dict):
        collection = payload.get("data")
        if collection is None:
            collection = payload.get("models")
    elif isinstance(payload, list):
        collection = payload
    else:
        collection = None

    if not isinstance(collection, list):
        raise ModelDiscoveryError("A resposta de modelos não tem uma lista data válida.")

    model_ids: set[str] = set()
    for item in collection:
        if isinstance(item, dict):
            model_id = item.get("id") or item.get("name")
        elif isinstance(item, str):
            model_id = item
        else:
            model_id = None
        if isinstance(model_id, str) and model_id.strip():
            model_ids.add(model_id.strip())

    if not model_ids:
        raise ModelDiscoveryError("O endpoint não devolveu nenhum identificador de modelo.")
    return sorted(model_ids, key=str.casefold)[:MAX_MODEL_IDS]


def fetch_openai_compatible_models(
    api_key: str,
    base_url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[str]:
    """Fetch model IDs without exposing the API key in errors or logs."""
    endpoint = models_endpoint(base_url)
    headers = {"Accept": "application/json"}
    token = str(api_key or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.get(endpoint, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise ModelDiscoveryError(f"Não foi possível consultar {endpoint}: {exc}") from exc

    if response.status_code >= 400:
        if response.status_code in (401, 403):
            raise ModelDiscoveryError(
                f"O endpoint recusou a credencial (HTTP {response.status_code}). Verifique a API key."
            )
        raise ModelDiscoveryError(f"O endpoint devolveu HTTP {response.status_code}.")

    try:
        payload = response.json()
    except ValueError as exc:
        raise ModelDiscoveryError("O endpoint devolveu uma resposta que não é JSON.") from exc
    return normalize_model_ids(payload)
