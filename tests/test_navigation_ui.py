from pathlib import Path


MAIN_SOURCE = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")


def test_automation_is_an_expander_with_youtube_child_page():
    assert 'automation_items = [' in MAIN_SOURCE
    assert '("Automação Youtube", ":material/schedule:", "Automação Youtube")' in MAIN_SOURCE
    assert 'elif target == "Automação":' in MAIN_SOURCE
    assert 'with st.expander("Automação", expanded=current_page in {item[0] for item in automation_items}' in MAIN_SOURCE
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
