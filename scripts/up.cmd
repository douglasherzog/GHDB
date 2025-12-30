@echo off
setlocal

set "REPOROOT=%~dp0.."
set "ENVFILE=%REPOROOT%\.env"

if not exist "%ENVFILE%" (
  echo Arquivo .env nao encontrado. Rode scripts\env-edit.cmd primeiro.
  exit /b 2
)

docker compose --env-file "%ENVFILE%" up -d --build
