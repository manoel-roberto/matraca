"""Testes unitários para o gerenciador de credenciais do Google Cloud."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from matraca.utils.credentials import (
    find_google_credentials,
    get_default_google_credentials_path,
    remove_google_credentials,
    save_google_credentials,
    validate_service_account_dict,
    validate_service_account_file,
)

_VALID_PAYLOAD = {
    "type": "service_account",
    "project_id": "test-project-123",
    "private_key_id": "abcd1234",
    "private_key": (
        "-----BEGIN PRIVATE KEY-----\n"
        "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCx\n"
        "-----END PRIVATE KEY-----\n"
    ),
    "client_email": "test-sa@test-project-123.iam.gserviceaccount.com",
    "client_id": "999888777",
}


@pytest.mark.unit
def test_validate_service_account_dict_valid() -> None:
    summary = validate_service_account_dict(_VALID_PAYLOAD)
    assert summary["project_id"] == "test-project-123"
    assert summary["client_email"] == "test-sa@test-project-123.iam.gserviceaccount.com"
    assert summary["client_id"] == "999888777"
    assert "private_key" not in summary
    assert get_default_google_credentials_path().name == "credenciais.json"


@pytest.mark.unit
def test_validate_service_account_dict_invalid_type() -> None:
    bad = dict(_VALID_PAYLOAD)
    bad["type"] = "authorized_user"
    with pytest.raises(ValueError, match="service_account"):
        validate_service_account_dict(bad)


@pytest.mark.unit
def test_validate_service_account_dict_missing_fields() -> None:
    bad = dict(_VALID_PAYLOAD)
    del bad["project_id"]
    with pytest.raises(ValueError, match="project_id"):
        validate_service_account_dict(bad)

    bad2 = dict(_VALID_PAYLOAD)
    bad2["private_key"] = "chave-invalida"
    with pytest.raises(ValueError, match="chave privada"):
        validate_service_account_dict(bad2)


@pytest.mark.unit
def test_save_and_validate_file(tmp_path: Path) -> None:
    dest = tmp_path / "credenciais.json"
    raw_bytes = json.dumps(_VALID_PAYLOAD).encode("utf-8")

    saved_path, summary = save_google_credentials(raw_bytes, dest_path=dest)
    assert saved_path == dest
    assert saved_path.exists()
    assert summary["project_id"] == "test-project-123"

    file_summary = validate_service_account_file(dest)
    assert file_summary["project_id"] == "test-project-123"


@pytest.mark.unit
def test_find_google_credentials_custom(tmp_path: Path) -> None:
    custom = tmp_path / "custom.json"
    custom.write_text(json.dumps(_VALID_PAYLOAD), encoding="utf-8")

    found = find_google_credentials(custom)
    assert found == custom.resolve()


@pytest.mark.unit
def test_remove_google_credentials(tmp_path: Path) -> None:
    dest = tmp_path / "to_delete.json"
    dest.write_text("{}", encoding="utf-8")
    assert dest.exists()
    assert remove_google_credentials(dest) is True
    assert not dest.exists()
