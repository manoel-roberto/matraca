"""Pipeline de normalização de texto para narração (RF-09, RF-10, A.13.3).

Executa uma sequência estrita e pura de etapas transformadoras. Cada etapa é
testável isoladamente e possui flag de ativação em `NormalizationConfig`.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field

from matraca.core.exceptions import NormalizacaoError
from matraca.text.dates import normalize_dates
from matraca.text.legal_terms import (
    normalize_articles_and_paragraphs,
    normalize_incisos,
    normalize_legal_abbreviations,
)
from matraca.text.linebreaks import join_broken_lines, undo_line_end_hyphenation
from matraca.text.numbers import (
    normalize_currency,
    normalize_decimal_and_thousands,
    normalize_laws,
    normalize_percentages,
)

# Siglas padrão e suas pronúncias recomendadas para síntese natural
DEFAULT_ACRONYMS: dict[str, str] = {
    "CF/88": "Constituição Federal de oitenta e oito",
    "CF": "Constituição Federal",
    "STF": "S T F",
    "STJ": "S T J",
    "TST": "T S T",
    "TSE": "T S E",
    "TRF": "T R F",
    "TJ": "T J",
    "MP": "Ministério Público",
    "MPU": "M P U",
    "OAB": "O A B",
    "CPC": "C P C",
    "CPP": "C P P",
    "CLT": "C L T",
    "CC": "Código Civil",
    "CP": "Código Penal",
    "CTN": "Código Tributário Nacional",
}

# Caracteres invisíveis ou de controle a remover
_ZERO_WIDTH = re.compile(r"[\u200B\u200C\u200D\uFEFF\xad]")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTIPLE_SPACES = re.compile(r"[ \t]+")


@dataclass(frozen=True)
class NormalizationConfig:
    """Configuração imutável do pipeline de normalização."""

    enable_unicode_cleanup: bool = True
    enable_line_reconstruction: bool = True
    enable_legal_abbreviations: bool = True
    enable_laws_and_dates: bool = True
    enable_currency_and_percents: bool = True
    enable_articles_and_incisos: bool = True
    enable_numbers: bool = True
    enable_acronyms: bool = True
    enable_prosody: bool = True
    custom_acronyms: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PipelineStep:
    """Uma etapa pura no pipeline."""

    name: str
    func: Callable[[str, NormalizationConfig], str]
    is_enabled: Callable[[NormalizationConfig], bool]


def _step_unicode(text: str, cfg: NormalizationConfig) -> str:
    text = unicodedata.normalize("NFC", text)
    text = _ZERO_WIDTH.sub("", text)
    text = _CONTROL_CHARS.sub("", text)
    # Padroniza aspas e apóstrofos
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    return text


def _step_linebreaks(text: str, cfg: NormalizationConfig) -> str:
    text = undo_line_end_hyphenation(text)
    return join_broken_lines(text)


def _step_legal_abbr(text: str, cfg: NormalizationConfig) -> str:
    return normalize_legal_abbreviations(text)


def _step_laws_and_dates(text: str, cfg: NormalizationConfig) -> str:
    text = normalize_laws(text)
    return normalize_dates(text)


def _step_currency_and_percents(text: str, cfg: NormalizationConfig) -> str:
    text = normalize_currency(text)
    return normalize_percentages(text)


def _step_articles_and_incisos(text: str, cfg: NormalizationConfig) -> str:
    text = normalize_articles_and_paragraphs(text)
    return normalize_incisos(text)


def _step_numbers(text: str, cfg: NormalizationConfig) -> str:
    return normalize_decimal_and_thousands(text)


def _step_acronyms(text: str, cfg: NormalizationConfig) -> str:
    acronyms = {**DEFAULT_ACRONYMS, **cfg.custom_acronyms}
    for acronym, replacement in acronyms.items():
        # Usa limite estrito de palavra \b
        pattern = rf"\b{re.escape(acronym)}\b"
        text = re.sub(pattern, replacement, text)
    return text


def _step_prosody(text: str, cfg: NormalizationConfig) -> str:
    # Remove espaços duplos horizontais
    lines = [_MULTIPLE_SPACES.sub(" ", line).strip() for line in text.split("\n")]
    res = "\n".join(lines)
    # Remove mais de duas quebras de linha seguidas
    res = re.sub(r"\n{3,}", "\n\n", res)
    return res.strip()


# Ordem estrita e documentada das etapas
PIPELINE_STEPS: tuple[PipelineStep, ...] = (
    PipelineStep("cleanup_unicode", _step_unicode, lambda c: c.enable_unicode_cleanup),
    PipelineStep("reconstruct_lines", _step_linebreaks, lambda c: c.enable_line_reconstruction),
    PipelineStep("legal_abbreviations", _step_legal_abbr, lambda c: c.enable_legal_abbreviations),
    PipelineStep("laws_and_dates", _step_laws_and_dates, lambda c: c.enable_laws_and_dates),
    PipelineStep(
        "currency_and_percents",
        _step_currency_and_percents,
        lambda c: c.enable_currency_and_percents,
    ),
    PipelineStep(
        "articles_and_incisos", _step_articles_and_incisos, lambda c: c.enable_articles_and_incisos
    ),
    PipelineStep("numbers", _step_numbers, lambda c: c.enable_numbers),
    PipelineStep("acronyms", _step_acronyms, lambda c: c.enable_acronyms),
    PipelineStep("adjust_prosody", _step_prosody, lambda c: c.enable_prosody),
)


def normalize_text(
    text: str, config: NormalizationConfig | None = None
) -> tuple[str, dict[str, int], tuple[str, ...]]:
    """Executa o pipeline completo de normalização sobre `text`.

    Devolve: (texto_normalizado, estatísticas, avisos).
    """
    if not text:
        return "", {"original_chars": 0, "normalized_chars": 0}, ()

    cfg = config or NormalizationConfig()
    current = text
    warnings: list[str] = []

    for step in PIPELINE_STEPS:
        if step.is_enabled(cfg):
            try:
                current = step.func(current, cfg)
            except Exception as exc:
                raise NormalizacaoError(
                    f"Falha na etapa de normalização: {step.name}.",
                    detail=f"{type(exc).__name__}: {exc}",
                ) from exc

    if not current.strip() and text.strip():
        warnings.append("O texto normalizado ficou vazio após o processamento.")

    stats = {
        "original_chars": len(text),
        "normalized_chars": len(current),
        "words": len(current.split()) if current else 0,
    }
    return current, stats, tuple(warnings)
