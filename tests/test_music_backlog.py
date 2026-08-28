from __future__ import annotations

from pathlib import Path


MAIN_SOURCE = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")


def test_music_backlog_is_registered_under_the_music_pipeline_menu():
    music_items = MAIN_SOURCE.split("music_items = [", 1)[1].split("]", 1)[0]

    assert '("Music Backlog", ":material/queue_music:", "Music Backlog")' in music_items
    assert '"Music Backlog": render_music_backlog' in MAIN_SOURCE
    assert '("Vozes Personalizadas", ":material/record_voice_over:", "Vozes Personalizadas")' in music_items
    assert '"Vozes Personalizadas": render_custom_music_voices' in MAIN_SOURCE


def test_custom_music_voices_is_an_empty_reserved_blueprint_area():
    voices = MAIN_SOURCE.split("def render_custom_music_voices()", 1)[1].split("def render_scripts", 1)[0]

    assert 'st.title("Vozes Personalizadas")' in voices
    assert "st.text_input(" not in voices
    assert "st.file_uploader(" not in voices


def test_music_backlog_uses_its_own_audio_task_pool():
    backlog = MAIN_SOURCE.split("def render_music_backlog()", 1)[1].split("def _thumbnail_editor_context", 1)[0]

    assert "tasks = list_music_tasks()" in backlog
    assert "_render_pipeline_progress_panel()" not in backlog
    assert "load_video_tasks_for_catalog()" not in backlog
    assert "Worker de vídeo" not in backlog


def test_music_backlog_has_the_same_state_controls_as_video_backlog():
    backlog = MAIN_SOURCE.split("def render_music_backlog()", 1)[1].split("def _thumbnail_editor_context", 1)[0]

    assert 'st.selectbox("Filtrar por estado"' in backlog
    assert 'key=f"music_backlog_start_{task[\'id\']}"' in backlog
    assert 'key=f"music_backlog_stop_{task[\'id\']}"' in backlog
    assert 'run_music_task(str(task["id"]), read_json("settings.json", {}))' in backlog
    assert 'transition_music_task(str(task["id"]), "blocked")' in backlog
    assert '"Descarregar música"' in backlog
    assert 'key=f"music_backlog_download_{task[\'id\']}"' in backlog
    assert '"Tipo")' in backlog
    assert '"Áudio")' in backlog


def test_music_creation_is_audio_only_and_supports_suno_and_lyria():
    creation = MAIN_SOURCE.split("def render_music_creation()", 1)[1].split("def render_scripts", 1)[0]

    assert 'st.selectbox("Provider de geração musical", ["Suno AI", "Google Lyria"]' in creation
    assert '"Idioma da letra/música"' in creation
    assert 'st.selectbox("Género musical", list(MUSIC_GENRES)' in creation
    assert 'st.selectbox("Vocal", list(MUSIC_VOCAL_OPTIONS)' in creation
    assert '"Referências culturais, paisagens, clima ou artistas similares (opcional)"' in creation
    assert 'st.button("Gerar campos musicais com IA"' in creation
    assert 'st.button("Gerar Música"' in creation
    assert 'st.session_state["music_task_generated_fields"] = generated' in creation
    assert 'Adicionar ao Music Backlog' not in creation
    assert "MoneyPrinterTurbo" in creation
    assert "render_new_video" not in creation
    assert '"Google Lyria API key"' in MAIN_SOURCE


def test_google_lyria_configuration_has_a_safe_api_test_control():
    settings = MAIN_SOURCE.split('st.markdown("#### Google Lyria — geração musical")', 1)[1].split('with st.expander("Publicação através do Upload-Post"', 1)[0]

    assert 'text_setting("Google Lyria API key", "lyria_api_key", secret=True' in settings
    assert 'st.selectbox("Modelo Google Lyria"' in settings
    assert 'st.form_submit_button("Guardar Google Lyria"' in settings
    assert 'test_voice_provider("google_lyria", {"lyria_api_key": lyria_api_key, "lyria_model": lyria_model})' in settings
    assert 'widget_key="api_test_voice_google_lyria"' in settings


def test_thumbnail_cards_offer_download_for_generated_images():
    thumbnails = MAIN_SOURCE.split("def render_thumbnails():", 1)[1].split("def render_automation():", 1)[0]

    assert '"Descarregar thumbnail"' in thumbnails
    assert 'key=f"thumbnail_download_{task_id}_{record[\'variant_index\']}"' in thumbnails
