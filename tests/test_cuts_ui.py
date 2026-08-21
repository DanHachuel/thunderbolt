from pathlib import Path


MAIN_SOURCE = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")


def test_cuts_page_uses_functional_clip_generator_renderer():
    assert "def render_cuts():" in MAIN_SOURCE
    assert '"Cortes": render_cuts' in MAIN_SOURCE
    assert "Create Viral Shorts" in MAIN_SOURCE
    assert 'st.tabs(["Upload ficheiro", "URL de vídeo", "Vídeos gerados", "Pasta local"])' in MAIN_SOURCE
    assert 'with st.expander("advanced options", expanded=False):' in MAIN_SOURCE
    assert 'st.button(\n            "Gerar Clips"' in MAIN_SOURCE


def test_cuts_page_has_output_formats_rights_confirmation_and_results():
    assert 'format_options = ["9:16", "1:1", "16:9"]' in MAIN_SOURCE
    assert 'Confirmo que possuo os direitos ou autorização para processar este conteúdo.' in MAIN_SOURCE
    assert 'st.video(str(clip["path"]))' in MAIN_SOURCE
    assert 'Descarregar todos os clips (ZIP)' in MAIN_SOURCE
    assert 'Descarregar manifesto JSON' in MAIN_SOURCE
    assert 'Histórico do Clip Generator' in MAIN_SOURCE
