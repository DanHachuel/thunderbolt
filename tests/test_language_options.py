import ast
from pathlib import Path


EXPECTED_LANGUAGES = [
    "00 – Apenas Música de Fundo (Sem Falas)",
    "01 – Inglês",
    "02 – Norueguês",
    "03 – Dinamarquês",
    "04 – Sueco",
    "05 – Holandês",
    "06 – Alemão",
    "07 – Luxemburguês",
    "08 – Finlandês",
    "09 – Hebraico",
    "10 – Japonês",
    "11 – Árabe (Golfo)",
    "12 – Islandês",
    "13 – Espanhol (Espanha)",
    "14 – Francês",
    "15 – Italiano",
    "16 – Coreano",
    "16 – Irlandês",
    "17 – Estoniano",
    "18 – Grego",
    "19 – Esloveno",
    "20 – Polonês",
    "21 – Tcheco",
    "22 – Lituano",
    "23 – Português (Portugal)",
    "24 – Eslovaco",
    "25 – Letão",
    "26 – Ucraniano",
    "27 – Húngaro",
    "28 – Afrikaans",
    "29 – Turco",
    "30 – Romeno",
    "31 – Russo",
    "32 – Croata",
    "33 – Árabe (Magreb)",
    "34 – Sérvio",
    "35 – Búlgaro",
    "36 – Português (Brasil)",
    "37 – Cantonês",
    "38 – Persa (Farsi)",
    "39 – Mandarim",
    "40 – Malaio",
    "41 – Espanhol (LatAm)",
    "42 – Vietnamita",
    "43 – Filipino (Tagalog)",
    "44 – Indonésio",
    "45 – Malayalam",
    "46 – Tailandês",
    "47 – Télugo",
    "48 – Tamil",
    "49 – Bengali",
    "50 – Hausa",
]


def test_video_language_options_match_requested_order():
    module = ast.parse(Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8"))
    assignment = next(node for node in module.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "VIDEO_LANGUAGE_OPTIONS" for target in node.targets))
    actual = ast.literal_eval(assignment.value)
    assert actual == EXPECTED_LANGUAGES
    assert len(actual) == 52
    assert actual[16].startswith("16 – Coreano")
    assert actual[17].startswith("16 – Irlandês")


def test_video_creation_and_scripts_use_language_options_constant():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    assert '"Script Language"' in source
    assert "VIDEO_LANGUAGE_OPTIONS" in source
    assert 'key=f"{prefix}_script_language"' in source
