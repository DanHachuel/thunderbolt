from app.main import classify_channel_platform, is_youtube_channel_record


def test_youtube_and_tiktok_filters_are_complementary():
    records = [
        {"platform": "youtube", "url": "https://www.youtube.com/@canal"},
        {"platform": "tiktok", "url": "https://www.tiktok.com/@canal"},
        {"platform": " YouTube "},
        {"platform": "Tik Tok"},
        {"url": "https://www.youtube.com/channel/UC123"},
        {"url": "https://www.tiktok.com/@canal"},
        {},
    ]
    youtube = [record for record in records if is_youtube_channel_record(record)]
    tiktok = [record for record in records if classify_channel_platform(record) == "tiktok"]
    assert len(youtube) == 2
    assert len(tiktok) == 2
    assert not set(map(id, youtube)) & set(map(id, tiktok))
    assert all(classify_channel_platform(record) == "youtube" for record in youtube)
    assert all(classify_channel_platform(record) == "tiktok" for record in tiktok)


def test_unknown_platform_is_not_assigned_to_youtube_by_default():
    assert classify_channel_platform({"url": "https://www.youtube.com/channel/UC123"}) == "unknown"
    assert not is_youtube_channel_record({"url": "https://www.youtube.com/channel/UC123"})


def test_youtube_channels_ui_uses_centralized_filter():
    from pathlib import Path
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert 'registered_channels = [channel for channel in read_json("channels.json", []) if is_youtube_channel_record(channel)]' in source
    assert 'channel.get("platform", "youtube") != "tiktok"' not in source
