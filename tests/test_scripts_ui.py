from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
STORAGE_SOURCE = (ROOT / "hermes_ui" / "storage.py").read_text(encoding="utf-8")


def test_scripts_is_between_music_and_upload_in_pipeline():
    music_item = '("Criação de Músicas", ":material/music_note:", "Criação de Músicas")'
    scripts_item = '("Roteiros", ":material/article:", "Roteiros")'
    upload_item = '("Upload", ":material/cloud_upload:", "Upload")'
    assert music_item in MAIN_SOURCE
    assert scripts_item in MAIN_SOURCE
    assert upload_item in MAIN_SOURCE
    assert MAIN_SOURCE.index(music_item) < MAIN_SOURCE.index(scripts_item) < MAIN_SOURCE.index(upload_item)
    assert '"Roteiros": render_scripts' in MAIN_SOURCE


def test_scripts_ui_exposes_storage_paths_and_blueprint_generation():
    assert 'st.info(f"**Ficheiros guardados em:** `{script_dir}`' in MAIN_SOURCE
    assert 'st.caption(f"Os vídeos são guardados em `{STORAGE / \'videos\'}`.")' in MAIN_SOURCE
    assert "Gerar com IA a partir do Blueprint" in MAIN_SOURCE
    assert "Histórico guardado" in MAIN_SOURCE


def test_storage_has_script_history_default():
    assert '"scripts.json": []' in STORAGE_SOURCE
