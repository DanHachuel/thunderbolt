from __future__ import annotations

import unittest

from hermes_ui.material_sources import (
    MATERIAL_CARDS_KEY,
    apply_material_source_cards_to_settings,
    ensure_material_source_cards,
    material_api_keys,
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

    def test_disabled_card_is_not_exported_and_new_card_rejects_unknown_provider(self) -> None:
        settings = {}
        cards = [new_material_card("coverr", card_id="coverr-one") | {"api_key": "secret", "enabled": False}]

        apply_material_source_cards_to_settings(settings, cards)

        self.assertEqual(material_api_keys(settings, "coverr"), [])
        with self.assertRaises(ValueError):
            new_material_card("unknown-provider")


if __name__ == "__main__":
    unittest.main()
