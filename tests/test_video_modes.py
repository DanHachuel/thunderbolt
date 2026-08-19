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
