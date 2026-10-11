"""Normalização de números, moeda, porcentagem, leis e números romanos (RF-09, A.13.3)."""

from __future__ import annotations

import re

from num2words import num2words

# Mapeamento de números romanos para inteiros
ROMAN_TO_INT: dict[str, int] = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
    "XIII": 13,
    "XIV": 14,
    "XV": 15,
    "XVI": 16,
    "XVII": 17,
    "XVIII": 18,
    "XIX": 19,
    "XX": 20,
    "XXI": 21,
    "XXII": 22,
    "XXIII": 23,
    "XXIV": 24,
    "XXV": 25,
    "XXVI": 26,
    "XXVII": 27,
    "XXVIII": 28,
    "XXIX": 29,
    "XXX": 30,
    "XL": 40,
    "L": 50,
    "LX": 60,
    "LXX": 70,
    "LXXX": 80,
    "XC": 90,
    "C": 100,
}

# Ordinais básicos masculinos e femininos
ORDINALS_MASC = {
    1: "primeiro",
    2: "segundo",
    3: "terceiro",
    4: "quarto",
    5: "quinto",
    6: "sexto",
    7: "sétimo",
    8: "oitavo",
    9: "nono",
    10: "décimo",
}

ORDINALS_FEM = {
    1: "primeira",
    2: "segunda",
    3: "terceira",
    4: "quarta",
    5: "quinta",
    6: "sexta",
    7: "sétima",
    8: "oitava",
    9: "nona",
    10: "décima",
}

# Regex para leis: Lei 8.666/93, Lei nº 14.133/2021, Decreto-Lei 200/67
_LAW_WITH_SLASH = re.compile(
    r"\b((?:Lei|Decreto(?:-Lei)?|Portaria|Resolução|Emenda Constitucional|Instrução Normativa)"
    r"(?:\s+(?:n[º°\.]+|número))?\s+)"
    r"([0-9]{1,3}(?:\.[0-9]{3})*|[0-9]+)"
    r"\s*/\s*"
    r"([0-9]{2,4})\b",
    re.IGNORECASE,
)

# Regex para moeda pt-BR: R$ 1.250,00 ou R$ 50,00 ou R$ 0,50
_CURRENCY_BR = re.compile(r"\bR\$\s*([0-9]{1,3}(?:\.[0-9]{3})*|[0-9]+)(?:,([0-9]{2}))?\b")

# Regex para percentual: 10%, 2,5%, 0,85%
_PERCENT = re.compile(r"\b([0-9]+(?:,[0-9]+)?)\s*%")

# Regex para números com separador de milhar pt-BR sem vírgula: 1.234.567
_THOUSANDS_NUM = re.compile(r"\b([0-9]{1,3}(?:\.[0-9]{3})+)\b")

# Regex para número decimal pt-BR: 1.234,56 ou 12,50
_DECIMAL_NUM = re.compile(r"\b([0-9]{1,3}(?:\.[0-9]{3})*|[0-9]+),([0-9]+)\b")


def int_to_cardinal(n: int) -> str:
    """Converte inteiro em cardinal por extenso pt-BR."""
    try:
        res = str(num2words(n, lang="pt_BR"))
        # Ajusta vírgula opcional de num2words para fluidez natural
        return res.replace(", ", " ")
    except Exception:
        return str(n)


def int_to_ordinal(n: int, gender: str = "m") -> str:
    """Converte inteiro em ordinal por extenso pt-BR até 10 direto, ou via num2words."""
    if gender == "f" and n in ORDINALS_FEM:
        return ORDINALS_FEM[n]
    if gender == "m" and n in ORDINALS_MASC:
        return ORDINALS_MASC[n]
    try:
        res = str(num2words(n, lang="pt_BR", to="ordinal"))
        if gender == "f":
            # num2words pt_BR gera masculino por padrão
            res = re.sub(r"o\b", "a", res)
        return res
    except Exception:
        return f"{n}º" if gender == "m" else f"{n}ª"


def year_to_words(year_str: str) -> str:
    """Converte ano de 2 ou 4 dígitos em palavras.

    Exemplos: '93' -> 'noventa e três', '2021' -> 'dois mil e vinte e um'.
    """
    val = int(year_str)
    if len(year_str) == 2:
        return int_to_cardinal(val)
    return int_to_cardinal(val)


def normalize_laws(text: str) -> str:
    """Normaliza referências a leis com barras.

    Exemplo: Lei 8.666/93 -> Lei oito mil seiscentos e sessenta e seis, de noventa e três.
    """

    def _replace_law(m: re.Match[str]) -> str:
        prefix = m.group(1)
        num_raw = m.group(2).replace(".", "")
        year_raw = m.group(3)

        num_words = int_to_cardinal(int(num_raw))
        year_words = year_to_words(year_raw)
        return f"{prefix}{num_words}, de {year_words}"

    return _LAW_WITH_SLASH.sub(_replace_law, text)


def normalize_currency(text: str) -> str:
    """Normaliza moeda em reais: R$ 1.250,00 -> mil duzentos e cinquenta reais."""

    def _replace_curr(m: re.Match[str]) -> str:
        int_part = int(m.group(1).replace(".", ""))
        cents_part = int(m.group(2)) if m.group(2) else 0

        parts: list[str] = []
        if int_part > 0:
            reais = int_to_cardinal(int_part)
            if (
                reais.endswith("milhão")
                or reais.endswith("milhões")
                or reais.endswith("bilhão")
                or reais.endswith("bilhões")
            ):
                unit = "de reais"
            else:
                unit = "real" if int_part == 1 else "reais"
            parts.append(f"{reais} {unit}")

        if cents_part > 0:
            cents = int_to_cardinal(cents_part)
            unit_cents = "centavo" if cents_part == 1 else "centavos"
            parts.append(f"{cents} {unit_cents}")

        if not parts:
            return "zero real"
        return " e ".join(parts)

    return _CURRENCY_BR.sub(_replace_curr, text)


def normalize_percentages(text: str) -> str:
    """Normaliza porcentagens: 10% -> dez por cento; 2,5% -> dois vírgula cinco por cento."""

    def _replace_pct(m: re.Match[str]) -> str:
        val = m.group(1)
        if "," in val:
            inteiro, dec = val.split(",", 1)
            int_w = int_to_cardinal(int(inteiro))
            dec_w = int_to_cardinal(int(dec))
            return f"{int_w} vírgula {dec_w} por cento"
        return f"{int_to_cardinal(int(val))} por cento"

    return _PERCENT.sub(_replace_pct, text)


def normalize_decimal_and_thousands(text: str) -> str:
    """Normaliza números decimais e números com separador de milhar por extenso."""

    # Decimais com vírgula primeiro: 1.234,56 ->
    # mil duzentos e trinta e quatro vírgula cinquenta e seis
    def _replace_dec(m: re.Match[str]) -> str:
        int_str = m.group(1).replace(".", "")
        dec_str = m.group(2)
        int_w = int_to_cardinal(int(int_str))
        dec_w = int_to_cardinal(int(dec_str))
        return f"{int_w} vírgula {dec_w}"

    text = _DECIMAL_NUM.sub(_replace_dec, text)

    # Separador de milhar sem vírgula: 1.234.567
    def _replace_thous(m: re.Match[str]) -> str:
        num_str = m.group(1).replace(".", "")
        return int_to_cardinal(int(num_str))

    return _THOUSANDS_NUM.sub(_replace_thous, text)
