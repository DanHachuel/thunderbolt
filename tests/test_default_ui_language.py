from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
LAUNCHER_SOURCE = (ROOT / "scripts" / "cli.mjs").read_text(encoding="utf-8")


class DefaultUiLanguageTests(unittest.TestCase):
    def test_root_defaults_to_english_without_query_parameter(self):
        self.assertIn('DEFAULT_UI_LANGUAGE = "en"', MAIN_SOURCE)
        self.assertIn('normalized = DEFAULT_UI_LANGUAGE', MAIN_SOURCE)
        self.assertNotIn('settings.get("ui_language") or "pt"', MAIN_SOURCE)

    def test_explicit_english_route_remains_supported(self):
        self.assertIn('supportedLanguages = new Set(["en",', LAUNCHER_SOURCE)
        self.assertIn('requestUrl.searchParams.set("lang", languagePrefix);', LAUNCHER_SOURCE)

    def test_other_language_routes_remain_supported(self):
        for code in ("pt", "es", "zh", "de", "vi", "tr", "ru", "id", "it"):
            self.assertIn(f'"{code}"', LAUNCHER_SOURCE)


if __name__ == "__main__":
    unittest.main()
