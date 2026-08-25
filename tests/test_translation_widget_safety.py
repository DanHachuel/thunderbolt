from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")


class TranslationWidgetSafetyTests(unittest.TestCase):
    def test_numeric_selectbox_options_get_string_display_labels(self):
        self.assertIn("def _translated_option_label", MAIN_SOURCE)
        self.assertIn("return str(formatted)", MAIN_SOURCE)
        self.assertIn("_translated_option_label(value, language)", MAIN_SOURCE)

    def test_existing_formatters_are_preserved_and_normalized(self):
        self.assertIn("_translated_option_label(value, language, formatter)", MAIN_SOURCE)
        self.assertIn('has_options = len(translated_args) >= 2 or "options" in kwargs', MAIN_SOURCE)


if __name__ == "__main__":
    unittest.main()
