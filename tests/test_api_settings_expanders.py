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
            "Imagem e Video",
            "LLM — providers e modelos",
            "Voz, TTS e música — Azure Speech, restantes serviços e Suno",
            "TikTok for Developers — Client ID e Client Secret",
            "Publicação através do Upload-Post",
            "Postiz — API key, integração e MCP",
        ]
        for label in labels:
            self.assertIn(f'st.expander("{label}", expanded=False)', MAIN_SOURCE)

    def test_voice_services_are_split_into_provider_cards(self):
        start = MAIN_SOURCE.index('with st.expander("Voz, TTS e música — Azure Speech, restantes serviços e Suno", expanded=False):')
        end = MAIN_SOURCE.index('with st.expander("TikTok for Developers — Client ID e Client Secret", expanded=False):', start)
        voice_block = MAIN_SOURCE[start:end]
        for provider in ("Azure Speech", "ElevenLabs", "SiliconFlow", "MiniMax TTS", "Chatterbox", "Sonilo", "Suno — agente musical opcional"):
            self.assertIn(f'st.markdown("#### {provider}")', voice_block)
        self.assertNotIn('voice_test_cols', voice_block)
        for widget_key in (
            'api_test_voice_azure',
            'api_test_voice_elevenlabs',
            'api_test_voice_siliconflow',
            'api_test_voice_minimax',
            'api_test_voice_chatterbox',
            'api_test_voice_sonilo',
            'api_test_voice_suno',
        ):
            self.assertIn(f'widget_key="{widget_key}"', voice_block)

    def test_api_settings_form_and_saved_configuration_remain_present(self):
        self.assertIn('with st.form("settings_form"):', MAIN_SOURCE)
        self.assertIn('st.form_submit_button("Guardar configurações do Thunderbolt"', MAIN_SOURCE)

    def test_nvidia_nim_limit_card_is_inside_llm_expander_before_provider_cards(self):
        start = MAIN_SOURCE.index('def render_llm_provider_cards(')
        end = MAIN_SOURCE.index('def _media_card_config_status(', start)
        llm_block = MAIN_SOURCE[start:end]
        self.assertIn('with st.expander("LLM — providers e modelos", expanded=False):', llm_block)
        limit_position = llm_block.index('st.markdown("### Limite LLM NVIDIA NIM")')
        first_provider_position = llm_block.index('for index in range(len(cards)):')
        self.assertLess(limit_position, first_provider_position)
        settings_start = MAIN_SOURCE.index('def render_settings():')
        settings_block = MAIN_SOURCE[settings_start:]
        self.assertNotIn('st.markdown("### Limite LLM NVIDIA NIM")', settings_block)

    def test_llm_and_media_sections_are_in_main_list_after_apify(self):
        llm_position = MAIN_SOURCE.index('render_llm_provider_cards(settings, embedded=True)')
        apify_position = MAIN_SOURCE.index('with st.expander("Niche Finder — Apify", expanded=False)')
        settings_position = MAIN_SOURCE.index('def render_settings():')
        media_position = MAIN_SOURCE.index('render_media_provider_cards(settings, embedded=True)', settings_position)
        self.assertLess(apify_position, llm_position)
        self.assertLess(llm_position, media_position)
        self.assertIn('with st.expander("Imagem e Video", expanded=False)', MAIN_SOURCE)
        self.assertNotIn('Nano Banana — geração de thumbnails', MAIN_SOURCE)
        self.assertNotIn('Niche Finder — execução remota no Kaggle', MAIN_SOURCE)
        self.assertNotIn('Niche Finder — execução através da Apify', MAIN_SOURCE)

    def test_media_cards_keep_rendering_constraints_out_of_provider_forms(self):
        media_renderer = MAIN_SOURCE[MAIN_SOURCE.index('def _render_media_provider_card('):MAIN_SOURCE.index('def render_media_provider_cards(')]
        self.assertNotIn('Aspect Ratio', media_renderer)
        self.assertNotIn('Image Size', media_renderer)
        self.assertNotIn('aspect_ratio', media_renderer)
        self.assertNotIn('image_size', media_renderer)

    def test_llm_card_uses_priority_instead_of_primary_checkbox(self):
        llm_renderer = MAIN_SOURCE[MAIN_SOURCE.index('def _render_llm_card('):MAIN_SOURCE.index('def render_llm_provider_cards(')]
        self.assertIn('st.number_input(', llm_renderer)
        self.assertIn('"Prioridade"', llm_renderer)
        self.assertNotIn('LLM principal', llm_renderer)
        self.assertNotIn('primary_llm', llm_renderer)
        self.assertNotIn('llm_card_{card_id}_primary', llm_renderer)

    def test_telegram_llm_card_disables_and_explains_priority(self):
        llm_renderer = MAIN_SOURCE[MAIN_SOURCE.index('def _render_llm_card('):MAIN_SOURCE.index('def render_llm_provider_cards(')]
        self.assertIn('disabled=bool(telegram_llm)', llm_renderer)
        self.assertIn('Exclusivo para Notificações de Telegram — prioridade ignorada no pool LLM.', llm_renderer)
        routing_source = (ROOT / 'hermes_ui' / 'provider_routing.py').read_text(encoding='utf-8')
        self.assertIn('not bool(card.get("telegram_llm", False))', routing_source)

    def test_llm_card_matches_reference_layout_structure(self):
        self.assertIn('endpoint_col, action_col = st.columns([1.65, 1.05])', MAIN_SOURCE)
        self.assertIn('action_buttons = st.columns(2)', MAIN_SOURCE)
        self.assertIn('status_cols = st.columns(3)', MAIN_SOURCE)
        self.assertIn('save_clicked = st.form_submit_button("Salvar", type="primary", use_container_width=True, key=f"llm_card_{card_id}_save")', MAIN_SOURCE)

    def test_api_keys_google_accounts_material_sources_and_voice_are_direct_sibling_tabs(self):
        tabs_position = MAIN_SOURCE.index('api_keys_tab, google_accounts_tab, material_sources_tab, ai_influencers_tab, voice_test_tab = render_localized_tabs(["API Keys", "Contas Google", "Fontes de Materiais", "AI Influencers", "Teste de Voz"])')
        api_position = MAIN_SOURCE.index('    with api_keys_tab:', tabs_position)
        google_position = MAIN_SOURCE.index('    with google_accounts_tab:', tabs_position)
        material_position = MAIN_SOURCE.index('    with material_sources_tab:', tabs_position)
        influencers_position = MAIN_SOURCE.index('    with ai_influencers_tab:', tabs_position)
        voice_position = MAIN_SOURCE.index('    with voice_test_tab:', tabs_position)
        self.assertLess(api_position, google_position)
        self.assertLess(google_position, material_position)
        self.assertLess(material_position, influencers_position)
        self.assertLess(influencers_position, voice_position)
        api_block = MAIN_SOURCE[api_position:google_position]
        self.assertNotIn('with st.expander("Banco de Dados Influencers", expanded=False):', api_block)
        self.assertIn('with st.container(border=True):', api_block)
        self.assertIn('with st.form("settings_form"):', api_block)
        influencers_block = MAIN_SOURCE[influencers_position:voice_position]
        self.assertIn('st.subheader("Banco de Dados Influencers")', influencers_block)
        self.assertIn('key="settings_influencer_db_backend"', influencers_block)
        self.assertIn('Supabase Project URL', influencers_block)
        self.assertIn('Supabase API key', influencers_block)
        self.assertIn('Supabase Storage bucket', influencers_block)
        self.assertIn('SQLite ficheiro local', influencers_block)
        self.assertIn('Guardar configuração do backend', influencers_block)
        self.assertIn('render_google_accounts()', MAIN_SOURCE[google_position:material_position])
        self.assertNotIn('render_localized_tabs(["Serviços e modelos", "Fontes de Materiais"])', MAIN_SOURCE)

    def test_material_sources_use_individual_cards_and_add_provider_button(self):
        self.assertIn('def _render_material_source_card(', MAIN_SOURCE)
        self.assertIn('with st.container(border=True):', MAIN_SOURCE[MAIN_SOURCE.index('def _render_material_source_card('):])
        self.assertIn('Configurar Nova Fonte de Materiais', MAIN_SOURCE)
        self.assertIn('key="add_material_source_card"', MAIN_SOURCE)
        self.assertIn('MATERIAL_CARDS_KEY = "material_source_cards"', (ROOT / "hermes_ui" / "material_sources.py").read_text(encoding="utf-8"))

    def test_streamlit_port_is_not_rendered_and_video_engine_path_is_read_only(self):
        self.assertNotIn('st.number_input("Porta Streamlit"', MAIN_SOURCE)
        self.assertNotIn('st.text_input("Pasta do motor de vídeo"', MAIN_SOURCE)
        self.assertIn('moneyprinter_path = str(settings.get("moneyprinter_path") or "").strip()', MAIN_SOURCE)
        self.assertIn('st.caption(f"Pasta do motor de vídeo:', MAIN_SOURCE)

    def test_llm_api_key_success_message_is_short_and_model_count_is_not_shown(self):
        self.assertIn('st.success("Último teste: API Key OK")', MAIN_SOURCE)
        self.assertNotIn('API OK — {_safe_url(base_url)} respondeu com {len(models)} modelo(s).', MAIN_SOURCE)

    def test_every_non_llm_api_key_expander_has_a_diagnostic_control(self):
        expected_controls = (
            'widget_key="api_test_kaggle"',
            'widget_key="api_test_apify"',
            'def render_media_provider_cards(',
            'test_media_provider_card(edited)',
            'widget_key="api_test_voice_azure"',
            'widget_key="api_test_voice_siliconflow"',
            'widget_key="api_test_voice_minimax"',
            'widget_key="api_test_voice_elevenlabs"',
            'widget_key="api_test_voice_chatterbox"',
            'widget_key="api_test_voice_sonilo"',
            'widget_key="api_test_voice_suno"',
            'widget_key="api_test_tiktok"',
            'widget_key="api_test_upload_post"',
            'widget_key="api_test_postiz"',
        )
        for control in expected_controls:
            self.assertIn(control, MAIN_SOURCE)
        self.assertIn('if st.form_submit_button("Testar chamada API"', MAIN_SOURCE)
        self.assertIn('st.form_submit_button("Testar Chamada API"', MAIN_SOURCE)
        self.assertIn('test_media_provider_card(edited)', MAIN_SOURCE)
        self.assertIn('settings["api_test_results"] = stored', MAIN_SOURCE)
        self.assertNotIn('widget_key="api_test_llm"', MAIN_SOURCE)

    def test_material_remote_cards_have_diagnostic_controls_but_local_source_does_not_fake_one(self):
        self.assertIn('test_material_source_credentials(provider, api_key)', MAIN_SOURCE)
        self.assertIn('f"material:{card_id}"', MAIN_SOURCE)
        self.assertIn('if not is_local:', MAIN_SOURCE)

    def test_new_api_tab_titles_have_all_language_translations(self):
        for language in LANGUAGE_CODES:
            self.assertIn("API Keys", UI_TRANSLATIONS[language])
            self.assertIn("Contas Google", UI_TRANSLATIONS[language])
            self.assertIn("Fontes de Materiais", UI_TRANSLATIONS[language])
            self.assertIn("Teste de Voz", UI_TRANSLATIONS[language])

    def test_material_card_labels_have_all_language_translations(self):
        labels = (
            "Configurar Nova Fonte de Materiais",
            "Provedor de materiais",
            "Fonte activa",
            "Usar esta fonte na pipeline",
            "Esta fonte não usa API key.",
        )
        for language in LANGUAGE_CODES:
            for label in labels:
                self.assertIn(label, UI_TRANSLATIONS[language])

    def test_new_api_expander_titles_have_all_language_translations(self):
        for language in LANGUAGE_CODES:
            self.assertIn("Niche Finder — Kaggle", UI_TRANSLATIONS[language])
            self.assertIn("Niche Finder — Apify", UI_TRANSLATIONS[language])
            self.assertIn("Imagem e Video", UI_TRANSLATIONS[language])

    def test_api_test_feedback_has_all_language_translations(self):
        labels = (
            "Testar chamada API",
            "A testar chamada API…",
            "Último teste: API Key OK",
            "Último teste: falta configuração",
            "Último teste: requer autorização ou endpoint seguro",
            "Último teste: chamada falhou",
            "Testar credenciais TTS e música",
        )
        for language in LANGUAGE_CODES:
            for label in labels:
                self.assertIn(label, UI_TRANSLATIONS[language])


if __name__ == "__main__":
    unittest.main()
