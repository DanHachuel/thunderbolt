from __future__ import annotations

from pathlib import Path


MAIN_SOURCE = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")


def test_music_backlog_is_registered_under_the_music_pipeline_menu():
    music_items = MAIN_SOURCE.split("music_items = [", 1)[1].split("]", 1)[0]

    assert '("Music Backlog", ":material/queue_music:", "Music Backlog")' in music_items
    assert '"Music Backlog": render_music_backlog' in MAIN_SOURCE


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
    assert '"Tipo")' in backlog
    assert '"Áudio")' in backlog


def test_music_creation_is_audio_only_and_supports_suno_and_lyria():
    creation = MAIN_SOURCE.split("def render_music_creation()", 1)[1].split("def render_scripts", 1)[0]

    assert 'st.selectbox("Provider de geração musical", ["Suno AI", "Google Lyria"]' in creation
    assert 'st.form_submit_button("Adicionar ao Music Backlog"' in creation
    assert "MoneyPrinterTurbo" in creation
    assert "render_new_video" not in creation
    assert '"Google Lyria API key"' in MAIN_SOURCE
