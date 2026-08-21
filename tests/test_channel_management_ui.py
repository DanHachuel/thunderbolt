from pathlib import Path


def test_channel_cards_expose_editable_darkplanner_sections():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert 'edit_channel_button_' in source
    assert 'Editar canal' in source
    assert 'Prompts do Canal' in source
    assert 'Canais de Referência' in source
    assert 'Narrador' in source
    assert 'Últimos 10 vídeos publicados' in source
    assert 'Actualizar últimos 10 vídeos' in source


def test_channel_video_views_support_list_and_kanban_with_edit_action():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert 'st.radio("Vista", ["Lista", "Kanban"]' in source
    assert 'Editar vídeo' in source
    assert 'channel_videos.json' in source
    assert 'fetch_channel_videos_public(channel, limit=10)' in source


def test_manual_and_imported_channel_forms_have_niche_field():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert 'key="yt_import_niche"' in source
    assert 'key="manual_channel_niche"' in source
    assert '"reference_channels"' in source
