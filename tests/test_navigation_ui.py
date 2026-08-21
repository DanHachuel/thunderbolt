from pathlib import Path


MAIN_SOURCE = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")


def test_automation_is_an_expander_with_youtube_child_page():
    assert 'automation_items = [' in MAIN_SOURCE
    assert '("Automação Youtube", ":material/schedule:", "Automação Youtube")' in MAIN_SOURCE
    assert 'elif target == "Automação":' in MAIN_SOURCE
    assert 'with st.expander("Automação", expanded=current_page in {item[0] for item in automation_items}' in MAIN_SOURCE
    assert '"Automação Youtube": render_automation' in MAIN_SOURCE
    assert 'st.title("Automação Youtube")' in MAIN_SOURCE


def test_youtube_navigation_labels_and_legacy_aliases_are_preserved():
    assert '("Canais Youtube", ":material/ondemand_video:", "Canais Youtube")' in MAIN_SOURCE
    assert '("Blueprints Youtube", ":material/library_books:", "Blueprints Youtube")' in MAIN_SOURCE
    assert '"Canais Youtube": render_channels' in MAIN_SOURCE
    assert '"Blueprints Youtube": render_blueprints' in MAIN_SOURCE
    assert '"Canais": "Canais Youtube"' in MAIN_SOURCE
    assert '"Blueprints": "Blueprints Youtube"' in MAIN_SOURCE
    assert '"Automação": "Automação Youtube"' in MAIN_SOURCE
