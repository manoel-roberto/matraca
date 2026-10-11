"""Configuração imutável e padrões do Matraca. Sem estado global mutável."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TableMode = Literal["ignore", "linear", "marker"]
FigureMode = Literal["ignore", "marker"]

MAX_UPLOAD_MB_DEFAULT = 50
"""Limite de upload da interface Web; mantenha em sincronia com `.streamlit/config.toml`."""


@dataclass(frozen=True)
class ExtractionConfig:
    """Parâmetros da extração de texto (A.13.2)."""

    remove_headers_footers: bool = True
    header_zone_pct: float = 0.10
    footer_zone_pct: float = 0.10
    repeat_threshold: float = 0.40
    sample_pages: int = 40
    detect_columns: bool = True
    remove_license_marks: bool = True
    tables: TableMode = "marker"
    figures: FigureMode = "ignore"
    extra_noise_patterns: tuple[str, ...] = ()
    """Expressões regulares adicionais (por linha) para ruído específico do material."""

    def __post_init__(self) -> None:
        for name in ("header_zone_pct", "footer_zone_pct"):
            value = getattr(self, name)
            if not 0.0 <= value <= 0.5:
                raise ValueError(f"{name} deve estar entre 0 e 0.5")
        if not 0.0 < self.repeat_threshold <= 1.0:
            raise ValueError("repeat_threshold deve estar em (0, 1]")
        if self.sample_pages < 1:
            raise ValueError("sample_pages deve ser >= 1")
