"""Detecção conservadora e explicável de cabeçalhos, rodapés e marcas d'água (RF-05, A.13.2).

Um bloco só é descartado quando **dois ou mais sinais** concordam, ou quando há um sinal forte
isolado (numeração de página na margem). Estar perto da margem, sozinho, nunca remove nada.

Sinais: `zona` (faixa superior/inferior), `repeticao` (mesmo texto, com dígitos trocados por `#`,
em várias páginas amostradas), `numeracao` (padrões como "Página 3 de 120", "3/120", "- 3 -"),
`rotacionado`, `claro` (marca d'água) e `padrao` (expressão regular configurada).
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass

from matraca.config import ExtractionConfig
from matraca.core.models import NoiseRecord, RawBlock, RawPage

_DIGITS = re.compile(r"\d+")
_SPACES = re.compile(r"\s+")
_NUMBERING = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"^(?:p[áa]gina|p[áa]g\.?)\s*\d+(?:\s*(?:de|/)\s*\d+)?$",
        r"^\d+\s*/\s*\d+$",
        r"^[-–—]\s*\d+\s*[-–—]$",
    )
)
_BARE_NUMBER = re.compile(r"^\d{1,4}$")
_LIGHT_MIN_LUMINANCE = 0.75  # cinza claro; branco puro (>= 0.98) é texto sobre fundo escuro
_LIGHT_MAX_LUMINANCE = 0.98
_LOW_ALPHA = 128
_ROTATION_TOLERANCE = 0.3
_SNIPPET_CHARS = 12


@dataclass(frozen=True)
class NoisePattern:
    """Expressão regular rotulada (o rótulo vira o motivo do descarte)."""

    label: str
    regex: re.Pattern[str]

    @classmethod
    def compile(cls, label: str, pattern: str) -> NoisePattern:
        """Compila `pattern`; lança `ValueError` com mensagem clara se for inválido."""
        try:
            return cls(label, re.compile(pattern, re.IGNORECASE))
        except re.error as exc:
            raise ValueError(f"Expressão regular inválida ({label}): {exc}") from exc


@dataclass(frozen=True)
class NoiseDecision:
    """Decisão de descarte: motivo e sinais que a sustentam."""

    reason: str
    signals: tuple[str, ...]


def repeat_key(text: str) -> str:
    """Chave de repetição: minúsculas, dígitos → `#`, espaços colapsados."""
    return _SPACES.sub(" ", _DIGITS.sub("#", text.lower())).strip()


def _luminance(color: int) -> float:
    r, g, b = (color >> 16) & 255, (color >> 8) & 255, color & 255
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


def _single_line(text: str) -> str:
    return _SPACES.sub(" ", text).strip()


class NoiseDetector:
    """Classifica blocos como ruído, usando um perfil de repetição de páginas amostradas."""

    def __init__(self, config: ExtractionConfig, patterns: Sequence[NoisePattern] = ()) -> None:
        self._config = config
        extra = [NoisePattern.compile("padrao_configurado", p) for p in config.extra_noise_patterns]
        self._patterns = (*patterns, *extra)
        self._repeated: frozenset[str] = frozenset()

    def fit(self, sample_pages: Sequence[RawPage]) -> None:
        """Calcula quais chaves de texto se repetem em páginas suficientes da amostra."""
        total = len(sample_pages)
        if total < 2:
            self._repeated = frozenset()
            return
        counts: dict[str, int] = {}
        for page in sample_pages:
            keys = {repeat_key(b.text) for b in page.blocks if b.kind == "text"}
            for key in keys:
                if len(key) >= 3:
                    counts[key] = counts.get(key, 0) + 1
        needed = max(2, math.ceil(self._config.repeat_threshold * total))
        self._repeated = frozenset(k for k, c in counts.items() if c >= needed)

    def classify(self, page: RawPage, block: RawBlock) -> NoiseDecision | None:
        """Devolve a decisão de descarte ou `None` (manter o bloco)."""
        text = block.text.strip()
        if block.kind != "text" or not text:
            return None
        flat = _single_line(text)
        signals: list[str] = []
        pattern_labels: list[str] = []

        in_zone = self._in_zone(page, block)
        if in_zone:
            signals.append("zona")
        if repeat_key(text) in self._repeated:
            signals.append("repeticao")
        if any(p.match(flat) for p in _NUMBERING) or (in_zone and _BARE_NUMBER.match(flat)):
            signals.append("numeracao")
        for pattern in self._patterns:
            if pattern.regex.search(text):
                pattern_labels.append(pattern.label)
        if pattern_labels:
            signals.append("padrao")
        signals.extend(self._watermark_signals(block))

        isolated_numbering = "numeracao" in signals and "zona" in signals
        if len(signals) < 2 and not isolated_numbering:
            return None
        return NoiseDecision(self._reason(signals, pattern_labels), tuple(signals))

    def _in_zone(self, page: RawPage, block: RawBlock) -> bool:
        top = self._config.header_zone_pct * page.height
        bottom = (1.0 - self._config.footer_zone_pct) * page.height
        _, y0, _, y1 = block.bbox
        return y1 <= top or y0 >= bottom

    @staticmethod
    def _watermark_signals(block: RawBlock) -> list[str]:
        lines = block.lines
        if not lines:
            return []
        found: list[str] = []
        if all(abs(line.direction[1]) > _ROTATION_TOLERANCE for line in lines):
            found.append("rotacionado")
        if all(
            line.alpha < _LOW_ALPHA
            or _LIGHT_MIN_LUMINANCE <= _luminance(line.color) < _LIGHT_MAX_LUMINANCE
            for line in lines
        ):
            found.append("claro")
        return found

    @staticmethod
    def _reason(signals: Sequence[str], pattern_labels: Sequence[str]) -> str:
        if "numeracao" in signals:
            return "numero_de_pagina"
        if pattern_labels:
            return pattern_labels[0]
        if "rotacionado" in signals or "claro" in signals:
            return "marca_dagua"
        return "cabecalho_rodape"


def make_record(page: int, decision: NoiseDecision, text: str) -> NoiseRecord:
    """Registro explicável do descarte: trecho curto + hash, nunca o texto integral."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
    snippet = f"{_single_line(text)[:_SNIPPET_CHARS]}… (len={len(text)}, sha256={digest})"
    return NoiseRecord(page=page, reason=decision.reason, signals=decision.signals, snippet=snippet)
