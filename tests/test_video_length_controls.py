from pathlib import Path

from hermes_ui.video_length import DEFAULT_AVERAGE_VIDEO_TIME, channel_video_length, channel_video_time_value, explicit_word_count, length_generation_settings, words_from_channel_time


MAIN_SOURCE = (Path(__file__).parents[1] / "app" / "main.py").read_text(encoding="utf-8")


def test_blueprint_character_range_becomes_word_reference():
    words, duration, source = channel_video_length({}, {"strict_character_range": [7000, 9000]})
    assert words == 1333
    assert duration == "09:00"
    assert source == "Blueprint/Prompt Master"


def test_channel_time_overrides_blueprint_reference():
    settings = length_generation_settings({"average_video_time": "02:00"}, {"word_count": 2400})
    assert settings["target_word_count"] == 300
    assert settings["target_video_duration"] == "02:00"
    assert settings["target_word_count_source"] == "canal"


def test_zero_channel_time_falls_back_to_prompt_master():
    assert explicit_word_count({}, "Escreva aproximadamente 600 palavras por roteiro.") == 600
    words, duration, source = channel_video_length({"average_video_time": "00:00"}, {}, "Escreva aproximadamente 600 palavras por roteiro.")
    assert (words, duration, source) == (600, "04:00", "Blueprint/Prompt Master")


def test_empty_channel_uses_twenty_minute_default():
    assert DEFAULT_AVERAGE_VIDEO_TIME == "20:00"
    assert channel_video_length({}, {}, "") == (3000, "20:00", "padrão do canal")


def test_channel_duration_uses_minutes_and_seconds():
    assert words_from_channel_time("12:00") == 1800
    assert words_from_channel_time("00:12") == 30


def test_legacy_default_is_migrated_without_changing_explicit_seconds():
    assert channel_video_time_value({"average_video_time": "00:12"}) == "20:00"
    assert channel_video_time_value({"average_video_time": "00:12", "average_video_word_count": 30}) == "00:12"
    assert channel_video_length({"average_video_time": "00:12"}, {}, "") == (3000, "20:00", "canal")


def test_channel_cards_have_average_time_and_refresh_controls():
    assert 'Tempo Medio de Video' in MAIN_SOURCE
    assert MAIN_SOURCE.count('Tempo Medio de Video') >= 4
    assert 'Tempo Medio de Video (HH:MM)' not in MAIN_SOURCE
    assert 'DEFAULT_AVERAGE_VIDEO_TIME' in MAIN_SOURCE
    assert MAIN_SOURCE.count('Guardar tempo') >= 1
    assert 'youtube_channel_average_video_time_' in MAIN_SOURCE
    assert 'tiktok_channel_average_video_time_' in MAIN_SOURCE
    assert 'refresh_youtube_metrics_' in MAIN_SOURCE
    assert 'refresh_tiktok_metrics_' in MAIN_SOURCE
    assert 'length_generation_settings' in MAIN_SOURCE
