from pathlib import Path


MAIN_SOURCE = Path(__file__).resolve().parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")


def test_translation_installation_uses_persistent_streamlit_guard():
    assert "_STREAMLIT_I18N_INSTALLED" not in MAIN_SOURCE
    assert 'getattr(st, "_thunderbolt_i18n_installed", False)' in MAIN_SOURCE
    assert 'getattr(current, "_thunderbolt_translated", False)' in MAIN_SOURCE
    assert "translated_method._thunderbolt_translated = True" in MAIN_SOURCE
    assert 'setattr(st, "_thunderbolt_i18n_installed", True)' in MAIN_SOURCE


def test_video_selectboxes_initialise_state_without_index_argument():
    language_block = MAIN_SOURCE[MAIN_SOURCE.index('settings["script_language"]'):MAIN_SOURCE.index('settings["video_script"]')]
    assert "language_state_key" in language_block
    assert "index=" not in language_block

    material_start = MAIN_SOURCE.index('settings["material_source"]')
    material_block = MAIN_SOURCE[material_start:MAIN_SOURCE.index('settings["style_ia"]', material_start)]
    assert "material_state_key" in material_block
    assert "index=" not in material_block

    aspect_start = MAIN_SOURCE.index('settings["video_aspect_ratio"]')
    aspect_block = MAIN_SOURCE[aspect_start:MAIN_SOURCE.index('settings["maximum_clip_duration"]', aspect_start)]
    assert "index=" not in aspect_block
