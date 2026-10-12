"""Registro das estratégias disponíveis (RF-04).

Adicionar uma estratégia não exige alterar UI nem motor de áudio: basta registrá-la.
O registro é uma instância (sem estado global); `default_registry()` monta o padrão.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from matraca.config import ExtractionConfig
from matraca.core.custom_strategy import CustomStrategyConfig
from matraca.core.exceptions import MatracaError
from matraca.core.models import ExtractionResult
from matraca.core.ports import PDFReader, PDFTextStrategy
from matraca.core.progress import CancellationToken, ProgressCallback
from matraca.core.strategy_config_service import StrategyConfigService
from matraca.extractors.custom_strategy import CustomStrategy
from matraca.extractors.default import DefaultStrategy
from matraca.extractors.estrategia_concursos import ConcursosStrategy

_log = logging.getLogger(__name__)

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

    def register_or_replace(self, strategy: PDFTextStrategy) -> None:
        """Registra uma nova estratégia ou substitui a existente pelo mesmo identificador."""
        self._items[strategy.name] = strategy

    def unregister(self, name: str) -> bool:
        """Remove uma estratégia pelo identificador. Retorna True se existia."""
        if name in self._items:
            del self._items[name]
            return True
        return False

    def load_custom_strategies(self, configs: Sequence[CustomStrategyConfig]) -> None:
        """Carrega e registra uma lista de configurações de estratégias customizadas."""
        for cfg in configs:
            self.register_or_replace(CustomStrategy(cfg))

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


def default_registry(strategy_service: StrategyConfigService | None = None) -> StrategyRegistry:
    """Registro padrão: Concursos, Padrão, customizadas do usuário e 'em breve'."""
    registry = StrategyRegistry()
    registry.register(ConcursosStrategy())
    registry.register(DefaultStrategy())

    # Carrega estratégias customizadas salvas pelo usuário
    service = strategy_service or StrategyConfigService()
    try:
        registry.load_custom_strategies(service.list_strategies())
    except Exception as exc:
        _log.warning("Falha ao carregar estratégias customizadas do disco: %s", exc)

    registry.register(ComingSoonStrategy("lei_seca", "Legislação seca (em breve)"))
    registry.register(ComingSoonStrategy("livro", "Livro (em breve)"))
    return registry
