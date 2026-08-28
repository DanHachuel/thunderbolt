"""Structured, original music briefs generated through the configured LLM pool."""

from __future__ import annotations

import json
from typing import Any

from .creative_generation import CreativeGenerationError, _chat_json
from .languages import language_code


MUSIC_GENRES = (
    "Pop", "Rock", "Hip Hop", "EDM (Eletrônica)", "Techno", "Country", "Folk", "Indie", "K-pop", "Jazz",
    "Reggae", "Classical", "Metal", "Punk", "Afrobeat (Nigéria)", "Ambient (Reino Unido)", "Anime (Japão)",
    "Arabic Pop / Khaleeji (Mundo Árabe)", "Austropop (Áustria)", "Ballad (Internacional)", "Banda (México)",
    "Blues (EUA)", "Bollywood / Indian (Índia)", "City Pop (Japão)", "Corridos Tumbados (México)", "C-pop (China)",
    "Cumbia (Colômbia)", "Dangdut (Indonésia)", "Dansband (Suécia)", "Deutschrap (Alemanha)",
    "Disco Polo (Polônia)", "Drum & Bass (Reino Unido)", "Entechno (Grécia)", "Fado (Portugal)",
    "Flamenco (Espanha)", "Forró (Brasil)", "Funk (Brasil)", "Fusion (Internacional)", "Gamolan (Indonésia)",
    "Gospel (EUA)", "Grime (Reino Unido)", "Hardstyle (Países Baixos)", "J-Pop (Japão)", "J-Rock (Japão)",
    "K-Hip Hop (Coreia do Sul)", "Kizomba (Angola)", "Klapa (Croácia)", "Klezmer (Judeu / Europa Oriental)",
    "Laïko (Grécia)", "Latin (América Latina)", "Mandopop (China / Taiwan)", "Māori (Nova Zelândia)", "MPB (Brasil)",
    "Mundart (Dialect Pop) (Suíça)", "Pasifika (Pacífico)", "Pimba (Portugal)", "Pop Sueco (Suécia)", "R&B (EUA)",
    "Rap Francês (França)", "Reggaeton (Porto Rico)", "Regional Mexicano (México)", "Samba / Pagode (Brasil)",
    "Schlager (Alemanha)", "Sertanejo (Brasil)", "Trot (Coreia do Sul)", "Urbano / Trap (América Latina)",
    "Variété (França)", "Vocaloid (Japão)",
)
MUSIC_VOCAL_OPTIONS = ("Masculino", "Feminina", "Coral")


def generate_music_fields(
    settings: dict[str, Any],
    *,
    theme: str,
    language: str,
    genre: str,
    vocal: str,
    references: str = "",
) -> dict[str, str]:
    """Generate original, ready-to-use music fields through the active LLM pool."""
    cleaned_theme = str(theme or "").strip()
    if not cleaned_theme:
        raise CreativeGenerationError("Escreva o tema ou assunto principal antes de gerar os campos musicais com IA.")
    selected_genre = str(genre or "").strip()
    selected_vocal = str(vocal or "").strip()
    selected_language = language_code(language)
    system = (
        "És um compositor e produtor musical. Cria uma canção inteiramente original, sem reproduzir letras, melodias, "
        "frases distintivas ou a identidade de artistas existentes. As referências fornecidas servem apenas para atributos "
        "de alto nível, como instrumentação, clima, contexto cultural e energia. Responde apenas com JSON válido contendo "
        "as chaves title, language, genre, vocal, cultural_references e music_prompt. "
        "music_prompt deve ser Markdown legível, pronto para uma ferramenta de geração musical, com exactamente estas secções: "
        "# 1. Nome da Música, # 2. Idioma da Música, # 3. Letra / Lyrics, # 4. Estilo / Style Prompt. "
        "A letra deve ser original, incluir [Intro], [Verse 1], [Pre-Chorus], [Chorus], [Verse 2], [Bridge], "
        "[Instrumental Solo], [Final Chorus] e [Outro], ter uma estrutura que vise pelo menos dois minutos, e o estilo deve "
        "informar subgénero, vocal, instrumentação, BPM, clima, produção e estrutura."
    )
    user = json.dumps(
        {
            "theme": cleaned_theme,
            "selected_language_code": selected_language,
            "selected_genre": selected_genre,
            "selected_vocal": selected_vocal,
            "cultural_landscape_weather_or_artist_references": str(references or "").strip(),
            "available_genres": list(MUSIC_GENRES),
            "available_vocals": list(MUSIC_VOCAL_OPTIONS),
            "requirements": {
                "minimum_target_duration_seconds": 120,
                "preserve_selected_language_genre_and_vocal_when_present": True,
                "output_original_content_only": True,
            },
        },
        ensure_ascii=False,
    )
    result = _chat_json(settings, system, user)
    music_prompt = str(result.get("music_prompt") or "").strip()
    if not music_prompt:
        raise CreativeGenerationError("O provider LLM não devolveu um prompt musical válido.")
    generated_genre = str(result.get("genre") or selected_genre).strip()
    generated_vocal = str(result.get("vocal") or selected_vocal).strip()
    return {
        "title": str(result.get("title") or cleaned_theme).strip()[:180],
        "language": language_code(result.get("language"), default=selected_language),
        "genre": generated_genre if generated_genre in MUSIC_GENRES else selected_genre,
        "vocal": generated_vocal if generated_vocal in MUSIC_VOCAL_OPTIONS else selected_vocal,
        "references": str(result.get("cultural_references") or references or "").strip()[:800],
        "prompt": music_prompt[:16000],
    }
