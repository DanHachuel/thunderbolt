from __future__ import annotations

from pathlib import Path


def test_upload_form_places_ai_description_action_between_description_and_tags():
    source = Path(__file__).resolve().parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    block = source.split("def render_upload_conventional():", 1)[1].split("def render_upload_direct():", 1)[0]
    assert block.index('description = st.text_area("Descrição"') < block.index('st.button("Gerar descrição com IA"') < block.index('tags_raw = st.text_input("Tags separadas por vírgula"')
    assert 'on_click=generate_upload_description_callback' in block
    assert 'st.session_state[description_state_key] = generate_video_description(' in block


def test_upload_form_detects_task_language_and_uses_canonical_dropdown():
    source = Path(__file__).resolve().parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    block = source.split("def render_upload_conventional():", 1)[1].split("def render_upload_direct():", 1)[0]
    youtube_block = block.split('if "YouTube" in destination:', 1)[1].split("quota_count = official_upload_count", 1)[0]

    assert 'detected_language = normalize_video_language(task.get("language") or channel.get("language") or "pt")' in youtube_block
    assert 'language = st.selectbox(' in youtube_block
    assert 'VIDEO_LANGUAGE_SELECTION_OPTIONS' in youtube_block
    assert 'format_func=video_language_label' in youtube_block
    assert 'st.text_input("Idioma", value="pt-BR"' not in youtube_block
