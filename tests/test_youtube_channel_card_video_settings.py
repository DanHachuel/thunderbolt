from pathlib import Path


SOURCE = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
YOUTUBE = SOURCE[SOURCE.index("def render_channels("):]


def test_youtube_channel_cards_have_video_and_average_time_expanders():
    card = YOUTUBE.split('with st.expander("Detalhes e configuração do canal", expanded=False):', 1)[1]
    assert 'with st.expander("Tempo Medio de Video", expanded=False):' in card
    assert 'def render_channel_video_defaults(channel: dict) -> None:' in SOURCE
    assert 'with st.expander("Configurações de vídeo", expanded=False):' in SOURCE
    assert 'Guardar configurações de vídeo' in SOURCE
    assert 'render_channel_video_defaults(channel)' in card
    assert 'st.button("Guardar tempo"' not in card


def test_youtube_channel_card_actions_are_below_summary_without_redundant_edit_buttons():
    card = YOUTUBE.split('with st.expander("Detalhes e configuração do canal", expanded=False):', 1)[1]
    assert 'st.button("Editar", key=f"edit_channel_button_{channel_id}", type="primary"' in card
    assert 'st.button("Apagar", key=f"delete_{channel_id}"' in card
    assert 'Editar Blueprint' not in card
    assert 'Editar Nicho' not in card
    assert 'Configurar Narrador/Voz' not in card
    assert card.index('st.columns(4, gap="small")') < card.index('st.button("Editar", key=f"edit_channel_button_{channel_id}"')


def test_video_defaults_persist_on_the_channel_record():
    assert 'default_video_source' in SOURCE
    assert 'default_video_aspect_ratio' in SOURCE
    assert 'default_video_encoder' in SOURCE
    assert 'default_maximum_clip_duration' in SOURCE
    assert 'default_videos_per_run' in SOURCE


def test_existing_channel_card_audio_and_subtitle_defaults_remain_available():
    assert 'with st.expander("Configurações de legendas", expanded=False):' in SOURCE
    assert 'with st.expander("Configurações de Audio", expanded=False):' in SOURCE
    assert 'render_channel_audio_subtitle_defaults(channel)' in SOURCE
