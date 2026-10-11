"""Estratégia Padrão: extração genérica, sem padrões específicos de um material."""

from __future__ import annotations

from matraca.extractors.base import BaseExtractor


class DefaultStrategy(BaseExtractor):
    """Extração genérica com remoção conservadora de ruído e ordem de leitura por colunas."""

    name = "padrao"
    display_name = "Padrão"
    implemented = True
