from pathlib import Path


SOURCE = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")


def test_both_automation_cards_show_channel_video_settings():
    youtube = SOURCE.split("def render_automation():", 1)[1].split("def render_upload_direct", 1)[0]
    tiktok = SOURCE.split("def render_tiktok_automation():", 1)[1].split("def render_automation():", 1)[0]
    for block in (youtube, tiktok):
        assert '**Idioma do roteiro**' in block
        assert '**Fonte do vídeo**' in block
        assert '**Proporção do vídeo**' in block
        assert '**Formato**' in block


def test_channel_source_legacy_values_are_normalized():
    from app.main import channel_video_source_value

    assert channel_video_source_value("pexels") == "Pexels/Pixabay"
    assert channel_video_source_value("full_ia") == "full_ia"
    assert channel_video_source_value("portrait") == "Pexels/Pixabay"
