import unittest

from hermes_ui.languages import (
    LANGUAGE_BY_CODE,
    LANGUAGE_CODES,
    LANGUAGE_FLAG_DATA_URIS,
    UI_TRANSLATIONS,
    VIDEO_LANGUAGE_CODES,
    language_code,
    language_label,
    ui_language_menu_label,
    video_language_options,
)


class UILanguagePickerTests(unittest.TestCase):
    def test_ui_catalog_contains_requested_languages_and_flags(self):
        expected = {
            "pl": ("Polish", "🇵🇱"),
            "ga": ("Irish", "🇮🇪"),
            "ar": ("Arabic", "🇸🇦"),
            "he": ("Hebrew", "🇮🇱"),
        }
        for code, (name, flag) in expected.items():
            self.assertIn(code, LANGUAGE_CODES)
            self.assertEqual(LANGUAGE_BY_CODE[code]["ui_name"], name)
            self.assertEqual(LANGUAGE_BY_CODE[code]["flag"], flag)
            self.assertIn(code, LANGUAGE_FLAG_DATA_URIS)

    def test_ui_picker_uses_english_names_without_parenthesized_codes(self):
        expected = {
            "en": "English",
            "zh": "Simplified Chinese",
            "de": "German",
            "vi": "Vietnamese",
            "tr": "Turkish",
            "pt": "Portuguese",
            "ru": "Russian",
            "es": "Spanish",
            "id": "Indonesian",
            "it": "Italian",
            "pl": "Polish",
            "ga": "Irish",
            "ar": "Arabic",
            "he": "Hebrew",
        }
        for code, label in expected.items():
            self.assertEqual(ui_language_menu_label(code), label)
            self.assertNotIn("(", ui_language_menu_label(code))
            self.assertNotIn(")", ui_language_menu_label(code))
            self.assertEqual(ui_language_menu_label(code, include_code=True), f"{label} ({code})")

    def test_legacy_language_label_keeps_creation_and_channel_display_contract(self):
        self.assertEqual(language_label("pt"), "Português (pt) 🇧🇷")
        self.assertEqual(language_label("en"), "Inglês (en) 🇺🇸")
        self.assertEqual(language_label("pl"), "Polaco (pl) 🇵🇱")
        self.assertEqual(language_code("Polish"), "pl")
        self.assertEqual(language_code("he-IL"), "he")

    def test_video_creation_keeps_only_the_original_ten_languages(self):
        expected = ("en", "zh", "de", "vi", "tr", "pt", "ru", "es", "id", "it")
        self.assertEqual(VIDEO_LANGUAGE_CODES, expected)
        options = video_language_options()
        self.assertEqual(options, ["music", *expected])
        for extra_code in ("pl", "ga", "ar", "he"):
            self.assertNotIn(extra_code, options)

    def test_new_ui_codes_have_safe_english_translation_fallback(self):
        for code in ("pl", "ga", "ar", "he"):
            self.assertIn(code, UI_TRANSLATIONS)
            self.assertEqual(UI_TRANSLATIONS[code]["Language"], "Language")


if __name__ == "__main__":
    unittest.main()
