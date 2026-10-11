#!/usr/bin/env bash
# Portão de qualidade A.8 do Matraca. Uso: scripts/check.sh [--cov]
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"; else PY="${PYTHON:-python3}"; fi

step() { printf '\n==> %s\n' "$1"; }

step "ruff check"
"$PY" -m ruff check .
step "ruff format --check"
"$PY" -m ruff format --check .
step "compileall"
"$PY" -m compileall -q matraca
step "mypy"
"$PY" -m mypy
step "import matraca (sem efeitos colaterais)"
"$PY" -c "import matraca; print('matraca', matraca.__version__)"
step "pytest"
if [ "${1:-}" = "--cov" ]; then
  "$PY" -m pytest --cov=matraca --cov-report=term-missing
else
  "$PY" -m pytest
fi
printf '\nOK: todas as verificações passaram.\n'
