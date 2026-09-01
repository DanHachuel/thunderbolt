from pathlib import Path


def test_api_configuration_shows_local_api_keys_storage_path():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    settings_block = source.split("def render_settings():", 1)[1].split("def render_", 1)[0]
    assert "Ficheiro local de todas as API keys" in settings_block
    assert "STORAGE / 'state' / 'settings.json'" in settings_block
    assert ".env" not in settings_block.split("settings = read_json", 1)[0]
