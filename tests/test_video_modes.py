import ast
from pathlib import Path


def _main_module():
    return ast.parse(Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8"))


def _constant(name):
    assignment = next(node for node in _main_module().body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets))
    return ast.literal_eval(assignment.value)


def test_ai_style_options_are_complete_and_ordered():
    assert _constant("AI_STYLE_OPTIONS") == [
        "Natural Realista", "Cocomelon style", "Retro 90s Cartoon", "Wool sculpture miniatures",
        "LEGO Style", "Paper cutout style", "Anime Style", "Studio Ghibli Style",
        "Stop Motion Style (Massinha)", "Ukiyo Style", "Pixel Animation", "Pixar Style",
    ]


def test_wide_style_labels_and_music_background_rule_are_present():
    assert _constant("WIDE_STYLE_OPTIONS") == ["Pexels/Pixabay", "full_ia", "Apenas Música"]
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert '"background_mode": "none" if style == "music"' in source
    assert 'st.selectbox("Estilo IA", AI_STYLE_OPTIONS' in source


def test_video_creation_has_ai_topic_blueprint_and_creative_controls():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert 'Gerar tópico/briefing com IA' in source
    assert 'Gerar títulos e thumbnails com IA' in source
    assert 'Gerar títulos e thumbnails para todos os canais' in source
    assert 'SEM BLUEPRINT CONFIGURADO' in source
    assert 'Canais incluídos' not in source


def test_general_mode_uses_all_registered_channels_without_partial_selector():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert 'selected = [str(channel["id"]) for channel in all_channels if channel.get("id")]' in source
    assert 'create_batch("general", selected, batch_topic, 1' in source
    assert 'channel_payloads' in source
