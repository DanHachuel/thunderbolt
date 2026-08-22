from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
PACKAGE_SOURCE = (ROOT / "package.json").read_text(encoding="utf-8")
THEME_CONFIG = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")


def test_streamlit_theme_config_defaults_to_light_with_moneyprinter_style_semantics():
    assert "[theme]" in THEME_CONFIG
    assert 'base = "light"' in THEME_CONFIG
    assert 'primaryColor = "#35A7FF"' in THEME_CONFIG
    assert 'backgroundColor = "#FFFFFF"' in THEME_CONFIG
    assert 'secondaryBackgroundColor = "#F3F6FA"' in THEME_CONFIG
    assert 'textColor = "#16202A"' in THEME_CONFIG
    assert '[client]\ntoolbarMode = "auto"' in THEME_CONFIG


def test_package_distributes_streamlit_theme_config_and_new_release_version():
    assert '"version": "0.2.87"' in PACKAGE_SOURCE
    assert '".streamlit/config.toml"' in PACKAGE_SOURCE


def test_custom_css_inherits_active_streamlit_theme_instead_of_forcing_dark_palette():
    css_start = MAIN_SOURCE.index("st.markdown(\"\"\"\n<style>")
    css_end = MAIN_SOURCE.index('</style>\n\"\"\", unsafe_allow_html=True)', css_start)
    css = MAIN_SOURCE[css_start:css_end]

    assert "background:transparent" in css
    assert "color:inherit" in css
    assert "currentColor" in css
    assert "color-mix(in srgb" in css
    for forced_dark_rule in (
        "background:#091018",
        "background:#101b25",
        "background:rgba(18,27,38,.92)",
        "color:#e7edf2",
        "color:#f4f8fb",
        "color:#9cafbf",
    ):
        assert forced_dark_rule not in css


def test_theme_fix_keeps_native_streamlit_toolbar_and_platform_chip_identity_colors():
    assert "stAppDeployButton" not in MAIN_SOURCE
    assert "stMainMenu" not in MAIN_SOURCE
    assert "stToolbar" not in MAIN_SOURCE
    assert '[data-testid="stMultiSelectTagsContainer"] span[data-tag][aria-label="YouTube"] { background:#ff0000 !important; }' in MAIN_SOURCE
    assert '[data-testid="stMultiSelectTagsContainer"] span[data-tag][aria-label="TikTok"] { background:#000000 !important; }' in MAIN_SOURCE
