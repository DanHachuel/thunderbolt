from pathlib import Path

from app.main import is_youtube_channel_record


def test_youtube_channels_table_filters_tiktok_records():
    assert is_youtube_channel_record({"platform": "youtube", "url": "https://www.youtube.com/@canal"})
    assert not is_youtube_channel_record({"platform": "tiktok", "url": "https://www.tiktok.com/@canal"})
    assert not is_youtube_channel_record({"url": "https://www.tiktok.com/@canal", "metrics_source": "tiktok_public_page"})
    assert not is_youtube_channel_record({"tiktok_username": "canal", "name": "Canal antigo"})


def test_youtube_channels_table_uses_centralized_legacy_filter():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    start = source.index('st.subheader("Canais cadastrados")')
    end = source.index('with batch_tab:', start)
    block = source[start:end]
    assert 'is_youtube_channel_record(channel)' in block
