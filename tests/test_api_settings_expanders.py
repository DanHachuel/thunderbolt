from pathlib import Path
import unittest

from hermes_ui.languages import LANGUAGE_CODES, UI_TRANSLATIONS


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")


class ApiSettingsExpandersTests(unittest.TestCase):
    def test_api_settings_expandable_sections_are_closed_by_default(self):
        labels = [
            "Niche Finder — Kaggle",
            "Niche Finder — Apify",
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

    def test_llm_section_is_in_main_list_between_apify_and_nano_banana(self):
        llm_position = MAIN_SOURCE.index('render_llm_provider_cards(settings, embedded=True)')
        apify_position = MAIN_SOURCE.index('with st.expander("Niche Finder — Apify", expanded=False)')
        nano_position = MAIN_SOURCE.index('with st.expander("Nano Banana — geração de thumbnails", expanded=False)')
        self.assertLess(apify_position, llm_position)
        self.assertLess(llm_position, nano_position)
        self.assertNotIn('Niche Finder — execução remota no Kaggle', MAIN_SOURCE)
        self.assertNotIn('Niche Finder — execução através da Apify', MAIN_SOURCE)

    def test_llm_card_matches_reference_layout_structure(self):
        self.assertIn('endpoint_col, action_col = st.columns([1.65, 1.05])', MAIN_SOURCE)
        self.assertIn('action_buttons = st.columns(2)', MAIN_SOURCE)
        self.assertIn('status_cols = st.columns(3)', MAIN_SOURCE)
        self.assertIn('save_clicked = st.form_submit_button("Salvar", type="primary", use_container_width=True, key=f"llm_card_{card_id}_save")', MAIN_SOURCE)

    def test_api_keys_material_sources_and_voice_are_direct_sibling_tabs(self):
        tabs_position = MAIN_SOURCE.index('api_keys_tab, material_sources_tab, voice_test_tab = render_localized_tabs(["API Keys", "Fontes de Materiais", "Teste de Voz"])')
        api_position = MAIN_SOURCE.index('    with api_keys_tab:', tabs_position)
        material_position = MAIN_SOURCE.index('    with material_sources_tab:', tabs_position)
        voice_position = MAIN_SOURCE.index('    with voice_test_tab:', tabs_position)
        self.assertLess(api_position, material_position)
        self.assertLess(material_position, voice_position)
        api_block = MAIN_SOURCE[api_position:material_position]
        self.assertIn('with st.container(border=True):', api_block)
        self.assertIn('with st.form("settings_form"):', api_block)
        self.assertNotIn('render_localized_tabs(["Serviços e modelos", "Fontes de Materiais"])', MAIN_SOURCE)

    def test_streamlit_port_is_not_rendered_and_video_engine_path_is_read_only(self):
        self.assertNotIn('st.number_input("Porta Streamlit"', MAIN_SOURCE)
        self.assertNotIn('st.text_input("Pasta do motor de vídeo"', MAIN_SOURCE)
        self.assertIn('moneyprinter_path = str(settings.get("moneyprinter_path") or "").strip()', MAIN_SOURCE)
        self.assertIn('st.caption(f"Pasta do motor de vídeo:', MAIN_SOURCE)

    def test_new_api_tab_titles_have_all_language_translations(self):
        for language in LANGUAGE_CODES:
            self.assertIn("API Keys", UI_TRANSLATIONS[language])
            self.assertIn("Fontes de Materiais", UI_TRANSLATIONS[language])
            self.assertIn("Teste de Voz", UI_TRANSLATIONS[language])

    def test_new_api_expander_titles_have_all_language_translations(self):
        for language in LANGUAGE_CODES:
            self.assertIn("Niche Finder — Kaggle", UI_TRANSLATIONS[language])
            self.assertIn("Niche Finder — Apify", UI_TRANSLATIONS[language])


if __name__ == "__main__":
    unittest.main()
