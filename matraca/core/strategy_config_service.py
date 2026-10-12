"""Serviço de gerenciamento e persistência de estratégias customizadas do usuário (CRUD).

Isolado no core: utiliza apenas stdlib (JSON e pathlib), garantindo Clean Architecture (RNF-01).
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

from matraca.core.custom_strategy import CustomStrategyConfig

_log = logging.getLogger(__name__)


def _default_storage_path() -> Path:
    override = os.environ.get("MATRACA_STATE_DIR")
    if override:
        return Path(override) / "custom_strategies.json"
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        return base / "matraca" / "custom_strategies.json"
    state = os.environ.get("XDG_STATE_HOME")
    base = Path(state) if state else Path.home() / ".local" / "state"
    return base / "matraca" / "custom_strategies.json"


class StrategyConfigService:
    """Gerencia a persistência segura (CRUD) de configurações de estratégias customizadas."""

    def __init__(self, storage_path: Path | None = None) -> None:
        self.storage_path = Path(storage_path or _default_storage_path())

    def list_strategies(self) -> list[CustomStrategyConfig]:
        """Devolve todas as estratégias customizadas cadastradas, ordenadas por nome de exibição."""
        data = self._read_raw()
        configs: list[CustomStrategyConfig] = []
        for item in data.values():
            if isinstance(item, dict):
                try:
                    configs.append(CustomStrategyConfig.from_dict(item))
                except Exception as exc:
                    _log.warning("Estratégia customizada corrompida ignorada: %s (%s)", item, exc)
        return sorted(configs, key=lambda c: c.display_name.lower())

    def get_strategy(self, name: str) -> CustomStrategyConfig | None:
        """Busca uma estratégia pelo seu identificador único."""
        clean_name = name.strip().lower()
        data = self._read_raw()
        raw = data.get(clean_name)
        if isinstance(raw, dict):
            try:
                return CustomStrategyConfig.from_dict(raw)
            except Exception as exc:
                _log.warning("Falha ao desserializar estratégia '%s': %s", clean_name, exc)
        return None

    def save_strategy(self, config: CustomStrategyConfig) -> None:
        """Salva ou atualiza uma estratégia customizada no arquivo de persistência atômica."""
        config.validate()
        data = self._read_raw()
        data[config.name] = config.to_dict()
        self._write_raw(data)
        _log.info("Estratégia customizada '%s' salva com sucesso.", config.name)

    def delete_strategy(self, name: str) -> bool:
        """Remove a estratégia identificada por `name`. Retorna True se existia e foi removida."""
        clean_name = name.strip().lower()
        data = self._read_raw()
        if clean_name in data:
            del data[clean_name]
            self._write_raw(data)
            _log.info("Estratégia customizada '%s' removida.", clean_name)
            return True
        return False

    def _read_raw(self) -> dict[str, dict[str, object]]:
        """Lê o arquivo JSON com tolerância a ausência e corrupção."""
        if not self.storage_path.exists():
            return {}
        try:
            content = self.storage_path.read_text(encoding="utf-8")
            if not content.strip():
                return {}
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return {str(k).strip().lower(): v for k, v in parsed.items() if isinstance(v, dict)}
            _log.warning(
                "Formato inválido no arquivo de estratégias (%s); reinicializando.", type(parsed)
            )
            return {}
        except Exception as exc:
            _log.warning(
                "Falha ao ler estratégias customizadas de '%s': %s", self.storage_path, exc
            )
            return {}

    def _write_raw(self, data: dict[str, dict[str, object]]) -> None:
        """Grava os dados em disco de forma segura e atômica."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(data, indent=2, ensure_ascii=False)

        # Grava em arquivo temporário no mesmo diretório para garantir atomicidade via os.replace
        temp_file: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.storage_path.parent,
                prefix="strategies_tmp_",
                delete=False,
            ) as tf:
                tf.write(serialized)
                temp_file = Path(tf.name)

            temp_file.replace(self.storage_path)
        except Exception:
            if temp_file and temp_file.exists():
                with contextlib.suppress(OSError):
                    temp_file.unlink()
            raise
