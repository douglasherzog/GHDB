$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvExample = Join-Path $RepoRoot 'env.example'
$EnvFile = Join-Path $RepoRoot '.env'

if (!(Test-Path $EnvFile)) {
  if (Test-Path $EnvExample) {
    Copy-Item -Force $EnvExample $EnvFile
  } else {
    New-Item -ItemType File -Force $EnvFile | Out-Null
  }
}

notepad $EnvFile
