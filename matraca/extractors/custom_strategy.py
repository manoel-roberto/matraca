"""Estratégia dinâmica baseada em configuração customizada criada pelo usuário."""

from __future__ import annotations

from matraca.core.custom_strategy import CustomStrategyConfig
from matraca.extractors.base import BaseExtractor
from matraca.extractors.noise import NoisePattern


class CustomStrategy(BaseExtractor):
    """Estratégia de extração customizada em tempo de execução."""

    implemented: bool = True

    def __init__(self, config: CustomStrategyConfig) -> None:
        self.config_data = config
        self.name: str = config.name
        self.display_name: str = config.display_name
        self.acronyms: dict[str, str] = dict(config.acronyms)

        compiled: list[NoisePattern] = []
        for idx, pat in enumerate(config.noise_patterns, start=1):
            clean_pat = pat.strip()
            if clean_pat:
                compiled.append(NoisePattern.compile(f"custom_{self.name}_{idx}", clean_pat))
        self.noise_patterns: tuple[NoisePattern, ...] = tuple(compiled)
