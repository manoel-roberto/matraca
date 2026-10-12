"""Modelo de dados para estratégias customizadas definidas pelo usuário."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from matraca.core.exceptions import EstrategiaInvalidaError

RESERVED_STRATEGY_NAMES: frozenset[str] = frozenset(
    {"concursos", "padrao", "default", "lei_seca", "livro", "base"}
)
_NAME_RE = re.compile(r"^[a-z0-9_]{2,40}$")


@dataclass(frozen=True)
class CustomStrategyConfig:
    """Configuração imutável de uma estratégia de extração/normalização customizada."""

    name: str
    display_name: str
    noise_patterns: tuple[str, ...] = ()
    acronyms: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Valida identificador, nome legível, regexes de ruído e dicionário de siglas."""
        clean_name = self.name.strip().lower()
        if not _NAME_RE.match(clean_name):
            raise EstrategiaInvalidaError(
                f"Identificador de estratégia inválido: '{self.name}'. "
                "Use de 2 a 40 caracteres com letras minúsculas, números e sublinhados."
            )
        if clean_name in RESERVED_STRATEGY_NAMES:
            raise EstrategiaInvalidaError(
                f"O identificador '{clean_name}' é reservado pelo sistema e "
                "não pode ser sobrescrito."
            )

        clean_display = self.display_name.strip()
        if not (1 <= len(clean_display) <= 80):
            raise EstrategiaInvalidaError(
                "O nome de exibição da estratégia deve ter entre 1 e 80 caracteres."
            )

        for idx, pat in enumerate(self.noise_patterns, start=1):
            if not isinstance(pat, str) or not pat.strip():
                raise EstrategiaInvalidaError(
                    f"Padrão de ruído #{idx} inválido: não pode ser vazio."
                )
            try:
                re.compile(pat.strip())
            except re.error as exc:
                raise EstrategiaInvalidaError(
                    f"Expressão regular inválida no padrão de ruído #{idx} ('{pat}'): {exc}"
                ) from exc

        for sigla, pronuncia in self.acronyms.items():
            if not isinstance(sigla, str) or not sigla.strip():
                raise EstrategiaInvalidaError(
                    "A sigla no dicionário de normalização não pode ser vazia."
                )
            if not isinstance(pronuncia, str) or not pronuncia.strip():
                raise EstrategiaInvalidaError(
                    f"A pronúncia para a sigla '{sigla}' não pode ser vazia."
                )

    def to_dict(self) -> dict[str, Any]:
        """Converte a configuração em dicionário primitivo pronto para serialização JSON."""
        return {
            "name": self.name.strip().lower(),
            "display_name": self.display_name.strip(),
            "noise_patterns": [p.strip() for p in self.noise_patterns if p.strip()],
            "acronyms": {k.strip(): v.strip() for k, v in self.acronyms.items() if k.strip()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CustomStrategyConfig:
        """Reconstrói uma instância validada a partir de dicionário."""
        name = str(data.get("name", "")).strip().lower()
        display_name = str(data.get("display_name", "")).strip()
        raw_patterns = data.get("noise_patterns", [])
        patterns = tuple(str(p).strip() for p in raw_patterns if str(p).strip())
        raw_acronyms = data.get("acronyms", {})
        acronyms = {
            str(k).strip(): str(v).strip() for k, v in raw_acronyms.items() if str(k).strip()
        }
        return cls(
            name=name,
            display_name=display_name,
            noise_patterns=patterns,
            acronyms=acronyms,
        )
