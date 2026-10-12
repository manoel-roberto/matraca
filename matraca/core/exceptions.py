"""Hierarquia de exceções do Matraca (A.12.4).

Cada erro carrega uma mensagem amigável em pt-BR (exibida nas interfaces) e um
detalhe técnico opcional (apenas para log). Nunca inclua texto de PDF no detalhe.
"""

from __future__ import annotations


class MatracaError(Exception):
    """Base de todos os erros previstos do Matraca."""

    default_message = "Ocorreu um erro inesperado no Matraca."

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        self.user_message: str = message or self.default_message
        self.detail: str | None = detail
        super().__init__(self.user_message)

    def log_text(self) -> str:
        """Texto para o log: mensagem amigável seguida do detalhe técnico, se houver."""
        if self.detail:
            return f"{self.user_message} | detalhe: {self.detail}"
        return self.user_message


class PDFInvalidoError(MatracaError):
    """PDF inexistente, ilegível, corrompido ou vazio."""

    default_message = "Não foi possível abrir o PDF. O arquivo pode estar corrompido ou vazio."


class PDFProtegidoError(MatracaError):
    """PDF protegido por senha (não suportado nesta versão)."""

    default_message = "O PDF está protegido por senha. Remova a proteção e tente novamente."


class PDFSemTextoError(MatracaError):
    """Nenhuma das páginas selecionadas possui camada de texto."""

    default_message = (
        "As páginas selecionadas não têm texto (PDF digitalizado?). "
        "Use um PDF pesquisável; o OCR não é suportado nesta versão."
    )


class SelecaoPaginasError(MatracaError):
    """Expressão de páginas inválida."""

    default_message = "A seleção de páginas é inválida."


class NormalizacaoError(MatracaError):
    """Falha ao normalizar o texto para narração."""

    default_message = "Não foi possível preparar o texto para narração."


class VozIndisponivelError(MatracaError):
    """Voz inexistente ou lista de vozes indisponível."""

    default_message = "A voz escolhida não está disponível. Atualize a lista de vozes."


class TTSErroDeRedeError(MatracaError):
    """Falha transitória de rede ao falar com o serviço de síntese."""

    default_message = "Falha de conexão com o serviço de voz. Verifique sua internet."


class TTSErroDeServicoError(MatracaError):
    """O serviço de síntese respondeu com erro (não transitório)."""

    default_message = "O serviço de voz retornou um erro. Tente novamente mais tarde."


class SaidaInvalidaError(MatracaError):
    """Caminho de saída inválido ou arquivo gerado inválido."""

    default_message = "O arquivo de saída é inválido."


class ArquivoJaExisteError(SaidaInvalidaError):
    """O arquivo de saída já existe e a política exige decisão do usuário."""

    default_message = "Já existe um arquivo com esse nome."

    def __init__(self, path: object, message: str | None = None) -> None:
        super().__init__(message, detail=f"caminho={path}")
        self.path = path


class CancelamentoError(MatracaError):
    """A operação foi cancelada pelo usuário."""

    default_message = "Operação cancelada."


class EstrategiaInvalidaError(MatracaError):
    """Configuração de estratégia customizada inválida ou nome reservado."""

    default_message = "A configuração da estratégia customizada é inválida."
