from pathlib import Path


SOURCE = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")


def test_tiktok_forms_persist_voice_automation_and_time():
    block = SOURCE.split("def render_tiktok_channels():", 1)[1].split("def is_youtube_channel_record", 1)[0]
    assert '"default_voice": voice' in block
    assert '"automation_on": automation_on' in block
    assert '"automation_time": automation_time.strip()' in block
    assert 'valid_hhmm(automation_time)' in block


def test_tiktok_cards_show_requested_channel_settings():
    block = SOURCE.split("def render_tiktok_channels():", 1)[1].split("def is_youtube_channel_record", 1)[0]
    assert 'Narrador/Voz Padrão' in block
    assert 'Estilo wide: Portrait 9:16' in block
    assert 'Automação: {\'ligada\' if automation_on else \'desligada\'}' in block
    assert '"Nicho": "niche"' in block
    assert '"Horário diário (HH:MM)": "automation_time"' in block
