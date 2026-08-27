from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
UI = (ROOT / "app" / "influencers_ui.py").read_text(encoding="utf-8")
SCHEMA = (ROOT / "seed" / "references" / "ai_influencers_schema.sql").read_text(encoding="utf-8")


def test_api_configuration_adds_ai_influencers_tab_and_database_expander():
    assert 'render_localized_tabs(["API Keys", "Contas Google", "Fontes de Materiais", "AI Influencers", "Teste de Voz"])' in MAIN
    assert 'with st.expander("Banco de Dados Influencers", expanded=False):' in MAIN
    assert "SQLite local funciona sem credenciais externas" in MAIN
    assert '"influencer_db_backend": influencer_db_backend' in MAIN
    assert '"influencer_supabase_url": influencer_supabase_url.strip()' in MAIN
    assert '"influencer_sqlite_path": influencer_sqlite_path.strip()' in MAIN


def test_ai_influencers_routes_are_real_and_content_has_three_subtabs():
    assert '"Personagens": lambda: render_ai_influencer_characters' in MAIN
    assert '"Geração de Conteúdo IA": lambda: render_ai_influencer_content' in MAIN
    assert 'language_options=VIDEO_LANGUAGE_SELECTION_OPTIONS' in MAIN
    assert 'language_formatter=video_language_label' in MAIN
    assert 'language_normalizer=normalize_video_language' in MAIN
    assert '"Motion Control": render_ai_influencer_motion_control' not in MAIN
    assert '("Motion Control", ":material/motion_mode:", "Motion Control")' not in MAIN
    assert 'st.tabs(["Imagens", "Vídeos", "Motion Control"])' in UI
    assert 'language_options: list[str] | None = None' in UI
    assert 'language = st.selectbox(' in UI
    assert 'edit_language = st.selectbox(' in UI
    assert 'format_func=language_formatter' in UI
    assert 'st.text_input("Idioma"' not in UI
    assert 'accept_multiple_files=True' in UI
    assert '".md"' in UI and '".json"' in UI
    assert 'st.file_uploader' in UI


def test_new_character_form_clears_fields_after_save():
    assert 'with st.form("influencer_create_form", clear_on_submit=True):' in UI
    assert 'key="influencer_new_name"' in UI
    assert 'key="influencer_new_language"' in UI
    assert 'key="influencer_new_instagram_id"' in UI
    assert 'key="influencer_new_bio"' in UI
    assert 'key="influencer_new_assets"' in UI


def test_video_ui_uses_active_video_pool_instead_of_hardcoded_veo():
    assert '_provider_options(settings, "video")' in UI
    assert 'media_cards_for_pool(settings, pool)' in UI
    assert 'Provider / modelo de vídeo' in UI
    assert 'Não existem providers activos no pool de vídeo' in UI
    assert 'Veo 3.1' not in UI


def test_supabase_schema_contains_legacy_entities_and_content_indexes():
    for table in ("influencers", "influencer_assets", "influencer_weekly_plans", "influencer_content"):
        assert f"create table if not exists public.{table}" in SCHEMA
    assert "unique (influencer_id, sha256)" in SCHEMA
    assert "idx_influencer_content_state" in SCHEMA
    assert "enable row level security" in SCHEMA
