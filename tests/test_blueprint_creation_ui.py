from pathlib import Path


MAIN_SOURCE = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")


def test_blueprint_creation_exposes_custom_name():
    assert 'st.text_input("Nome do Blueprint"' in MAIN_SOURCE
    assert 'blueprint_name = st.text_input("Nome do Blueprint"' in MAIN_SOURCE
    assert 'Informe o nome do Blueprint antes de criar.' in MAIN_SOURCE
    assert 'channel_name, blueprint_name)' in MAIN_SOURCE
