from hermes_ui.video_length import (
    DEFAULT_AVERAGE_VIDEO_TIME,
    DEFAULT_TIKTOK_AVERAGE_VIDEO_TIME,
    channel_video_length,
    channel_video_time_value,
    default_average_video_time,
)


def test_youtube_uses_the_twenty_minute_default():
    channel = {"platform": "youtube"}
    assert default_average_video_time(channel) == DEFAULT_AVERAGE_VIDEO_TIME == "20:00"
    assert channel_video_time_value(channel) == "20:00"
    assert channel_video_length(channel)[1] == "20:00"


def test_tiktok_uses_one_minute_twenty_default_in_channel_and_automation_fallback():
    channel = {"platform": "tiktok"}
    assert default_average_video_time(channel) == DEFAULT_TIKTOK_AVERAGE_VIDEO_TIME == "01:20"
    assert channel_video_time_value(channel) == "01:20"
    assert channel_video_length(channel)[1] == "01:20"


def test_existing_platform_duration_override_is_preserved():
    assert channel_video_time_value({"platform": "tiktok", "average_video_time": "02:30"}) == "02:30"
