from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
STORAGE_SOURCE = (ROOT / "hermes_ui" / "storage.py").read_text(encoding="utf-8")
PACKAGE_SOURCE = (ROOT / "package.json").read_text(encoding="utf-8")


def test_tiktok_pipeline_is_separate_and_expansible():
    assert 'pipeline_tiktok_items = [' in MAIN_SOURCE
    assert '("Prompts Master", ":material/auto_awesome:", "Prompts Master")' in MAIN_SOURCE
    assert 'elif target == "Pipeline TikTok":' in MAIN_SOURCE
    assert '"Prompts Master": render_tiktok_prompt_masters' in MAIN_SOURCE


def test_prompt_master_storage_is_not_blueprints_storage():
    assert 'TIKTOK_PROMPT_MASTERS = STORAGE / "tiktok" / "prompts_master"' in STORAGE_SOURCE
    assert 'def list_prompt_master_files()' in STORAGE_SOURCE
    assert 'def load_prompt_master_file(path: Path)' in STORAGE_SOURCE
    assert 'storage/tiktok/prompts_master/**/*.md' in PACKAGE_SOURCE
    assert 'BLUEPRINTS / "importados"' in STORAGE_SOURCE


def test_prompt_master_ui_has_upload_library_editor_and_actions():
    for label in (
        "Subir Prompt Master (.md)",
        "Guardar Prompt Master",
        "Prompts Master existentes",
        "Pesquisar Prompt Master",
        "Guardar alterações",
        "Descarregar",
        "Apagar",
    ):
        assert label in MAIN_SOURCE
    assert 'mime="text/markdown"' in MAIN_SOURCE
    assert 'st.markdown(content)' in MAIN_SOURCE
