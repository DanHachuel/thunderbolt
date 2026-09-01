from pathlib import Path


def test_youtube_search_button_validates_input_and_calls_selected_lookup():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    start = source.index('if st.button("Buscar no YouTube"')
    end = source.index('with col2:', start)
    block = source[start:end]
    assert 'search_source = str(source or "").strip()' in block
    assert 'youtube.fetch_channel_public(search_source)' in block
    assert 'youtube.fetch_channel(search_source)' in block
    assert 'with st.spinner("A pesquisar o canal no YouTube…")' in block
    assert 'except Exception as exc:' in block
    assert 'st.session_state["yt_message"]' in block


def test_public_lookup_accepts_only_youtube_domain():
    source = Path(__file__).parents[1].joinpath("integrations", "platforms.py").read_text(encoding="utf-8")
    assert 'host != "youtube.com" and not host.endswith(".youtube.com")' in source
