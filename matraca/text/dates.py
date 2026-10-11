"""Normalização de datas em formato pt-BR (RF-09, A.13.3)."""

from __future__ import annotations

import re

from matraca.text.numbers import int_to_cardinal

MONTH_NAMES = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}

# Data no formato dd/mm/aaaa ou dd/mm/aa com dia e mês de 2 dígitos (ou 1 se explícito)
_DATE_SLASH = re.compile(r"\b(0?[1-9]|[12][0-9]|3[01])/(0?[1-9]|1[0-2])/([12][0-9]{3}|[0-9]{2})\b")

# Data por extenso com dia numeral: 1º de abril de 2021 ou 15 de março de 2020
_DATE_EXTENSO = re.compile(
    r"\b(1[º°]|0?[1-9]|[12][0-9]|3[01])\s+de\s+"
    r"(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)"
    r"\s+de\s+([12][0-9]{3})\b",
    re.IGNORECASE,
)


def normalize_dates(text: str) -> str:
    """Normaliza datas estritas no padrão dd/mm/aaaa para texto falado.

    Casos ambíguos (ex: 3/4 ou 2020/2021) NÃO são capturados por esta regex.
    """

    def _replace_slash_date(m: re.Match[str]) -> str:
        day = int(m.group(1))
        month = int(m.group(2))
        year_str = m.group(3)

        # No Brasil, o primeiro dia do mês é falado como "primeiro"
        day_spoken = "primeiro" if day == 1 else int_to_cardinal(day)
        month_spoken = MONTH_NAMES.get(month, "")

        year = int(year_str)
        if len(year_str) == 2:
            # Interpreta 2 dígitos: >= 50 século XX (19xx), < 50 século XXI (20xx)
            year = 1900 + year if year >= 50 else 2000 + year
        year_spoken = int_to_cardinal(year)

        return f"{day_spoken} de {month_spoken} de {year_spoken}"

    text = _DATE_SLASH.sub(_replace_slash_date, text)

    def _replace_extenso_date(m: re.Match[str]) -> str:
        day_raw = m.group(1)
        month_name = m.group(2).lower()
        year_val = int(m.group(3))

        if day_raw in ("1º", "1°", "1", "01"):
            day_spoken = "primeiro"
        else:
            day_spoken = int_to_cardinal(int(day_raw))

        year_spoken = int_to_cardinal(year_val)
        return f"{day_spoken} de {month_name} de {year_spoken}"

    return _DATE_EXTENSO.sub(_replace_extenso_date, text)
