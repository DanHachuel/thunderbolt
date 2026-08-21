from pathlib import Path


MAIN_SOURCE = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")


def test_direct_credentials_are_visible_by_default_in_requested_pages():
    assert 'st.expander("Upload directo — conta e canal", expanded=True)' in MAIN_SOURCE
    assert 'DELEGATED_SESSION_ID deste canal (individual)' in MAIN_SOURCE
    assert 'st.expander("Upload directo — sessão YouTube Frontend API", expanded=True)' in MAIN_SOURCE
    assert 'st.file_uploader("Ficheiro de cookies"' in MAIN_SOURCE
    assert 'st.text_input("sessionInfo token"' in MAIN_SOURCE
    assert 'Guardar cookies e sessionInfo por conta' in MAIN_SOURCE


def test_direct_credentials_are_not_stored_as_one_global_upload_path():
    assert 'storage/youtube_direct_accounts/<conta>/cookies.json' in MAIN_SOURCE
    assert 'direct_account_session_fields[direct_account_id]' in MAIN_SOURCE
    assert 'direct_account_id = str(direct_account["id"])' in MAIN_SOURCE
