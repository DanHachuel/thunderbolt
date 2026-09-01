from pathlib import Path


def test_youtube_channel_delete_ui_has_confirmation_and_persistence_call():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    start = source.index('delete_key = f"delete_pending_{channel_id}"')
    end = source.index('if st.session_state.get(edit_key):', start)
    block = source[start:end]
    assert 'st.session_state[delete_key] = True' in block
    assert 'st.button("Confirmar apagar"' in block
    assert 'removed = delete_channel(channel_id)' in block
    assert 'st.button("Cancelar"' in block
    assert 'st.rerun()' in block


def test_youtube_channel_page_filters_both_table_and_card_loops():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    start = source.index('def render_channels():')
    end = source.index('def render_', start + 20)
    block = source[start:end]
    expected = 'is_youtube_channel_record(channel)'
    assert block.count(expected) >= 2
    assert '\n    channels = read_json("channels.json", [])' not in block
