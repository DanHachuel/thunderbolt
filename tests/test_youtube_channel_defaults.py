from hermes_ui import storage
from hermes_ui.domain import create_batch, create_channel, create_tasks_for_batch, update_channel


def _use_storage(tmp_path):
    storage.STORAGE = tmp_path / "storage"
    storage.STATE = storage.STORAGE / "state"
    storage.BLUEPRINTS = storage.STORAGE / "blueprints"
    storage.ensure_storage()


def test_youtube_channel_seed_defaults_are_exactly_requested(tmp_path):
    _use_storage(tmp_path)
    channel = create_channel("Canal YouTube", "https://youtube.com/@canal", {"platform": "youtube"})
    assert channel["default_maximum_clip_duration"] == 5
    assert channel["default_video_aspect_ratio"] == "Landscape 16:9"
    assert channel["default_enable_subtitles"] is True
    assert channel["default_background_music_source"] == "Sem música"
    assert channel["average_video_time"] == "20:00"


def test_youtube_batch_tasks_receive_the_four_seed_defaults(tmp_path):
    _use_storage(tmp_path)
    channel = create_channel("Canal YouTube", "https://youtube.com/@canal", {"platform": "youtube"})
    batch = create_batch("single", [channel["id"]], "Tema", 1, {})
    task = create_tasks_for_batch(batch)[0]
    settings = task["generation_settings"]
    assert settings["maximum_clip_duration"] == 5
    assert settings["video_aspect_ratio"] == "Landscape 16:9"
    assert settings["enable_subtitles"] is True
    assert settings["background_music_source"] == "Sem música"


def test_existing_youtube_values_are_not_overwritten_by_seed_defaults(tmp_path):
    _use_storage(tmp_path)
    channel = create_channel("Canal YouTube", "https://youtube.com/@canal", {"platform": "youtube"})
    channel = update_channel(channel["id"], {
        "default_maximum_clip_duration": 15,
        "default_video_aspect_ratio": "Square 1:1",
        "default_enable_subtitles": False,
        "default_background_music_source": "Random Background Music",
    })
    assert channel["default_maximum_clip_duration"] == 15
    assert channel["default_video_aspect_ratio"] == "Square 1:1"
    assert channel["default_enable_subtitles"] is False
    assert channel["default_background_music_source"] == "Random Background Music"
