"""Reconstrução de linhas, parágrafos e hifenização (RF-09, A.13.4).

Trabalha sobre o texto extraído para unir linhas quebradas no meio de frases,
desfazer hifenização ao final de linha e preservar a estrutura de parágrafos,
listas, incisos e títulos.
"""

from __future__ import annotations

import re

# Prefixos comuns em português onde o hífen DEVE ser mantido mesmo se quebrar de linha
_PREFIXES_KEEP_HYPHEN = frozenset(
    {
        "ex",
        "vice",
        "semi",
        "anti",
        "super",
        "pos",
        "pós",
        "pre",
        "pré",
        "pro",
        "pró",
        "sub",
        "sobre",
        "auto",
        "co",
        "contra",
        "infra",
        "ultra",
    }
)

_LINEBREAK_HYPHEN = re.compile(r"(\b[a-zA-ZÀ-ÿ]+)[-\xad\u2010\u2011]\s*\n\s*([a-zA-ZÀ-ÿ]+\b)")
_LIST_OR_LEGAL_START = re.compile(
    r"^\s*(?:[-•●▪◦]|\(?[a-zA-Z0-9IVXLCDM]+\)[-–—\s]?|[0-9]{1,3}[.)]|Art\.|Arts\.|§|§§|Parágrafo|Inciso|Alínea)\b"
)
_HEADING_LIKE = re.compile(r"^[A-Z0-9À-Ý\s\-_:]{4,80}$")


def undo_line_end_hyphenation(text: str) -> str:
    """Une palavras hifenizadas no fim de linha (ex: pala-\\nvra -> palavra).

    Preserva hífens de compostos ou prefixos reconhecidos (ex: ex-\\npresidente -> ex-presidente).
    """

    def _replace_hyphen(match: re.Match[str]) -> str:
        prefix = match.group(1)
        suffix = match.group(2)
        if prefix.lower() in _PREFIXES_KEEP_HYPHEN:
            return f"{prefix}-{suffix}"
        return f"{prefix}{suffix}"

    return _LINEBREAK_HYPHEN.sub(_replace_hyphen, text)


def join_broken_lines(text: str) -> str:
    """Une linhas quebradas no meio de frases preservando parágrafos e listas.

    Regras:
    - Linhas vazias indicam quebra de parágrafo e são preservadas.
    - Se a linha anterior termina sem pontuação final (. ! ? : ;) e a próxima
      não parece ser um item de lista, título ou dispositivo legal, une com espaço.
    """
    lines = text.split("\n")
    if len(lines) <= 1:
        return text

    merged: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if merged and merged[-1] != "":
                merged.append("")
            continue

        if not merged or merged[-1] == "":
            merged.append(stripped)
            continue

        prev = merged[-1]

        # Se a linha anterior termina com pontuação final forte ou dois pontos, não une
        ends_with_terminal = prev and prev[-1] in {".", "!", "?", ":", ";"}
        is_new_block = (
            _LIST_OR_LEGAL_START.match(stripped) is not None
            or _HEADING_LIKE.match(stripped) is not None
        )

        if not ends_with_terminal and not is_new_block:
            # Continuação da frase anterior
            merged[-1] = f"{prev} {stripped}"
        else:
            merged.append(stripped)

    # Reconstitui os parágrafos preservando quebras duplas
    result_paragraphs: list[str] = []
    current_par: list[str] = []

    for item in merged:
        if item == "":
            if current_par:
                result_paragraphs.append(" ".join(current_par))
                current_par = []
        else:
            current_par.append(item)

    if current_par:
        result_paragraphs.append(" ".join(current_par))

    return "\n\n".join(result_paragraphs)
