$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot '.env'

if (Test-Path $EnvFile) {
  & docker compose --env-file $EnvFile down
} else {
  & docker compose down
}
