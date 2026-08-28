from __future__ import annotations

from pathlib import Path


MAIN_SOURCE = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")


def test_music_backlog_is_registered_under_the_music_pipeline_menu():
    music_items = MAIN_SOURCE.split("music_items = [", 1)[1].split("]", 1)[0]

    assert '("Music Backlog", ":material/queue_music:", "Music Backlog")' in music_items
    assert '"Music Backlog": render_music_backlog' in MAIN_SOURCE


def test_music_and_video_backlogs_filter_the_shared_task_catalog():
    assert "def load_music_tasks_for_catalog()" in MAIN_SOURCE
    assert "def load_standard_video_tasks_for_catalog()" in MAIN_SOURCE
    assert 'return [task for task in load_video_tasks_for_catalog() if _is_music_task(task)]' in MAIN_SOURCE
    assert 'return [task for task in load_video_tasks_for_catalog() if not _is_music_task(task)]' in MAIN_SOURCE


def test_music_backlog_has_the_same_state_controls_as_video_backlog():
    backlog = MAIN_SOURCE.split("def render_music_backlog()", 1)[1].split("def _thumbnail_editor_context", 1)[0]

    assert 'st.selectbox("Filtrar por estado"' in backlog
    assert 'key=f"music_backlog_start_{task[\'id\']}"' in backlog
    assert 'key=f"music_backlog_stop_{task[\'id\']}"' in backlog
    assert 'transition_task(task["id"], "doing")' in backlog
    assert 'transition_task(task["id"], "blocked")' in backlog
