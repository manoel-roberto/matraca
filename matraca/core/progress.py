"""Progresso e cancelamento, independentes de qualquer toolkit (A.12.7)."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from matraca.core.exceptions import CancelamentoError


class Stage(StrEnum):
    """Etapas de um trabalho PDF → MP3."""

    VALIDATING = "validating"
    EXTRACTING = "extracting"
    NORMALIZING = "normalizing"
    SYNTHESIZING = "synthesizing"
    FINALIZING = "finalizing"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ProgressEvent:
    """Evento de progresso publicado pelos serviços do núcleo."""

    stage: Stage
    current: int = 0
    total: int = 0
    message: str = ""

    @property
    def fraction(self) -> float:
        """Fração concluída da etapa atual, entre 0.0 e 1.0."""
        if self.total <= 0:
            return 0.0
        return min(1.0, max(0.0, self.current / self.total))


ProgressCallback = Callable[[ProgressEvent], None]


class CancellationToken:
    """Token de cancelamento cooperativo, seguro entre threads."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        """Solicita o cancelamento (idempotente)."""
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        """Indica se o cancelamento foi solicitado."""
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        """Lança `CancelamentoError` se o cancelamento foi solicitado."""
        if self._event.is_set():
            raise CancelamentoError()

    def wait(self, timeout: float) -> bool:
        """Espera até `timeout` segundos; devolve True se foi cancelado nesse intervalo."""
        return self._event.wait(timeout)
