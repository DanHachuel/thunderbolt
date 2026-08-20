import pytest

from integrations.openai_model_discovery import (
    ModelDiscoveryError,
    fetch_openai_compatible_models,
    models_endpoint,
    normalize_model_ids,
)


def test_models_endpoint_appends_models_once():
    assert models_endpoint("https://integrate.api.nvidia.com/v1") == "https://integrate.api.nvidia.com/v1/models"
    assert models_endpoint("https://provider.test/v1/") == "https://provider.test/v1/models"
    assert models_endpoint("https://provider.test/v1/models") == "https://provider.test/v1/models"


def test_normalize_model_ids_supports_openai_data_and_sorts():
    payload = {
        "data": [
            {"id": "nvidia_nim/z-model"},
            {"id": "nvidia_nim/a-model"},
            {"id": "nvidia_nim/z-model"},
            {"name": "nvidia_nim/name-fallback"},
            {"id": ""},
        ]
    }
    assert normalize_model_ids(payload) == [
        "nvidia_nim/a-model",
        "nvidia_nim/name-fallback",
        "nvidia_nim/z-model",
    ]


def test_fetch_models_uses_bearer_header_and_timeout(monkeypatch):
    captured = {}

    class Response:
        status_code = 200

        def json(self):
            return {"data": [{"id": "nvidia_nim/minimaxai/minimax-m3"}]}

    def fake_get(url, *, headers, timeout):
        captured.update(url=url, headers=headers, timeout=timeout)
        return Response()

    monkeypatch.setattr("integrations.openai_model_discovery.requests.get", fake_get)
    result = fetch_openai_compatible_models("secret-token", "https://integrate.api.nvidia.com/v1")
    assert result == ["nvidia_nim/minimaxai/minimax-m3"]
    assert captured == {
        "url": "https://integrate.api.nvidia.com/v1/models",
        "headers": {"Accept": "application/json", "Authorization": "Bearer secret-token"},
        "timeout": 12,
    }


def test_fetch_models_reports_auth_failure_without_echoing_secret(monkeypatch):
    class Response:
        status_code = 401

    monkeypatch.setattr("integrations.openai_model_discovery.requests.get", lambda *args, **kwargs: Response())
    with pytest.raises(ModelDiscoveryError, match="API key") as exc_info:
        fetch_openai_compatible_models("secret-token", "https://provider.test/v1")
    assert "secret-token" not in str(exc_info.value)


def test_normalize_model_ids_rejects_invalid_response():
    with pytest.raises(ModelDiscoveryError, match="lista data"):
        normalize_model_ids({"object": "list"})
    with pytest.raises(ModelDiscoveryError, match="nenhum identificador"):
        normalize_model_ids({"data": [{"object": "model"}]})
