from __future__ import annotations

from unittest import TestCase
from unittest.mock import Mock, patch

from integrations.openai_model_discovery import (
    OpenAICompatibleAPIError,
    chat_completions_endpoint,
    models_endpoint,
    validate_openai_compatible_api_key,
)


class OpenAICompatibleApiValidationTests(TestCase):
    def test_openrouter_base_url_builds_official_endpoints_without_query_suffix(self) -> None:
        base_url = "https://openrouter.ai/api/v1?"

        self.assertEqual(
            models_endpoint(base_url),
            "https://openrouter.ai/api/v1/models",
        )
        self.assertEqual(
            chat_completions_endpoint(base_url),
            "https://openrouter.ai/api/v1/chat/completions",
        )

    def test_openrouter_404_explains_base_url_and_model_requirements(self) -> None:
        response = Mock(status_code=404)
        with patch("integrations.openai_model_discovery.requests.post", return_value=response):
            with self.assertRaises(OpenAICompatibleAPIError) as raised:
                validate_openai_compatible_api_key(
                    "sk-openrouter-test",
                    "https://openrouter.ai/api/v1",
                    "modelo-inexistente",
                )

        self.assertIn("https://openrouter.ai/api/v1", str(raised.exception))
        self.assertIn("openai/gpt-4o-mini", str(raised.exception))
        self.assertIn("chat/completions", str(raised.exception))

    def test_validation_posts_minimal_authenticated_chat_request(self) -> None:
        response = Mock(status_code=200)
        with patch("integrations.openai_model_discovery.requests.post", return_value=response) as post:
            validate_openai_compatible_api_key(
                "sk-test-secret",
                "https://integrate.api.nvidia.com/v1",
                "meta/llama-3.1-8b-instruct",
            )

        post.assert_called_once_with(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer sk-test-secret",
                "Content-Type": "application/json",
            },
            json={
                "model": "meta/llama-3.1-8b-instruct",
                "messages": [{"role": "user", "content": "Responda apenas OK."}],
                "max_tokens": 1,
                "temperature": 0,
            },
            timeout=12,
        )

    def test_validation_reports_rejected_api_key_without_exposing_it(self) -> None:
        secret = "sk-never-leak"
        response = Mock(status_code=401)
        with patch("integrations.openai_model_discovery.requests.post", return_value=response):
            with self.assertRaises(OpenAICompatibleAPIError) as raised:
                validate_openai_compatible_api_key(secret, "https://api.example.com/v1", "model-a")

        self.assertIn("API key", str(raised.exception))
        self.assertNotIn(secret, str(raised.exception))


if __name__ == "__main__":
    import unittest

    unittest.main()
