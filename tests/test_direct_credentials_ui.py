from pathlib import Path


MAIN_SOURCE = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")


def test_direct_credentials_keep_cookies_in_document_but_api_key_in_account_section():
    assert 'Subir documento de cookies/credenciais' in MAIN_SOURCE
    assert 'Aceita o JSON do YouTube-Video-Upload-Frontend-Api' in MAIN_SOURCE
    assert 'Guardar documento nesta conta' in MAIN_SOURCE
    assert 'credentials.json' in MAIN_SOURCE
    assert '### INNERTUBE_API_KEY' in MAIN_SOURCE
    assert 'Guardar INNERTUBE_API_KEY' in MAIN_SOURCE
    assert 'fora do documento de cookies.' in MAIN_SOURCE


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
    assert 'direct_innertube_api_key = str(settings.get("direct_innertube_api_key"' not in MAIN_SOURCE
    assert 'st.caption("As credenciais e parâmetros do Upload directo — cookies, sessionInfo, INNERTUBE_API_KEY' not in MAIN_SOURCE
    assert 'number_input("Chunk size' not in MAIN_SOURCE
    assert 'redirect_uri_mismatch' in MAIN_SOURCE or 'loopback_redirect_uri' in MAIN_SOURCE


def test_innertube_key_block_is_between_account_status_and_add_account():
    status_marker = 'Contas que ainda precisam de dados no documento:'
    key_marker = '### INNERTUBE_API_KEY'
    add_marker = '### Adicionar outra conta Gmail'
    assert MAIN_SOURCE.index(status_marker) < MAIN_SOURCE.index(key_marker) < MAIN_SOURCE.index(add_marker)
    assert 'with st.form("innertube_api_key_form")' in MAIN_SOURCE
    assert 'key=f"innertube_api_key_{selected_key_account_id}"' in MAIN_SOURCE


def test_google_accounts_use_collapsed_name_email_cards_and_external_add_form():
    assert 'with st.expander(f"{account_label_snapshot} — {account_email_snapshot}", expanded=False):' in MAIN_SOURCE
    assert 'st.divider()' in MAIN_SOURCE
    assert 'with st.form("add_batch_account_form")' in MAIN_SOURCE
    assert 'ensure_credentials_document(STORAGE, batch_account, settings, channel_state)' in MAIN_SOURCE
    assert 'associação de canais não depende da completude deste documento' in MAIN_SOURCE


def test_api_settings_keep_api_keys_and_voice_test_tabs():
    expected = 'render_localized_tabs(["API Keys", "Teste de vozes"])'
    assert expected in MAIN_SOURCE
    assert 'st.subheader("API Keys")' in MAIN_SOURCE
    assert 'st.subheader("Execução local")' not in MAIN_SOURCE


def test_legacy_cookie_inputs_are_not_rendered():
    for label in ("SID global legado", "SSID global legado", "HSID global legado", "APISID global legado", "SAPISID global legado", "sessionInfo token global legado"):
        assert label not in MAIN_SOURCE
