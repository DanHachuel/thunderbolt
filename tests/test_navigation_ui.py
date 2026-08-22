from pathlib import Path


MAIN_SOURCE = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")


def test_automation_is_an_expander_with_youtube_child_page():
    assert 'automation_items = [' in MAIN_SOURCE
    assert '("Automação Youtube", ":material/schedule:", "Automação Youtube")' in MAIN_SOURCE
    assert 'elif target == "Automação":' in MAIN_SOURCE
    assert 'with st.expander(ui_text("Automação", ui_language), expanded=current_page in {item[0] for item in automation_items}' in MAIN_SOURCE
    assert '"Automação Youtube": render_automation' in MAIN_SOURCE
    assert 'st.title("Automação Youtube")' in MAIN_SOURCE


def test_youtube_navigation_labels_and_legacy_aliases_are_preserved():
    assert '("Canais Youtube", ":material/ondemand_video:", "Canais Youtube")' in MAIN_SOURCE
    assert '("Blueprints Youtube", ":material/library_books:", "Blueprints Youtube")' in MAIN_SOURCE
    assert '"Canais Youtube": render_channels' in MAIN_SOURCE
    assert '"Blueprints Youtube": render_blueprints' in MAIN_SOURCE
    assert '"Canais": "Canais Youtube"' in MAIN_SOURCE
    assert '"Blueprints": "Blueprints Youtube"' in MAIN_SOURCE
    assert '"Automação": "Automação Youtube"' in MAIN_SOURCE


def test_settings_children_are_split_into_google_api_and_notifications():
    assert '("Contas Google", ":material/account_circle:", "Contas Google")' in MAIN_SOURCE
    assert '("Configuração API", ":material/settings:", "Configuração API")' in MAIN_SOURCE
    assert '("Notificações", ":material/notifications:", "Notificações")' in MAIN_SOURCE
    assert '"Contas Google": render_google_accounts' in MAIN_SOURCE
    assert '"Configuração API": render_settings' in MAIN_SOURCE
    assert '"Notificações": render_notifications' in MAIN_SOURCE
    assert '"Configurações Técnicas": "Configuração API"' in MAIN_SOURCE


def test_models_ai_has_meta_tutorial_renderer():
    assert '("Tutorial Meta", ":material/menu_book:", "Tutorial Meta")' in MAIN_SOURCE
    assert '"Tutorial Meta": render_models_ai_tutorial' in MAIN_SOURCE
    assert 'https://github.com/gyoridavid/ai_agents_az/blob/main/episode_8/guide-instagram.md' in MAIN_SOURCE
    assert 'ROOT / "seed" / "references" / "guide-instagram.md"' in MAIN_SOURCE


def test_google_configuration_keeps_account_fields_and_api_page_does_not_duplicate_them():
    google_start = MAIN_SOURCE.index("def render_google_accounts():")
    settings_start = MAIN_SOURCE.index("def render_settings():")
    notifications_start = MAIN_SOURCE.index("def render_notifications():")
    google_page = MAIN_SOURCE[google_start:settings_start]
    api_page = MAIN_SOURCE[settings_start:notifications_start]
    assert "INNERTUBE_API_KEY" in google_page
    assert "sessionInfo" in google_page
    assert "google_global_api_settings_form" in google_page
    assert "google_page_youtube_client_id" in google_page
    assert "google_page_youtube_client_secret" in google_page
    assert "google_page_youtube_api_key" in google_page
    assert 'YouTube OAuth Client ID' not in api_page
    assert 'YouTube OAuth Client Secret' not in api_page
    assert 'YouTube Data API Key' not in api_page


def test_tutorial_reference_is_packaged_and_contains_meta_setup_sections():
    tutorial_path = Path(__file__).resolve().parents[1] / "seed" / "references" / "guide-instagram.md"
    tutorial = tutorial_path.read_text(encoding="utf-8")
    assert "# Setting up Instagram for automations with n8n" in tutorial
    assert "## Convert the Instagram account to a professional account" in tutorial
    assert "### 3. Create a Facebook application" in tutorial
    assert "pages_show_list" in tutorial
    assert "instagram_content_publish" in tutorial
    assert "https://github.com/gyoridavid/ai_agents_az/blob/main/episode_8/guide-instagram.md" in tutorial
    assert "Join our Skool community" not in tutorial
    assert "Be part of a growing community" not in tutorial


def test_models_ai_is_renamed_in_visible_navigation_with_legacy_alias():
    assert '("AI Influencers", ":material/smart_toy:", "AI Influencers")' in MAIN_SOURCE
    assert 'elif target == "AI Influencers":' in MAIN_SOURCE
    assert 'with st.expander(ui_text("AI Influencers", ui_language)' in MAIN_SOURCE
    assert '"AI Influencers": lambda: render_edit_placeholder("AI Influencers"' in MAIN_SOURCE
    assert '("Models AI", ":material/smart_toy:", "Models AI")' not in MAIN_SOURCE


def test_edition_contains_media_download_page_and_controls():
    assert '("Download Mídia", ":material/download:", "Download Mídia")' in MAIN_SOURCE
    assert '"Download Mídia": render_media_download' in MAIN_SOURCE
    assert 'def render_media_download()' in MAIN_SOURCE
    for label in ("URLs para descarregar", "Tipo de mídia", "Qualidade", "Contentor", "Formato de áudio", "Permitir playlist", "Descarregar legendas", "Incorporar metadados", "Iniciar download", "Histórico de downloads"):
        assert label in MAIN_SOURCE
    assert 'from hermes_ui.media_downloader import' in MAIN_SOURCE


def test_api_keys_contains_material_sources_subtab_with_multi_key_controls():
    settings_start = MAIN_SOURCE.index("def render_settings():")
    settings_page = MAIN_SOURCE[settings_start:]
    material_sources_page = MAIN_SOURCE[MAIN_SOURCE.index("def render_material_source_api_keys("):]
    assert 'api_keys_tab, voice_test_tab = st.tabs(["API Keys", "Teste de vozes"])' in settings_page
    assert 'api_service_tab, material_sources_tab = st.tabs(["Serviços e modelos", "Fontes de materiais"])' in settings_page
    assert 'with material_sources_tab:' in settings_page
    assert 'render_material_source_api_keys(settings)' in settings_page
    for label in ("Fonte de materiais", "Adicionar outra chave", "Guardar fonte e chaves"):
        assert label in material_sources_page
    assert 'Pexels API keys' not in settings_page
    assert 'Pixabay API keys' not in settings_page
    assert 'Pasta de materiais' not in settings_page
    assert 'Caminho FFmpeg' not in settings_page
    assert 'Proxy HTTP' not in settings_page
    assert 'Alinhar materiais ao roteiro' not in settings_page


def test_language_picker_uses_native_layout_without_touching_streamlit_toolbar():
    assert '"Language"' in MAIN_SOURCE
    assert "ui_language_menu_label" in MAIN_SOURCE
    assert "LANGUAGE_FLAG_DATA_URIS" in MAIN_SOURCE
    assert 'top_language_code_selector' in MAIN_SOURCE
    assert 'st.popover' not in MAIN_SOURCE
    assert 'stAppDeployButton' not in MAIN_SOURCE
    assert 'stMainMenu' not in MAIN_SOURCE
    assert 'right:1.5rem' not in MAIN_SOURCE
