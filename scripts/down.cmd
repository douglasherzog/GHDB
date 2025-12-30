@echo off
setlocal

set "REPOROOT=%~dp0.."
set "ENVFILE=%REPOROOT%\.env"

if exist "%ENVFILE%" (
  docker compose --env-file "%ENVFILE%" down
) else (
  docker compose down
)
