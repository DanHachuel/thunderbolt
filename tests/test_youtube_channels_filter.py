from app.main import is_youtube_channel_record


def test_youtube_channels_table_filters_tiktok_records():
    assert is_youtube_channel_record({"platform": "youtube", "url": "https://www.youtube.com/@canal"})
    assert not is_youtube_channel_record({"platform": "tiktok", "url": "https://www.tiktok.com/@canal"})
    assert not is_youtube_channel_record({"url": "https://www.tiktok.com/@canal", "metrics_source": "tiktok_public_page"})
    assert not is_youtube_channel_record({"tiktok_username": "canal", "name": "Canal antigo"})
    assert not is_youtube_channel_record({"metadata": {"source": "Tik Tok", "profile": {"network": "short video"}}})


def test_youtube_channels_table_keeps_youtube_records_without_platform():
    assert is_youtube_channel_record({"url": "https://www.youtube.com/channel/UC123", "metrics_source": "youtube_public_page"})
