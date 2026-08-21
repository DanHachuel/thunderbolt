from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
STORAGE_SOURCE = (ROOT / "hermes_ui" / "storage.py").read_text(encoding="utf-8")


def test_upload_has_postiz_tab_and_uses_postiz_adapter():
    assert 'st.tabs(["Upload convencional", "Upload directo", "Postiz"])' in MAIN_SOURCE
    assert "def render_upload_postiz():" in MAIN_SOURCE
    assert "Carregar integrações Postiz" in MAIN_SOURCE
    assert "Enviar vídeo para Postiz" in MAIN_SOURCE
    assert "PostizAdapter(settings)" in MAIN_SOURCE


def test_technical_settings_expose_postiz_api_and_mcp_fields():
    assert "Postiz — API key, integração e MCP" in MAIN_SOURCE
    assert 'text_setting("Postiz API key", "postiz_api_key", secret=True' in MAIN_SOURCE
    assert 'text_setting("Postiz Public API Base URL", "postiz_base_url"' in MAIN_SOURCE
    assert 'text_setting("Postiz MCP URL", "postiz_mcp_url"' in MAIN_SOURCE
    assert '"postiz_api_key": postiz_api_key' in MAIN_SOURCE


def test_fallback_order_is_documented_in_conventional_upload():
    order_text = "1. API Oficial"
    assert order_text in MAIN_SOURCE
    assert "2. Upload directo" in MAIN_SOURCE
    assert "3. Postiz" in MAIN_SOURCE
    assert "upload_with_default_route(" in MAIN_SOURCE


def test_postiz_settings_have_local_storage_defaults():
    assert '"postiz_enabled": False' in STORAGE_SOURCE
    assert '"postiz_base_url": "https://api.postiz.com/public/v1"' in STORAGE_SOURCE
    assert '"postiz_mcp_url": "https://api.postiz.com/mcp"' in STORAGE_SOURCE
