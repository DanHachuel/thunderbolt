from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")


class ApiSettingsExpandersTests(unittest.TestCase):
    def test_api_settings_expandable_sections_are_closed_by_default(self):
        labels = [
            "Niche Finder — execução remota no Kaggle",
            "Niche Finder — execução através da Apify",
            "Nano Banana — geração de thumbnails",
            "LLM — providers e modelos",
            "Voz, TTS e música — Azure Speech, restantes serviços e Suno",
            "TikTok for Developers — Client ID e Client Secret",
            "Publicação através do Upload-Post",
            "Postiz — API key, integração e MCP",
        ]
        for label in labels:
            self.assertIn(f'st.expander("{label}", expanded=False)', MAIN_SOURCE)

    def test_api_settings_form_and_saved_configuration_remain_present(self):
        self.assertIn('with st.form("settings_form"):', MAIN_SOURCE)
        self.assertIn('st.form_submit_button("Guardar configurações do Thunderbolt"', MAIN_SOURCE)


if __name__ == "__main__":
    unittest.main()
