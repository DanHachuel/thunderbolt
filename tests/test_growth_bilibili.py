from hermes_ui.growth_bilibili import BILIBILI_CARDS
from hermes_ui.languages import ui_text


def test_bilibili_dashboard_uses_eight_platform_specific_cards():
    assert [card[0] for card in BILIBILI_CARDS] == [
        "Validação de Procura",
        "Thumbnail",
        "Título e Intenção",
        "Hook e Retenção",
        "Ritmo e Edição",
        "Engagement 三连",
        "Tráfego e Algoritmo",
        "Conversão e Saúde",
    ]
    assert BILIBILI_CARDS[5][3][0][2] == "> 4%"
    assert BILIBILI_CARDS[6][3][0][2] == "40–60%"


def test_bilibili_navigation_label_is_translated_for_supported_languages():
    for language in ("pt", "en", "zh", "de", "vi", "tr", "ru", "es", "id", "it"):
        assert ui_text("Analista Bilibili", language).strip()
