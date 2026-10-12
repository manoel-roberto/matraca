"""Gerenciador seguro de credenciais para serviços externos (Google Cloud).

Garante que nenhuma chave privada seja registrada em logs ou exposta em interfaces,
permitindo a importação e persistência local de arquivos de conta de serviço.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from matraca.utils.paths import default_state_dir

_log = logging.getLogger(__name__)


def get_default_google_credentials_path() -> Path:
    """Retorna o caminho padrão de persistência das credenciais no diretório de estado."""
    return default_state_dir() / "credenciais.json"


def find_google_credentials(custom_path: Path | str | None = None) -> Path | None:
    """Localiza o arquivo de credenciais da conta de serviço Google Cloud.

    Ordem de busca:
    1. Caminho explícito fornecido (custom_path)
    2. Variável de ambiente GOOGLE_APPLICATION_CREDENTIALS
    3. Arquivo 'credenciais.json' no diretório de trabalho atual (Path.cwd())
    4. Arquivo 'credenciais.json' no diretório de estado do usuário
    """
    if custom_path:
        p = Path(custom_path).expanduser().resolve()
        if p.is_file():
            return p

    env_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if env_path:
        p = Path(env_path).expanduser().resolve()
        if p.is_file():
            return p

    local_path = Path.cwd() / "credenciais.json"
    if local_path.is_file():
        return local_path.resolve()

    state_path = get_default_google_credentials_path()
    if state_path.is_file():
        return state_path.resolve()

    return None


def validate_service_account_dict(data: dict[str, Any]) -> dict[str, str]:
    """Valida a estrutura de uma chave de conta de serviço Google Cloud.

    Retorna um dicionário seguro com informações públicas (project_id, client_email).
    Nunca retorna ou expõe a chave privada (private_key).
    """
    if not isinstance(data, dict):
        raise ValueError("O conteúdo das credenciais deve ser um objeto JSON.")

    if data.get("type") != "service_account":
        raise ValueError(
            "Tipo de credencial inválido. É esperado um arquivo do tipo 'service_account'."
        )

    project_id = str(data.get("project_id", "")).strip()
    if not project_id:
        raise ValueError("Arquivo de credenciais inválido: campo 'project_id' ausente.")

    client_email = str(data.get("client_email", "")).strip()
    if not client_email:
        raise ValueError("Arquivo de credenciais inválido: campo 'client_email' ausente.")

    private_key = str(data.get("private_key", "")).strip()
    if not private_key or "BEGIN PRIVATE KEY" not in private_key:
        raise ValueError("Arquivo de credenciais inválido: chave privada ausente ou malformada.")

    return {
        "project_id": project_id,
        "client_email": client_email,
        "client_id": str(data.get("client_id", "")).strip(),
    }


def validate_service_account_file(file_path: Path | str) -> dict[str, str]:
    """Lê e valida um arquivo de credenciais JSON do disco."""
    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo de credenciais não encontrado: {path}")

    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
    except Exception as exc:
        raise ValueError(f"Falha ao ler o arquivo JSON de credenciais: {exc}") from exc

    return validate_service_account_dict(data)


def save_google_credentials(
    source_content: str | bytes | dict[str, Any],
    dest_path: Path | None = None,
) -> tuple[Path, dict[str, str]]:
    """Salva credenciais validadas no diretório de destino com permissões restritas.

    Retorna uma tupla (caminho_salvo, metadados_publicos).
    """
    if isinstance(source_content, bytes):
        raw_str = source_content.decode("utf-8")
        data = json.loads(raw_str)
    elif isinstance(source_content, str):
        data = json.loads(source_content)
    elif isinstance(source_content, dict):
        data = source_content
    else:
        raise ValueError("Conteúdo de credenciais inválido.")

    summary = validate_service_account_dict(data)

    target = dest_path or get_default_google_credentials_path()
    target.parent.mkdir(parents=True, exist_ok=True)

    json_str = json.dumps(data, indent=2)
    target.write_text(json_str, encoding="utf-8")

    # Em sistemas Unix, restringe a permissão do arquivo para leitura/escrita pelo proprietário
    if sys.platform != "win32":
        with contextlib.suppress(OSError):
            os.chmod(target, 0o600)

    _log.info(
        "Credenciais da conta de serviço salvas com sucesso em %s (Projeto: %s)",
        target,
        summary["project_id"],
    )
    return target, summary


def remove_google_credentials(path: Path | None = None) -> bool:
    """Remove o arquivo de credenciais do disco se ele existir."""
    target = path or get_default_google_credentials_path()
    if target.exists():
        try:
            target.unlink()
            _log.info("Credenciais removidas de %s", target)
            return True
        except OSError as exc:
            _log.warning("Falha ao remover arquivo de credenciais %s: %s", target, exc)
            return False
    return False
