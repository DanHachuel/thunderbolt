"""Canonical country catalog for social-account metadata."""

from __future__ import annotations

COUNTRY_OPTIONS: tuple[str, ...] = (
    "Abecásia", "Afeganistão", "África do Sul", "Albânia", "Alemanha", "Andorra", "Angola",
    "Antígua e Barbuda", "Arábia Saudita", "Argélia", "Argentina", "Armênia", "Austrália", "Áustria",
    "Azerbaijão", "Bahamas", "Bahrein", "Bangladesh", "Barbados", "Bélgica", "Belize", "Benim",
    "Bielorrússia", "Bolívia", "Bósnia e Herzegovina", "Botsuana", "Brasil", "Brunei", "Bulgária",
    "Burquina Fasso", "Burundi", "Butão", "Cabo Verde", "Camarões", "Camboja", "Canadá", "Catar",
    "Cazaquistão", "Chade", "Chile", "China", "Chipre", "Chipre do Norte", "Cingapura", "Colômbia",
    "Comores", "Congo", "Coreia do Norte", "Coreia do Sul", "Costa do Marfim", "Costa Rica", "Croácia",
    "Cuba", "Dinamarca", "Djibouti", "Dominica", "República Dominicana", "Egito", "El Salvador",
    "Emirados Árabes Unidos", "Equador", "Eritreia", "Eslováquia", "Eslovênia", "Espanha",
    "Estados Federados da Micronésia", "Estados Unidos", "Estônia", "Essuatíni (Suazilândia)", "Etiópia",
    "Fiji", "Filipinas", "Finlândia", "França", "Gabão", "Gâmbia", "Gana", "Geórgia", "Granada",
    "Grécia", "Guatemala", "Guiana", "Guiné", "Guiné-Bissau", "Guiné Equatorial", "Haiti", "Honduras",
    "Hungria", "Iêmen", "Ilhas Cook", "Índia", "Indonésia", "Irã", "Irlanda", "Islândia", "Israel",
    "Itália", "Jamaica", "Japão", "Jordânia", "Kiribati", "Kosovo", "Kuwait", "Laos", "Lesoto",
    "Letônia", "Líbano", "Libéria", "Líbia", "Liechtenstein", "Lituânia", "Luxemburgo", "Macedônia do Norte",
    "Madagascar", "Malásia", "Malawi", "Maldivas", "Mali", "Malta", "Marrocos", "Ilhas Marshall",
    "Maurício", "Mauritânia", "México", "Mianmar", "Moçambique", "Moldávia", "Mônaco", "Mongólia",
    "Montenegro", "Namíbia", "Nauru", "Nepal", "Nicarágua", "Níger", "Nigéria", "Niue", "Noruega",
    "Nova Zelândia", "Omã", "Ossétia do Sul", "Países Baixos", "Palau", "Palestina", "Panamá",
    "Papua-Nova Guiné", "Paquistão", "Paraguai", "Peru", "Polônia", "Portugal", "Quênia", "Quirguistão",
    "Reino Unido", "República Centro-Africana", "República Checa", "República Democrática do Congo", "Romênia",
    "Ruanda", "Rússia", "Saara Ocidental (República Árabe Saharaui Democrática)", "Samoa", "San Marino",
    "Santa Lúcia", "São Cristóvão e Nevis", "São Tomé e Príncipe", "São Vicente e Granadinas", "Senegal",
    "Serra Leoa", "Sérvia", "Seicheles", "Somália", "Somalilândia", "Sri Lanka", "Sudão", "Sudão do Sul",
    "Suécia", "Suíça", "Suriname", "Síria", "Tajiquistão", "Tailândia", "Taiwan", "Tanzânia",
    "Timor-Leste", "Togo", "Tonga", "Transnístria", "Trinidad e Tobago", "Tunísia", "Turcomenistão",
    "Turquia", "Tuvalu", "Ucrânia", "Uganda", "Uruguai", "Uzbequistão", "Vanuatu", "Vaticano (Santa Sé)",
    "Venezuela", "Vietnã", "Zâmbia", "Zimbábue",
)


def country_index(value: object) -> int:
    """Return the selector index while keeping legacy/empty values usable."""
    value = str(value or "").strip()
    return COUNTRY_OPTIONS.index(value) if value in COUNTRY_OPTIONS else 0


__all__ = ["COUNTRY_OPTIONS", "country_index"]
