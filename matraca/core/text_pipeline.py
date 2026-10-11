"""Serviço que orquestra a normalização de texto a partir da extração (RF-09, RF-10)."""

from __future__ import annotations

from matraca.core.models import ExtractionResult, NarrationText
from matraca.text.normalization import NormalizationConfig, normalize_text


class TextPipelineService:
    """Orquestra a transformação de ExtractionResult em NarrationText alinhado."""

    def __init__(self, config: NormalizationConfig | None = None) -> None:
        self.config = config or NormalizationConfig()

    def process(self, extraction: ExtractionResult) -> NarrationText:
        """Processa blocos extraídos e gera NarrationText com alinhamento 1:1 de parágrafos."""
        original_pars: list[str] = []
        normalized_pars: list[str] = []
        all_warnings: list[str] = list(extraction.warnings)
        total_original_chars = 0
        total_normalized_chars = 0
        total_words = 0

        for page in extraction.pages:
            for block in page.blocks:
                orig = block.text.strip()
                if not orig:
                    continue

                norm, stats, warns = normalize_text(orig, self.config)
                # Garante que o parágrafo normalizado não é vazio se o original tiver conteúdo
                norm_clean = norm if norm.strip() else orig

                original_pars.append(orig)
                normalized_pars.append(norm_clean)

                total_original_chars += stats.get("original_chars", len(orig))
                total_normalized_chars += stats.get("normalized_chars", len(norm_clean))
                total_words += stats.get("words", len(norm_clean.split()))

                if warns:
                    all_warnings.extend(warns)

        stats_dict = {
            "paragraphs": len(normalized_pars),
            "original_chars": total_original_chars,
            "normalized_chars": total_normalized_chars,
            "words": total_words,
        }

        return NarrationText(
            paragraphs=tuple(normalized_pars),
            original_paragraphs=tuple(original_pars),
            stats=stats_dict,
            warnings=tuple(all_warnings),
        )
