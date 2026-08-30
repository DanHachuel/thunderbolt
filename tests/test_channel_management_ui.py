from pathlib import Path


def test_channel_cards_show_four_compact_defaults_and_collapsed_videos():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert 'edit_channel_button_' in source
    assert 'Editar canal' in source
    assert '**Blueprint Padrão**' in source
    assert '**Nicho**' in source
    assert '**Narrador/Voz Padrão**' in source
    assert '**Idioma**' in source
    assert 'with st.expander("Últimos 10 vídeos publicados", expanded=False):' in source
    assert 'Actualizar últimos 10 vídeos' in source
    assert 'st.columns(4, gap="small")' in source


def test_channel_video_views_are_list_only_with_edit_action():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert 'Apresentação dos canais' not in source
    assert 'youtube_channels_view_mode' not in source
    assert 'render_registered_channels_kanban' not in source
    assert 'Editar vídeo' in source
    assert 'channel_videos.json' in source
    assert 'fetch_channel_videos_public(channel, limit=10)' in source


def test_automation_cards_show_the_same_four_channel_defaults():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert '"**Idioma Padrão**"' in source
    assert '"Blueprint Padrão"' in source
    assert '"**Nicho Padrão**"' in source
    assert '"Narrador/Voz Padrão"' in source
    assert 'language_label(channel.get("language") or "pt")' in source
    assert 'channel_niche_label(channel)' in source


def test_manual_and_imported_channel_forms_have_niche_field():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert 'key="yt_import_niche"' in source
    assert 'key="manual_channel_niche"' in source
    assert '"reference_channels"' in source


def test_registered_channels_table_is_only_in_spreadsheet_tab_and_scrollable():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    spreadsheet_start = source.index("with spreadsheet_tab:")
    batch_start = source.index("with batch_tab:")
    spreadsheet_block = source[spreadsheet_start:batch_start]
    assert 'st.subheader("Canais cadastrados")' in spreadsheet_block
    assert 'registered_rows' in spreadsheet_block
    assert 'height=420' in spreadsheet_block
    assert 'Use a barra inferior para navegar horizontalmente' in spreadsheet_block
    assert source.count('st.subheader("Canais cadastrados")') == 1
    for column in (
        "URL canal", "Nome canal", "Handle canal", "Narrador/ voz padrão", "Idioma", "Nicho",
        "Blueprint Padrão", "Estilo Wide", "Activo", "Descrição",
        "Conta Google do Documento deste Canal", "Automação Ligada", "Horário diário (HH:MM)",
        "DELEGATED_SESSION_ID", "Duração Padrão Vídeos (Min)", "Origem",
    ):
        assert f'"{column}"' in spreadsheet_block
