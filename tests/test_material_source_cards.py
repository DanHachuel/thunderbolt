from __future__ import annotations

import unittest

from hermes_ui.material_sources import (
    MATERIAL_CARDS_KEY,
    apply_material_source_cards_to_settings,
    ensure_material_source_cards,
    material_api_keys,
    material_source_cards,
    new_material_card,
)


class MaterialSourceCardTests(unittest.TestCase):
    def test_legacy_keys_migrate_to_independent_cards_without_loss(self) -> None:
        settings = {
            "video_source": "pexels",
            "material_api_keys": {"pexels": ["pexels-one", "pexels-two"]},
        }

        migrated, changed = ensure_material_source_cards(settings)

        self.assertTrue(changed)
        self.assertEqual([card["provider"] for card in migrated[MATERIAL_CARDS_KEY]], ["pexels", "pexels"])
        self.assertEqual(material_api_keys(migrated, "pexels"), ["pexels-one", "pexels-two"])
        self.assertEqual(migrated["pexels_api_keys"], ["pexels-one", "pexels-two"])

    def test_repeated_provider_cards_are_exported_as_rotating_keys(self) -> None:
        settings = {}
        cards = [
            new_material_card("pexels", card_id="pexels-primary") | {"api_key": "one"},
            new_material_card("pexels", card_id="pexels-secondary") | {"api_key": "two"},
            new_material_card("pixabay", card_id="pixabay-primary") | {"api_key": "three"},
        ]

        apply_material_source_cards_to_settings(settings, cards, "pexels-secondary")

        self.assertEqual(settings["video_source"], "pexels")
        self.assertEqual(settings["material_active_card_id"], "pexels-secondary")
        self.assertEqual(material_api_keys(settings, "pexels"), ["one", "two"])
        self.assertEqual(material_api_keys(settings, "pixabay"), ["three"])

    def test_priority_orders_material_cards_and_preserves_legacy_order_when_missing(self) -> None:
        settings = {
            MATERIAL_CARDS_KEY: [
                {"id": "pixabay-card", "provider": "pixabay", "api_key": "two", "priority": 2},
                {"id": "pexels-card", "provider": "pexels", "api_key": "one", "priority": 1},
            ],
            "material_active_card_id": "pexels-card",
        }

        cards, changed = ensure_material_source_cards(settings)

        self.assertTrue(changed)
        self.assertEqual([card["id"] for card in cards[MATERIAL_CARDS_KEY]], ["pexels-card", "pixabay-card"])
        self.assertEqual([card["priority"] for card in cards[MATERIAL_CARDS_KEY]], [1, 2])
        self.assertEqual([card["id"] for card in material_source_cards(settings)], ["pexels-card", "pixabay-card"])

    def test_priority_is_persisted_and_invalid_values_use_position_fallback(self) -> None:
        settings = {}
        cards = [
            new_material_card("pexels", card_id="pexels-low") | {"api_key": "one", "priority": 5},
            new_material_card("pixabay", card_id="pixabay-invalid") | {"api_key": "two", "priority": "invalid"},
        ]

        apply_material_source_cards_to_settings(settings, cards, "pexels-low")

        self.assertEqual([card["id"] for card in settings[MATERIAL_CARDS_KEY]], ["pixabay-invalid", "pexels-low"])
        self.assertEqual([card["priority"] for card in settings[MATERIAL_CARDS_KEY]], [2, 5])

    def test_disabled_card_is_not_exported_and_new_card_rejects_unknown_provider(self) -> None:
        settings = {}
        cards = [new_material_card("coverr", card_id="coverr-one") | {"api_key": "secret", "enabled": False}]

        apply_material_source_cards_to_settings(settings, cards)

        self.assertEqual(material_api_keys(settings, "coverr"), [])
        with self.assertRaises(ValueError):
            new_material_card("unknown-provider")


if __name__ == "__main__":
    unittest.main()
