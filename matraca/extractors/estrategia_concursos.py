"""Estratégia Concursos (RF-04): ajustes para materiais de estudo para concursos.

Os padrões vêm de `concursos_patterns.toml` (inferidos, configuráveis; ver ADR-009).
Dados pessoais em marcas de licenciamento não devem ser narrados: são removidos quando
identificados com confiança (≥ 2 sinais) e a remoção é informada nos avisos.
"""

from __future__ import annotations

import re
import tomllib
from importlib import resources
from pathlib import Path

from matraca.extractors.base import BaseExtractor
from matraca.extractors.noise import NoisePattern

_PATTERNS_FILE = "concursos_patterns.toml"

_DEFAULT_FALLBACK_TOML = """# Padrões default da estratégia Concursos
[licenca]
label = "marca_licenca"
patterns = [
  '\\b(?:licenciad[oa]|exclusiv[oa])\\s+(?:para|de)\\b',
  '\\bCPF\\b\\D{0,5}\\d{3}\\.?\\d{3}\\.?\\d{3}-?\\d{2}\\b',
  '\\b\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}\\b',
]

[curso]
label = "cabecalho_curso"
patterns = [
  '(?:https?://)?(?:www\\.)?estrategia(?:concursos)?\\.[a-z.]+\\S*',
]

[bancas]
names = [
  "CESPE", "CEBRASPE", "FCC", "FGV", "VUNESP", "CESGRANRIO",
  "IBFC", "IDECAN", "QUADRIX", "FUNDATEC", "AOCP", "IADES",
  "CONSULPLAN", "FUNCAB"
]
"""


def load_pattern_config(path: Path | None = None) -> dict[str, object]:
    """Carrega o TOML de padrões (do pacote, ou de `path` se informado)."""
    if path is not None:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    try:
        text = resources.files("matraca.extractors").joinpath(_PATTERNS_FILE).read_text("utf-8")
        return tomllib.loads(text)
    except Exception:
        fallback_file = Path(__file__).parent / _PATTERNS_FILE
        if fallback_file.exists():
            return tomllib.loads(fallback_file.read_text(encoding="utf-8"))
        return tomllib.loads(_DEFAULT_FALLBACK_TOML)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ValueError("Esperada uma lista de textos no arquivo de padrões.")
    return list(value)


def build_noise_patterns(config: dict[str, object]) -> tuple[NoisePattern, ...]:
    """Converte as seções com `label` e `patterns` do TOML em `NoisePattern`."""
    out: list[NoisePattern] = []
    for section in config.values():
        if isinstance(section, dict) and "patterns" in section:
            label = str(section.get("label", "padrao_configurado"))
            out.extend(NoisePattern.compile(label, p) for p in _string_list(section["patterns"]))
    return tuple(out)


def build_banca_regex(config: dict[str, object]) -> re.Pattern[str]:
    """Regex do formato inequívoco `(BANCA/ANO)` no início do bloco."""
    bancas = config.get("bancas")
    names = _string_list(bancas.get("names", [])) if isinstance(bancas, dict) else []
    if not names:
        return re.compile(r"(?!x)x")  # nunca casa
    alternatives = "|".join(re.escape(n) for n in names)
    return re.compile(rf"^\(\s*({alternatives})\s*/\s*((?:19|20)\d{{2}})\s*\)\s*", re.IGNORECASE)


class ConcursosStrategy(BaseExtractor):
    """Extração para materiais de concursos (padrões configuráveis)."""

    name = "concursos"
    display_name = "Concursos"
    implemented = True

    def __init__(self, pattern_file: Path | None = None) -> None:
        config = load_pattern_config(pattern_file)
        self.noise_patterns = build_noise_patterns(config)
        self._banca = build_banca_regex(config)

    def transform_block(self, text: str) -> str:
        """`(CESPE/2019) Texto` → `Questão da banca CESPE, de 2019. Texto` (só se inequívoco)."""
        match = self._banca.match(text)
        if not match:
            return text
        banca, year = match.group(1).upper(), match.group(2)
        rest = text[match.end() :]
        return f"Questão da banca {banca}, de {year}. {rest}".rstrip()
