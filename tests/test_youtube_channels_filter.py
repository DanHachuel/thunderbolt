from pathlib import Path


def test_youtube_channels_table_filters_tiktok_records():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    start = source.index('st.subheader("Canais cadastrados")')
    end = source.index('with batch_tab:', start)
    block = source[start:end]
    assert 'channel.get("platform") or "youtube"' in block
    assert '!= "tiktok"' in block
    assert 'registered_rows = [' in block
