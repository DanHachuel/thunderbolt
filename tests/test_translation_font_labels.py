from hermes_ui.languages import translate_ui_content


def test_font_token_does_not_corrupt_fonte_labels():
    assert translate_ui_content("Fonte do vídeo", "pt") == "Fonte do vídeo"
    assert "Fonteeeee" not in translate_ui_content("Video Source", "pt")
    assert "Fontee" not in translate_ui_content("Fonte de materiais", "pt")


def test_video_source_has_stable_portuguese_translation():
    translated = translate_ui_content("Video Source", "pt")
    assert translated == "Fonte do vídeo"
