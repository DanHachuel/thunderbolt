from pathlib import Path

from hermes_ui.video_length import channel_video_length, explicit_word_count, length_generation_settings


MAIN_SOURCE = (Path(__file__).parents[1] / "app" / "main.py").read_text(encoding="utf-8")


def test_blueprint_character_range_becomes_word_reference():
    words, duration, source = channel_video_length({}, {"strict_character_range": [7000, 9000]})
    assert words == 1333
    assert duration == "00:09"
    assert source == "Blueprint/Prompt Master"


def test_channel_time_overrides_blueprint_reference():
    settings = length_generation_settings({"average_video_time": "00:02"}, {"word_count": 2400})
    assert settings["target_word_count"] == 300
    assert settings["target_video_duration"] == "00:02"
    assert settings["target_word_count_source"] == "canal"


def test_zero_channel_time_falls_back_to_prompt_master():
    assert explicit_word_count({}, "Escreva aproximadamente 600 palavras por roteiro.") == 600
    words, duration, source = channel_video_length({"average_video_time": "00:00"}, {}, "Escreva aproximadamente 600 palavras por roteiro.")
    assert (words, duration, source) == (600, "00:04", "Blueprint/Prompt Master")


def test_channel_cards_have_average_time_and_refresh_controls():
    assert 'Tempo Medio de Video (HH:MM)' in MAIN_SOURCE
    assert 'refresh_youtube_metrics_' in MAIN_SOURCE
    assert 'refresh_tiktok_metrics_' in MAIN_SOURCE
    assert 'length_generation_settings' in MAIN_SOURCE
