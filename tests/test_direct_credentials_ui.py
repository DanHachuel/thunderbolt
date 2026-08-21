from pathlib import Path


MAIN_SOURCE = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")


def test_direct_credentials_are_document_uploads_not_individual_fields():
    assert 'Documento de credenciais desta conta Google' in MAIN_SOURCE
    assert 'Documento JSON único com cookies SID/SSID/HSID/APISID/SAPISID' in MAIN_SOURCE
    assert 'Guardar documento de Upload directo desta conta' in MAIN_SOURCE
    assert 'As credenciais e parâmetros do Upload directo' in MAIN_SOURCE
    assert 'Não são editados nesta UI' in MAIN_SOURCE


def test_direct_credentials_are_read_per_account_and_channel_from_document():
    assert 'credentials_document_path' in MAIN_SOURCE or 'credentials.json' in MAIN_SOURCE
    assert 'document_status(STORAGE, selected_channel_account, channel, settings, channels)' in MAIN_SOURCE
    assert 'delegated_session_ids' in MAIN_SOURCE
    assert 'st.text_input("DELEGATED_SESSION_ID deste canal (individual)"' not in MAIN_SOURCE
    assert 'sessionInfo token desta conta Google' in MAIN_SOURCE
    assert 'Repetir campos para nova conta' in MAIN_SOURCE
    assert 'Apagar conta' in MAIN_SOURCE
    assert 'st.file_uploader("Ficheiro de cookies desta conta Google"' not in MAIN_SOURCE
    assert 'text_setting("INNERTUBE_API_KEY"' not in MAIN_SOURCE
    assert 'number_input("Chunk size' not in MAIN_SOURCE
    assert 'redirect_uri_mismatch' in MAIN_SOURCE or 'loopback_redirect_uri' in MAIN_SOURCE


def test_technical_settings_are_split_into_three_unnumbered_tabs():
    expected = 'st.tabs(["Contas Google/YouTube — canais em lote", "API Keys", "Teste de vozes"])'
    assert expected in MAIN_SOURCE
    assert 'st.subheader("API Keys")' in MAIN_SOURCE
    assert 'st.subheader("Execução local")' not in MAIN_SOURCE


def test_legacy_cookie_inputs_are_not_rendered():
    for label in ("SID global legado", "SSID global legado", "HSID global legado", "APISID global legado", "SAPISID global legado", "sessionInfo token global legado"):
        assert label not in MAIN_SOURCE
