"""Registro das estratégias disponíveis (RF-04).

Adicionar uma estratégia não exige alterar UI nem motor de áudio: basta registrá-la.
O registro é uma instância (sem estado global); `default_registry()` monta o padrão.
"""

from __future__ import annotations

from collections.abc import Sequence

from matraca.config import ExtractionConfig
from matraca.core.exceptions import MatracaError
from matraca.core.models import ExtractionResult
from matraca.core.ports import PDFReader, PDFTextStrategy
from matraca.core.progress import CancellationToken, ProgressCallback
from matraca.extractors.default import DefaultStrategy
from matraca.extractors.estrategia_concursos import ConcursosStrategy

DEFAULT_STRATEGY_NAME = "concursos"


class ComingSoonStrategy:
    """Estratégia anunciada e ainda não implementada ("em breve"): não é selecionável."""

    implemented = False

    def __init__(self, name: str, display_name: str) -> None:
        self.name = name
        self.display_name = display_name

    def extract(
        self,
        reader: PDFReader,
        pages: Sequence[int],
        config: ExtractionConfig,
        progress: ProgressCallback | None = None,
        cancel: CancellationToken | None = None,
    ) -> ExtractionResult:
        raise MatracaError(f"A estratégia “{self.display_name}” ainda não está disponível.")


class StrategyRegistry:
    """Coleção ordenada de estratégias por nome estável."""

    def __init__(self) -> None:
        self._items: dict[str, PDFTextStrategy] = {}

    def register(self, strategy: PDFTextStrategy) -> None:
        """Registra a estratégia; nomes duplicados são erro de programação."""
        if strategy.name in self._items:
            raise ValueError(f"Estratégia já registrada: {strategy.name}")
        self._items[strategy.name] = strategy

    def all(self) -> list[PDFTextStrategy]:
        """Todas, incluindo as marcadas como "em breve" (para exibição)."""
        return list(self._items.values())

    def selectable(self) -> list[PDFTextStrategy]:
        """Apenas as implementadas."""
        return [s for s in self._items.values() if s.implemented]

    def get(self, name: str) -> PDFTextStrategy:
        """Devolve a estratégia selecionável `name`; erro amigável se inexistente/em breve."""
        strategy = self._items.get(name)
        if strategy is None:
            raise MatracaError(f"Estratégia desconhecida: {name}.")
        if not strategy.implemented:
            raise MatracaError(f"A estratégia “{strategy.display_name}” ainda não está disponível.")
        return strategy


def default_registry() -> StrategyRegistry:
    """Registro padrão: Concursos, Padrão e "em breve" (Legislação seca, Livro)."""
    registry = StrategyRegistry()
    registry.register(ConcursosStrategy())
    registry.register(DefaultStrategy())
    registry.register(ComingSoonStrategy("lei_seca", "Legislação seca (em breve)"))
    registry.register(ComingSoonStrategy("livro", "Livro (em breve)"))
    return registry
