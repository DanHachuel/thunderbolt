from pathlib import Path


MAIN_SOURCE = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")


def test_direct_credentials_are_document_uploads_not_individual_fields():
    assert 'Subir documento de cookies/credenciais' in MAIN_SOURCE
    assert 'Aceita o JSON do YouTube-Video-Upload-Frontend-Api' in MAIN_SOURCE
    assert 'Guardar documento nesta conta' in MAIN_SOURCE
    assert 'credentials.json' in MAIN_SOURCE
    assert 'restantes valores continuam exclusivamente no documento' in MAIN_SOURCE


def test_direct_credentials_are_read_per_account_and_channel_from_document():
    assert 'credentials_document_path' in MAIN_SOURCE or 'credentials.json' in MAIN_SOURCE
    assert 'document_status(STORAGE, selected_channel_account, channel, settings, channels)' in MAIN_SOURCE
    assert 'delegated_session_ids' in MAIN_SOURCE
    assert 'st.text_input("DELEGATED_SESSION_ID deste canal (individual)"' not in MAIN_SOURCE
    assert 'sessionInfo token desta conta Google' in MAIN_SOURCE
    assert 'Adicionar outra conta Gmail' in MAIN_SOURCE
    assert 'Apagar conta' in MAIN_SOURCE
    assert 'merge_credentials_document' in MAIN_SOURCE
    assert 'Documento incompleto:' in MAIN_SOURCE
    assert 'st.file_uploader("Ficheiro de cookies desta conta Google"' not in MAIN_SOURCE
    assert 'text_setting("INNERTUBE_API_KEY"' not in MAIN_SOURCE
    assert 'number_input("Chunk size' not in MAIN_SOURCE
    assert 'redirect_uri_mismatch' in MAIN_SOURCE or 'loopback_redirect_uri' in MAIN_SOURCE


def test_google_accounts_use_collapsed_name_email_cards_and_external_add_form():
    assert 'with st.expander(f"{account_label_snapshot} — {account_email_snapshot}", expanded=False):' in MAIN_SOURCE
    assert 'st.divider()' in MAIN_SOURCE
    assert 'with st.form("add_batch_account_form")' in MAIN_SOURCE
    assert 'ensure_credentials_document(STORAGE, batch_account, settings, channel_state)' in MAIN_SOURCE
    assert 'associação de canais não depende da completude deste documento' in MAIN_SOURCE


def test_technical_settings_are_split_into_three_unnumbered_tabs():
    expected = 'st.tabs(["Contas Google/YouTube — canais em lote", "API Keys", "Teste de vozes"])'
    assert expected in MAIN_SOURCE
    assert 'st.subheader("API Keys")' in MAIN_SOURCE
    assert 'st.subheader("Execução local")' not in MAIN_SOURCE


def test_legacy_cookie_inputs_are_not_rendered():
    for label in ("SID global legado", "SSID global legado", "HSID global legado", "APISID global legado", "SAPISID global legado", "sessionInfo token global legado"):
        assert label not in MAIN_SOURCE
