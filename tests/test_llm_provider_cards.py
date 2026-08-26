from __future__ import annotations

from unittest import TestCase
from unittest.mock import patch

from hermes_ui.llm_providers import (
    DEFAULT_LLM_CARD_ID,
    LLM_ACTIVE_CARD_KEY,
    LLM_CARDS_KEY,
    apply_llm_cards_to_settings,
    ensure_llm_provider_cards,
    provider_definition,
    test_llm_provider_card,
)


class LlmProviderCardTests(TestCase):
    def test_openai_nim_is_always_first_default_card(self) -> None:
        settings, changed = ensure_llm_provider_cards({})
        self.assertTrue(changed)
        self.assertEqual(settings[LLM_CARDS_KEY][0]["id"], DEFAULT_LLM_CARD_ID)
        self.assertEqual(settings[LLM_CARDS_KEY][0]["provider"], "openai")
        self.assertEqual(settings[LLM_CARDS_KEY][0]["priority"], 1)
        self.assertEqual(settings[LLM_ACTIVE_CARD_KEY], DEFAULT_LLM_CARD_ID)
        self.assertEqual(settings["llm_provider"], "openai")

    def test_legacy_explicit_provider_is_added_without_losing_legacy_values(self) -> None:
        settings, _ = ensure_llm_provider_cards(
            {
                "llm_provider": "gemini",
                "gemini_api_key": "gem-key",
                "gemini_model_name": "gemini-2.5-flash",
            }
        )
        cards = settings[LLM_CARDS_KEY]
        self.assertEqual(cards[0]["provider"], "gemini")
        self.assertEqual(cards[1]["provider"], "openai")
        self.assertEqual(cards[0]["api_key"], "gem-key")
        self.assertEqual(cards[0]["priority"], 1)
        self.assertEqual(cards[1]["priority"], 2)
        self.assertEqual(settings[LLM_ACTIVE_CARD_KEY], cards[0]["id"])

    def test_fixed_endpoints_hide_base_url_but_local_and_openai_show_it(self) -> None:
        self.assertTrue(provider_definition("openai").show_base_url)
        self.assertFalse(provider_definition("openrouter").show_base_url)
        self.assertTrue(provider_definition("ollama").show_base_url)
        self.assertFalse(provider_definition("ollama").requires_api_key)

    def test_multiple_cards_can_repeat_the_same_provider(self) -> None:
        cards = [
            {"id": "one", "provider": "openai", "api_key": "a", "model": "m", "base_url": "https://one/v1"},
            {"id": "two", "provider": "openai", "api_key": "b", "model": "m", "base_url": "https://two/v1"},
        ]
        settings = apply_llm_cards_to_settings({}, cards, "two")
        self.assertEqual(len(settings[LLM_CARDS_KEY]), 2)
        self.assertEqual(settings[LLM_CARDS_KEY][0]["priority"], 2)
        self.assertEqual(settings[LLM_CARDS_KEY][1]["priority"], 1)
        self.assertEqual(settings[LLM_ACTIVE_CARD_KEY], "two")
        self.assertEqual(settings["openai_api_key"], "b")
        self.assertEqual(settings["openai_base_url"], "https://two/v1")

    def test_explicit_priorities_order_cards_and_ignore_legacy_active_id(self) -> None:
        settings = {
            LLM_CARDS_KEY: [
                {"id": "third", "provider": "groq", "priority": 3, "model": "m"},
                {"id": "first", "provider": "openai", "priority": 1, "model": "m"},
                {"id": "second", "provider": "deepseek", "priority": 2, "model": "m"},
            ],
            LLM_ACTIVE_CARD_KEY: "third",
        }
        migrated, _ = ensure_llm_provider_cards(settings)
        self.assertEqual([card["id"] for card in migrated[LLM_CARDS_KEY]], ["first", "second", "third"])
        self.assertEqual(migrated[LLM_ACTIVE_CARD_KEY], "first")
        self.assertEqual(migrated["llm_provider"], "openai")

    def test_telegram_card_is_exclusive_and_routed_by_id(self) -> None:
        cards = [
            {"id": "one", "provider": "openai", "telegram_llm": True},
            {"id": "two", "provider": "groq", "telegram_llm": True},
        ]
        settings = apply_llm_cards_to_settings({}, cards, "one")
        self.assertFalse(settings[LLM_CARDS_KEY][0]["telegram_llm"])
        self.assertTrue(settings[LLM_CARDS_KEY][1]["telegram_llm"])
        self.assertEqual(settings["llm_telegram_card_id"], "two")

    def test_missing_key_is_redacted_and_success_is_stable(self) -> None:
        missing = test_llm_provider_card({"provider": "groq", "model": "llama"})
        self.assertFalse(missing["ok"])
        self.assertIn("Missing key", missing["message"])
        secret = "sk-super-secret"
        with patch("hermes_ui.llm_providers.validate_openai_compatible_api_key") as validate_key:
            success = test_llm_provider_card(
                {"provider": "groq", "api_key": secret, "model": "model-a"}
            )
        self.assertTrue(success["ok"])
        self.assertNotIn(secret, success["message"])
        self.assertEqual(success["message"], "API Key OK")
        validate_key.assert_called_once_with(secret, "https://api.groq.com/openai/v1", "model-a")

    def test_provider_error_does_not_expose_api_key(self) -> None:
        secret = "sk-do-not-leak"
        with patch(
            "hermes_ui.llm_providers.validate_openai_compatible_api_key",
            side_effect=ValueError(f"bad response containing {secret}"),
        ):
            result = test_llm_provider_card(
                {"provider": "groq", "api_key": secret, "model": "model-a"}
            )
        self.assertFalse(result["ok"])
        self.assertNotIn(secret, result["message"])


if __name__ == "__main__":
    import unittest

    unittest.main()
