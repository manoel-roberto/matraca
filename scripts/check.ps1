# Portão de qualidade A.8 do Matraca (Windows). Uso: scripts\check.ps1 [-Cov]
# Nota: este script não pôde ser executado no ambiente de desenvolvimento (Linux).
param([switch]$Cov)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$venvPy = ".venv\Scripts\python.exe"
if (Test-Path $venvPy) { $py = $venvPy } else { $py = "python" }

function Step($msg, [scriptblock]$cmd) {
    Write-Host "`n==> $msg"
    & $cmd
    if ($LASTEXITCODE -ne 0) { throw "Falhou: $msg" }
}

Step "ruff check" { & $py -m ruff check . }
Step "ruff format --check" { & $py -m ruff format --check . }
Step "compileall" { & $py -m compileall -q matraca }
Step "mypy" { & $py -m mypy }
Step "import matraca" { & $py -c "import matraca; print('matraca', matraca.__version__)" }
if ($Cov) {
    Step "pytest (cobertura)" { & $py -m pytest --cov=matraca --cov-report=term-missing }
} else {
    Step "pytest" { & $py -m pytest }
}
Write-Host "`nOK: todas as verificações passaram."
