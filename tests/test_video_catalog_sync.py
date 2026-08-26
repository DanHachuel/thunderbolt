"""Contracts for the shared video catalog and automation card state display."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")


def test_backlog_and_automation_use_the_same_complete_task_catalog():
    assert "def load_video_tasks_for_catalog()" in MAIN_SOURCE
    assert MAIN_SOURCE.count("tasks = load_video_tasks_for_catalog()") >= 2
    assert "Return the complete persisted task catalog shared by Backlog and Automation" in MAIN_SOURCE


def test_automation_video_cards_show_state_progress_and_format_like_backlog():
    assert MAIN_SOURCE.count("_render_video_task_state(task)") >= 2
    assert MAIN_SOURCE.count("_video_task_format(task)") >= 2
    for state in ("to_do", "doing", "blocked", "done", "failed", "cancelled"):
        assert f'"{state}":' in MAIN_SOURCE
    assert 'st.progress(progress, text=f"{progress}%")' in MAIN_SOURCE
    assert 'st.caption("Formato")' in MAIN_SOURCE
    assert 'value = task.get("format") or task.get("style_wide") or task.get("style") or "wide"' in MAIN_SOURCE


def test_backlog_includes_extra_states_instead_of_dropping_them_from_the_filter():
    assert 'extra_states = sorted({str(task.get("state") or "unknown")' in MAIN_SOURCE
    assert 'state_filter = st.selectbox("Filtrar por estado", ["Todos", *known_states, *extra_states]' in MAIN_SOURCE
