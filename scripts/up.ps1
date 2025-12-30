$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot '.env'

if (!(Test-Path $EnvFile)) {
  Write-Host "Arquivo .env nao encontrado. Rode scripts\\env-edit.ps1 primeiro." -ForegroundColor Yellow
  exit 2
}

& docker compose --env-file $EnvFile up -d --build
