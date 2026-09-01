from app.main import classify_channel_platform, is_youtube_channel_record


def test_youtube_and_tiktok_filters_are_complementary_with_legacy_records():
    records = [
        {"platform": "youtube", "url": "https://www.youtube.com/@canal"},
        {"platform": "tiktok", "url": "https://www.tiktok.com/@canal"},
        {"platform": " YouTube "},
        {"platform": "Tik Tok"},
        {"url": "https://www.youtube.com/channel/UC123"},
        {"url": "https://www.tiktok.com/@canal"},
        {"name": "YouTube antigo", "handle": "@canal"},
        {},
    ]
    youtube = [record for record in records if is_youtube_channel_record(record)]
    tiktok = [record for record in records if classify_channel_platform(record) == "tiktok"]
    assert len(youtube) == 5
    assert len(tiktok) == 3
    assert not set(map(id, youtube)) & set(map(id, tiktok))
    assert all(classify_channel_platform(record) == "youtube" for record in youtube)
    assert all(classify_channel_platform(record) == "tiktok" for record in tiktok)


def test_legacy_youtube_records_remain_visible_but_tiktok_markers_do_not():
    assert is_youtube_channel_record({"url": "https://www.youtube.com/channel/UC123"})
    assert is_youtube_channel_record({"name": "Canal antigo", "handle": "@canal"})
    assert not is_youtube_channel_record({"url": "https://www.tiktok.com/@canal"})
    assert not is_youtube_channel_record({"metrics_source": "tiktok_public_page"})


def test_youtube_channels_ui_filters_both_table_and_card_loops():
    from pathlib import Path
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    start = source.index('def render_channels():')
    end = source.index('def render_', start + 20)
    block = source[start:end]
    assert block.count('is_youtube_channel_record(channel)') >= 2
    assert '\n    channels = read_json("channels.json", [])' not in block
