from pathlib import Path

from hermes_ui.languages import LANGUAGE_CATALOG, LANGUAGE_CODES, language_code, language_label, ui_text, video_language_label
from integrations.moneyprinter_config import build_moneyprinter_config


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
STORAGE_SOURCE = (ROOT / "hermes_ui" / "storage.py").read_text(encoding="utf-8")


def test_moneyprinter_language_catalog_has_requested_codes_and_flags():
    assert LANGUAGE_CODES == ("en", "zh", "de", "vi", "tr", "pt", "ru", "es", "id", "it")
    assert [item["flag"] for item in LANGUAGE_CATALOG] == ["🇺🇸", "🇨🇳", "🇩🇪", "🇻🇳", "🇹🇷", "🇧🇷", "🇷🇺", "🇪🇸", "🇮🇩", "🇮🇹"]
    assert language_label("en") == "🇺🇸 Inglês (en)"
    assert language_label("zh") == "🇨🇳 Chinês Simplificado (zh)"


def test_language_normalization_preserves_legacy_values():
    assert language_code("36 – Português (Brasil)") == "pt"
    assert language_code("01 – Inglês") == "en"
    assert language_code("42 – Vietnamita") == "vi"
    assert language_code("44 – Indonésio") == "id"
    assert video_language_label("music").startswith("🎵")
    assert "🇷🇺" in video_language_label("ru")


def test_ui_translation_and_header_picker_are_present():
    assert ui_text("Configurações", "es") == "Configuración"
    assert "def render_ui_language_picker(language: str)" in MAIN_SOURCE
    assert "with st.popover(language_flag(current)" in MAIN_SOURCE
    assert "right:1.5rem" in MAIN_SOURCE
    assert "ui_language_picker" in MAIN_SOURCE
    assert "save_ui_language(selected)" in MAIN_SOURCE
    assert '"ui_language": "pt"' in STORAGE_SOURCE


def test_moneyprinter_config_persists_ui_and_video_language_codes():
    payload = build_moneyprinter_config({"ui_language": "de", "video_language": "it"})
    assert payload["ui"]["language"] == "de"
    assert payload["ui"]["video_language"] == "it"


def test_video_selector_uses_flag_formatter_and_canonical_codes():
    assert "VIDEO_LANGUAGE_SELECTION_OPTIONS" in MAIN_SOURCE
    assert "format_func=video_language_label" in MAIN_SOURCE
    assert '"video_language": "pt"' in STORAGE_SOURCE
