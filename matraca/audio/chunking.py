"""Segmentador de texto para narração de áudio (A.13.5).

Divide o texto normalizado em blocos seguros para envio ao TTS, respeitando
a hierarquia semântica: parágrafos > frases > vírgulas > palavras.
"""

from __future__ import annotations

import re

# Padrão conservador de limite em caracteres para chunks de TTS
DEFAULT_CHUNK_MAX_CHARS = 1500

# Abreviações comuns que não devem ser tratadas como fim de sentença
_COMMON_ABBREVIATIONS = (
    r"art",
    r"arts",
    r"dr",
    r"dra",
    r"sr",
    r"sra",
    r"etc",
    r"ex",
    r"inc",
    r"fl",
    r"fls",
    r"pag",
    r"pags",
    r"p",
    r"par",
    r"prof",
    r"profa",
    r"min",
    r"des",
    r"gov",
    r"dept",
)

_ABBR_PATTERN = re.compile(
    r"\b(?:" + "|".join(_COMMON_ABBREVIATIONS) + r")\.\s*$",
    re.IGNORECASE,
)


def _split_into_sentences(text: str) -> list[str]:
    """Divide texto em frases respeitando pontuação e abreviações."""
    # Encontra posições de pontuação final (. ! ?)
    tokens: list[str] = []
    start = 0
    i = 0
    n = len(text)

    while i < n:
        char = text[i]
        if char in {".", "!", "?"}:
            # Verifica se é abreviação conhecida
            substr_before = text[start : i + 1]
            if char == "." and _ABBR_PATTERN.search(substr_before):
                i += 1
                continue

            # Verifica se é número com separador de milhar (ex: 1.000)
            if (
                char == "."
                and i > 0
                and text[i - 1].isdigit()
                and i + 1 < n
                and text[i + 1].isdigit()
            ):
                i += 1
                continue

            # Fim de sentença candidato
            if i + 1 == n or text[i + 1].isspace():
                sentence = text[start : i + 1].strip()
                if sentence:
                    tokens.append(sentence)
                i += 1
                # Pula espaços
                while i < n and text[i].isspace():
                    i += 1
                start = i
                continue
        i += 1

    if start < n:
        tail = text[start:].strip()
        if tail:
            tokens.append(tail)

    return tokens or ([text.strip()] if text.strip() else [])


def _split_by_clause(text: str) -> list[str]:
    """Divide sentença por vírgulas ou ponto-e-vírgulas."""
    parts = re.split(r"(?<=[,;])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _split_by_words(text: str, max_chars: int) -> list[str]:
    """Divide texto longo por espaços em branco sem cortar palavras."""
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    current_words: list[str] = []
    current_len = 0

    for w in words:
        word_len = len(w)
        # Se uma única palavra for maior que max_chars, ela forma um chunk próprio
        if not current_words and word_len >= max_chars:
            chunks.append(w)
            continue

        extra = 1 if current_words else 0
        if current_len + extra + word_len <= max_chars:
            current_words.append(w)
            current_len += extra + word_len
        else:
            if current_words:
                chunks.append(" ".join(current_words))
            current_words = [w]
            current_len = word_len

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def _fit_smaller_pieces(pieces: list[str], max_chars: int) -> list[str]:
    """Agrupa peças menores garantindo que a soma não exceda max_chars."""
    chunks: list[str] = []
    current_acc: list[str] = []
    current_len = 0

    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        p_len = len(piece)

        if p_len > max_chars:
            # Descarrega o que tínhamos acumulado
            if current_acc:
                chunks.append(" ".join(current_acc))
                current_acc = []
                current_len = 0

            # Como a peça é maior que max_chars, tenta dividir por orações (, ;)
            clauses = _split_by_clause(piece)
            if len(clauses) > 1 and all(len(c) <= max_chars for c in clauses):
                sub_chunks = _fit_smaller_pieces(clauses, max_chars)
                chunks.extend(sub_chunks)
            else:
                # Se ainda houver pedaço maior que max_chars, divide por palavras
                word_chunks = _split_by_words(piece, max_chars)
                chunks.extend(word_chunks)
            continue

        extra = 1 if current_acc else 0
        if current_len + extra + p_len <= max_chars:
            current_acc.append(piece)
            current_len += extra + p_len
        else:
            if current_acc:
                chunks.append(" ".join(current_acc))
            current_acc = [piece]
            current_len = p_len

    if current_acc:
        chunks.append(" ".join(current_acc))

    return chunks


def chunk_text(text: str, max_chars: int = DEFAULT_CHUNK_MAX_CHARS) -> list[str]:
    """Segmenta o texto normalizado respeitando hierarquia semântica.

    Ordem de prioridade para cortes:
    1. Parágrafos (quebras de linha duplas ou simples)
    2. Frases (pontuação terminal '.', '!', '?')
    3. Orações (vírgula ',', ponto e vírgula ';')
    4. Palavras (espaço em branco)
    """
    if max_chars < 50:
        raise ValueError("max_chars deve ser pelo menos 50")

    clean = text.strip()
    if not clean:
        return []

    # Se o texto inteiro já cabe no limite, retorna imediatamente
    if len(clean) <= max_chars:
        return [clean]

    # 1. Divide em parágrafos
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\n", clean) if p.strip()]

    chunks: list[str] = []
    current_group: list[str] = []
    current_len = 0

    for p in paragraphs:
        p_len = len(p)
        if p_len <= max_chars:
            extra = 2 if current_group else 0  # "\n\n" entre parágrafos
            if current_len + extra + p_len <= max_chars:
                current_group.append(p)
                current_len += extra + p_len
            else:
                if current_group:
                    chunks.append("\n\n".join(current_group))
                current_group = [p]
                current_len = p_len
        else:
            # Parágrafo maior que max_chars: descarrega grupo anterior
            if current_group:
                chunks.append("\n\n".join(current_group))
                current_group = []
                current_len = 0

            # 2. Divide parágrafo grande em frases
            sentences = _split_into_sentences(p)
            sentence_chunks = _fit_smaller_pieces(sentences, max_chars)
            chunks.extend(sentence_chunks)

    if current_group:
        chunks.append("\n\n".join(current_group))

    return [c.strip() for c in chunks if c.strip()]
