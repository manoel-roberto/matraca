"""Normalização de termos, abreviações e dispositivos jurídicos (RF-09, A.13.3)."""

from __future__ import annotations

import re

from matraca.text.numbers import ROMAN_TO_INT, int_to_cardinal, int_to_ordinal

# Abreviação de número: nº, n.º, nº., n°, n.°
_NUM_ABBR = re.compile(r"\bn[º°\.]+\s*", re.IGNORECASE)

# Expressões latinas/jurídicas comuns
_JURIDICAL_EXPRESSIONS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bc/c\b", re.IGNORECASE), "combinado com"),
    (re.compile(r"\bp\.\s*ex\.(?=\s|[.,;:]|$)", re.IGNORECASE), "por exemplo"),
    (re.compile(r"\barts\.(?=\s|[0-9]|$)", re.IGNORECASE), "Artigos "),
    (re.compile(r"\bart\.(?=\s|[0-9]|$)", re.IGNORECASE), "Artigo "),
    (re.compile(r"\binc\.(?=\s|[IVXLCDM]|$)", re.IGNORECASE), "inciso "),
    (re.compile(r"\bal\.(?=\s|[a-zA-Z]|$)", re.IGNORECASE), "alínea "),
    (re.compile(r"§§\s*", re.IGNORECASE), "parágrafos "),
    (re.compile(r"§\s*único\b", re.IGNORECASE), "parágrafo único"),
    (re.compile(r"§\s*", re.IGNORECASE), "parágrafo "),
]

# Casos em que números romanos NÃO são incisos (ex: Reis, Séculos, Títulos, Capítulos)
_NON_INCISO_MONARCH = re.compile(
    r"\b(Papa|Rei|Rainha|D\.|Dom|Príncipe|Princesa)\s+([A-Za-zÀ-ÿ]+\s+)?([IVXLCDM]+)\b",
    re.IGNORECASE,
)
_NON_INCISO_ROMAN = re.compile(
    r"\b(Século|Sec\.|Capítulo|Cap\.|Título|Tit\.|Livro)\s+([IVXLCDM]+)\b",
    re.IGNORECASE,
)

# Inciso explícito: "inciso II" ou "incisos I e II"
_INCISO_EXPLICIT = re.compile(
    r"\b(incisos?)\s+([IVXLCDM]+)\b",
    re.IGNORECASE,
)

# Inciso no início de dispositivo legal: "II - texto" ou "II – texto"
_INCISO_START_LINE = re.compile(
    r"(^|\n)\s*([IVXLCDM]+)\s*[-–—]\s*",
)

# Artigos e parágrafos coordenados: "Artigos 5º e 6º", "parágrafos 1º e 2º"
_ARTIGO_COORD = re.compile(
    r"\b(Artigos?)\s+([0-9]{1,4})(?:[º°ª\.]*)?\s+e\s+([0-9]{1,4})(?:[º°ª\.]*)?",
    re.IGNORECASE,
)
_PARAGRAFO_COORD = re.compile(
    r"\b(parágrafos?)\s+([0-9]{1,4})(?:[º°ª\.]*)?\s+e\s+([0-9]{1,4})(?:[º°ª\.]*)?",
    re.IGNORECASE,
)

# Artigo singular ou plural seguido de numeral: "Artigo 5º", "Artigo 5"
_ARTIGO_NUMERAL = re.compile(
    r"\b(Artigos?)\s+([0-9]{1,4})([º°ªa-zA-Z\.]*)?",
    re.IGNORECASE,
)

# Parágrafo singular ou plural seguido de numeral: "parágrafo 1º", "parágrafo 10"
_PARAGRAFO_NUMERAL = re.compile(
    r"\b(parágrafos?)\s+([0-9]{1,4})([º°ªa-zA-Z\.]*)?",
    re.IGNORECASE,
)


def _format_article_number(num: int) -> str:
    """Artigos até 9 são ordinais (Artigo quinto); a partir de 10 são cardinais (Artigo dez)."""
    if 1 <= num <= 9:
        return int_to_ordinal(num, gender="m")
    return int_to_cardinal(num)


def _format_paragraph_number(num: int) -> str:
    """Parágrafos até 9 são ordinais (parágrafo primeiro); a partir de 10 são cardinais.

    Exemplo: 10 -> parágrafo dez.
    """
    if 1 <= num <= 9:
        return int_to_ordinal(num, gender="m")
    return int_to_cardinal(num)


def normalize_legal_abbreviations(text: str) -> str:
    """Substitui abreviações e símbolos jurídicos preservando palavras compostas."""
    # Primeiro protege expressões como 'Martin', 'Particular', 'Cart.' garantindo \b
    for pattern, replacement in _JURIDICAL_EXPRESSIONS:
        text = pattern.sub(replacement, text)

    # Substitui nº / n.º por 'número '
    text = _NUM_ABBR.sub("número ", text)

    return text


def normalize_articles_and_paragraphs(text: str) -> str:
    """Normaliza leitura de artigos (Artigo quinto / Artigo trinta e sete) e parágrafos."""

    # Trata primeiro pares coordenados com "e"
    def _replace_art_coord(m: re.Match[str]) -> str:
        word = m.group(1)
        n1 = int(m.group(2))
        n2 = int(m.group(3))
        return f"{word} {_format_article_number(n1)} e {_format_article_number(n2)}"

    text = _ARTIGO_COORD.sub(_replace_art_coord, text)

    def _replace_par_coord(m: re.Match[str]) -> str:
        word = m.group(1)
        n1 = int(m.group(2))
        n2 = int(m.group(3))
        return f"{word} {_format_paragraph_number(n1)} e {_format_paragraph_number(n2)}"

    text = _PARAGRAFO_COORD.sub(_replace_par_coord, text)

    # Trata ocorrências individuais
    def _replace_art(m: re.Match[str]) -> str:
        word = m.group(1)
        num = int(m.group(2))
        return f"{word} {_format_article_number(num)}"

    text = _ARTIGO_NUMERAL.sub(_replace_art, text)

    def _replace_par(m: re.Match[str]) -> str:
        word = m.group(1)
        num = int(m.group(2))
        return f"{word} {_format_paragraph_number(num)}"

    text = _PARAGRAFO_NUMERAL.sub(_replace_par, text)
    return text


def normalize_incisos(text: str) -> str:
    """Normaliza incisos para numeração cardinal (ex: inciso dois), preservando outros romanos."""

    # Trata monarcas e papas com ou sem nome intermediário (ex: Rei João II -> Rei João segundo)
    def _replace_monarch(m: re.Match[str]) -> str:
        prefix = m.group(1)
        name = m.group(2) or ""
        roman = m.group(3).upper()
        val = ROMAN_TO_INT.get(roman)
        if val is None:
            return m.group(0)
        return f"{prefix} {name}{int_to_ordinal(val, gender='m')}".strip()

    text = _NON_INCISO_MONARCH.sub(_replace_monarch, text)

    # Protege não-incisos (ex: Século XX, Capítulo II)
    def _replace_non_inciso(m: re.Match[str]) -> str:
        prefix = m.group(1)
        roman = m.group(2).upper()
        val = ROMAN_TO_INT.get(roman)
        if val is None:
            return m.group(0)

        prefix_lower = prefix.lower()
        if "século" in prefix_lower or "sec." in prefix_lower:
            return f"{prefix} {int_to_cardinal(val)}"
        if any(k in prefix_lower for k in ("capítulo", "cap.", "título", "tit.")):
            return f"{prefix} {_format_article_number(val)}"
        return m.group(0)

    text = _NON_INCISO_ROMAN.sub(_replace_non_inciso, text)

    # Incisos explícitos: "inciso II" -> "inciso dois"
    def _replace_inciso_exp(m: re.Match[str]) -> str:
        word = m.group(1)
        roman = m.group(2).upper()
        val = ROMAN_TO_INT.get(roman)
        if val is not None:
            return f"{word} {int_to_cardinal(val)}"
        return m.group(0)

    text = _INCISO_EXPLICIT.sub(_replace_inciso_exp, text)

    # Incisos no início de linha: "II - ..." -> "inciso dois - ..."
    def _replace_inciso_start(m: re.Match[str]) -> str:
        prefix_nl = m.group(1)
        roman = m.group(2).upper()
        val = ROMAN_TO_INT.get(roman)
        if val is not None:
            return f"{prefix_nl}inciso {int_to_cardinal(val)} - "
        return m.group(0)

    text = _INCISO_START_LINE.sub(_replace_inciso_start, text)
    return text
