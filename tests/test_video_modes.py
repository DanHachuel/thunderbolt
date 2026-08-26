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
    assert 'Gerar tópico, roteiro e palavras-chave com IA' in source
    assert 'Gerar Thumbnail com IA' in source
    assert 'Gerar títulos e thumbnails com IA' not in source
    assert 'Gerar títulos e thumbnails para todos os canais' not in source
    assert 'SEM BLUEPRINT CONFIGURADO' in source
    assert 'Canais incluídos' not in source


def test_video_creation_has_exactly_four_primary_expanders_and_thumbnail_action():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert 'with st.expander("Configurações de vídeo", expanded=False):' in source
    assert 'with st.expander("Configurações de áudio", expanded=False):' in source
    assert 'with st.expander("Configurações de legendas", expanded=False):' in source
    assert 'with st.expander("Gerar Thumbnail com IA", expanded=False):' in source
    assert 'with st.expander("Advanced Script Settings", expanded=False):' not in source
    assert 'generate_thumbnail_variants_for_ui(' in source
    assert 'generated["title_candidates"] = existing_payload.get("title_candidates", [])' in source


def test_automation_card_matches_reference_layout_without_changing_control_keys():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert 'header_cols = st.columns([0.55, 2.35, 1.35, 1.5, 1.35])' in source
    assert 'enabled = st.toggle("Automação ligada"' in source
    assert 'key=f"automation_on_{channel_id}"' in source
    assert 'key=f"automation_time_{channel_id}"' in source
    assert 'key=f"automation_save_{channel_id}"' in source
    assert 'default_cols = st.columns([1.15, 1.15, 1.5, 1.7, 1.35], gap="small")' in source
    assert 'with default_cols[0]:' in source and 'with default_cols[1]:' in source
    assert 'with default_cols[2]:' in source and 'with default_cols[3]:' in source


def test_general_mode_uses_all_registered_channels_without_partial_selector():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert 'selected = [str(channel["id"]) for channel in all_channels if channel.get("id")]' in source
    assert 'create_batch("general", selected, batch_topic, 1' in source
    assert 'channel_payloads' in source
