"""Testes unitários de validação, persistência e execução de estratégias customizadas."""

from __future__ import annotations

from pathlib import Path

import pytest

from matraca.audio.fake_tts import FakeTTSBackend
from matraca.audio.mp3_writer import DirectMp3Joiner
from matraca.core.audio_service import AudioService
from matraca.core.custom_strategy import CustomStrategyConfig
from matraca.core.exceptions import EstrategiaInvalidaError
from matraca.core.job_service import JobService
from matraca.core.models import RawBlock, RawLine, RawPage
from matraca.core.pdf_service import PDFService
from matraca.core.strategy_config_service import StrategyConfigService
from matraca.extractors.custom_strategy import CustomStrategy
from matraca.extractors.registry import default_registry

pytestmark = pytest.mark.unit


def test_custom_strategy_config_validation() -> None:
    # 1. Configuração válida
    cfg = CustomStrategyConfig(
        name="meu_curso",
        display_name="Meu Curso Online",
        noise_patterns=("^Cabeçalho Curso.*", r"Marca\s+D'água"),
        acronyms={"PGE": "Procuradoria Geral do Estado"},
    )
    assert cfg.name == "meu_curso"
    assert cfg.display_name == "Meu Curso Online"
    assert len(cfg.noise_patterns) == 2
    assert cfg.acronyms["PGE"] == "Procuradoria Geral do Estado"

    # 2. Identificador inválido
    with pytest.raises(EstrategiaInvalidaError, match="Identificador"):
        CustomStrategyConfig(name="Nome Com Espaço", display_name="Nome")
    with pytest.raises(EstrategiaInvalidaError, match="Identificador"):
        CustomStrategyConfig(name="x", display_name="Muito Curto")

    # 3. Nomes reservados não podem ser usados
    for reserved in ("concursos", "padrao", "default", "livro", "lei_seca"):
        with pytest.raises(EstrategiaInvalidaError, match="reservado"):
            CustomStrategyConfig(name=reserved, display_name="Tentativa")

    # 4. Nome de exibição vazio
    with pytest.raises(EstrategiaInvalidaError, match="nome de exibição"):
        CustomStrategyConfig(name="valido", display_name="   ")

    # 5. Regex de ruído inválida
    with pytest.raises(EstrategiaInvalidaError, match="Expressão regular inválida"):
        CustomStrategyConfig(name="valido", display_name="Valido", noise_patterns=("[unclosed",))

    # 6. Sigla ou pronúncia vazia
    with pytest.raises(EstrategiaInvalidaError, match="sigla"):
        CustomStrategyConfig(name="valido", display_name="Valido", acronyms={"   ": "Pronúncia"})
    with pytest.raises(EstrategiaInvalidaError, match="pronúncia"):
        CustomStrategyConfig(name="valido", display_name="Valido", acronyms={"SIGLA": "  "})


def test_strategy_config_service_crud(tmp_path: Path) -> None:
    storage_file = tmp_path / "custom_strategies.json"
    service = StrategyConfigService(storage_file)

    # 1. Inicialmente vazio
    assert service.list_strategies() == []
    assert service.get_strategy("curso_a") is None

    # 2. Criação (Salvar)
    cfg1 = CustomStrategyConfig(
        name="curso_a",
        display_name="Curso Alfa",
        noise_patterns=(r"^Alfa\s+\d+$",),
        acronyms={"TJSP": "Tribunal de Justiça de São Paulo"},
    )
    service.save_strategy(cfg1)

    loaded = service.get_strategy("curso_a")
    assert loaded is not None
    assert loaded.name == "curso_a"
    assert loaded.display_name == "Curso Alfa"
    assert loaded.noise_patterns == (r"^Alfa\s+\d+$",)
    assert loaded.acronyms == {"TJSP": "Tribunal de Justiça de São Paulo"}
    assert len(service.list_strategies()) == 1

    # 3. Atualização
    cfg1_mod = CustomStrategyConfig(
        name="curso_a",
        display_name="Curso Alfa Atualizado",
        noise_patterns=(),
        acronyms={"TJSP": "T J São Paulo"},
    )
    service.save_strategy(cfg1_mod)
    reloaded = service.get_strategy("curso_a")
    assert reloaded is not None
    assert reloaded.display_name == "Curso Alfa Atualizado"
    assert reloaded.acronyms == {"TJSP": "T J São Paulo"}

    # 4. Segunda estratégia e ordenação por display_name
    cfg2 = CustomStrategyConfig(
        name="curso_b",
        display_name="Apostila Beta",
    )
    service.save_strategy(cfg2)
    all_strats = service.list_strategies()
    assert len(all_strats) == 2
    assert all_strats[0].name == "curso_b"  # "Apostila Beta" vem antes de "Curso Alfa..."

    # 5. Exclusão
    assert service.delete_strategy("curso_a") is True
    assert service.delete_strategy("curso_a") is False  # Já não existe
    assert len(service.list_strategies()) == 1
    assert service.get_strategy("curso_a") is None


def test_registry_integration_with_custom_strategies(tmp_path: Path) -> None:
    storage_file = tmp_path / "strategies.json"
    service = StrategyConfigService(storage_file)

    cfg = CustomStrategyConfig(
        name="curso_custom",
        display_name="Meu Curso Personalizado",
        noise_patterns=(r"^Material Exclusivo.*",),
        acronyms={"PGE": "Procuradoria Geral do Estado"},
    )
    service.save_strategy(cfg)

    # Inicializa registro padrão apontando para o service
    registry = default_registry(service)

    # Deve estar disponível e selecionável
    selectable = registry.selectable()
    names = [s.name for s in selectable]
    assert "concursos" in names
    assert "padrao" in names
    assert "curso_custom" in names

    strat = registry.get("curso_custom")
    assert isinstance(strat, CustomStrategy)
    assert strat.display_name == "Meu Curso Personalizado"
    assert len(strat.noise_patterns) == 1
    assert strat.acronyms == {"PGE": "Procuradoria Geral do Estado"}


def test_job_service_custom_strategy_and_acronyms(tmp_path: Path) -> None:
    storage_file = tmp_path / "strategies.json"
    strat_service = StrategyConfigService(storage_file)

    cfg = CustomStrategyConfig(
        name="estrategia_teste",
        display_name="Estratégia Teste",
        noise_patterns=(),
        acronyms={"SEFAZ": "Secretaria da Fazenda"},
    )
    strat_service.save_strategy(cfg)

    registry = default_registry(strat_service)

    # PDF falso em memória
    class FakePDFReader:
        path = Path("fake.pdf")
        page_count = 1
        is_encrypted = False

        def __enter__(self) -> FakePDFReader:
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def metadata(self) -> dict[str, str]:
            return {}

        def read_page(self, number: int, *, with_tables: bool = False) -> RawPage:
            line = RawLine(
                text="O concurso da SEFAZ foi publicado.", bbox=(50.0, 50.0, 400.0, 70.0)
            )
            block = RawBlock(kind="text", bbox=(50.0, 50.0, 400.0, 70.0), lines=(line,))
            return RawPage(number=1, width=595.0, height=842.0, blocks=(block,))

        def render_page_thumbnail(self, number: int, *, max_dimension: int = 300) -> bytes:
            return b"\x89PNG\r\n\x1a\n"

    pdf_service = PDFService(reader_factory=lambda p: FakePDFReader())
    audio_service = AudioService(backend=FakeTTSBackend(), joiner=DirectMp3Joiner())

    job_service = JobService(
        pdf_service=pdf_service,
        audio_service=audio_service,
        registry=registry,
        strategy_service=strat_service,
    )

    # Gera prévia com a estratégia customizada
    preview = job_service.get_preview(
        pdf_path=Path("fake.pdf"),
        pages_expr="1",
        strategy_name="estrategia_teste",
    )

    # SEFAZ deve ter sido normalizado para "Secretaria da Fazenda"
    assert "Secretaria da Fazenda" in preview.text
    assert "SEFAZ" not in preview.text
